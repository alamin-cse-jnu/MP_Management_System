from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.mixins import perm_required
from utils.bn_digits import search_q
from .forms import ConstituencyForm, ParliamentForm, SpecialPositionForm
from .models import Constituency, Parliament


# ── PARLIAMENT ────────────────────────────────────────────────────────────────

@perm_required
def parliament_list(request):
    parliaments = Parliament.objects.order_by('-ordinal')
    return render(request, 'parliament/parliament_list.html', {
        'parliaments': parliaments,
    })


@perm_required
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


@perm_required
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


@perm_required
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

@perm_required
def constituency_list(request):
    qs = Constituency.objects.select_related('district', 'district__division')
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


@perm_required
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


@perm_required
def constituency_update(request, pk):
    constituency = get_object_or_404(Constituency, pk=pk)
    # Preserve the list's page/filter state through the edit round-trip.
    next_qs = request.POST.get('next') or request.GET.get('next', '')
    form = ConstituencyForm(request.POST or None, instance=constituency)
    if form.is_valid():
        form.save()
        messages.success(request, f'"{constituency}" আপডেট হয়েছে।')
        list_url = reverse('parliament:constituency_list')
        return redirect(f'{list_url}?{next_qs}' if next_qs else list_url)
    return render(request, 'parliament/constituency_form.html', {
        'form': form,
        'title_bn': 'নির্বাচনী এলাকা সম্পাদনা',
        'title_en':  'Edit Constituency',
        'is_create': False,
        'object': constituency,
        'next_qs': next_qs,
    })


@perm_required
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


# ── PARLIAMENTARY POSITIONS (Speaker / Whip / Leader of the House …) ──────────
# The office a member holds *in the House*, as opposed to a ministry (they run a
# department) or a committee chair (they run a committee). One member can hold
# all three at once, so this is its own record rather than a field on any of
# them. Entry works from here AND from the MP profile tab, the same way ministry
# and committee assignments do (business rule 10).

def _position_qs():
    from apps.mp.models import SpecialPositionHistory
    return SpecialPositionHistory.objects.select_related(
        'mp', 'parliament', 'role').prefetch_related('mp__election_infos__party')


@perm_required
def position_list(request):
    from apps.master.models import SpecialRoleType

    qs = _position_qs()

    parliament_id = request.GET.get('parliament', '')
    role_id       = request.GET.get('role', '')
    status        = request.GET.get('status', 'active')
    q             = request.GET.get('q', '').strip()

    if not parliament_id:
        active_p = Parliament.objects.filter(is_active=True).first()
        if active_p:
            parliament_id = str(active_p.pk)

    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if role_id:
        qs = qs.filter(role_id=role_id)
    if status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status != 'all':
        qs = qs.filter(is_active=True)
    if q:
        # An operator reads ১৫২ off the screen and types it back, so every search
        # over an ID goes through search_q, which ORs both digit spellings.
        qs = qs.filter(search_q(q, ['mp__name_bn', 'mp__name_en', 'mp__mp_id',
                                    'role__name_bn', 'role__name_en', 'go_number']))

    paginator = Paginator(qs, 25)
    page      = paginator.get_page(request.GET.get('page'))

    # Which single-holder offices nobody is sitting in. The page exists to answer
    # "who is the Chief Whip", so an office with no holder is worth naming.
    vacant = []
    if parliament_id and status != 'inactive':
        filled = set(_position_qs().filter(parliament_id=parliament_id, is_active=True)
                     .values_list('role_id', flat=True))
        vacant = [r for r in SpecialRoleType.objects.filter(
            is_active=True, is_unique_per_parliament=True).order_by('ordering')
            if r.pk not in filled]

    return render(request, 'parliament/position_list.html', {
        'page_obj':      page,
        'parliaments':   Parliament.objects.order_by('-ordinal'),
        'roles':         SpecialRoleType.objects.filter(is_active=True).order_by('ordering'),
        'parliament_id': parliament_id,
        'role_id':       role_id,
        'status':        status,
        'q':             q,
        'vacant':        vacant,
        'total_count':   paginator.count,
    })


