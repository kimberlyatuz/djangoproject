from django.db import models
from app1.models import PatientDemographics

class PatientSurvival(models.Model):
    patient = models.OneToOneField(
        PatientDemographics,
        on_delete=models.CASCADE,
        related_name='patient_survival_record'
    )
    entry_date = models.DateField()  # Date of hospice admission
    last_followup = models.DateField()
    event_occurred = models.BooleanField(
        default=False,
        help_text="True if death occurred, False if censored"
    )
    covariates = models.JSONField(
        blank=True,
        help_text="Additional risk factors (e.g., {'pain_level': 4, 'diagnosis_stage': 3})"
    )

    class Meta:
        verbose_name = "Survival Analysis Record"

class SurvivalData(models.Model):
    POD_CHOICES = [
        ('home', 'Home'),
        ('hospital', 'Hospital'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed_died', 'Closed - Died'),
        ('closed_recovered', 'Closed - Recovered'),
        ('closed_transferred', 'Closed - Transferred'),
        ('closed_lost', 'Closed - Lost to Follow Up'),
    ]

    CARE_LEVEL_CHOICES = [
        ('low', 'Low Care'),
        ('medium', 'Medium Care'),
        ('high', 'High Care'),
    ]

    patient = models.ForeignKey(PatientDemographics, on_delete=models.CASCADE, related_name='survival_data')
    diagnosis = models.CharField(max_length=200)
    days_in_care = models.PositiveIntegerField(blank=True, null=True)
    pod = models.CharField(max_length=20, choices=POD_CHOICES, blank=True, null=True)
    dod = models.DateField(blank=True, null=True, verbose_name="Date of Death")
    date_case_registered = models.DateField()
    file_status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    level_of_care = models.CharField(max_length=20, choices=CARE_LEVEL_CHOICES, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.patient} - {self.diagnosis} ({self.file_status})"

    class Meta:
        verbose_name = "Survival Data"
        verbose_name_plural = "Survival Data"
