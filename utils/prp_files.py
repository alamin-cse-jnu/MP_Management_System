"""
Shared helpers for the PRP form attachment (the scanned data-collection form
an MP submits, from which this system's records are typed).

Unlike a GO document, a PRP form is one page carrying the MP's NID, passport
and bank account numbers together, so it is **never** written under MEDIA_ROOT:
nginx serves that directory straight off disk with no authentication. These
files live under settings.PRIVATE_MEDIA_ROOT and are readable only through
`mp:prp_form_file`, which runs the same login + role check as every other page.

The storage is a *callable*, not an instance, on purpose: Django serialises a
FileSystemStorage instance into the migration with its `location` baked in, so
the developer's Windows path would ship to the server. A callable is serialised
as a reference and re-read from settings wherever it runs.
"""
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.utils.translation import gettext_lazy as _

#: A scan is a PDF nine times out of ten, but a phone photo of the form is a
#: legitimate way to get it into the system, so images are accepted too.
PRP_FILE_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')
PRP_FILE_MAX_MB = 20
PRP_FILE_ACCEPT = '.pdf,.jpg,.jpeg,.png'


class PrivateFileSystemStorage(FileSystemStorage):
    """FileSystemStorage that refuses to produce a URL.

    Plain FileSystemStorage does NOT help here: its `base_url` falls back to
    settings.MEDIA_URL when none is given, so `mp.prp_form_file.url` would
    quietly return `/media/prp_forms/…` — a path nginx happily serves from the
    *public* media volume, which is not where these bytes are. That is a dead
    link at best and a misleading one at worst. Raising instead makes a stray
    `.url` in a template fail in review rather than ship.
    """

    def url(self, name):
        raise ValueError(
            'PRP form scans are not served by URL. Link to mp:prp_form_file '
            'instead — it checks the login and the role first.'
        )


def prp_storage():
    """Private storage for PRP form attachments (see the class above)."""
    return PrivateFileSystemStorage(location=str(settings.PRIVATE_MEDIA_ROOT))


def prp_form_upload_to(instance, filename):
    """prp_forms/<mp_id>_<random>.<ext>

    The random half keeps two uploads for the same MP from colliding while a
    replace is in flight, and means the on-disk name is not derivable from the
    MP ID alone — defence in depth behind the view's permission check.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in PRP_FILE_EXTENSIONS:
        ext = '.pdf'
    mp_id = (getattr(instance, 'mp_id', '') or 'mp').replace('/', '_')
    return f'prp_forms/{mp_id}_{uuid.uuid4().hex[:8]}{ext}'


def validate_prp_file(f):
    """Validator for the PRP form upload — accepts PDF / JPG / JPEG / PNG."""
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in PRP_FILE_EXTENSIONS:
        raise ValidationError(
            _('শুধুমাত্র PDF, JPG, JPEG বা PNG ফাইল আপলোড করা যাবে। '
              'Only PDF, JPG, JPEG or PNG files are allowed.')
        )
    size = getattr(f, 'size', 0) or 0
    if size > PRP_FILE_MAX_MB * 1024 * 1024:
        raise ValidationError(
            _('ফাইলের সর্বোচ্চ আকার %(mb)d MB। File must be at most %(mb)d MB.')
            % {'mb': PRP_FILE_MAX_MB}
        )


def prp_content_type(name):
    """Content type for inline display of a stored PRP file."""
    ext = os.path.splitext(name or '')[1].lower()
    return {
        '.pdf':  'application/pdf',
        '.jpg':  'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png':  'image/png',
    }.get(ext, 'application/octet-stream')


def prp_is_pdf(name):
    """True if the stored PRP file is a PDF (embed it), False for an image."""
    return os.path.splitext(name or '')[1].lower() == '.pdf'
