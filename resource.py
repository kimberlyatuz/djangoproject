from import_export import resources
from .models import FormSubmission

class FormSubmissionResource(resources.ModelResource):
    class Meta:
        model = FormSubmission

    def export(self, selected_ids=None, *args, **kwargs):
        if selected_ids:
            queryset = self.get_queryset().filter(id__in=selected_ids)
        else:
            queryset = self.get_queryset()

        dataset = super().export(queryset, *args, **kwargs)
        return dataset

