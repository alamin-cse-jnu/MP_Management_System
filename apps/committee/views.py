from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.master.models import CommitteePosition, StandingCommittee
from apps.mp.form_fields import MPChoiceField
from apps.mp.models import MP
from apps.parliament.models import Parliament
from apps.accounts.mixins import perm_required
from .forms import CommitteeAssignmentForm, CommitteeBulkStep1Form
from .models import CommitteeAssignment

_SESSION_KEY = 'committee_bulk'


@perm_required
def assignment_list(request):
    qs = CommitteeAssignment.objects.select_related(
        'mp', 'parliament', 'committee', 'position'
    )

    parliament_id = request.GET.get('parliament', '')
    committee_id  = request.GET.get('committee', '')
    position_id   = request.GET.get('position', '')
    q             = request.GET.get('q', '').strip()
    status        = request.GET.get('status', 'active')

    if not parliament_id:
        active_p = Parliament.objects.filter(is_active=True).first()
        if active_p:
            parliament_id = str(active_p.pk)

    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if committee_id:
        qs = qs.filter(committee_id=committee_id)
    if position_id:
        qs = qs.filter(position_id=position_id)
    if q:
        qs = qs.filter(
            Q(mp__name_bn__icontains=q) | Q(mp__name_en__icontains=q) |
            Q(committee__name_bn__icontains=q) | Q(committee__name_en__icontains=q)
        )
    if status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status != 'all':
        qs = qs.filter(is_active=True)

    paginator = Paginator(qs, 25)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'committee/assignment_list.html', {
        'page_obj':     page,
        'parliaments':  Parliament.objects.order_by('-ordinal'),
        'committees':   StandingCommittee.objects.filter(is_active=True).order_by('name_bn'),
        'positions':    CommitteePosition.objects.filter(is_active=True).order_by('ordering'),
        'parliament_id': parliament_id,
        'committee_id': committee_id,
        'position_id':  position_id,
        'q':            q,
        'status':       status,
    })


