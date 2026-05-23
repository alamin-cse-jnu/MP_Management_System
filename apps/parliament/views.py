from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ConstituencyForm, ParliamentForm
from .models import Constituency, Parliament


# ── PARLIAMENT ────────────────────────────────────────────────────────────────

@login_required
def parliament_list(request):
    parliaments = Parliament.objects.order_by('-ordinal')
    return render(request, 'parliament/parliament_list.html', {
        'parliaments': parliaments,
    })


@login_required
def parliament_create(request):
    form = ParliamentForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'নতুন সংসদ তৈরি হয়েছে।')
        return redirect('parliament:parliament_list')
    return render(request, 'parliament/parliament_form.html', {
        'form': form,
        'title_bn': 'নতুন সংসদ যোগ করুন',
        'title_en':  'Add New Parliament',
        'is_create': True,
    })


@login_required
def parliament_update(request, pk):
    parliament = get_object_or_404(Parliament, pk=pk)
    form = ParliamentForm(request.POST or None, instance=parliament)
    if form.is_valid():
        form.save()
        messages.success(request, f'"{parliament}" আপডেট হয়েছে।')
        return redirect('parliament:parliament_list')
    return render(request, 'parliament/parliament_form.html', {
        'form': form,
        'title_bn': 'সংসদ সম্পাদনা',
        'title_en':  'Edit Parliament',
        'is_create': False,
        'object': parliament,
    })


@login_required
@require_POST
def parliament_activate(request, pk):
    """Set this parliament as the single active parliament (mutex)."""
    parliament = get_object_or_404(Parliament, pk=pk)
    parliament.is_active = True
    parliament.save()   # save() handles deactivating all others
    messages.success(
        request,
        f'"{parliament}" বর্তমান সক্রিয় সংসদ হিসেবে নির্ধারণ করা হয়েছে।'
    )
    return redirect('parliament:parliament_list')


# ── CONSTITUENCY ──────────────────────────────────────────────────────────────

@login_required
def constituency_list(request):
    qs = Constituency.objects.all()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(display_bn__icontains=q) | Q(display_en__icontains=q)
        )
    status = request.GET.get('status', 'active')
    if status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status == 'all':
        pass
    else:
        qs = qs.filter(is_active=True)
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'parliament/constituency_list.html', {
        'page_obj': page,
        'q': q,
        'status': status,
    })


@login_required
def constituency_create(request):
    form = ConstituencyForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'নতুন নির্বাচনী এলাকা তৈরি হয়েছে।')
        return redirect('parliament:constituency_list')
    return render(request, 'parliament/constituency_form.html', {
        'form': form,
        'title_bn': 'নতুন নির্বাচনী এলাকা',
        'title_en':  'New Constituency',
        'is_create': True,
    })


@login_required
def constituency_update(request, pk):
    constituency = get_object_or_404(Constituency, pk=pk)
    form = ConstituencyForm(request.POST or None, instance=constituency)
    if form.is_valid():
        form.save()
        messages.success(request, f'"{constituency}" আপডেট হয়েছে।')
        return redirect('parliament:constituency_list')
    return render(request, 'parliament/constituency_form.html', {
        'form': form,
        'title_bn': 'নির্বাচনী এলাকা সম্পাদনা',
        'title_en':  'Edit Constituency',
        'is_create': False,
        'object': constituency,
    })


@login_required
@require_POST
def constituency_toggle(request, pk):
    constituency = get_object_or_404(Constituency, pk=pk)
    constituency.is_active = not constituency.is_active
    constituency.save(update_fields=['is_active'])
    label = 'সক্রিয়' if constituency.is_active else 'নিষ্ক্রিয়'
    messages.success(request, f'"{constituency}" {label} করা হয়েছে।')
    return redirect(
        f"{request.build_absolute_uri('?')}?status={request.GET.get('status', 'active')}"
        if False else 'parliament:constituency_list'
    )
