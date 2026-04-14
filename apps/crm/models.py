from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Company(TimeStampedModel):
    class CompanyType(models.TextChoices):
        CUSTOMER = "customer", "고객사"
        PARTNER = "partner", "파트너"
        AGENCY = "agency", "기관"
        INTERNAL = "internal", "내부"

    name = models.CharField(max_length=255)
    company_type = models.CharField(max_length=20, choices=CompanyType.choices, default=CompanyType.CUSTOMER)
    industry = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Contact(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=120)
    title = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["company__name", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.company.name})"


class Opportunity(TimeStampedModel):
    class Stage(models.TextChoices):
        LEAD = "lead", "리드"
        QUALIFIED = "qualified", "검토중"
        PROPOSAL = "proposal", "제안"
        NEGOTIATION = "negotiation", "협상"
        WON = "won", "수주"
        LOST = "lost", "실주"

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="opportunities")
    primary_contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL, related_name="opportunities")
    title = models.CharField(max_length=255)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.LEAD)
    customer_need = models.TextField(blank=True)
    expected_value = models.DecimalField(max_digits=14, decimal_places=0, null=True, blank=True)
    probability = models.PositiveSmallIntegerField(default=10)
    due_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="owned_opportunities")
    next_action = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title
