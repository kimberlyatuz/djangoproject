from django.urls import path
from . import views

urlpatterns = [
    path('analysis/', views.survival, name='survival_analysis'),
    path('survival/add/', views.add_survival_data, name='add_survival_data'),
    path('survival/import/', views.import_survival_data, name='import_survival_data'),
    path('patient/<int:patient_id>/', views.individual_prediction, name='individual_prediction'),
    path('export/', views.export_survival_data, name='export_survival_data'),
]