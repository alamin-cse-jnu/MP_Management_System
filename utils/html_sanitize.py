"""Allowlist sanitiser for editor-authored HTML.

The NOC body is written in CKEditor and rendered with ``|safe`` on the preview,
print and PDF pages, so it must be cleaned on the way IN. Only authenticated
staff can reach the editor, but a stored ``<script>`` would still execute for
every later viewer — including on the print page a different user opens.

Stdlib only (``html.parser``) — no bleach dependency. Unknown tags are dropped
but their **text is kept**, so nothing a user typed silently disappears.
"""

from html import escape
from html.parser import HTMLParser

# Tags the document templates and CKEditor's toolbar can produce.
ALLOWED_TAGS = {
    'p', 'br', 'hr', 'div', 'span', 'section',
    'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'sub', 'sup', 'mark',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
    'img', 'a', 'figure', 'figcaption',
}

# Tags whose CONTENT must go too, not just the tag.
DROP_WITH_CONTENT = {'script', 'style', 'iframe', 'object', 'embed', 'noscript',
                     'form', 'input', 'button', 'select', 'textarea', 'link', 'meta'}

VOID_TAGS = {'br', 'hr', 'img', 'col'}

# Emitted as their children only — the wrapper itself is dropped.
#
# CKEditor wraps every table it saves in ``<figure class="table">``. That class
# is ALSO a Bootstrap component: `.table > :not(caption) > * > *` then paints
# `border-bottom: 1px solid` and 8px padding onto every <tr>, so a saved
# document grew a black rule under each row that the original letters do not
# have. `figure` adds a Reboot bottom margin on top of that. Neither carries any
# meaning in a printed letter, so the wrapper goes.
TRANSPARENT_TAGS = {'figure'}

# Class names that collide with Bootstrap components. Stripped wherever they
# appear so editor output can never inherit app chrome.
DENY_CLASSES = {'table'}

ALLOWED_ATTRS = {
    '*':     {'style', 'class', 'dir', 'lang', 'title'},
    'img':   {'src', 'alt', 'width', 'height'},
    'a':     {'href', 'target', 'rel'},
    'td':    {'colspan', 'rowspan', 'align', 'valign'},
    'th':    {'colspan', 'rowspan', 'align', 'valign', 'scope'},
    'table': {'border', 'cellpadding', 'cellspacing', 'align', 'width'},
    'col':   {'span', 'width'},
    'ol':    {'start', 'type'},
}

# CSS declarations worth keeping — layout/typography only, nothing that can load
# a remote resource or position an element over the page.
ALLOWED_CSS = {
    'text-align', 'font-weight', 'font-style', 'font-size', 'font-family',
    'text-decoration', 'color', 'background-color', 'width', 'height',
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'border', 'border-top', 'border-bottom', 'border-left', 'border-right',
    'border-collapse', 'vertical-align', 'line-height', 'text-indent',
    'list-style-type', 'white-space',
}

_SAFE_URL_SCHEMES = ('http://', 'https://', 'mailto:', '/', '#', './', '../')


def _clean_style(value):
    kept = []
    for decl in value.split(';'):
        if ':' not in decl:
            continue
        prop, _, val = decl.partition(':')
        prop = prop.strip().lower()
        val = val.strip()
        if prop in ALLOWED_CSS and 'url(' not in val.lower() and 'expression' not in val.lower():
            kept.append(f'{prop}: {val}')
    return '; '.join(kept)


def _clean_url(value, allow_data_image=False):
    v = (value or '').strip()
    low = v.lower().replace('\t', '').replace('\n', '').replace('\r', '')
    if allow_data_image and low.startswith('data:image/'):
        return v
    if low.startswith(_SAFE_URL_SCHEMES):
        return v
    return ''


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.open_tags = []
        self._suppress_depth = 0        # inside a DROP_WITH_CONTENT element

    # ── tags ────────────────────────────────────────────────────────────────
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in DROP_WITH_CONTENT:
            self._suppress_depth += 1
            return
        if self._suppress_depth or tag not in ALLOWED_TAGS:
            return
        if tag in TRANSPARENT_TAGS:
            # Keep the contents, drop the wrapper. Tracked so the matching end
            # tag is dropped too and the output stays balanced.
            self.open_tags.append(f'~{tag}')
            return

        allowed = ALLOWED_ATTRS.get('*', set()) | ALLOWED_ATTRS.get(tag, set())
        parts = []
        for name, value in attrs:
            name = (name or '').lower()
            # on* handlers are the whole reason this function exists.
            if name.startswith('on') or name not in allowed:
                continue
            value = value or ''
            if name == 'style':
                value = _clean_style(value)
                if not value:
                    continue
            elif name == 'class':
                value = ' '.join(c for c in value.split() if c not in DENY_CLASSES)
                if not value:
                    continue
            elif name == 'src':
                value = _clean_url(value, allow_data_image=True)
                if not value:
                    continue
            elif name == 'href':
                value = _clean_url(value)
                if not value:
                    continue
            parts.append(f' {name}="{escape(value, quote=True)}"')

        if tag in VOID_TAGS:
            self.out.append(f'<{tag}{"".join(parts)}>')
        else:
            self.out.append(f'<{tag}{"".join(parts)}>')
            self.open_tags.append(tag)

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if tag in VOID_TAGS or tag in ALLOWED_TAGS:
            self.handle_starttag(tag, attrs)
            if tag not in VOID_TAGS and self.open_tags and self.open_tags[-1] == tag:
                self.open_tags.pop()
                self.out.append(f'</{tag}>')

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in DROP_WITH_CONTENT:
            self._suppress_depth = max(0, self._suppress_depth - 1)
            return
        if self._suppress_depth or tag in VOID_TAGS or tag not in ALLOWED_TAGS:
            return
        marker = f'~{tag}' if tag in TRANSPARENT_TAGS else tag
        if marker in self.open_tags:
            # Close anything left dangling inside it so the output stays balanced.
            while self.open_tags:
                open_tag = self.open_tags.pop()
                if not open_tag.startswith('~'):
                    self.out.append(f'</{open_tag}>')
                if open_tag == marker:
                    break

    def handle_data(self, data):
        if not self._suppress_depth:
            self.out.append(escape(data, quote=False))

    def handle_comment(self, data):
        pass        # conditional comments can carry markup — drop them

    def result(self):
        while self.open_tags:
            open_tag = self.open_tags.pop()
            if not open_tag.startswith('~'):
                self.out.append(f'</{open_tag}>')
        return ''.join(self.out)


def sanitize_html(html):
    """Return `html` with only allowlisted tags, attributes and CSS left."""
    if not html:
        return ''
    parser = _Sanitizer()
    parser.feed(html)
    parser.close()
    return parser.result()
