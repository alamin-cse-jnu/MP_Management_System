"""
Shared helpers for GO (Government Order) document uploads.

Used across Ministry, Committee, Institution and Foreign Travel modules so
every GO attachment behaves identically: same allowed types, same size limit,
same upload location, and the same template-friendly helpers for listing.
"""
import os

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Allowed document/image formats for a GO attachment.
GO_FILE_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')
GO_FILE_MAX_MB = 10


def validate_go_file(f):
    """Validator for GO upload FileFields — accepts PDF / JPG / JPEG / PNG."""
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in GO_FILE_EXTENSIONS:
        raise ValidationError(
            _('শুধুমাত্র PDF, JPG, JPEG বা PNG ফাইল আপলোড করা যাবে। '
              'Only PDF, JPG, JPEG or PNG files are allowed.')
        )
    size = getattr(f, 'size', 0) or 0
    if size > GO_FILE_MAX_MB * 1024 * 1024:
        raise ValidationError(
            _('ফাইলের সর্বোচ্চ আকার %(mb)d MB। File must be at most %(mb)d MB.')
            % {'mb': GO_FILE_MAX_MB}
        )


def go_file_is_image(name):
    """True if the GO file is an image (renderable inline), False for PDF."""
    return os.path.splitext(name or '')[1].lower() in ('.jpg', '.jpeg', '.png')


# Accept attribute for the <input type="file"> on GO upload forms.
GO_FILE_ACCEPT = '.pdf,.jpg,.jpeg,.png'
