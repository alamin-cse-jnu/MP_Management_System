from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.master.models import GovernmentInstitution, InstitutionRole
from apps.mp.form_fields import MPChoiceField
from apps.mp.models import MP
from apps.parliament.models import Parliament
from apps.accounts.mixins import perm_required
from .forms import InstitutionAssignmentForm, InstitutionBulkAssignForm
from .models import InstitutionAssignment


@perm_required
def assignment_list(request):
    qs = InstitutionAssignment.objects.select_related(
        'mp', 'parliament', 'institution', 'role'
    )

    parliament_id  = request.GET.get('parliament', '')
    institution_id = request.GET.get('institution', '')
    mp_id          = request.GET.get('mp', '')
    q              = request.GET.get('q', '').strip()
    status         = request.GET.get('status', 'active')

    if not parliament_id:
        active_p = Parliament.objects.filter(is_active=True).first()
        if active_p:
            parliament_id = str(active_p.pk)

    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if institution_id:
        qs = qs.filter(institution_id=institution_id)
    if mp_id:
        qs = qs.filter(mp_id=mp_id)
    if q:
        qs = qs.filter(
            Q(mp__name_bn__icontains=q) | Q(mp__name_en__icontains=q) |
            Q(institution__name_bn__icontains=q) | Q(institution__name_en__icontains=q)
        )
    if status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status != 'all':
        qs = qs.filter(is_active=True)

    paginator = Paginator(qs, 25)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'institution/assignment_list.html', {
        'page_obj':      page,
        'parliaments':   Parliament.objects.order_by('-ordinal'),
        'institutions':  GovernmentInstitution.objects.filter(is_active=True).order_by('name_bn'),
        'mp_filter_field': MPChoiceField(required=False, empty_label='-- সব সদস্য / All MPs --'),
        'parliament_id': parliament_id,
        'institution_id': institution_id,
        'mp_id':         mp_id,
        'q':             q,
        'status':        status,
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

    # From an MP profile → single MP preset. From the module → bulk multi-MP.
    if mp:
        form = InstitutionAssignmentForm(request.POST or None, request.FILES or None,
                                         initial=initial, mp_preset=True)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mp = mp
            obj.save()
            messages.success(request, 'প্রতিষ্ঠান নিয়োগ সংরক্ষিত হয়েছে।')
            return redirect(reverse('mp:mp_detail', args=[mp.pk]) + '?active=tab-general')
    else:
        form = InstitutionBulkAssignForm(request.POST or None, request.FILES or None, initial=initial)
        if form.is_valid():
            n = form.save_rows()
            messages.success(request, f'{n} জন সদস্যের প্রতিষ্ঠান নিয়োগ সংরক্ষিত হয়েছে।')
            return redirect('institution:assignment_list')

    return render(request, 'institution/assignment_form.html', {
        'form':      form,
        'mp':        mp,
        'is_create': True,
        'is_bulk':   mp is None,
        'title_bn':  'নতুন প্রতিষ্ঠান নিয়োগ',
        'title_en':  'New Institution Assignment',
    })


@perm_required
def assignment_update(request, pk):
    obj  = get_object_or_404(InstitutionAssignment, pk=pk)
    # Edit loads everything including the MP (selectable/searchable).
    form = InstitutionAssignmentForm(request.POST or None, request.FILES or None,
                                     instance=obj, mp_preset=False)
    if form.is_valid():
        form.save()
        messages.success(request, 'প্রতিষ্ঠান নিয়োগ আপডেট হয়েছে।')
        return redirect('institution:assignment_list')
    return render(request, 'institution/assignment_form.html', {
        'form':      form,
        'obj':       obj,
        'is_create': False,
        'title_bn':  'প্রতিষ্ঠান নিয়োগ সম্পাদনা',
        'title_en':  'Edit Institution Assignment',
    })


@perm_required
@require_POST
def assignment_delete(request, pk):
    get_object_or_404(InstitutionAssignment, pk=pk).delete()
    messages.success(request, 'প্রতিষ্ঠান নিয়োগ মুছে ফেলা হয়েছে।')
    return redirect('institution:assignment_list')


@perm_required
@require_POST
def assignment_toggle(request, pk):
    obj = get_object_or_404(InstitutionAssignment, pk=pk)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active'])
    messages.success(request, 'স্ট্যাটাস পরিবর্তন হয়েছে।')
    return redirect('institution:assignment_list')
