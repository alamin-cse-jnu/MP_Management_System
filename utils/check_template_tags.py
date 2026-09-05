"""Fail on template tags that span a newline.

`django.template.base.tag_re` is compiled WITHOUT `re.DOTALL`:

    tag_re = _lazy_re_compile(r"({%.*?%}|{{.*?}}|{#.*?#})")

so `.` never matches a newline and an opener whose closer sits on the *next*
line is not recognised as a tag at all. Django does not warn — the whole
construct is emitted as **literal text on the page**. This is the same trap as
the `{# … #}` comment rule, and it bites `{% … %}` and `{{ … }}` identically:
a `{% ui "long bangla string"` wrapped onto a second line for the English half
renders the tag source to the user.

Run from the project root:

    python utils/check_template_tags.py          # exit 1 on any hit
"""
import io
import os
import re
import sys

# An opener, then a newline, before the matching closer.
PATTERNS = [
    ('{% … %}', re.compile(r'\{%(?:(?!%\}).)*\n(?:(?!%\}).)*%\}', re.S)),
    ('{{ … }}', re.compile(r'\{\{(?:(?!\}\}).)*\n(?:(?!\}\}).)*\}\}', re.S)),
    ('{# … #}', re.compile(r'\{#(?:(?!#\}).)*\n(?:(?!#\}).)*#\}', re.S)),
]


def scan(root='templates'):
    hits = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            if not name.endswith('.html'):
                continue
            path = os.path.join(dirpath, name)
            text = io.open(path, encoding='utf-8').read()
            for label, rx in PATTERNS:
                for m in rx.finditer(text):
                    hits.append((path, text.count('\n', 0, m.start()) + 1,
                                 label, m.group(0)))
    return hits


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else 'templates'
    hits = scan(root)
    for path, line, label, snippet in hits:
        if len(snippet) > 200:
            snippet = snippet[:200] + ' …'
        print(f'{path}:{line}  {label} spans a newline — renders as literal text')
        for l in snippet.splitlines():
            print('    ' + l.strip())
    if hits:
        print(f'\n{len(hits)} multi-line tag(s). Put each one on a single line.')
        return 1
    print(f'{root}: no multi-line template tags.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
