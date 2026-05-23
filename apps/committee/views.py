from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.master.models import CommitteePosition, StandingCommittee
from apps.mp.models import MP
from apps.parliament.models import Parliament
from .forms import CommitteeAssignmentForm
from .models import CommitteeAssignment


@login_required
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


@login_required
def assignment_create(request):
    mp_pk = request.GET.get('mp') or request.POST.get('_mp_pk')
    mp    = get_object_or_404(MP, pk=mp_pk) if mp_pk else None

    active_p = Parliament.objects.filter(is_active=True).first()
    initial  = {}
    if mp:
        initial['parliament'] = mp.parliament
    elif active_p:
        initial['parliament'] = active_p

    form = CommitteeAssignmentForm(request.POST or None, initial=initial, mp_preset=bool(mp))
    if form.is_valid():
        obj = form.save(commit=False)
        if mp:
            obj.mp = mp
        obj.save()
        messages.success(request, 'কমিটির তথ্য সংরক্ষিত হয়েছে।')
        if mp:
            return redirect(reverse('mp:mp_detail', args=[mp.pk]) + '?active=tab-committee')
        return redirect('committee:assignment_list')

    return render(request, 'committee/assignment_form.html', {
        'form':      form,
        'mp':        mp,
        'is_create': True,
        'title_bn':  'নতুন কমিটি নিয়োগ',
        'title_en':  'New Committee Assignment',
    })


@login_required
def assignment_update(request, pk):
    obj  = get_object_or_404(CommitteeAssignment, pk=pk)
    form = CommitteeAssignmentForm(request.POST or None, instance=obj, mp_preset=True)
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


@login_required
@require_POST
def assignment_delete(request, pk):
    obj = get_object_or_404(CommitteeAssignment, pk=pk)
    mp_pk = obj.mp_id
    obj.delete()
    messages.success(request, 'কমিটির তথ্য মুছে ফেলা হয়েছে।')
    if request.POST.get('from_mp'):
        return redirect(reverse('mp:mp_detail', args=[mp_pk]) + '?active=tab-committee')
    return redirect('committee:assignment_list')


@login_required
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
