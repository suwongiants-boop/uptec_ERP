from django.contrib import messages
from django.db.models import Count, Max
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.crm.models import Company, Opportunity
from apps.documents.forms import DocumentRevisionRequestForm, ReferenceDocumentForm
from apps.documents.models import (
    DocumentRevisionAsset,
    DocumentRevisionRequest,
    DocumentTemplate,
    GeneratedDocument,
    ReferenceDocument,
)
from apps.documents.services.comparison import ComparisonDocumentGenerator
from apps.documents.services.exporters import DocumentExportService
from apps.documents.services.generator import DocumentAssembler
from apps.documents.services.preview import DocumentPreviewBuilder
from apps.documents.services.versioning import DocumentVersioningService


class DocumentTemplateListView(ListView):
    model = DocumentTemplate
    template_name = "documents/template_list.html"
    context_object_name = "templates"


class GeneratedDocumentListView(ListView):
    model = GeneratedDocument
    template_name = "documents/generated_document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        queryset = GeneratedDocument.objects.select_related("template", "company", "opportunity", "created_by")
        opportunity_id = self.request.GET.get("opportunity")
        if opportunity_id:
            queryset = queryset.filter(opportunity_id=opportunity_id)
        return queryset.order_by("-updated_at")


class DocumentGenerationCenterView(TemplateView):
    template_name = "documents/generation_center.html"

    @staticmethod
    def _optional_related(model, raw_value):
        value = (raw_value or "").strip()
        if not value:
            return None
        try:
            value = int(value)
        except (TypeError, ValueError):
            return None
        return model.objects.filter(pk=value).first()

    @staticmethod
    def _active_template(raw_value):
        value = (raw_value or "").strip()
        if not value:
            return None
        try:
            value = int(value)
        except (TypeError, ValueError):
            return None
        return DocumentTemplate.objects.filter(pk=value, is_active=True).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        templates = list(DocumentTemplate.objects.filter(is_active=True).order_by("template_type", "name"))
        reference_counts = {
            item["template__template_type"]: item["total"]
            for item in GeneratedDocument.objects.values("template__template_type").annotate(total=Count("id"))
        }
        library_counts = {
            item["category"]: item["total"]
            for item in ReferenceDocument.objects.filter(is_active=True).values("category").annotate(total=Count("id"))
        }
        context["template_options"] = [
            {
                "id": item.id,
                "name": item.name,
                "template_type": item.template_type,
                "template_type_display": item.get_template_type_display(),
                "reference_count": reference_counts.get(item.template_type, 0),
                "library_count": library_counts.get(item.template_type, 0),
            }
            for item in templates
        ]
        context["companies"] = Company.objects.filter(is_active=True).order_by("name")
        context["opportunities"] = Opportunity.objects.select_related("company").order_by("-updated_at")
        context["selected_opportunity_id"] = self.request.GET.get("opportunity", "")
        context["posted"] = kwargs.get("posted") or {}
        return context

    def post(self, request, *args, **kwargs):
        template = self._active_template(request.POST.get("template_id"))
        if not template:
            messages.error(request, "문서 카테고리를 먼저 선택해주세요.")
            return self.render_to_response(self.get_context_data(posted=request.POST))

        generation_request = (request.POST.get("generation_request") or "").strip()
        company = self._optional_related(Company, request.POST.get("company_id"))
        opportunity = self._optional_related(Opportunity, request.POST.get("opportunity_id"))

        source_documents = list(
            GeneratedDocument.objects.select_related("template", "company", "opportunity")
            .filter(template__template_type=template.template_type)
            .order_by("-updated_at")
        )
        reference_documents = list(
            ReferenceDocument.objects.filter(category=template.template_type, is_active=True)
            .select_related("company", "opportunity")
            .order_by("-updated_at")
        )

        title = request.POST.get("title", "").strip() or f"{template.name}_초안"
        generated_document = GeneratedDocument.objects.create(
            title=title,
            template=template,
            company=company,
            opportunity=opportunity,
            created_by=request.user if request.user.is_authenticated else None,
            status=GeneratedDocument.Status.DRAFT,
        )

        base_payload = ComparisonDocumentGenerator().build_payload(
            generated_document,
            source_documents,
            reference_documents,
        )
        generated_document.assembled_content = DocumentPreviewBuilder().enrich_payload(
            generated_document,
            base_payload,
            generation_request=generation_request,
        )
        generated_document.save(update_fields=["assembled_content", "updated_at"])
        DocumentVersioningService().create_snapshot(
            generated_document,
            source_event="initial_generation",
            note="Initial prompt-based preview generation",
        )

        messages.success(
            request,
            "요청사항을 반영한 1차 HTML 미리보기를 생성했습니다. 상세 화면에서 수정 요청을 넣으면 2차 미리보기가 다시 만들어집니다.",
        )
        return redirect("generated-document-detail", pk=generated_document.pk)


