import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from apps.accounts.mixins import perm_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    CustomUserCreateForm, CustomUserUpdateForm,
    MenuForm, RoleForm, SubMenuForm,
)
from .models import CustomUser, Menu, Role, RolePermission, SubMenu


# ── ERROR HANDLERS ───────────────────────────────────────────────────────────

def permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)


# ── AUTH ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next') or 'accounts:dashboard'
            return redirect(next_url)
        error = 'ব্যবহারকারী নাম বা পাসওয়ার্ড সঠিক নয়।'
    return render(request, 'accounts/login.html', {'error': error})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@perm_required
def dashboard(request):
    from apps.committee.models import CommitteeAssignment
    from apps.institution.models import InstitutionAssignment
    from apps.ministry.models import MinistryAssignment
    from apps.mp.models import MP, ElectionInfo
    from apps.parliament.models import Parliament
    from apps.travel.models import ForeignTour

    active_parliament = Parliament.objects.filter(is_active=True).first()

    mp_qs = MP.objects.filter(is_active=True)
    if active_parliament:
        mp_qs = mp_qs.filter(parliament=active_parliament)

    total_mps  = mp_qs.count()
    women_mps  = mp_qs.filter(member_type='reserved').count()
    direct_mps = mp_qs.filter(member_type='direct').count()

    min_qs  = MinistryAssignment.objects.filter(is_active=True)
    com_qs  = CommitteeAssignment.objects.filter(is_active=True)
    ins_qs  = InstitutionAssignment.objects.filter(is_active=True)
    tour_qs = ForeignTour.objects.all()
    if active_parliament:
        min_qs  = min_qs.filter(parliament=active_parliament)
        com_qs  = com_qs.filter(parliament=active_parliament)
        ins_qs  = ins_qs.filter(parliament=active_parliament)
        tour_qs = tour_qs.filter(parliament=active_parliament)

    total_ministers   = min_qs.count()
    total_com_assigns = com_qs.count()
    total_institutions = ins_qs.count()
    total_tours       = tour_qs.count()
    with_photo        = mp_qs.exclude(photo='').exclude(photo__isnull=True).count()

    # Party distribution
    party_stats = []
    if active_parliament:
        party_stats = list(
            ElectionInfo.objects
            .filter(parliament=active_parliament, mp__is_active=True, party__isnull=False)
            .values('party__name_bn')
            .annotate(count=Count('id'))
            .order_by('-count')[:12]
        )

    # Division distribution
    division_stats = list(
        mp_qs
        .filter(home_district__division__isnull=False)
        .values('home_district__division__name_bn')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Gender distribution
    gender_stats = list(
        mp_qs.filter(gender__isnull=False)
        .values('gender__name_en', 'gender__name_bn')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Religion distribution
    religion_stats = list(
        mp_qs.filter(religion__isnull=False)
        .values('religion__name_en', 'religion__name_bn')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Times elected distribution
    times_stats = []
    if active_parliament:
        times_stats = list(
            ElectionInfo.objects
            .filter(parliament=active_parliament, mp__is_active=True)
            .values('times_elected')
            .annotate(count=Count('id'))
            .order_by('times_elected')
        )

    # ── Chart JSON data ────────────────────────────────────────────────────────
    # Party chart — top 9 + "Others" bucket
    p_labels = [r['party__name_bn'] or 'দল নেই' for r in party_stats[:9]]
    p_values = [r['count'] for r in party_stats[:9]]
    if len(party_stats) > 9:
        p_labels.append('অন্যান্য')
        p_values.append(sum(r['count'] for r in party_stats[9:]))
    party_chart_data = json.dumps({'labels': p_labels, 'values': p_values}, ensure_ascii=False)

    # Division chart
    division_chart_data = json.dumps({
        'labels': [r['home_district__division__name_bn'] or 'অজ্ঞাত' for r in division_stats],
        'values': [r['count'] for r in division_stats],
    }, ensure_ascii=False)

    # Gender chart
    gender_chart_data = json.dumps({
        'labels': [r['gender__name_bn'] or r['gender__name_en'] or 'অজ্ঞাত' for r in gender_stats],
        'values': [r['count'] for r in gender_stats],
    }, ensure_ascii=False)

    # Religion chart
    religion_chart_data = json.dumps({
        'labels': [r['religion__name_bn'] or r['religion__name_en'] or 'অজ্ঞাত' for r in religion_stats],
        'values': [r['count'] for r in religion_stats],
    }, ensure_ascii=False)

    # Times elected chart
    times_chart_data = json.dumps({
        'labels': [str(r['times_elected']) for r in times_stats],
        'values': [r['count'] for r in times_stats],
    }, ensure_ascii=False)

    # Recent MPs (last 6 added)
    recent_mps = list(
        mp_qs.select_related('home_district')
        .prefetch_related(
            'election_infos__party',
            'election_infos__constituency',
        )
        .order_by('-created_at')[:6]
    )

    # Recent audit activity
    try:
        from apps.reports.models import AuditLog
        recent_activity = list(
            AuditLog.objects.select_related('user').order_by('-timestamp')[:10]
        )
    except Exception:
        recent_activity = []

    return render(request, 'accounts/dashboard.html', {
        'active_parliament':   active_parliament,
        'total_mps':           total_mps,
        'women_mps':           women_mps,
        'direct_mps':          direct_mps,
        'total_ministers':     total_ministers,
        'total_com_assigns':   total_com_assigns,
        'total_institutions':  total_institutions,
        'total_tours':         total_tours,
        'with_photo':          with_photo,
        'party_stats':         party_stats,
        'division_stats':      division_stats,
        'party_chart_data':    party_chart_data,
        'division_chart_data': division_chart_data,
        'gender_chart_data':   gender_chart_data,
        'religion_chart_data': religion_chart_data,
        'times_chart_data':    times_chart_data,
        'recent_mps':          recent_mps,
        'recent_activity':     recent_activity,
    })


@require_POST
def set_language(request):
    try:
        data = json.loads(request.body)
        lang = data.get('language', 'bn')
    except Exception:
        lang = request.POST.get('language', 'bn')

    if lang in ('bn', 'en'):
        request.session['LANGUAGE'] = lang
    return JsonResponse({'ok': True})


# ── ROLES ────────────────────────────────────────────────────────────────────

@perm_required
def role_list(request):
    qs = Role.objects.all()
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(name_bn__icontains=q) | Q(name_en__icontains=q))
    status = request.GET.get('status', 'active')
    if status == 'inactive':
        qs = qs.filter(is_active=False)
    elif status == 'all':
        pass
    else:
        qs = qs.filter(is_active=True)
    qs = qs.order_by('name_bn')
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/role_list.html', {
        'page_obj': page,
        'q': q,
        'status': status,
    })


