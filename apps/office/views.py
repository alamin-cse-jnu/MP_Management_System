from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.mp.models import MP
from .forms import OfficeAddressForm
from .models import ParliamentOfficeAddress


@login_required
def office_edit(request, mp_pk):
    mp  = get_object_or_404(MP, pk=mp_pk)
    try:
        obj = mp.office_address
    except ParliamentOfficeAddress.DoesNotExist:
        obj = None

    form = OfficeAddressForm(request.POST or None, instance=obj)
    if form.is_valid():
        addr = form.save(commit=False)
        addr.mp = mp
        addr.save()
        messages.success(request, 'সংসদ অফিস ঠিকানা সংরক্ষিত হয়েছে।')
        return redirect(reverse('mp:mp_detail', args=[mp.pk]) + '?active=tab-general')
    return render(request, 'office/office_form.html', {
        'form':      form,
        'mp':        mp,
        'obj':       obj,
        'title_bn': 'সংসদ অফিস ঠিকানা',
        'title_en':  'Parliament Office Address',
    })
