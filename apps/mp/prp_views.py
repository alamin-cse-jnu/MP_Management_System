"""
PRP form tracking — the paper form an MP submits, from which this system's
records are typed.

Two independent facts are tracked and never collapsed into one status field
(see MPQuerySet / MP.prp_status):

  * ``prp_form_submitted`` — the office has the hardcopy. Only a human knows
    this, so it is a tick.
  * ``prp_form_file``      — a scan is in the system. Derived from the file,
    never typed.

That is what lets the office tell "form never came" from "form came but nobody
has scanned it yet", which is the list this module exists to produce.

The scan itself lives outside MEDIA_ROOT (see utils/prp_files.py) because nginx
serves that directory with no authentication and one page of a PRP form carries
the MP's NID, passport and bank account numbers together. ``prp_form_file``
below is the only route to those bytes.
"""
import os

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.accounts.mixins import _run_permission_check, perm_required
from apps.parliament.models import Parliament
from utils.bn_digits import search_q
from utils.prp_files import PRP_FILE_ACCEPT, PRP_FILE_MAX_MB, prp_content_type

from .forms import PRPFormUploadForm
from .models import MP, ElectionInfo

#: status key → the MPQuerySet method that narrows to it. Shared with the
#: report so the tracking page and the report can never disagree about what
#: "submitted but not uploaded" means.
PRP_STATUS_FILTERS = {
    'complete':        lambda qs: qs.prp_complete(),
    'awaiting_upload': lambda qs: qs.prp_awaiting_upload(),
    'not_submitted':   lambda qs: qs.prp_not_submitted(),
    'unticked':        lambda qs: qs.prp_unticked(),
    'uploaded':        lambda qs: qs.prp_uploaded(),
}


