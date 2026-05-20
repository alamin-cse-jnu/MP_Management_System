from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.master.models import TravelType
from apps.mp.models import MP
from apps.parliament.models import Parliament
from .forms import ForeignTourForm, ParticipantForm, TourCountryForm
from .models import ForeignTour, ForeignTourCountry, ForeignTourParticipant


@login_required
def tour_list(request):
    qs = ForeignTour.objects.select_related(
        'parliament', 'tour_type', 'purpose'
    ).annotate(
        mp_count=Count('participants', distinct=True),
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
            Q(participants__mp__name_en__icontains=q)
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


@login_required
def tour_create(request):
    active_p = Parliament.objects.filter(is_active=True).first()
    initial  = {'parliament': active_p} if active_p else {}
    form = ForeignTourForm(request.POST or None, initial=initial)
    if form.is_valid():
        tour = form.save(commit=False)
        tour.created_by = request.user
        tour.save()
        messages.success(request, 'বিদেশ ভ্রমণ GO তৈরি হয়েছে। এখন সদস্য ও দেশ যোগ করুন।')
        return redirect('travel:tour_detail', pk=tour.pk)
    return render(request, 'travel/tour_form.html', {
        'form':      form,
        'is_create': True,
        'title_bn':  'নতুন বিদেশ ভ্রমণ GO',
    })


@login_required
def tour_detail(request, pk):
    tour             = get_object_or_404(ForeignTour, pk=pk)
    participants     = tour.participants.select_related('mp').all()
    countries        = tour.countries.select_related('country').all()
    participant_form = ParticipantForm(tour=tour)
    country_form     = TourCountryForm(tour=tour)
    return render(request, 'travel/tour_detail.html', {
        'tour':             tour,
        'participants':     participants,
        'countries':        countries,
        'participant_form': participant_form,
        'country_form':     country_form,
    })


@login_required
def tour_update(request, pk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    form = ForeignTourForm(request.POST or None, instance=tour)
    if form.is_valid():
        form.save()
        messages.success(request, 'বিদেশ ভ্রমণ তথ্য আপডেট হয়েছে।')
        return redirect('travel:tour_detail', pk=tour.pk)
    return render(request, 'travel/tour_form.html', {
        'form':      form,
        'tour':      tour,
        'is_create': False,
        'title_bn':  'বিদেশ ভ্রমণ সম্পাদনা',
    })


@login_required
@require_POST
def tour_delete(request, pk):
    get_object_or_404(ForeignTour, pk=pk).delete()
    messages.success(request, 'বিদেশ ভ্রমণ GO মুছে ফেলা হয়েছে।')
    return redirect('travel:tour_list')


@login_required
@require_POST
def participant_add(request, pk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    form = ParticipantForm(request.POST, tour=tour)
    if form.is_valid():
        p = form.save(commit=False)
        p.tour = tour
        p.save()
        messages.success(request, 'সদস্য যোগ করা হয়েছে।')
    else:
        messages.error(request, 'সদস্য যোগ করা যায়নি। তথ্য পরীক্ষা করুন।')
    return redirect('travel:tour_detail', pk=pk)


@login_required
@require_POST
def participant_remove(request, pk, ppk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    get_object_or_404(ForeignTourParticipant, pk=ppk, tour=tour).delete()
    messages.success(request, 'সদস্য বাদ দেওয়া হয়েছে।')
    return redirect('travel:tour_detail', pk=pk)


@login_required
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
    return redirect('travel:tour_detail', pk=pk)


@login_required
@require_POST
def country_remove(request, pk, cpk):
    tour = get_object_or_404(ForeignTour, pk=pk)
    get_object_or_404(ForeignTourCountry, pk=cpk, tour=tour).delete()
    messages.success(request, 'দেশ বাদ দেওয়া হয়েছে।')
    return redirect('travel:tour_detail', pk=pk)
