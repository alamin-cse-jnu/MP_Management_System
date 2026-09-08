import csv
import io
from django.http import HttpResponse
from django.template.loader import render_to_string

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def export_csv(filename, headers, rows):
    # charset must be plain utf-8: Django encodes EVERY response.write() with
    # the declared codec, so 'utf-8-sig' prepended a BOM to every row and
    # corrupted the first column of every line. Write the BOM once instead —
    # Excel still needs it to detect UTF-8.
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    response.write('﻿')
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([str(v) if v is not None else '' for v in row])
    return response


def _html_to_pdf(html, base_url):
    """HTML string → PDF bytes.

    Engine cascade: WeasyPrint (correct Bangla shaping — used on the
    Linux/Docker server) → xhtml2pdf (pure-Python fallback for Windows dev;
    Bangla shaping is limited but it always produces a valid PDF).
    """
    try:
        from weasyprint import HTML as WP_HTML
        return WP_HTML(string=html, base_url=base_url).write_pdf()
    except Exception:
        pass
    from xhtml2pdf import pisa
    buf = io.BytesIO()
    pisa.pisaDocument(io.BytesIO(html.encode('utf-8')), buf)
    return buf.getvalue()


def _pdf_chunk(args):
    """Process-pool worker: one HTML chunk → PDF bytes.

    Must stay a module-level function (picklable) and must never touch the ORM:
    it runs in a fork of a gunicorn worker and shares that worker's database
    socket, so a query — or a `connection.close()` — here would corrupt the
    parent's connection. It only lays out an HTML string that was rendered in
    the parent.
    """
    html, base_url = args
    return _html_to_pdf(html, base_url)


def _split_workers(n_rows, split_size):
    """How many processes to lay this report out with (1 = render inline).

    WeasyPrint costs ~40 ms per row of a wide Bangla table and is single
    threaded, so a 348-row report is ~15 s of one core. Splitting it into a few
    chunks and merging the PDFs cuts the wait roughly by the number of chunks.

    The cap is deliberate. Report generation is a shared, concurrent workload:
    one user's PDF must not take the whole box. So this never asks for more than
    3 processes, never more than the rows justify, and returns 1 outright when
    the load average says the other cores are already busy — under load, serial
    rendering keeps total throughput higher than everyone forking at once.
    """
    import os
    if os.name != 'posix':
        return 1                       # spawn (Windows) would re-import Django
    if n_rows <= split_size:
        return 1
    cpu = os.cpu_count() or 1
    if cpu < 2:
        return 1
    try:
        load = os.getloadavg()[0]
    except (OSError, AttributeError):
        load = 0.0
    headroom = cpu - load
    if headroom < 1.5:
        return 1
    # Never more than half the cores: on the 4-core server that means a report
    # splits in two, leaving the other half for everyone else's page loads.
    return max(1, min(3, cpu // 2, int(headroom), -(-n_rows // split_size)))


def render_report_pdf(request, template, ctx, filename, landscape=True,
                      split_key=None, split_size=120):
    """Render a print template to a downloadable PDF (Phase 17.2 / 17.6).

    `split_key` names a list in `ctx` (the report's rows). When it is long
    enough — and the server is not already busy — the rows are cut into chunks,
    each chunk is laid out in its own process, and the PDFs are merged. The
    template is handed `start_index` (so row numbers continue across chunks),
    `hide_print_header` (the letterhead belongs on the first chunk only) and
    `hide_report_footer` (the totals line belongs on the last).

    Returns the PDF as an ``attachment`` so the browser downloads it instead of
    opening a print dialog.
    """
    from pathlib import Path
    from django.conf import settings

    ctx = dict(ctx)
    ctx['pdf_mode']      = True          # suppress the auto window.print() script
    ctx['pdf_landscape'] = landscape     # A4 landscape @page for wide tables

    # Embed the Bangla font by absolute file URI so WeasyPrint can load it
    # without depending on collected static files.
    font_path = Path(settings.BASE_DIR) / 'static' / 'fonts' / 'SolaimanLipi.ttf'
    ctx['pdf_font_uri'] = font_path.as_uri() if font_path.exists() else ''
    base_url = str(settings.BASE_DIR)

    rows    = ctx.get(split_key) if split_key else None
    workers = _split_workers(len(rows), split_size) if rows else 1

    if workers > 1:
        pdf_bytes = _render_split_pdf(request, template, ctx, base_url,
                                      split_key, rows, workers)
    else:
        pdf_bytes = _html_to_pdf(render_to_string(template, ctx, request=request),
                                 base_url)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _render_split_pdf(request, template, ctx, base_url, split_key, rows, workers):
    """Lay the report out in `workers` processes and merge the pieces."""
    import concurrent.futures
    import multiprocessing

    size   = -(-len(rows) // workers)
    chunks = [rows[i:i + size] for i in range(0, len(rows), size)]
    htmls  = []
    offset = 0
    for i, chunk in enumerate(chunks):
        cctx = dict(ctx)
        cctx[split_key]           = chunk
        cctx['start_index']       = offset
        cctx['hide_print_header'] = i > 0
        cctx['hide_report_footer'] = i < len(chunks) - 1
        htmls.append((render_to_string(template, cctx, request=request), base_url))
        offset += len(chunk)

    try:
        from pypdf import PdfWriter
    except ImportError:
        # No merger available — fall back to one document, still correct.
        return _html_to_pdf(render_to_string(template, ctx, request=request), base_url)

    ctxm = multiprocessing.get_context('fork')
    parts = None
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=len(htmls),
                                                    mp_context=ctxm) as pool:
            parts = list(pool.map(_pdf_chunk, htmls, timeout=300))
    except Exception:
        parts = None
    if not parts:
        return _html_to_pdf(render_to_string(template, ctx, request=request), base_url)

    writer = PdfWriter()
    for part in parts:
        writer.append(io.BytesIO(part))
    out = io.BytesIO()
    writer.write(out)
    writer.close()
    return out.getvalue()


def export_excel(filename, headers, rows, sheet_title='রিপোর্ট'):
    if not HAS_OPENPYXL:
        return HttpResponse('openpyxl not installed', status=500)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]

    thin = Side(border_style='thin', color='CCCCCC')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    header_fill = PatternFill('solid', fgColor='0D9488')
    header_font = Font(bold=True, color='FFFFFF')
    alt_fill = PatternFill('solid', fgColor='F0FDFA')

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
    ws.row_dimensions[1].height = 28

    for row_idx, row in enumerate(rows, 2):
        for col_idx, val in enumerate(row, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=str(val) if val is not None else '')
            cell.border = border
            if row_idx % 2 == 0:
                cell.fill = alt_fill

    for col in ws.columns:
        max_len = max((len(str(c.value or '')) for c in col if c.value), default=8)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 45)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    return response