@perm_required
def position_create(request):
    """From an MP profile (?mp=<pk>) the member is fixed; from the module the
    member is picked on the form."""
    from apps.mp.models import MP

    mp_pk = request.GET.get('mp') or request.POST.get('_mp_pk')
    mp    = get_object_or_404(MP, pk=mp_pk) if mp_pk else None
    active_p = Parliament.objects.filter(is_active=True).first()

    initial = {'parliament': mp.parliament if mp else active_p}
    form = SpecialPositionForm(request.POST or None, initial=initial,
                               mp_preset=bool(mp))
    if mp:
        # The single-holder guard runs during validation, so the MP has to be on
        # the instance before that — not after form.save(commit=False).
        form.instance.mp = mp
    if form.is_valid():
        obj = form.save(commit=False)
        if mp:
            obj.mp = mp
        obj.save()
        messages.success(request, 'সংসদীয় পদের তথ্য সংরক্ষিত হয়েছে।')
        if mp:
            return redirect(reverse('mp:mp_detail', args=[mp.pk]) + '?active=tab-special')
        return redirect('parliament:position_list')

    return render(request, 'parliament/position_form.html', {
        'form':      form,
        'mp':        mp,
        'is_create': True,
        'title_bn':  'নতুন সংসদীয় পদ',
        'title_en':  'New Parliamentary Position',
    })


@perm_required
def position_update(request, pk):
    from apps.mp.models import SpecialPositionHistory

    obj  = get_object_or_404(SpecialPositionHistory, pk=pk)
    form = SpecialPositionForm(request.POST or None, instance=obj, mp_preset=False)
    if form.is_valid():
        form.save()
        messages.success(request, 'সংসদীয় পদের তথ্য আপডেট হয়েছে।')
        if request.GET.get('from_mp'):
            return redirect(reverse('mp:mp_detail', args=[obj.mp_id]) + '?active=tab-special')
        return redirect('parliament:position_list')
    return render(request, 'parliament/position_form.html', {
        'form':      form,
        'mp':        obj.mp,
        'obj':       obj,
        'is_create': False,
        'title_bn':  'সংসদীয় পদ সম্পাদনা',
        'title_en':  'Edit Parliamentary Position',
        'from_mp':   request.GET.get('from_mp', ''),
    })


@perm_required
@require_POST
def position_toggle(request, pk):
    """End or restore a term. Restoring is refused when someone else already
    sits in a single-holder office — the same rule the form enforces."""
    from apps.mp.models import SpecialPositionHistory

    obj = get_object_or_404(SpecialPositionHistory, pk=pk)
    obj.is_active = not obj.is_active
    clash = obj.current_holder_conflict()
    if clash:
        messages.error(request,
                       f'"{obj.role.name_bn}" পদে ইতিমধ্যে {clash.mp.name_bn} বহাল আছেন।')
    else:
        obj.save(update_fields=['is_active'])
        messages.success(request, 'অবস্থা পরিবর্তন হয়েছে।')
    if request.POST.get('from_mp'):
        return redirect(reverse('mp:mp_detail', args=[obj.mp_id]) + '?active=tab-special')
    return redirect('parliament:position_list')


@perm_required
@require_POST
def position_delete(request, pk):
    from apps.mp.models import SpecialPositionHistory

    obj   = get_object_or_404(SpecialPositionHistory, pk=pk)
    mp_pk = obj.mp_id
    obj.delete()
    messages.success(request, 'সংসদীয় পদের তথ্য মুছে ফেলা হয়েছে।')
    if request.POST.get('from_mp'):
        return redirect(reverse('mp:mp_detail', args=[mp_pk]) + '?active=tab-special')
    return redirect('parliament:position_list')
