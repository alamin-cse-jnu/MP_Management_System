"""NOC list, editor, preview and the three export formats."""

import os
import re
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.mixins import perm_required
from apps.mp.models import MP
from apps.reports.utils import render_report_pdf
from apps.travel.models import ForeignTour
from utils.bn_digits import search_q
from utils.html_sanitize import sanitize_html
from utils.html_to_docx import html_to_docx

from . import generation
from .forms import NOCForm, NOCLetterheadForm, NOCTemplateForm
from .models import LANGUAGE_BN, LANGUAGE_CHOICES, NOC, NOCLetterhead, NOCTemplate

PRINT_TEMPLATE = 'noc/print/noc_document.html'


# ── helpers ──────────────────────────────────────────────────────────────────

def _document_ctx(noc):
    """Context the A4 document shell needs, shared by preview/print/PDF/Word."""
    return {
        'noc': noc,
        # Sanitised again at render time: rows created before the sanitiser
        # existed, or edited straight in the DB, must not slip through.
        'body_html': sanitize_html(noc.body_html),
        'is_bangla': noc.is_bangla,
    }


def _slug(noc):
    base = f'NOC-{noc.memo_no or noc.pk}-{noc.mp.mp_id}'
    return re.sub(r'[^A-Za-z0-9._-]+', '-', base).strip('-')


def _regenerate_body(noc):
    """(Re)build `noc.body_html` from its template and the current data."""
    template = noc.template or NOCTemplate.default_for(noc.language)
    if template is None:
        return False
    ctx = generation.build_context(
        noc.mp, tour=noc.tour, spouse=noc.spouse,
        issue_date=noc.issue_date, memo_no=noc.memo_no,
        signatory=noc.signatory,
    )
    noc.template = template
    noc.body_html = generation.render_body(template.body_html, ctx)
    return True


# ── list ─────────────────────────────────────────────────────────────────────

@perm_required
def noc_list(request):
    qs = NOC.objects.select_related('mp', 'tour', 'template').all()

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(search_q(q, [
            'memo_no', 'mp__name_bn', 'mp__name_en', 'mp__mp_id', 'tour__go_number',
        ]))

    language = request.GET.get('language', '')
    if language:
        qs = qs.filter(language=language)

    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    ctx = {
        'page_obj': page, 'q': q, 'language': language, 'status': status,
        'languages': LANGUAGE_CHOICES, 'statuses': NOC.STATUS_CHOICES,
    }
    # Live search re-runs this view over HTMX and swaps only the results block.
    if request.headers.get('HX-Request'):
        return render(request, 'noc/_noc_list_results.html', ctx)
    return render(request, 'noc/noc_list.html', ctx)


# ── create ───────────────────────────────────────────────────────────────────

@perm_required
@require_POST
def noc_create(request, tour_pk, mp_pk):
    """Issue a fresh NOC for one MP on one tour, then open the editor."""
    tour = get_object_or_404(ForeignTour, pk=tour_pk)
    mp = get_object_or_404(MP, pk=mp_pk)
    language = request.POST.get('language', LANGUAGE_BN)
    if language not in dict(LANGUAGE_CHOICES):
        language = LANGUAGE_BN

    issue_date = date.today()
    serial = generation.next_serial(issue_date)
    noc = NOC(
        tour=tour, mp=mp, language=language,
        serial_no=serial,
        memo_no=generation.suggest_memo_no(serial, issue_date),
        issue_date=issue_date,
        created_by=request.user, updated_by=request.user,
    )
    # Default the signatory to whoever last signed one — usually the same desk.
    last = NOC.objects.exclude(signatory=None).order_by('-created_at').first()
    if last and last.signatory and last.signatory.is_active:
        noc.snapshot_signatory(last.signatory)
    noc.signatory_email = NOCLetterhead.current().email

    _regenerate_body(noc)
    noc.save()
    messages.success(request, 'NOC-এর খসড়া তৈরি হয়েছে — প্রয়োজনে সম্পাদনা করে সংরক্ষণ করুন।')
    return redirect('noc:noc_edit', pk=noc.pk)


# ── edit ─────────────────────────────────────────────────────────────────────

