"""
Fixes Bangla text encoding garbled by CP850 misinterpretation.

The original UTF-8 SQL dump was re-saved as UTF-16 LE by a Windows app
that interpreted each UTF-8 byte as a CP850 character. This command
reverses that: encodes each stored character back to CP850 to recover
the original byte, then decodes the byte stream as UTF-8.
"""

from django.core.management.base import BaseCommand
from django.apps import apps


def fix_encoding(text):
    """Reverse CP850 garbling: stored char → CP850 byte → reassemble as UTF-8."""
    if not text:
        return text
    # If already proper Bangla Unicode (U+0980–U+09FF), skip
    if any('ঀ' <= c <= '৿' for c in text):
        return text
    try:
        raw = bytes(c.encode('cp850')[0] for c in text)
        return raw.decode('utf-8', errors='replace')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


class Command(BaseCommand):
    help = 'Fix CP850-garbled Bangla text in all model _bn fields'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Show what would change without saving')
        parser.add_argument('--app', type=str, default=None,
                            help='Limit to a specific app (e.g. master, mp)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_app = options.get('app')
        total_fixed = 0

        for model in apps.get_models():
            app_label = model._meta.app_label
            if target_app and app_label != target_app:
                continue
            # Only process our custom apps
            if app_label not in ('master', 'mp', 'parliament', 'ministry',
                                  'committee', 'institution', 'travel',
                                  'office', 'reports', 'accounts'):
                continue

            # Collect text fields with _bn suffix or known Bangla-only fields
            bn_fields = [
                f.name for f in model._meta.get_fields()
                if hasattr(f, 'column') and hasattr(f, 'max_length')
                and (f.name.endswith('_bn') or f.name in (
                    'title_bn', 'description_bn', 'note_bn',
                    'full_name_bn', 'profession_details_bn',
                    'nationality',
                ))
            ]
            if not bn_fields:
                continue

            model_label = f'{app_label}.{model.__name__}'
            fixed_count = 0

            for obj in model.objects.all():
                changed = False
                for field in bn_fields:
                    val = getattr(obj, field, None)
                    if not val:
                        continue
                    fixed = fix_encoding(val)
                    if fixed != val:
                        if dry_run:
                            self.stdout.write(
                                f'  [{model_label}.{field}] '
                                f'{val[:40]!r} → {fixed[:40]!r}'
                            )
                        else:
                            setattr(obj, field, fixed)
                        changed = True

                if changed and not dry_run:
                    obj.save(update_fields=bn_fields)
                    fixed_count += 1

            if fixed_count:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{model_label}: fixed {fixed_count} rows'
                    )
                )
                total_fixed += fixed_count

        action = 'Would fix' if dry_run else 'Fixed'
        self.stdout.write(self.style.SUCCESS(
            f'\n{action} {total_fixed} rows total.'
        ))
