from django.db import models

from apps.core.models import TimeStampedModel
from apps.crm.models import Company


class Technology(TimeStampedModel):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    description = models.TextField()
    approved_summary = models.TextField(blank=True, help_text="AI and document generation should prefer this approved summary.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self) -> str:
        return self.name


class ServiceOffering(TimeStampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    technologies = models.ManyToManyField(Technology, related_name="service_offerings", blank=True)
    target_industries = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Reference(TimeStampedModel):
    title = models.CharField(max_length=255)
    client = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, related_name="references")
    technologies = models.ManyToManyField(Technology, related_name="references", blank=True)
    service_offerings = models.ManyToManyField(ServiceOffering, related_name="references", blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    summary = models.TextField()
    impact = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ["-end_date", "-updated_at"]

    def __str__(self) -> str:
        return self.title


class Patent(TimeStampedModel):
    title = models.CharField(max_length=255)
    application_no = models.CharField(max_length=100, blank=True)
    registration_no = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=100, blank=True)
    summary = models.TextField(blank=True)
    related_technologies = models.ManyToManyField(Technology, related_name="patents", blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class Certification(TimeStampedModel):
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True)
    issued_on = models.DateField(null=True, blank=True)
    summary = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Partner(TimeStampedModel):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="partner_profile")
    relationship_summary = models.TextField(blank=True)
    exclusive_scope = models.CharField(max_length=255, blank=True)
    is_preferred = models.BooleanField(default=False)

    class Meta:
        ordering = ["company__name"]

    def __str__(self) -> str:
        return self.company.name


class PartnerHardware(TimeStampedModel):
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name="hardware_items")
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    summary = models.TextField(blank=True)
    applicable_technologies = models.ManyToManyField(Technology, related_name="partner_hardware", blank=True)
    exclusive_supply = models.BooleanField(default=False)

    class Meta:
        ordering = ["partner__company__name", "name"]

    def __str__(self) -> str:
        return f"{self.partner.company.name} - {self.name}"
