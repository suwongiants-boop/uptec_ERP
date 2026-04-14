from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.crm.models import Company, Opportunity
from apps.knowledge.models import Certification, Patent, Reference, Technology


class DocumentTemplate(TimeStampedModel):
    class TemplateType(models.TextChoices):
        COMPANY_OVERVIEW = "company_overview", "회사소개서"
        SALES_PROPOSAL = "sales_proposal", "영업 제안서"
        GOVERNMENT_PROPOSAL = "government_proposal", "정부과제 문서"
        DEMO_REPORT = "demo_report", "실증 보고서"
        MEETING_NOTE = "meeting_note", "회의록"

    name = models.CharField(max_length=255)
    template_type = models.CharField(max_length=40, choices=TemplateType.choices)
    description = models.TextField(blank=True)
    source_file = models.FileField(upload_to="document_templates/", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["template_type", "name"]

    def __str__(self) -> str:
        return self.name


class ReferenceDocument(TimeStampedModel):
    class FileFormat(models.TextChoices):
        PPTX = "pptx", "PPT"
        XLSX = "xlsx", "Excel"
        PDF = "pdf", "PDF"
        DOCX = "docx", "Word"
        ETC = "etc", "기타"

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=40, choices=DocumentTemplate.TemplateType.choices)
    file_format = models.CharField(max_length=20, choices=FileFormat.choices, default=FileFormat.PDF)
    source_file = models.FileField(upload_to="reference_documents/")
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reference_documents",
    )
    opportunity = models.ForeignKey(
        Opportunity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reference_documents",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_reference_documents",
    )
    summary = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="예: company,overview,solution",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class DocumentBlock(TimeStampedModel):
    class BlockType(models.TextChoices):
        TEXT = "text", "텍스트"
        SLIDE = "slide", "슬라이드"
        TABLE = "table", "표"
        IMAGE = "image", "이미지"

    class ApprovalStatus(models.TextChoices):
        DRAFT = "draft", "초안"
        APPROVED = "approved", "승인"
        ARCHIVED = "archived", "보관"

    template = models.ForeignKey(
        DocumentTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blocks",
    )
    title = models.CharField(max_length=255)
    block_type = models.CharField(max_length=20, choices=BlockType.choices, default=BlockType.TEXT)
    content = models.TextField()
    tags = models.CharField(max_length=255, blank=True)
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.DRAFT,
    )
    technologies = models.ManyToManyField(Technology, related_name="document_blocks", blank=True)
    references = models.ManyToManyField(Reference, related_name="document_blocks", blank=True)
    patents = models.ManyToManyField(Patent, related_name="document_blocks", blank=True)
    certifications = models.ManyToManyField(Certification, related_name="document_blocks", blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class GeneratedDocument(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "초안"
        REVIEW = "review", "검토중"
        APPROVED = "approved", "승인완료"
        EXPORTED = "exported", "배포완료"

    title = models.CharField(max_length=255)
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.PROTECT,
        related_name="generated_documents",
    )
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_documents",
    )
    opportunity = models.ForeignKey(
        Opportunity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_documents",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_documents",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    assembled_content = models.JSONField(default=dict, blank=True)
    exported_file = models.FileField(upload_to="generated_documents/", blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class DocumentRevisionRequest(TimeStampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        IN_PROGRESS = "in_progress", "In Progress"
        APPLIED = "applied", "Applied"

    document = models.ForeignKey(
        GeneratedDocument,
        on_delete=models.CASCADE,
        related_name="revision_requests",
    )
    request_round = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    general_feedback = models.TextField(blank=True)
    text_feedback = models.TextField(blank=True)
    image_feedback = models.TextField(blank=True)
    block_feedback = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="document_revision_requests",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.document.title} revision {self.request_round}"


class DocumentRevisionAsset(TimeStampedModel):
    revision_request = models.ForeignKey(
        DocumentRevisionRequest,
        on_delete=models.CASCADE,
        related_name="assets",
    )
    image_file = models.FileField(upload_to="document_revision_assets/")
    original_name = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.original_name or self.image_file.name


class DocumentVersionSnapshot(TimeStampedModel):
    class SourceEvent(models.TextChoices):
        INITIAL_GENERATION = "initial_generation", "Initial Generation"
        REVISION_REGENERATION = "revision_regeneration", "Revision Regeneration"
        MANUAL_REGENERATION = "manual_regeneration", "Manual Regeneration"

    class SyncStatus(models.TextChoices):
        PENDING_SETUP = "pending_setup", "Pending Setup"
        COMMITTED_LOCAL = "committed_local", "Committed Locally"
        SYNCED = "synced", "Synced"
        FAILED = "failed", "Failed"

    document = models.ForeignKey(
        GeneratedDocument,
        on_delete=models.CASCADE,
        related_name="version_snapshots",
    )
    version_number = models.PositiveIntegerField()
    source_event = models.CharField(max_length=40, choices=SourceEvent.choices)
    note = models.CharField(max_length=255, blank=True)
    generation_request = models.TextField(blank=True)
    snapshot_payload = models.JSONField(default=dict, blank=True)
    rendered_html = models.TextField(blank=True)
    sync_status = models.CharField(max_length=30, choices=SyncStatus.choices, default=SyncStatus.PENDING_SETUP)
    sync_message = models.TextField(blank=True)
    sync_commit_hash = models.CharField(max_length=80, blank=True)
    sync_repo_path = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["-version_number", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["document", "version_number"], name="unique_document_version_snapshot")
        ]

    def __str__(self) -> str:
        return f"{self.document.title} v{self.version_number}"


class GenerationJob(TimeStampedModel):
    class JobStatus(models.TextChoices):
        QUEUED = "queued", "대기"
        RUNNING = "running", "실행중"
        FAILED = "failed", "실패"
        COMPLETED = "completed", "완료"

    document = models.ForeignKey(GeneratedDocument, on_delete=models.CASCADE, related_name="jobs")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generation_jobs",
    )
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.QUEUED)
    output_format = models.CharField(max_length=20, default="pptx")
    execution_log = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.document.title} ({self.output_format})"
