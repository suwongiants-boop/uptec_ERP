from django.contrib import admin

from apps.crm.models import Company, Contact, Opportunity


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "company_type", "industry", "is_active", "updated_at")
    list_filter = ("company_type", "industry", "is_active")
    search_fields = ("name", "industry", "summary")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "title", "email", "phone")
    list_filter = ("company",)
    search_fields = ("name", "company__name", "email", "phone")


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "stage", "probability", "expected_value", "due_date", "owner", "updated_at")
    list_filter = ("stage", "company__industry")
    search_fields = ("title", "company__name", "customer_need", "next_action")
    autocomplete_fields = ("company", "primary_contact", "owner")
