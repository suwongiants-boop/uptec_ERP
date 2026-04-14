from django import forms

from apps.crm.models import Company, Opportunity


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "company_type",
            "industry",
            "website",
            "summary",
            "is_active",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
        }


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = [
            "company",
            "title",
            "stage",
            "customer_need",
            "expected_value",
            "probability",
            "due_date",
            "next_action",
        ]
        widgets = {
            "customer_need": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