@perm_required
def assignment_create(request):
    """From an MP profile → single-MP form. From the module → bulk step 1."""
    mp_pk = request.GET.get('mp') or request.POST.get('_mp_pk')
    mp    = get_object_or_404(MP, pk=mp_pk) if mp_pk else None

    active_p = Parliament.objects.filter(is_active=True).first()

    # ── From MP profile: single assignment (MP fixed) ──
    if mp:
        initial = {'parliament': mp.parliament}
        form = CommitteeAssignmentForm(request.POST or None, request.FILES or None,
                                       initial=initial, mp_preset=True)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mp = mp
            obj.save()
            messages.success(request, 'কমিটির তথ্য সংরক্ষিত হয়েছে।')
            return redirect(reverse('mp:mp_detail', args=[mp.pk]) + '?active=tab-committee')
        return render(request, 'committee/assignment_form.html', {
            'form':      form,
            'mp':        mp,
            'is_create': True,
            'title_bn':  'নতুন কমিটি নিয়োগ',
            'title_en':  'New Committee Assignment',
        })

    # ── From module: step 1 (committee + count + MPs) → step 2 (positions) ──
    initial = {'parliament': active_p} if active_p else {}
    form = CommitteeBulkStep1Form(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        cd = form.cleaned_data
        request.session[_SESSION_KEY] = {
            'parliament': cd['parliament'].pk,
            'committee':  cd['committee'].pk,
            'mp_ids':     [m.pk for m in cd['mps']],
            'start_date': cd['start_date'].isoformat(),
            'end_date':   cd['end_date'].isoformat() if cd['end_date'] else '',
            'go_number':  cd['go_number'],
            'go_date':    cd['go_date'].isoformat() if cd['go_date'] else '',
        }
        return redirect('committee:assign_positions')

    return render(request, 'committee/assignment_step1.html', {
        'form':      form,
        'is_create': True,
        'title_bn':  'নতুন কমিটি নিয়োগ (ধাপ ১/২)',
        'title_en':  'New Committee Assignment (Step 1 of 2)',
    })


@perm_required
def assign_positions(request):
    """Step 2: choose a position (পদবী) for each selected MP, then save N rows."""
    data = request.session.get(_SESSION_KEY)
    if not data:
        messages.error(request, 'আগে কমিটি ও সদস্য নির্বাচন করুন।')
        return redirect('committee:assignment_create')

    committee  = get_object_or_404(StandingCommittee, pk=data['committee'])
    parliament = get_object_or_404(Parliament, pk=data['parliament'])
    mps        = list(MPChoiceField.annotated_queryset().filter(pk__in=data['mp_ids']))
    positions  = CommitteePosition.objects.filter(is_active=True).order_by('ordering')

    if request.method == 'POST':
        # Validate every MP has a position selected.
        chosen = {}
        missing = False
        for m in mps:
            pos_id = request.POST.get(f'pos_{m.pk}')
            if not pos_id:
                missing = True
                break
            chosen[m.pk] = pos_id
        if missing:
            messages.error(request, 'প্রতিটি সদস্যের জন্য পদবী নির্বাচন করুন।')
        else:
            go_file = request.FILES.get('go_file')
            file_name = None
            for i, m in enumerate(mps):
                obj = CommitteeAssignment(
                    mp=m, parliament=parliament, committee=committee,
                    position_id=chosen[m.pk],
                    start_date=data['start_date'] or None,
                    end_date=data['end_date'] or None,
                    go_number=data['go_number'],
                    go_date=data['go_date'] or None,
                )
                if i == 0:
                    obj.go_file = go_file
                    obj.save()
                    file_name = obj.go_file.name if obj.go_file else None
                else:
                    if file_name:
                        obj.go_file = file_name
                    obj.save()
            del request.session[_SESSION_KEY]
            messages.success(request, f'{len(mps)} জন সদস্যের কমিটি নিয়োগ সংরক্ষিত হয়েছে।')
            return redirect('committee:assignment_list')

    # Build the position dropdown choices once (bilingual labels in template).
    rows = []
    for m in mps:
        rows.append({'mp': m, 'label': MPChoiceField().label_from_instance(m)})

    return render(request, 'committee/assignment_step2.html', {
        'committee':  committee,
        'parliament': parliament,
        'rows':       rows,
        'positions':  positions,
        'go_accept':  '.pdf,.jpg,.jpeg,.png',
        'title_bn':   'কমিটি নিয়োগ — পদবী নির্ধারণ (ধাপ ২/২)',
        'title_en':   'Committee Assignment — Positions (Step 2 of 2)',
    })


@perm_required
def assignment_update(request, pk):
    obj  = get_object_or_404(CommitteeAssignment, pk=pk)
    form = CommitteeAssignmentForm(request.POST or None, request.FILES or None,
                                   instance=obj, mp_preset=False)
    if form.is_valid():
        form.save()
        messages.success(request, 'কমিটির তথ্য আপডেট হয়েছে।')
        if request.GET.get('from_mp'):
            return redirect(reverse('mp:mp_detail', args=[obj.mp_id]) + '?active=tab-committee')
        return redirect('committee:assignment_list')
    return render(request, 'committee/assignment_form.html', {
        'form':      form,
        'mp':        obj.mp,
        'obj':       obj,
        'is_create': False,
        'title_bn':  'কমিটি নিয়োগ সম্পাদনা',
        'title_en':  'Edit Committee Assignment',
        'from_mp':   request.GET.get('from_mp', ''),
    })


@perm_required
@require_POST
def assignment_delete(request, pk):
    obj = get_object_or_404(CommitteeAssignment, pk=pk)
    mp_pk = obj.mp_id
    obj.delete()
    messages.success(request, 'কমিটির তথ্য মুছে ফেলা হয়েছে।')
    if request.POST.get('from_mp'):
        return redirect(reverse('mp:mp_detail', args=[mp_pk]) + '?active=tab-committee')
    return redirect('committee:assignment_list')


@perm_required
@require_POST
def assignment_toggle(request, pk):
    obj = get_object_or_404(CommitteeAssignment, pk=pk)
    mp_pk = obj.mp_id
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active'])
    messages.success(request, 'স্ট্যাটাস পরিবর্তন হয়েছে।')
    if request.POST.get('from_mp'):
        return redirect(reverse('mp:mp_detail', args=[mp_pk]) + '?active=tab-committee')
    return redirect('committee:assignment_list')
