import django_tables2 as tables
from .models import FormSubmission

class FormSubmissionTable(tables.Table):
    class Meta:
        model = FormSubmission
        fields = ('id', 'submitted_at', 'user', 'user_form', 'title', 'status')  # Fields to display
        attrs = {'class': 'table table-bordered table-striped'}  # Add Bootstrap classes (optional)