"""Forms for the NOC editor."""

from django import forms

from utils.form_dates import normalize_date_fields

from apps.mp.models import Spouse
from apps.officer.form_fields import OfficerChoiceField

from .models import NOC, NOCLetterhead, NOCTemplate


class _BootstrapMixin:
    """Same treatment the rest of the system gives its widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.FileInput)):
                continue
            css = 'form-select' if isinstance(widget, forms.Select) else 'form-control'
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = f'{existing} {css}'.strip()
        normalize_date_fields(self)


class NOCForm(_BootstrapMixin, forms.ModelForm):
    """Metadata beside the editor. ``body_html`` is posted by CKEditor."""

    signatory = OfficerChoiceField()

    class Meta:
        model = NOC
        # `template` is deliberately NOT here: it is plumbing for Regenerate,
        # not something the user picks per document.
        fields = ['memo_no', 'issue_date', 'signatory', 'spouse',
                  'status', 'body_html']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            # Hidden: CKEditor owns this value and writes it back on submit.
            'body_html': forms.Textarea(attrs={'id': 'noc-editor', 'rows': 24}),
        }

    def __init__(self, *args, mp=None, **kwargs):
        super().__init__(*args, **kwargs)
        mp = mp or getattr(self.instance, 'mp', None)

        # Only this MP's own spouses may be named as accompanying.
        self.fields['spouse'].queryset = (
            Spouse.objects.filter(mp=mp) if mp else Spouse.objects.none())
        self.fields['spouse'].required = False
        self.fields['spouse'].empty_label = '— কেউ নন / none —'

        self.fields['memo_no'].widget.attrs['autocomplete'] = 'off'
        self.fields['body_html'].required = False


class NOCCreateForm(forms.Form):
    """The small dialog behind the 'issue NOC' buttons on the tour page."""
    language = forms.ChoiceField(choices=NOC._meta.get_field('language').choices)


class NOCLetterheadForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = NOCLetterhead
        exclude = ['is_active']


class NOCTemplateForm(_BootstrapMixin, forms.ModelForm):
    class Meta:
        model = NOCTemplate
        fields = ['name_bn', 'name_en', 'language', 'body_html',
                  'is_default', 'is_active', 'ordering']
        widgets = {
            'body_html': forms.Textarea(attrs={'id': 'noc-editor', 'rows': 24}),
        }