@perm_required
def noc_edit(request, pk):
    noc = get_object_or_404(NOC.objects.select_related('mp', 'tour', 'signatory'), pk=pk)

    # Snapshot the state BEFORE the form touches it. `form.is_valid()` runs
    # construct_instance(), which writes the posted values straight onto `noc` —
    # so anything read after that point is already the NEW value. (Comparing
    # against it is exactly why changing the signatory silently did nothing.)
    old_signatory_id = noc.signatory_id
    template = noc.template or NOCTemplate.default_for(noc.language)
    old_ctx = generation.build_context(
        noc.mp, tour=noc.tour, spouse=noc.spouse, issue_date=noc.issue_date,
        memo_no=noc.memo_no, signatory=noc.signatory)
    was_pristine = generation.is_pristine(
        noc.body_html, template.body_html if template else '', old_ctx)

    form = NOCForm(request.POST or None, instance=noc, mp=noc.mp)

    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)

        # Re-freeze the signature block whenever an officer is chosen. Always,
        # not only on change: the snapshot columns are what the document prints,
        # and a re-save must never leave them stale.
        officer = form.cleaned_data.get('signatory')
        obj.snapshot_signatory(officer)
        if officer is not None:
            obj.signatory_email = NOCLetterhead.current().email

        # The body is authored in a rich-text editor and later rendered |safe.
        obj.body_html = sanitize_html(form.cleaned_data.get('body_html', ''))

        # Keep the document in step with the fields beside it. Editing the date
        # or the signatory has to change the printed letter, not just the row.
        new_ctx = generation.build_context(
            obj.mp, tour=obj.tour, spouse=obj.spouse, issue_date=obj.issue_date,
            memo_no=obj.memo_no, signatory=officer)
        body_untouched = (obj.body_html or '').strip() == (
            generation.render_body(template.body_html, old_ctx).strip()
            if template else None)

        if template and (was_pristine and body_untouched):
            # Never hand-edited — re-render, so values that had no old text to
            # find (a signatory that was blank until now) still land.
            obj.body_html = generation.render_body(template.body_html, new_ctx)
        else:
            obj.body_html, unpatched = generation.patch_body(
                obj.body_html, old_ctx, new_ctx)
            if unpatched:
                messages.warning(
                    request,
                    'দলিলে কিছু তথ্য নিজে থেকে বদলানো যায়নি ({}) — প্রয়োজনে '
                    '"টেমপ্লেট থেকে তৈরি করুন" চাপুন।'.format(', '.join(unpatched)))

        obj.updated_by = request.user
        obj.save()
        messages.success(request, 'NOC সংরক্ষিত হয়েছে।')
        return redirect('noc:noc_detail', pk=obj.pk)

    if request.method == 'POST':
        messages.error(request, 'সংরক্ষণ করা যায়নি — নিচের ত্রুটিগুলো ঠিক করুন।')

    return render(request, 'noc/noc_form.html', {
        'noc': noc, 'form': form,
        'letterhead': NOCLetterhead.current(),
        'old_signatory_id': old_signatory_id,
    })


@perm_required
@require_POST
def noc_regenerate(request, pk):
    """Rebuild the body from the template, discarding manual edits.

    The button submits the *editor* form, so the metadata typed beside the
    document (date, signatory, spouse, memo, status) is applied FIRST and the
    rebuilt body carries it. Regenerating off the stored row instead — what the
    old CSRF-only form did — silently rebuilt with the previous values, so a
    freshly typed date or signatory looked like it had no effect at all.
    """
    noc = get_object_or_404(
        NOC.objects.select_related('mp', 'tour', 'signatory'), pk=pk)
    # Read before binding: `is_valid()` runs construct_instance() and writes the
    # posted values straight onto the instance (CLAUDE.md gotcha 3).
    old_signatory_id = noc.signatory_id

    # A page cached before this change posts nothing but the CSRF token; then
    # the stored values are all there is to rebuild from.
    if 'issue_date' in request.POST:
        form = NOCForm(request.POST, instance=noc, mp=noc.mp)
        if not form.is_valid():
            messages.error(request, 'সংরক্ষণ করা যায়নি — নিচের ত্রুটিগুলো ঠিক করুন।')
            return render(request, 'noc/noc_form.html', {
                'noc': noc, 'form': form,
                'letterhead': NOCLetterhead.current(),
                'old_signatory_id': old_signatory_id,
            })
        noc = form.save(commit=False)
        # Same rule as the editor: re-freeze the signature block every time, so
        # the snapshot columns the document prints are never stale.
        officer = form.cleaned_data.get('signatory')
        noc.snapshot_signatory(officer)
        if officer is not None:
            noc.signatory_email = NOCLetterhead.current().email

    rebuilt = _regenerate_body(noc)
    noc.updated_by = request.user
    # Saved either way — the metadata just typed must not be thrown away only
    # because the language has no template to rebuild the body from.
    noc.save()

    if rebuilt:
        messages.success(request, 'টেমপ্লেট থেকে দলিলটি পুনরায় তৈরি করা হয়েছে।')
    else:
        messages.error(request, f'"{noc.get_language_display()}" ভাষার কোনো সক্রিয় টেমপ্লেট নেই।')
    return redirect('noc:noc_edit', pk=noc.pk)


