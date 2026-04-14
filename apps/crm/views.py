from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views.generic import DetailView, ListView

from apps.crm.forms import CompanyForm, OpportunityForm
from apps.crm.models import Company, Opportunity


class CompanyListView(ListView):
    model = Company
    template_name = "crm/company_list.html"
    context_object_name = "companies"

    def get_queryset(self):
        queryset = Company.objects.order_by("name")
        query = self.request.GET.get("q", "").strip()
        company_type = self.request.GET.get("company_type", "").strip()
        active = self.request.GET.get("active", "").strip()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(industry__icontains=query)
                | Q(summary__icontains=query)
            )
        if company_type:
            queryset = queryset.filter(company_type=company_type)
        if active in {"true", "false"}:
            queryset = queryset.filter(is_active=(active == "true"))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or CompanyForm()
        context["filters"] = {
            "q": self.request.GET.get("q", ""),
            "company_type": self.request.GET.get("company_type", ""),
            "active": self.request.GET.get("active", ""),
        }
        context["company_type_choices"] = Company.CompanyType.choices
        return context

    def post(self, request, *args, **kwargs):
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save()
            messages.success(request, "고객사를 등록했습니다.")
            return HttpResponseRedirect(f"/crm/companies/{company.pk}/")
        messages.error(request, "고객사 등록 중 입력값을 다시 확인해주세요.")
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


class CompanyDetailView(DetailView):
    model = Company
    template_name = "crm/company_detail.html"
    context_object_name = "company"


class OpportunityListView(ListView):
    model = Opportunity
    template_name = "crm/opportunity_list.html"
    context_object_name = "opportunities"

    def get_queryset(self):
        queryset = Opportunity.objects.select_related("company", "owner").order_by("-updated_at")
        query = self.request.GET.get("q", "").strip()
        stage = self.request.GET.get("stage", "").strip()
        company_id = self.request.GET.get("company", "").strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(customer_need__icontains=query)
                | Q(next_action__icontains=query)
                | Q(company__name__icontains=query)
            )
        if stage:
            queryset = queryset.filter(stage=stage)
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or OpportunityForm()
        context["filters"] = {
            "q": self.request.GET.get("q", ""),
            "stage": self.request.GET.get("stage", ""),
            "company": self.request.GET.get("company", ""),
        }
        context["stage_choices"] = Opportunity.Stage.choices
        context["companies"] = Company.objects.filter(is_active=True).order_by("name")
        return context

    def post(self, request, *args, **kwargs):
        form = OpportunityForm(request.POST)
        if form.is_valid():
            opportunity = form.save(commit=False)
            if request.user.is_authenticated:
                opportunity.owner = request.user
            opportunity.save()
            messages.success(request, "영업기획을 등록했습니다.")
            return HttpResponseRedirect(f"/crm/opportunities/{opportunity.pk}/")
        messages.error(request, "영업기획 등록 중 입력값을 다시 확인해주세요.")
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))


class OpportunityDetailView(DetailView):
    model = Opportunity
    template_name = "crm/opportunity_detail.html"
    context_object_name = "opportunity"

    def get_queryset(self):
        return Opportunity.objects.select_related("company", "primary_contact", "owner")
