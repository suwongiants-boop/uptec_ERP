from django.contrib import admin

from apps.documents.models import (
    DocumentBlock,
    DocumentRevisionAsset,
    DocumentRevisionRequest,
    DocumentTemplate,
    DocumentVersionSnapshot,
    GeneratedDocument,
    GenerationJob,
    ReferenceDocument,
)


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "template_type", "is_active", "updated_at")
    list_filter = ("template_type", "is_active")
    search_fields = ("name", "description")


@admin.register(DocumentBlock)
class DocumentBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "block_type", "approval_status", "template", "updated_at")
    list_filter = ("block_type", "approval_status", "template")
    search_fields = ("title", "content", "tags")
    filter_horizontal = ("technologies", "references", "patents", "certifications")
    autocomplete_fields = ("template",)


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "template", "company", "status", "created_by", "updated_at")
    list_filter = ("status", "template__template_type")
    search_fields = ("title", "company__name", "opportunity__title")
    autocomplete_fields = ("template", "company", "opportunity", "created_by")


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = ("document", "status", "output_format", "requested_by", "created_at")
    list_filter = ("status", "output_format")
    search_fields = ("document__title", "execution_log")
    autocomplete_fields = ("document", "requested_by")


@admin.register(ReferenceDocument)
class ReferenceDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "get_category_display", "file_format", "company", "is_active", "updated_at")
    list_filter = ("category", "file_format", "is_active")
    search_fields = ("title", "summary", "extracted_text", "tags", "company__name")
    autocomplete_fields = ("company", "opportunity", "uploaded_by")


@admin.register(DocumentRevisionRequest)
class DocumentRevisionRequestAdmin(admin.ModelAdmin):
    list_display = ("document", "request_round", "status", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("document__title", "general_feedback", "text_feedback", "image_feedback")
    autocomplete_fields = ("document", "created_by")


@admin.register(DocumentRevisionAsset)
class DocumentRevisionAssetAdmin(admin.ModelAdmin):
    list_display = ("revision_request", "original_name", "created_at")
    search_fields = ("revision_request__document__title", "original_name", "note")
    autocomplete_fields = ("revision_request",)


@admin.register(DocumentVersionSnapshot)
class DocumentVersionSnapshotAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "source_event", "sync_status", "sync_commit_hash", "created_at")
    list_filter = ("source_event", "sync_status")
    search_fields = ("document__title", "note", "sync_message", "sync_commit_hash")
    autocomplete_fields = ("document",)
