from django.urls import path

from apps.documents.views import (
    AssembleDocumentView,
    DocumentGenerationCenterView,
    DocumentTemplateListView,
    ExportDocumentView,
    GeneratedDocumentDetailView,
    GeneratedDocumentListView,
    ReferenceDocumentLibraryView,
)


urlpatterns = [
    path("generator/", DocumentGenerationCenterView.as_view(), name="document-generation-center"),
    path("library/", ReferenceDocumentLibraryView.as_view(), name="reference-document-library"),
    path("templates/", DocumentTemplateListView.as_view(), name="document-template-list"),
    path("generated/", GeneratedDocumentListView.as_view(), name="generated-document-list"),
    path("generated/<int:pk>/", GeneratedDocumentDetailView.as_view(), name="generated-document-detail"),
    path("generated/<int:pk>/assemble/", AssembleDocumentView.as_view(), name="generated-document-assemble"),
    path("generated/<int:pk>/export/<str:export_format>/", ExportDocumentView.as_view(), name="generated-document-export"),
]
