from django.urls import path

from apps.crm.views import CompanyDetailView, CompanyListView, OpportunityDetailView, OpportunityListView


urlpatterns = [
    path("companies/", CompanyListView.as_view(), name="company-list"),
    path("companies/<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
    path("opportunities/", OpportunityListView.as_view(), name="opportunity-list"),
    path("opportunities/<int:pk>/", OpportunityDetailView.as_view(), name="opportunity-detail"),
]