@perm_required
def role_create(request):
    form = RoleForm(request.POST or None)
    if form.is_valid():
        role = form.save(commit=False)
        role.created_by = request.user
        role.save()
        messages.success(request, f"'{role}' ভূমিকা তৈরি হয়েছে।")
        return redirect('accounts:role_list')
    return render(request, 'accounts/role_form.html', {
        'form': form,
        'title_bn': 'নতুন ভূমিকা',
        'title_en':  'New Role',
        'is_create': True,
    })


@perm_required
def role_update(request, pk):
    role = get_object_or_404(Role, pk=pk)
    form = RoleForm(request.POST or None, instance=role)
    if form.is_valid():
        form.save()
        messages.success(request, f"'{role}' আপডেট হয়েছে।")
        return redirect('accounts:role_list')
    return render(request, 'accounts/role_form.html', {
        'form': form,
        'title_bn': 'ভূমিকা সম্পাদনা',
        'title_en':  'Edit Role',
        'is_create': False,
        'object': role,
    })


@perm_required
@require_POST
def role_toggle(request, pk):
    role = get_object_or_404(Role, pk=pk)
    role.is_active = not role.is_active
    role.save(update_fields=['is_active'])
    label = 'সক্রিয়' if role.is_active else 'নিষ্ক্রিয়'
    messages.success(request, f'"{role}" {label} করা হয়েছে।')
    return redirect('accounts:role_list')


@perm_required
def role_permissions(request, pk):
    role = get_object_or_404(Role, pk=pk)
    menus = Menu.objects.filter(is_active=True).prefetch_related(
        'submenus'
    ).order_by('ordering')

    if request.method == 'POST':
        all_submenus = SubMenu.objects.all()
        for sub in all_submenus:
            perm_data = {
                'can_view':   f'view_{sub.pk}'   in request.POST,
                'can_add':    f'add_{sub.pk}'    in request.POST,
                'can_edit':   f'edit_{sub.pk}'   in request.POST,
                'can_delete': f'delete_{sub.pk}' in request.POST,
                'can_export': f'export_{sub.pk}' in request.POST,
            }
            RolePermission.objects.update_or_create(
                role=role, submenu=sub, defaults=perm_data
            )
        messages.success(request, f'"{role}" ভূমিকার অনুমতি সংরক্ষণ হয়েছে।')
        return redirect('accounts:role_list')

    perms_qs = RolePermission.objects.filter(role=role)
    perm_sets = {
        'view':   set(p.submenu_id for p in perms_qs if p.can_view),
        'add':    set(p.submenu_id for p in perms_qs if p.can_add),
        'edit':   set(p.submenu_id for p in perms_qs if p.can_edit),
        'delete': set(p.submenu_id for p in perms_qs if p.can_delete),
        'export': set(p.submenu_id for p in perms_qs if p.can_export),
    }
    return render(request, 'accounts/role_permissions.html', {
        'role': role,
        'menus': menus,
        'perm_sets': perm_sets,
    })


