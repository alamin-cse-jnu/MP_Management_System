from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.master.models import TravelType
from apps.mp.models import MP
from apps.parliament.models import Parliament
from apps.accounts.mixins import perm_required
from .forms import (CountryFormSet, ForeignTourForm, OfficerForm, OfficerFormSet,
                    ParticipantBulkForm, TourCountryForm, TourParticipantsForm)
from .models import (ForeignTour, ForeignTourCountry, ForeignTourOfficer,
                     ForeignTourParticipant)


@perm_required
def tour_list(request):
    qs = ForeignTour.objects.select_related(
        'parliament', 'tour_type', 'purpose'
    ).annotate(
        mp_count=Count('participants', distinct=True),
        officer_count=Count('officers', distinct=True),
        country_count=Count('countries', distinct=True),
    )

    parliament_id  = request.GET.get('parliament', '')
    tour_type_id   = request.GET.get('tour_type', '')
    q              = request.GET.get('q', '').strip()

    if not parliament_id:
        active_p = Parliament.objects.filter(is_active=True).first()
        if active_p:
            parliament_id = str(active_p.pk)

    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    if tour_type_id:
        qs = qs.filter(tour_type_id=tour_type_id)
    if q:
        qs = qs.filter(
            Q(go_number__icontains=q) |
            Q(participants__mp__name_bn__icontains=q) |
            Q(participants__mp__name_en__icontains=q) |
            Q(officers__name__icontains=q) |
            Q(officers__officer_id__icontains=q)
        ).distinct()

    paginator = Paginator(qs, 25)
    page      = paginator.get_page(request.GET.get('page'))

    return render(request, 'travel/tour_list.html', {
        'page_obj':     page,
        'parliaments':  Parliament.objects.order_by('-ordinal'),
        'tour_types':   TravelType.objects.filter(is_active=True).order_by('ordering'),
        'parliament_id': parliament_id,
        'tour_type_id': tour_type_id,
        'q':            q,
    })


def _tour_form(request, tour):
    """Single-page create/edit: tour header + countries + officers + participants,
    all saved in one submit (Phase 17.10)."""
    is_create = tour is None

    active_p = Parliament.objects.filter(is_active=True).first()
    initial  = {'parliament': active_p} if (is_create and active_p) else {}

    form       = ForeignTourForm(request.POST or None, request.FILES or None,
                                 instance=tour, initial=initial)
    country_fs = CountryFormSet(request.POST or None, instance=tour, prefix='country')
    officer_fs = OfficerFormSet(request.POST or None, instance=tour, prefix='officer')

    part_initial = {}
    if tour is not None:
        part_initial['mps'] = list(tour.participants.values_list('mp_id', flat=True))
    part_form = TourParticipantsForm(request.POST or None, initial=part_initial)

    if request.method == 'POST':
        if form.is_valid() and country_fs.is_valid() and officer_fs.is_valid() and part_form.is_valid():
            tour = form.save(commit=False)
            if is_create:
                tour.created_by = request.user
            tour.save()

            country_fs.instance = tour
            country_fs.save()
            officer_fs.instance = tour
            officer_fs.save()

            # Reconcile participants: add newly-checked MPs, drop unchecked ones.
            selected = {m.pk for m in part_form.cleaned_data['mps']}
            existing = set(tour.participants.values_list('mp_id', flat=True))
            for mp_pk in selected - existing:
                ForeignTourParticipant.objects.get_or_create(tour=tour, mp_id=mp_pk)
            ForeignTourParticipant.objects.filter(tour=tour).exclude(
                mp_id__in=selected).delete()

            messages.success(
                request,
                'বিদেশ ভ্রমণ GO তৈরি হয়েছে।' if is_create else 'বিদেশ ভ্রমণ তথ্য আপডেট হয়েছে।')
            return redirect('travel:tour_detail', pk=tour.pk)
        messages.error(request, 'তথ্য সংরক্ষণ করা যায়নি — নিচের ত্রুটিগুলো ঠিক করুন।')

    return render(request, 'travel/tour_form.html', {
        'form':       form,
        'country_fs': country_fs,
        'officer_fs': officer_fs,
        'part_form':  part_form,
        'tour':       tour,
        'is_create':  is_create,
        'title_bn':   'নতুন বিদেশ ভ্রমণ GO' if is_create else 'বিদেশ ভ্রমণ সম্পাদনা',
        'title_en':   'New Foreign Tour GO' if is_create else 'Edit Foreign Tour',
    })


