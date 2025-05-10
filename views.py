import pandas as pd
from lifelines import KaplanMeierFitter
from django.shortcuts import render, redirect
from .models import PatientSurvival, SurvivalData
from app1.models import PatientDemographics
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import base64
from django.contrib import messages
from .forms import SurvivalDataForm
import plotly.express as px
from plotly.offline import plot
import plotly.graph_objects as go


def survival(request):
    try:
        # Query data from both models
        patient_records = PatientSurvival.objects.all()
        survival_records = SurvivalData.objects.all()

        if not patient_records.exists() and not survival_records.exists():
            return render(request, 'survival_analysis/results.html', {
                'has_data': False,
                'message': 'No survival data available. Please add data first.'
            })

        context = {'has_data': True}

        # --- 1. PatientSurvival Analysis ---
        if patient_records.exists():
            df_patient = pd.DataFrame.from_records(patient_records.values(
                'event_occurred', 'entry_date', 'last_followup'
            ))
            df_patient['duration'] = (pd.to_datetime(df_patient['last_followup']) -
                                      pd.to_datetime(df_patient['entry_date'])).dt.days

            kmf = KaplanMeierFitter()
            kmf.fit(df_patient['duration'], df_patient['event_occurred'])

            # Prepare DataFrame for Plotly
            km_df = kmf.survival_function_.reset_index()
            km_df = km_df.rename(columns={
                'timeline': 'Time (days)',
                'Overall Survival': 'Survival Probability'
            })

            fig_patient = px.line(
                km_df,
                x='Time (days)',
                y='Survival Probability',
                title='<b>Patient Survival Analysis</b>',
                labels={'Survival Probability': 'Survival Probability'}
            )
            fig_patient.update_layout(
                hovermode="x unified",
                plot_bgcolor='white',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray', range=[0, 1])
            )
            context['patient_plot'] = fig_patient.to_html(full_html=False)

        # --- 2. SurvivalData Analysis ---
        if survival_records.exists():
            df_survival = pd.DataFrame(list(survival_records.values(
                'days_in_care', 'file_status', 'diagnosis', 'level_of_care'
            )))
            df_survival['event'] = df_survival['file_status'].apply(
                lambda x: 1 if x == 'closed_died' else 0
            )

            # Overall survival curve
            kmf = KaplanMeierFitter()
            kmf.fit(df_survival['days_in_care'].dropna(),
                    df_survival['event'])

            km_df = kmf.survival_function_.reset_index()
            km_df = km_df.rename(columns={
                'timeline': 'Time (days)',
                'KM_estimate': 'Survival Probability'
            })

            fig_overall = px.line(
                km_df,
                x='Time (days)',
                y='Survival Probability',
                title='<b>Overall Survival Analysis</b>'
            )
            fig_overall.update_layout(
                hovermode="x unified",
                plot_bgcolor='white',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray', range=[0, 1])
            )

            # Grouped analysis (by diagnosis)
            diagnosis_figs = {}
            for diagnosis in df_survival['diagnosis'].unique():
                subset = df_survival[df_survival['diagnosis'] == diagnosis]
                kmf.fit(subset['days_in_care'], subset['event'])

                km_df = kmf.survival_function_.reset_index()
                km_df = km_df.rename(columns={
                    'timeline': 'Time (days)',
                    'KM_estimate': 'Survival Probability'
                })

                fig = px.line(
                    km_df,
                    x='Time (days)',
                    y='Survival Probability',
                    title=f'<b>Diagnosis: {diagnosis}</b>'
                )
                diagnosis_figs[diagnosis] = fig.to_html(full_html=False)

            context.update({
                'overall_plot': fig_overall.to_html(full_html=False),
                'diagnosis_plots': diagnosis_figs,
                'diagnoses': list(diagnosis_figs.keys())
            })

        return render(request, 'survival_analysis/results.html', context)

    except Exception as e:
        return render(request, 'survival_analysis/results.html', {
            'has_data': False,
            'message': f'Error generating analysis: {str(e)}'
        })

def add_survival_data(request):
    if request.method == 'POST':
        form = SurvivalDataForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('survival_analysis')
    else:
        form = SurvivalDataForm()

    return render(request, 'survival_analysis/add_survival_data.html', {'form': form})