@perm_required
@require_POST
def noc_delete(request, pk):
    """Delete a DRAFT. A finalised NOC has been issued under a memo number, so
    it is not removable from the UI — the button is hidden and this refuses it
    too, since hiding a control is not a permission check."""
    noc = get_object_or_404(NOC, pk=pk)
    tour_pk = noc.tour_id

    fallback = (reverse('travel:tour_detail', args=[tour_pk]) if tour_pk
                else reverse('noc:noc_list'))
    # Honour ?next only when it is a local path — never an absolute URL.
    nxt = request.POST.get('next', '')
    target = nxt if (nxt.startswith('/') and not nxt.startswith('//')) else fallback

    if noc.status == NOC.STATUS_FINAL:
        messages.error(request, 'চূড়ান্ত NOC মোছা যায় না — আগে খসড়ায় ফেরত নিন।')
        return redirect(target)

    noc.delete()
    messages.success(request, 'খসড়া NOC মুছে ফেলা হয়েছে।')
    return redirect(target)


# ── preview + exports ────────────────────────────────────────────────────────

@perm_required
def noc_detail(request, pk):
    """Preview, and the three download/print formats behind ?format=."""
    noc = get_object_or_404(NOC.objects.select_related('mp', 'tour', 'signatory'), pk=pk)
    ctx = _document_ctx(noc)
    fmt = request.GET.get('format', '')

    if fmt == 'print':
        return render(request, PRINT_TEMPLATE, ctx)

    if fmt == 'pdf':
        # Portrait: this is a letter, not one of the wide tabular reports.
        return render_report_pdf(request, PRINT_TEMPLATE, ctx,
                                 f'{_slug(noc)}.pdf', landscape=False)

    if fmt == 'docx':
        buf = html_to_docx(
            ctx['body_html'],
            static_root=os.path.join(settings.BASE_DIR, 'static'),
            title=f'NOC {noc.memo_no}',
        )
        response = HttpResponse(
            buf.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{_slug(noc)}.docx"'
        return response

    ctx['back_url'] = (reverse('travel:tour_detail', args=[noc.tour_id])
                       if noc.tour_id else reverse('noc:noc_list'))
    return render(request, 'noc/noc_detail.html', ctx)


# ── settings (letterhead + templates) ────────────────────────────────────────

@perm_required
def noc_settings(request):
    """Letterhead + the standard wording, both editable without a deploy."""
    letterhead = NOCLetterhead.current()
    form = NOCLetterheadForm(request.POST or None, instance=letterhead)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'লেটারহেড সংরক্ষিত হয়েছে।')
        return redirect('noc:noc_settings')
    return render(request, 'noc/noc_settings.html', {
        'form': form,
        'templates': NOCTemplate.objects.all(),
    })


@perm_required
def noc_template_edit(request, pk):
    template = get_object_or_404(NOCTemplate, pk=pk)
    form = NOCTemplateForm(request.POST or None, instance=template)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.body_html = sanitize_html(obj.body_html)
        obj.save()
        messages.success(request, 'টেমপ্লেট সংরক্ষিত হয়েছে।')
        return redirect('noc:noc_settings')
    return render(request, 'noc/noc_template_form.html', {
        'form': form, 'template_obj': template,
        'placeholders': sorted(generation.build_context(MP.objects.first()).keys())
        if MP.objects.exists() else [],
    })
