import os
from io import StringIO

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.mixins import perm_required
from .models import Officer

SUBMENU_URL_NAME = 'officer:officer_list'


def _can_run_sync(user):
    """Trigger sync = superadmin, or can_edit on the Officers submenu."""
    if getattr(user, 'is_superadmin', False):
        return True
    from apps.accounts.models import RolePermission, SubMenu
    if not getattr(user, 'role', None):
        return False
    sm = SubMenu.objects.filter(url_name=SUBMENU_URL_NAME).first()
    if not sm:
        return False
    perm = RolePermission.objects.filter(role=user.role, submenu=sm).first()
    return bool(perm and perm.can_edit)


@perm_required
def officer_list(request):
    """Read-only roster. Retired officers stay visible with their reason — this
    is where you find out why someone can no longer be added to a tour."""
    qs = Officer.objects.all()

    q      = request.GET.get('q', '').strip()
    wing   = request.GET.get('wing', '')
    status = request.GET.get('status', 'active')

    if q:
        qs = qs.filter(
            Q(name_bn__icontains=q) | Q(name_en__icontains=q) |
            Q(prp_id__icontains=q) |
            Q(designation_bn__icontains=q) | Q(designation_en__icontains=q)
        )
    if wing == '__none__':
        qs = qs.filter(wing_bn='', wing_en='')
    elif wing:
        qs = qs.filter(Q(wing_bn=wing) | Q(wing_en=wing))
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'retired':
        qs = qs.filter(is_active=False)

    # Roster order is PRP ID ascending (user's call) — every prp_id is a
    # 9-digit numeric string, so the plain text sort IS the numeric sort.
    # Explicit ordering is also required because annotate() sets group_by,
    # which makes Meta.ordering invisible to the paginator
    # (UnorderedObjectListWarning).
    qs = qs.annotate(tour_count=Count('tour_assignments', distinct=True)
                     ).order_by('prp_id')

    wings = sorted({w for w in Officer.objects.exclude(wing_bn='')
                    .values_list('wing_bn', flat=True)})
    has_unwinged = Officer.objects.filter(wing_bn='', wing_en='').exists()

    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'officer/officer_list.html', {
        'page_obj':      page,
        'q':             q,
        'wing':          wing,
        'status':        status,
        'wings':         wings,
        'has_unwinged':  has_unwinged,
        'active_count':  Officer.objects.selectable().count(),
        'retired_count': Officer.objects.retired().count(),
        'last_synced':   Officer.objects.aggregate(m=Max('last_synced_at'))['m'],
        'can_sync':      _can_run_sync(request.user),
    })


@perm_required
@require_POST
def officer_sync_run(request):
    """Pull the PRP employee roster (class-1 active only) and report the counts."""
    if not _can_run_sync(request.user):
        raise PermissionDenied

    if not (os.environ.get('PRP_API_USER') and os.environ.get('PRP_API_PASS')):
        messages.error(
            request,
            'PRP API ক্রেডেনশিয়াল কনফিগার করা নেই (সার্ভারে PRP_API_USER / '
            'PRP_API_PASS পরিবেশ ভেরিয়েবল সেট করুন)।')
        return redirect('officer:officer_list')

    buf = StringIO()
    try:
        call_command('sync_officers', stdout=buf, stderr=buf)
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f'কর্মকর্তা সিঙ্ক ব্যর্থ হয়েছে: {exc}')
        return redirect('officer:officer_list')

    summary = ' '.join(line for line in buf.getvalue().splitlines()
                       if line.startswith(('created', '[DRY')))
    messages.success(
        request,
        f'কর্মকর্তা সিঙ্ক সম্পন্ন। সক্রিয় (ক্লাস-১) কর্মকর্তা: '
        f'{Officer.objects.selectable().count()} জন। {summary}')
    return redirect('officer:officer_list')