def import_survival_data(request):
    if request.method == 'POST' and request.FILES.get('survival_file'):
        try:
            file = request.FILES['survival_file']
            df = pd.read_excel(file)

            # Convert date columns if they exist
            date_columns = ['Dod', 'DateCaseRegistered']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Process each row
            success_count = 0
            for _, row in df.iterrows():
                try:
                    patient = PatientDemographics.objects.get(referral_number=row['Ref Number'])

                    # Create or update survival data
                    SurvivalData.objects.update_or_create(
                        patient=patient,
                        defaults={
                            'diagnosis': row.get('Diagnosis', ''),
                            'days_in_care': row.get('DaysInCare', None),
                            'pod': row.get('Pod', '').lower() if pd.notna(row.get('Pod')) else None,
                            'dod': row.get('Dod', None),
                            'date_case_registered': row.get('DateCaseRegistered', timezone.now().date()),
                            'file_status': row.get('FileStatus', 'active').lower().replace(' ', '_'),
                            'level_of_care': row.get('Levelofcare', '').lower() if pd.notna(
                                row.get('Levelofcare')) else None,
                        }
                    )
                    success_count += 1
                except (PatientDemographics.DoesNotExist, KeyError) as e:
                    continue

            messages.success(request, f'Successfully imported {success_count} records!')
            return redirect('survival_analysis')
        except Exception as e:
            messages.error(request, f'Error importing data: {str(e)}')

    return render(request, 'survival_analysis/import_survival_data.html')

def predictive_analytics(request):
    # Get all survival data
    survival_data = SurvivalData.objects.all()

    # Prepare data for Kaplan-Meier analysis
    if survival_data.exists():
        # Convert to DataFrame for analysis
        data = pd.DataFrame(list(survival_data.values(
            'id', 'days_in_care', 'file_status', 'diagnosis', 'level_of_care'
        )))

        # Create event column (1 if died, 0 otherwise)
        data['event'] = data['file_status'].apply(lambda x: 1 if x == 'closed_died' else 0)

        # Filter out cases with no days_in_care
        data = data.dropna(subset=['days_in_care'])

        if not data.empty:
            # Kaplan-Meier analysis
            kmf = KaplanMeierFitter()

            # Overall survival
            kmf.fit(data['days_in_care'], data['event'], label='Overall Survival')
            overall_survival = kmf.survival_function_.reset_index()

            # By diagnosis
            diagnoses = data['diagnosis'].unique()
            diagnosis_curves = {}
            for diagnosis in diagnoses:
                subset = data[data['diagnosis'] == diagnosis]
                kmf.fit(subset['days_in_care'], subset['event'], label=diagnosis)
                diagnosis_curves[diagnosis] = kmf.survival_function_.reset_index()

            # By care level
            care_levels = data['level_of_care'].dropna().unique()
            care_level_curves = {}
            for level in care_levels:
                subset = data[data['level_of_care'] == level]
                kmf.fit(subset['days_in_care'], subset['event'], label=level)
                care_level_curves[level] = kmf.survival_function_.reset_index()

            # Create visualizations
            overall_fig = px.line(
                overall_survival,
                x='timeline',
                y='KM_estimate',
                title='Overall Survival Curve',
                labels={'timeline': 'Days in Care', 'KM_estimate': 'Survival Probability'}
            )

            # Convert figures to JSON for template
            overall_graph = overall_fig.to_json()

            context = {
                'has_data': True,
                'overall_graph': overall_graph,
                'total_cases': len(data),
                'death_cases': sum(data['event']),
                'survival_rate': 1 - (sum(data['event']) / len(data)),
                'diagnoses': diagnoses,
                'care_levels': care_levels,
            }
        else:
            context = {'has_data': False, 'message': 'No valid survival data available for analysis.'}
    else:
        context = {'has_data': False, 'message': 'No survival data available.'}

    return render(request, 'survival_data/results.html', context)


from django.http import HttpResponse
from openpyxl import Workbook


def export_survival_data(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="survival_data.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.title = "Survival Data"

    # Add headers
    headers = [
        'Patient ID', 'Patient Name', 'Diagnosis',
        'Days in Care', 'Place of Death', 'Date of Death',
        'Status', 'Level of Care'
    ]
    ws.append(headers)

    # Add data
    for data in SurvivalData.objects.all().select_related('patient'):
        ws.append([
            data.patient.id,
            str(data.patient),
            data.diagnosis,
            data.days_in_care or '',
            data.get_pod_display() if data.pod else '',
            data.dod.strftime('%Y-%m-%d') if data.dod else '',
            data.get_file_status_display(),
            data.get_level_of_care_display() if data.level_of_care else ''
        ])

    wb.save(response)
    return response


def individual_prediction(request, patient_id):
    try:
        patient = PatientDemographics.objects.get(pk=patient_id)
        survival_data = SurvivalData.objects.filter(patient=patient).first()

        if not survival_data:
            return render(request, 'survival_analysis/individual.html', {
                'patient': patient,
                'has_data': False,
                'message': 'No survival data available for this patient.'
            })

        # Simple prediction logic (replace with your actual model)
        risk_score = 0.5  # Placeholder - calculate based on actual data

        return render(request, 'survival_analysis/individual.html', {
            'patient': patient,
            'survival_data': survival_data,
            'risk_score': f"{risk_score * 100:.1f}%",
            'has_data': True
        })
    except PatientDemographics.DoesNotExist:
        raise Http404("Patient not found")