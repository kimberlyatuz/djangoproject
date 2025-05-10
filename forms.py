from django import forms
from .models import SurvivalData
from app1.models import PatientDemographics
from django.utils import timezone


class SurvivalDataForm(forms.ModelForm):
    class Meta:
        model = SurvivalData
        fields = '__all__'
        widgets = {
            'dod': forms.DateInput(attrs={'type': 'date'}),
            'date_case_registered': forms.DateInput(attrs={'type': 'date', 'value': timezone.now().date()}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_days_in_care(self):
        days = self.cleaned_data.get('days_in_care')
        if days is not None and days < 0:
            raise forms.ValidationError("Days in care cannot be negative.")
        return days

    def clean(self):
        cleaned_data = super().clean()
        dod = cleaned_data.get('dod')
        file_status = cleaned_data.get('file_status')

        if file_status == 'closed_died' and not dod:
            raise forms.ValidationError("Date of death is required when status is 'Closed - Died'.")

        return cleaned_data