# ── USERS ────────────────────────────────────────────────────────────────────

@perm_required
def user_list(request):
    qs = CustomUser.objects.select_related('role').order_by('full_name_bn', 'username')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(full_name_bn__icontains=q) |
            Q(full_name_en__icontains=q)
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
    return render(request, 'accounts/user_list.html', {
        'page_obj': page,
        'q': q,
        'status': status,
    })


@perm_required
def user_create(request):
    form = CustomUserCreateForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.created_by = request.user
        user.save()
        messages.success(request, f"'{user.username}' ব্যবহারকারী তৈরি হয়েছে।")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title_bn': 'নতুন ব্যবহারকারী',
        'title_en':  'New User',
        'is_create': True,
    })


@perm_required
def user_update(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    form = CustomUserUpdateForm(request.POST or None, instance=user_obj)
    if form.is_valid():
        form.save()
        messages.success(request, f"'{user_obj.username}' আপডেট হয়েছে।")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title_bn': 'ব্যবহারকারী সম্পাদনা',
        'title_en':  'Edit User',
        'is_create': False,
        'object': user_obj,
    })


@perm_required
@require_POST
def user_toggle(request, pk):
    user_obj = get_object_or_404(CustomUser, pk=pk)
    if user_obj == request.user:
        messages.error(request, 'নিজের অ্যাকাউন্ট নিষ্ক্রিয় করা যাবে না।')
        return redirect('accounts:user_list')
    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=['is_active'])
    label = 'সক্রিয়' if user_obj.is_active else 'নিষ্ক্রিয়'
    messages.success(request, f'"{user_obj.username}" {label} করা হয়েছে।')
    return redirect('accounts:user_list')


# ── MENUS ────────────────────────────────────────────────────────────────────

@perm_required
def menu_list(request):
    menus = Menu.objects.prefetch_related('submenus').order_by('ordering', 'name_bn')
    return render(request, 'accounts/menu_list.html', {'menus': menus})


@perm_required
def menu_create(request):
    form = MenuForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'মেনু তৈরি হয়েছে।')
        return redirect('accounts:menu_list')
    return render(request, 'accounts/menu_form.html', {
        'form': form,
        'title_bn': 'নতুন মেনু',
        'title_en':  'New Menu',
        'is_create': True,
    })


@perm_required
def menu_update(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    form = MenuForm(request.POST or None, instance=menu)
    if form.is_valid():
        form.save()
        messages.success(request, f"'{menu}' আপডেট হয়েছে।")
        return redirect('accounts:menu_list')
    return render(request, 'accounts/menu_form.html', {
        'form': form,
        'title_bn': 'মেনু সম্পাদনা',
        'title_en':  'Edit Menu',
        'is_create': False,
        'object': menu,
    })


@perm_required
@require_POST
def menu_toggle(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    menu.is_active = not menu.is_active
    menu.save(update_fields=['is_active'])
    label = 'সক্রিয়' if menu.is_active else 'নিষ্ক্রিয়'
    messages.success(request, f'"{menu}" {label} করা হয়েছে।')
    return redirect('accounts:menu_list')


# ── SUBMENUS ─────────────────────────────────────────────────────────────────

@perm_required
def submenu_create(request):
    initial = {}
    menu_pk = request.GET.get('menu')
    if menu_pk:
        initial['menu'] = menu_pk
    form = SubMenuForm(request.POST or None, initial=initial)
    if form.is_valid():
        form.save()
        messages.success(request, 'সাব-মেনু তৈরি হয়েছে।')
        return redirect('accounts:menu_list')
    return render(request, 'accounts/submenu_form.html', {
        'form': form,
        'title_bn': 'নতুন সাব-মেনু',
        'title_en':  'New Sub-menu',
        'is_create': True,
    })


@perm_required
def submenu_update(request, pk):
    sub = get_object_or_404(SubMenu, pk=pk)
    form = SubMenuForm(request.POST or None, instance=sub)
    if form.is_valid():
        form.save()
        messages.success(request, f"'{sub}' আপডেট হয়েছে।")
        return redirect('accounts:menu_list')
    return render(request, 'accounts/submenu_form.html', {
        'form': form,
        'title_bn': 'সাব-মেনু সম্পাদনা',
        'title_en':  'Edit Sub-menu',
        'is_create': False,
        'object': sub,
    })


@perm_required
@require_POST
def submenu_toggle(request, pk):
    sub = get_object_or_404(SubMenu, pk=pk)
    sub.is_active = not sub.is_active
    sub.save(update_fields=['is_active'])
    label = 'সক্রিয়' if sub.is_active else 'নিষ্ক্রিয়'
    messages.success(request, f'"{sub}" {label} করা হয়েছে।')
    return redirect('accounts:menu_list')