@perm_required
def tour_create(request):
    return _tour_form(request, tour=None)


@perm_required
def tour_detail(request, pk):
    """Read-only view of a tour. Editing happens on the manage/edit page."""
    tour         = get_object_or_404(ForeignTour, pk=pk)
    participants = tour.participants.select_related('mp').all()
    officers     = tour.officers.all()
    countries    = tour.countries.select_related('country').all()
    ctx = {
        'tour':         tour,
        'participants': participants,
        'officers':     officers,
        'countries':    countries,
    }
    if request.GET.get('format') == 'print':
        return render(request, 'travel/print/tour_detail.html', ctx)
    return render(request, 'travel/tour_detail.html', ctx)


@perm_required
def tour_update(request, pk):
    """Single-page edit — same form as create."""
    tour = get_object_or_404(ForeignTour, pk=pk)
    return _tour_form(request, tour=tour)


@perm_required
@require_POST
def tour_delete(request, pk):
    get_object_or_404(ForeignTour, pk=pk).delete()
    messages.success(request, 'বিদেশ ভ্রমণ GO মুছে ফেলা হয়েছে।')
    return redirect('travel:tour_list')


@perm_required
@require_POST
def participant_add(request, pk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    form = ParticipantBulkForm(request.POST, tour=tour)
    if form.is_valid():
        mps = form.cleaned_data['mps']
        for mp_obj in mps:
            ForeignTourParticipant.objects.get_or_create(tour=tour, mp=mp_obj)
        messages.success(request, f'{len(mps)} জন সদস্য যোগ করা হয়েছে।')
    else:
        messages.error(request, 'সদস্য যোগ করা যায়নি। তথ্য পরীক্ষা করুন।')
    return redirect('travel:tour_update', pk=pk)


@perm_required
@require_POST
def participant_remove(request, pk, ppk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    get_object_or_404(ForeignTourParticipant, pk=ppk, tour=tour).delete()
    messages.success(request, 'সদস্য বাদ দেওয়া হয়েছে।')
    return redirect('travel:tour_update', pk=pk)


@perm_required
@require_POST
def officer_add(request, pk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    form = OfficerForm(request.POST)
    if form.is_valid():
        officer = form.save(commit=False)
        officer.tour = tour
        officer.save()
        messages.success(request, 'কর্মকর্তা যোগ করা হয়েছে।')
    else:
        messages.error(request, 'কর্মকর্তা যোগ করা যায়নি। তথ্য পরীক্ষা করুন।')
    return redirect('travel:tour_update', pk=pk)


@perm_required
@require_POST
def officer_remove(request, pk, opk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    get_object_or_404(ForeignTourOfficer, pk=opk, tour=tour).delete()
    messages.success(request, 'কর্মকর্তা বাদ দেওয়া হয়েছে।')
    return redirect('travel:tour_update', pk=pk)


@perm_required
@require_POST
def country_add(request, pk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    form = TourCountryForm(request.POST, tour=tour)
    if form.is_valid():
        c = form.save(commit=False)
        c.tour = tour
        c.save()
        messages.success(request, 'দেশ যোগ করা হয়েছে।')
    else:
        messages.error(request, 'দেশ যোগ করা যায়নি। তথ্য পরীক্ষা করুন।')
    return redirect('travel:tour_update', pk=pk)


@perm_required
@require_POST
def country_remove(request, pk, cpk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    get_object_or_404(ForeignTourCountry, pk=cpk, tour=tour).delete()
    messages.success(request, 'দেশ বাদ দেওয়া হয়েছে।')
    return redirect('travel:tour_update', pk=pk)