def _safe_next(request, fallback):
    """Return the posted `next` URL when it points back into this site."""
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    if nxt and url_has_allowed_host_and_scheme(
            nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return nxt
    return fallback


# ── WRITE ─────────────────────────────────────────────────────────────────────

@perm_required
@require_POST
def prp_form_edit(request, pk):
    """Save the hardcopy tick and/or a new scan.

    An empty file input leaves the stored scan alone. The tick and the
    attachment share one form, so saving one must never silently drop the
    other; removing a scan is the separate, explicit delete below.
    """
    mp   = get_object_or_404(MP, pk=pk)
    back = _safe_next(request, reverse('mp:mp_detail', args=[pk]) + '?active=tab-prp')

    # Read the stored filename BEFORE binding the form: is_valid() writes the
    # posted values onto the instance, so afterwards this would already be the
    # *new* name and the replaced file would be orphaned on disk forever.
    old_name = mp.prp_form_file.name or ''

    form = PRPFormUploadForm(request.POST, request.FILES, instance=mp)
    if not form.is_valid():
        for errors in form.errors.values():
            for err in errors:
                messages.error(request, err)
        return redirect(back)

    obj    = form.save(commit=False)
    upload = request.FILES.get('prp_form_file')
    if upload is not None:
        obj.prp_form_original_name = upload.name[:255]
        obj.prp_form_uploaded_at   = timezone.now()
        obj.prp_form_uploaded_by   = request.user
        # A scan cannot exist unless the hardcopy arrived, so uploading one
        # settles the tick too. Without this the operator has to remember a
        # second click, and every forgotten click is a false entry on the
        # "submitted but not uploaded" chase list.
        obj.prp_form_submitted = True
    obj.updated_by = request.user
    obj.save()

    if old_name and old_name != obj.prp_form_file.name:
        # Housekeeping only: the replacement is already saved and the row
        # already points at it. If the superseded file cannot be removed — a
        # reader still has it open, the volume was restored read-only — that
        # must not turn a successful upload into a 500 and lose the operator's
        # work. Worst case a stray file sits in a directory nothing serves.
        try:
            obj.prp_form_file.storage.delete(old_name)
        except OSError:
            pass

    if upload is not None:
        messages.success(request, f'{mp.name_bn}: PRP ফরম আপলোড হয়েছে।')
    elif obj.prp_form_submitted:
        messages.success(request, f'{mp.name_bn}: PRP ফরম জমা হিসেবে চিহ্নিত হয়েছে।')
    else:
        messages.success(request, f'{mp.name_bn}: PRP ফরমের অবস্থা হালনাগাদ হয়েছে।')
    return redirect(back)


@perm_required
@require_POST
def prp_form_delete(request, pk):
    """Remove the scan.

    The hardcopy tick is deliberately left alone: losing the scan does not
    un-receive the paper, so the MP moves back onto the scanning backlog
    rather than vanishing from every list.
    """
    mp   = get_object_or_404(MP, pk=pk)
    back = _safe_next(request, reverse('mp:mp_detail', args=[pk]) + '?active=tab-prp')
    if not mp.prp_form_file:
        messages.error(request, 'মুছে ফেলার মতো কোনো ফাইল নেই।')
        return redirect(back)

    # Clear the row even if the bytes resist deletion (a reader still holds the
    # handle, say). An orphaned file in a directory nothing serves is harmless;
    # a 500 that leaves the operator staring at a scan they just deleted is not.
    stored = mp.prp_form_file.name
    try:
        mp.prp_form_file.storage.delete(stored)
    except OSError:
        pass
    mp.prp_form_file = ''
    mp.prp_form_original_name = ''
    mp.prp_form_uploaded_at   = None
    mp.prp_form_uploaded_by   = None
    mp.updated_by = request.user
    mp.save()
    messages.success(request, f'{mp.name_bn}: PRP ফরমের স্ক্যান কপি মুছে ফেলা হয়েছে।')
    return redirect(back)


# ── READ ──────────────────────────────────────────────────────────────────────

@perm_required
def prp_form_file(request, pk):
    """Stream the scan for in-browser viewing (or download with ?download=1).

    This is the ONLY route to these bytes. They are stored outside MEDIA_ROOT
    precisely so nginx cannot hand them to an anonymous request. @perm_required
    cannot resolve a submenu for this URL — there is none — so the module's
    view permission is checked explicitly against the tracking page.
    """
    _run_permission_check(request, 'mp:prp_form_list')
    mp = get_object_or_404(MP, pk=pk)
    if not mp.prp_form_file:
        raise Http404

    ext = os.path.splitext(mp.prp_form_file.name)[1].lower()
    try:
        handle = mp.prp_form_file.open('rb')
    except (FileNotFoundError, OSError):
        # The row claims a file but the bytes are gone (a database restored
        # without its volume, say). A 404 is honest; a 500 traceback is not.
        raise Http404
    return FileResponse(
        handle,
        as_attachment=request.GET.get('download') == '1',
        filename=f'PRP-{mp.mp_id}{ext}',
        content_type=prp_content_type(mp.prp_form_file.name),
    )


@perm_required
def prp_form_list(request):
    """Tracking page — who has submitted, who is scanned, who is outstanding."""
    qs = MP.objects.select_related('parliament', 'prp_form_uploaded_by').prefetch_related(
        Prefetch(
            'election_infos',
            queryset=ElectionInfo.objects.select_related('constituency', 'party'),
        ),
    )

    parliament_id = request.GET.get('parliament', '')
    if parliament_id:
        qs = qs.filter(parliament_id=parliament_id)
    else:
        active_p = Parliament.objects.filter(is_active=True).first()
        if active_p:
            qs = qs.filter(parliament=active_p)
            parliament_id = str(active_p.pk)

    # Technocrats never count towards the 350 (rule 23), so the default view is
    # the seated members; the filter reveals them when they are wanted.
    member_type = request.GET.get('member_type', '')
    if member_type:
        qs = qs.filter(member_type=member_type)
    else:
        qs = qs.parliament_members()

    qs = qs.filter(is_active=True)

    # The tiles count the whole filtered population, so they stay put while the
    # operator narrows by status or types in the search box — a tile that
    # changed with the search would be reporting the search, not the backlog.
    counts = qs.prp_counts()

    status = request.GET.get('status', '')
    if status in PRP_STATUS_FILTERS:
        qs = PRP_STATUS_FILTERS[status](qs)

    q = request.GET.get('q', '').strip()
    if q:
        # Bangla numerals too: the list prints ০১৩০০০১০১, so typing it must work.
        qs = qs.filter(search_q(q, ['name_bn', 'name_en', 'mp_id']))

    paginator = Paginator(qs.order_by('mp_id'), 25)
    ctx = {
        'page_obj':      paginator.get_page(request.GET.get('page')),
        'q':             q,
        'parliament_id': parliament_id,
        'parliaments':   Parliament.objects.order_by('-ordinal'),
        'member_type':   member_type,
        'status':        status,
        'counts':        counts,
        'total_count':   paginator.count,
        'accept':        PRP_FILE_ACCEPT,
        'max_mb':        PRP_FILE_MAX_MB,
    }
    # Live search swaps ONLY the results region: an hx-target containing the
    # search box destroys the focused input mid-keystroke (gotcha 13).
    if request.headers.get('HX-Request'):
        return render(request, 'mp/_prp_list_results.html', ctx)
    return render(request, 'mp/prp_form_list.html', ctx)
