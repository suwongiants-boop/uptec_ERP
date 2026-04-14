from django.db.models import Count
from django.views.generic import TemplateView

from apps.crm.models import Company, Opportunity
from apps.documents.models import GeneratedDocument
from apps.knowledge.models import Certification, Patent, Reference, Technology


class DashboardView(TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "companies": Company.objects.count(),
            "opportunities": Opportunity.objects.count(),
            "technologies": Technology.objects.count(),
            "references": Reference.objects.count(),
            "patents": Patent.objects.count(),
            "certifications": Certification.objects.count(),
            "documents": GeneratedDocument.objects.count(),
        }
        context["recent_opportunities"] = (
            Opportunity.objects.select_related("company").order_by("-updated_at")[:5]
        )
        context["recent_documents"] = (
            GeneratedDocument.objects.select_related("template", "created_by")
            .order_by("-updated_at")[:5]
        )
        stage_counts = Opportunity.objects.values("stage").annotate(total=Count("id")).order_by("stage")
        context["opportunity_stage_counts"] = [
            {
                "code": row["stage"],
                "label": Opportunity.Stage(row["stage"]).label,
                "total": row["total"],
            }
            for row in stage_counts
        ]
        return context