class GeneratedDocumentDetailView(DetailView):
    model = GeneratedDocument
    template_name = "documents/generated_document_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return GeneratedDocument.objects.select_related(
            "template",
            "company",
            "opportunity",
            "created_by",
        ).prefetch_related("revision_requests__assets", "version_snapshots")

    def _block_feedback_rows(self, posted_values=None):
        assembled = self.object.assembled_content or {}
        blocks = assembled.get("blocks", [])
        posted_values = posted_values or {}
        return [
            {
                "index": index,
                "title": block.get("title", f"Section {index + 1}"),
                "type": block.get("type", "text"),
                "content": block.get("content", ""),
                "tags": block.get("tags", ""),
                "feedback_value": posted_values.get(f"block_feedback_{index}", ""),
            }
            for index, block in enumerate(blocks)
        ]

    def _revision_requests_queryset(self):
        return DocumentRevisionRequest.objects.filter(document=self.object).prefetch_related("assets").order_by("-created_at")

    def _extract_block_feedback(self):
        feedback_rows = []
        for block in self._block_feedback_rows(self.request.POST):
            requested_change = (self.request.POST.get(f"block_feedback_{block['index']}") or "").strip()
            if not requested_change:
                continue
            feedback_rows.append(
                {
                    "title": block["title"],
                    "type": block["type"],
                    "current_content": block["content"],
                    "requested_change": requested_change,
                }
            )
        return feedback_rows

    def _create_revision_request(self, form, block_feedback):
        latest_round = self.object.revision_requests.aggregate(max_round=Max("request_round"))["max_round"] or 0
        revision_request = form.save(commit=False)
        revision_request.document = self.object
        revision_request.request_round = latest_round + 1
        revision_request.created_by = self.request.user if self.request.user.is_authenticated else None
        revision_request.block_feedback = block_feedback
        revision_request.save()

        for image in self.request.FILES.getlist("additional_images"):
            DocumentRevisionAsset.objects.create(
                revision_request=revision_request,
                image_file=image,
                original_name=image.name,
            )

        return revision_request

    def _regenerate_preview(self):
        payload = self.object.assembled_content or {}
        if not payload.get("blocks"):
            payload = DocumentAssembler().build_payload(self.object)

        self.object.assembled_content = DocumentPreviewBuilder().enrich_payload(
            self.object,
            payload,
            generation_request=payload.get("generation_request", ""),
            revision_requests=self._revision_requests_queryset(),
        )
        self.object.save(update_fields=["assembled_content", "updated_at"])

    def get_context_data(self, **kwargs):
        assembled = self.object.assembled_content or {}
        if assembled.get("blocks") and not assembled.get("preview_pages"):
            self._regenerate_preview()
            assembled = self.object.assembled_content or {}

        context = super().get_context_data(**kwargs)
        context["summary"] = assembled.get("summary", {})
        context["blocks"] = assembled.get("blocks", [])
        context["generation_request"] = assembled.get("generation_request", "")
        context["preview_pages"] = assembled.get("preview_pages", [])
        context["preview_meta"] = assembled.get("preview_meta", {})
        context["preview_blocks"] = self._block_feedback_rows(kwargs.get("block_feedback_values"))
        context["revision_form"] = kwargs.get("revision_form") or DocumentRevisionRequestForm()
        context["revision_requests"] = self._revision_requests_queryset()
        context["version_snapshots"] = self.object.version_snapshots.all()
        context["is_category_reference_generation"] = (
            assembled.get("generation_mode") == "category_reference_generate"
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = DocumentRevisionRequestForm(request.POST, request.FILES)
        block_feedback = self._extract_block_feedback()
        uploaded_images = request.FILES.getlist("additional_images")

        if form.is_valid():
            if not any(
                [
                    form.cleaned_data.get("general_feedback"),
                    form.cleaned_data.get("text_feedback"),
                    form.cleaned_data.get("image_feedback"),
                    block_feedback,
                    uploaded_images,
                ]
            ):
                form.add_error(None, "적어도 하나 이상의 수정 요청 또는 이미지를 입력해주세요.")
            else:
                revision_request = self._create_revision_request(form, block_feedback)
                self.object.status = GeneratedDocument.Status.REVIEW
                self.object.save(update_fields=["status", "updated_at"])
                self._regenerate_preview()
                DocumentVersioningService().create_snapshot(
                    self.object,
                    source_event="revision_regeneration",
                    note=f"Revision round {revision_request.request_round} applied to HTML preview",
                )
                messages.success(
                    request,
                    f"{revision_request.request_round}차 수정 요청을 반영해 HTML 미리보기를 다시 생성했습니다.",
                )
                return redirect("generated-document-detail", pk=self.object.pk)

        messages.error(request, "수정 요청 저장 중 입력값을 다시 확인해주세요.")
        context = self.get_context_data(
            revision_form=form,
            block_feedback_values=request.POST,
        )
        return self.render_to_response(context)


class ReferenceDocumentLibraryView(TemplateView):
    template_name = "documents/reference_document_library.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or ReferenceDocumentForm()
        context["reference_documents"] = (
            ReferenceDocument.objects.select_related("company", "opportunity", "uploaded_by")
            .order_by("-updated_at")
        )
        return context

    def post(self, request, *args, **kwargs):
        form = ReferenceDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            reference_document = form.save(commit=False)
            reference_document.uploaded_by = request.user if request.user.is_authenticated else None
            reference_document.save()
            messages.success(request, "기존 문서를 보관소에 등록했습니다.")
            return HttpResponseRedirect("/documents/library/")

        messages.error(request, "기존 문서 등록 중 입력값을 다시 확인해주세요.")
        return self.render_to_response(self.get_context_data(form=form))


class AssembleDocumentView(View):
    def post(self, request, pk):
        document = GeneratedDocument.objects.select_related("template", "company", "opportunity").get(pk=pk)
        payload = document.assembled_content or {}
        if not payload.get("blocks"):
            payload = DocumentAssembler().build_payload(document)

        document.assembled_content = DocumentPreviewBuilder().enrich_payload(
            document,
            payload,
            generation_request=payload.get("generation_request", ""),
            revision_requests=document.revision_requests.all(),
        )
        document.save(update_fields=["assembled_content", "updated_at"])
        DocumentVersioningService().create_snapshot(
            document,
            source_event="manual_regeneration",
            note="Manual HTML preview regeneration",
        )
        messages.success(request, "현재 요청사항 기준으로 HTML 미리보기를 다시 생성했습니다.")
        return redirect("generated-document-detail", pk=pk)


class ExportDocumentView(View):
    def get(self, request, pk, export_format):
        document = (
            GeneratedDocument.objects.select_related("template", "company", "opportunity")
            .prefetch_related("revision_requests__assets")
            .get(pk=pk)
        )
        return DocumentExportService().build_response(document, export_format)
