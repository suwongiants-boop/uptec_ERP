from django.contrib import admin

from apps.knowledge.models import Certification, Partner, PartnerHardware, Patent, Reference, ServiceOffering, Technology


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "category", "description", "approved_summary")


@admin.register(ServiceOffering)
class ServiceOfferingAdmin(admin.ModelAdmin):
    list_display = ("name", "target_industries", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description", "target_industries")
    filter_horizontal = ("technologies",)


@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "start_date", "end_date", "is_public", "updated_at")
    list_filter = ("is_public",)
    search_fields = ("title", "client__name", "summary", "impact")
    filter_horizontal = ("technologies", "service_offerings")


@admin.register(Patent)
class PatentAdmin(admin.ModelAdmin):
    list_display = ("title", "application_no", "registration_no", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("title", "application_no", "registration_no", "summary")
    filter_horizontal = ("related_technologies",)


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ("name", "issuer", "issued_on", "updated_at")
    search_fields = ("name", "issuer", "summary")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("company", "exclusive_scope", "is_preferred", "updated_at")
    list_filter = ("is_preferred",)
    search_fields = ("company__name", "exclusive_scope", "relationship_summary")
    autocomplete_fields = ("company",)


@admin.register(PartnerHardware)
class PartnerHardwareAdmin(admin.ModelAdmin):
    list_display = ("name", "partner", "category", "exclusive_supply", "updated_at")
    list_filter = ("category", "exclusive_supply")
    search_fields = ("name", "partner__company__name", "summary")
    filter_horizontal = ("applicable_technologies",)
    autocomplete_fields = ("partner",)
