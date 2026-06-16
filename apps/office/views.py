from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.mixins import perm_required
from apps.mp.models import MP
from .forms import OfficeAddressForm, PAStaffFormSet
from .models import ParliamentOfficeAddress


@perm_required
def office_edit(request, mp_pk):
    mp  = get_object_or_404(MP, pk=mp_pk)
    try:
        obj = mp.office_address
    except ParliamentOfficeAddress.DoesNotExist:
        obj = None

    if request.method == 'POST':
        form    = OfficeAddressForm(request.POST, instance=obj)
        formset = PAStaffFormSet(request.POST, instance=obj, prefix='pa_staff')
        if form.is_valid() and formset.is_valid():
            addr = form.save(commit=False)
            addr.mp = mp
            addr.save()
            formset.instance = addr
            formset.save()
            messages.success(request, 'সংসদ অফিস ঠিকানা সংরক্ষিত হয়েছে।')
            return redirect(reverse('mp:mp_detail', args=[mp.pk]) + '?active=tab-general')
    else:
        form    = OfficeAddressForm(instance=obj)
        formset = PAStaffFormSet(instance=obj, prefix='pa_staff')

    return render(request, 'office/office_form.html', {
        'form':     form,
        'formset':  formset,
        'mp':       mp,
        'obj':      obj,
        'title_bn': 'সংসদ অফিস ঠিকানা',
        'title_en': 'Parliament Office Address',
    })
