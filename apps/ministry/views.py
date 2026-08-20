from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Min, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.master.models import Ministry, MinisterType
from apps.mp.models import MP
from apps.parliament.models import Parliament
from apps.accounts.mixins import perm_required
from .forms import MinistryAssignmentForm
from .models import MinistryAssignment


@perm_required
def assignment_list(request):
    qs = MinistryAssignment.objects.select_related(
        'mp', 'parliament', 'ministry', 'minister_type'
    )

    parliament_id   = request.GET.get('parliament', '')
    minister_type_id = request.GET.get('minister_type', '')
    member_type     = request.GET.get('member_type', '')
    q               = request.GET.get('q', '').strip()

    if not parliament_id:
        active_p = Parliament.objects.filter(is_active=True).first()
        if active_p:
            parliament_id = str(active_p.pk)

    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if minister_type_id:
        qs = qs.filter(minister_type_id=minister_type_id)
    # The cabinet contains both seat-holding MPs and technocrat ministers;
    # show everyone by default, filterable either way.
    if member_type == 'technocrat':
        qs = qs.filter(mp__member_type='technocrat')
    elif member_type == 'mp':
        qs = qs.exclude(mp__member_type='technocrat')
    if q:
        qs = qs.filter(
            Q(mp__name_bn__icontains=q) | Q(mp__name_en__icontains=q) |
            Q(ministry__name_bn__icontains=q) | Q(ministry__name_en__icontains=q)
        )

    # ── One row per MINISTER, not per assignment ─────────────────────────────
    # 13 ministers hold several ministries (up to 3). Paginating raw assignments
    # scattered a person's rows across pages — e.g. one minister's 3 ministries
    # landed on pages 1, 2 and 3 — so the list read as if only one ministry was
    # recorded. Group by MP and paginate the GROUPS, so a minister's ministries
    # are always shown together and can never straddle a page boundary.
    #
    # order_by() first: the model's Meta.ordering would otherwise be folded into
    # the GROUP BY and break the grouping.
    groups = (
        qs.order_by()
          .values('mp')
          .annotate(rank=Min('minister_type__ordering'), sort_name=Min('mp__name_bn'))
          .order_by('rank', 'sort_name')
    )

    paginator = Paginator(groups, 25)
    page      = paginator.get_page(request.GET.get('page'))

    # Pull this page's assignments in one query; qs keeps Meta.ordering
    # (minister_type rank, then ministry name) within each minister.
    page_mp_ids = [g['mp'] for g in page]
    by_mp = {}
    for a in qs.filter(mp_id__in=page_mp_ids):
        by_mp.setdefault(a.mp_id, []).append(a)

    mps = {m.pk: m for m in MP.objects.filter(pk__in=page_mp_ids)}
    rows = [
        {'mp': mps[mp_id], 'assignments': by_mp.get(mp_id, [])}
        for mp_id in page_mp_ids if mp_id in mps
    ]

    return render(request, 'ministry/assignment_list.html', {
        'page_obj':        page,
        'rows':            rows,
        'assignment_count': qs.count(),
        'parliaments':     Parliament.objects.order_by('-ordinal'),
        'minister_types':  MinisterType.objects.filter(is_active=True).order_by('ordering'),
        'parliament_id':   parliament_id,
        'minister_type_id': minister_type_id,
        'member_type':     member_type,
        'q':               q,
    })


@perm_required
def assignment_create(request):
    mp_pk = request.GET.get('mp') or request.POST.get('_mp_pk')
    mp    = get_object_or_404(MP, pk=mp_pk) if mp_pk else None

    active_p = Parliament.objects.filter(is_active=True).first()
    initial  = {}
    if mp:
        initial['parliament'] = mp.parliament
    elif active_p:
        initial['parliament'] = active_p

    form = MinistryAssignmentForm(request.POST or None, request.FILES or None,
                                  initial=initial, mp_preset=bool(mp))
    if form.is_valid():
        obj = form.save(commit=False)
        if mp:
            obj.mp = mp
        obj.save()
        messages.success(request, 'মন্ত্রণালয়ের তথ্য সংরক্ষিত হয়েছে।')
        if mp:
            return redirect(reverse('mp:mp_detail', args=[mp.pk]) + '?active=tab-ministry')
        return redirect('ministry:assignment_list')

    return render(request, 'ministry/assignment_form.html', {
        'form':      form,
        'mp':        mp,
        'is_create': True,
        'title_bn':  'নতুন মন্ত্রণালয় নিয়োগ',
        'title_en':  'New Ministry Assignment',
    })


@perm_required
def assignment_update(request, pk):
    obj = get_object_or_404(MinistryAssignment, pk=pk)
    # Edit loads everything including the MP (selectable/searchable), per spec.
    form = MinistryAssignmentForm(request.POST or None, request.FILES or None,
                                  instance=obj, mp_preset=False)
    if form.is_valid():
        form.save()
        messages.success(request, 'মন্ত্রণালয়ের তথ্য আপডেট হয়েছে।')
        if request.GET.get('from_mp'):
            return redirect(reverse('mp:mp_detail', args=[obj.mp_id]) + '?active=tab-ministry')
        return redirect('ministry:assignment_list')
    return render(request, 'ministry/assignment_form.html', {
        'form':      form,
        'mp':        obj.mp,
        'obj':       obj,
        'is_create': False,
        'title_bn':  'মন্ত্রণালয় নিয়োগ সম্পাদনা',
        'title_en':  'Edit Ministry Assignment',
        'from_mp':   request.GET.get('from_mp', ''),
    })


@perm_required
@require_POST
def assignment_delete(request, pk):
    obj = get_object_or_404(MinistryAssignment, pk=pk)
    mp_pk = obj.mp_id
    obj.delete()
    messages.success(request, 'মন্ত্রণালয়ের তথ্য মুছে ফেলা হয়েছে।')
    if request.POST.get('from_mp'):
        return redirect(reverse('mp:mp_detail', args=[mp_pk]) + '?active=tab-ministry')
    return redirect('ministry:assignment_list')
