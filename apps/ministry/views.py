from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.master.models import Ministry, MinisterType
from apps.mp.models import MP
from apps.parliament.models import Parliament
from .forms import MinistryAssignmentForm
from .models import MinistryAssignment


@login_required
def assignment_list(request):
    qs = MinistryAssignment.objects.select_related(
        'mp', 'parliament', 'ministry', 'minister_type'
    )

    parliament_id   = request.GET.get('parliament', '')
    minister_type_id = request.GET.get('minister_type', '')
    q               = request.GET.get('q', '').strip()
    status          = request.GET.get('status', 'active')

    if not parliament_id:
        active_p = Parliament.objects.filter(is_active=True).first()
        if active_p:
            parliament_id = str(active_p.pk)

    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if minister_type_id:
        qs = qs.filter(minister_type_id=minister_type_id)
    if q:
        qs = qs.filter(
            Q(mp__name_bn__icontains=q) | Q(mp__name_en__icontains=q) |
            Q(ministry__name_bn__icontains=q) | Q(ministry__name_en__icontains=q)
        )
    if status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status != 'all':
        qs = qs.filter(is_active=True)

    paginator = Paginator(qs, 25)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'ministry/assignment_list.html', {
        'page_obj':        page,
        'parliaments':     Parliament.objects.order_by('-ordinal'),
        'minister_types':  MinisterType.objects.filter(is_active=True).order_by('ordering'),
        'parliament_id':   parliament_id,
        'minister_type_id': minister_type_id,
        'q':               q,
        'status':          status,
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

    form = MinistryAssignmentForm(request.POST or None, initial=initial)
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


@login_required
def assignment_update(request, pk):
    obj = get_object_or_404(MinistryAssignment, pk=pk)
    form = MinistryAssignmentForm(request.POST or None, instance=obj)
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


@login_required
@require_POST
def assignment_delete(request, pk):
    obj = get_object_or_404(MinistryAssignment, pk=pk)
    mp_pk = obj.mp_id
    obj.delete()
    messages.success(request, 'মন্ত্রণালয়ের তথ্য মুছে ফেলা হয়েছে।')
    if request.POST.get('from_mp'):
        return redirect(reverse('mp:mp_detail', args=[mp_pk]) + '?active=tab-ministry')
    return redirect('ministry:assignment_list')


@login_required
@require_POST
def assignment_toggle(request, pk):
    obj = get_object_or_404(MinistryAssignment, pk=pk)
    mp_pk = obj.mp_id
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active'])
    messages.success(request, 'স্ট্যাটাস পরিবর্তন হয়েছে।')
    if request.POST.get('from_mp'):
        return redirect(reverse('mp:mp_detail', args=[mp_pk]) + '?active=tab-ministry')
    return redirect('ministry:assignment_list')
