from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from apps.crm.models import Company, Opportunity
from apps.documents.models import (
    DocumentBlock,
    DocumentRevisionRequest,
    DocumentTemplate,
    DocumentVersionSnapshot,
    GeneratedDocument,
    ReferenceDocument,
)
from apps.documents.services.comparison import ComparisonDocumentGenerator
from apps.documents.services.generator import DocumentAssembler


class DocumentAssemblerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="pass1234",
        )
        self.company = Company.objects.create(name="Test Customer")
        self.opportunity = Opportunity.objects.create(
            company=self.company,
            title="Test Proposal",
            stage=Opportunity.Stage.PROPOSAL,
            owner=self.user,
        )
        self.client = Client()

    def test_build_payload_includes_only_approved_blocks(self):
        template = DocumentTemplate.objects.create(
            name="Test Template",
            template_type=DocumentTemplate.TemplateType.SALES_PROPOSAL,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Approved Block",
            block_type=DocumentBlock.BlockType.TEXT,
            content="approved content",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Draft Block",
            block_type=DocumentBlock.BlockType.TEXT,
            content="draft content",
            approval_status=DocumentBlock.ApprovalStatus.DRAFT,
        )
        document = GeneratedDocument.objects.create(
            title="Generated Draft",
            template=template,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )

        payload = DocumentAssembler().build_payload(document)

        self.assertEqual(payload["company"], "Test Customer")
        self.assertEqual(len(payload["blocks"]), 1)
        self.assertEqual(payload["blocks"][0]["title"], "Approved Block")

    def test_compare_generator_reuses_and_generates_missing_blocks(self):
        source_template = DocumentTemplate.objects.create(
            name="Source Overview",
            template_type=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
        )
        target_template = DocumentTemplate.objects.create(
            name="Target Proposal",
            template_type=DocumentTemplate.TemplateType.SALES_PROPOSAL,
        )

        DocumentBlock.objects.create(
            template=source_template,
            title="Company Overview",
            block_type=DocumentBlock.BlockType.TEXT,
            content="source overview content",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )
        DocumentBlock.objects.create(
            template=target_template,
            title="Company Overview",
            block_type=DocumentBlock.BlockType.TEXT,
            content="",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )
        DocumentBlock.objects.create(
            template=target_template,
            title="Expected Effect",
            block_type=DocumentBlock.BlockType.TEXT,
            content="",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="effect,proposal",
        )

        source_document = GeneratedDocument.objects.create(
            title="Existing Overview",
            template=source_template,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )
        source_document.assembled_content = DocumentAssembler().build_payload(source_document)
        source_document.save(update_fields=["assembled_content"])

        target_document = GeneratedDocument.objects.create(
            title="Comparison Draft",
            template=target_template,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )

        payload = ComparisonDocumentGenerator().build_payload(target_document, [source_document])

        self.assertEqual(payload["summary"]["reused_block_count"], 1)
        self.assertEqual(payload["summary"]["generated_block_count"], 1)
        decisions = {block["title"]: block["decision"] for block in payload["blocks"]}
        self.assertEqual(decisions["Company Overview"], "reuse")
        self.assertEqual(decisions["Expected Effect"], "generate")

    def test_generation_center_uses_all_documents_in_selected_category(self):
        category_template_a = DocumentTemplate.objects.create(
            name="Sales Proposal A",
            template_type=DocumentTemplate.TemplateType.SALES_PROPOSAL,
        )
        category_template_b = DocumentTemplate.objects.create(
            name="Sales Proposal B",
            template_type=DocumentTemplate.TemplateType.SALES_PROPOSAL,
        )
        other_category_template = DocumentTemplate.objects.create(
            name="Company Overview C",
            template_type=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
        )

        for template in [category_template_a, category_template_b]:
            DocumentBlock.objects.create(
                template=template,
                title="Shared Overview",
                block_type=DocumentBlock.BlockType.TEXT,
                content=f"{template.name} content",
                approval_status=DocumentBlock.ApprovalStatus.APPROVED,
                tags="company,overview",
            )

        DocumentBlock.objects.create(
            template=other_category_template,
            title="Other Category Block",
            block_type=DocumentBlock.BlockType.TEXT,
            content="other category content",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )

        source_a = GeneratedDocument.objects.create(
            title="Sales Proposal Draft A",
            template=category_template_a,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )
        source_b = GeneratedDocument.objects.create(
            title="Sales Proposal Draft B",
            template=category_template_b,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )
        other_source = GeneratedDocument.objects.create(
            title="Company Overview Draft C",
            template=other_category_template,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )

        assembler = DocumentAssembler()
        for document in [source_a, source_b, other_source]:
            document.assembled_content = assembler.build_payload(document)
            document.save(update_fields=["assembled_content"])

        response = self.client.post(
            "/documents/generator/",
            {
                "title": "Category Reference Result",
                "template_id": str(category_template_a.id),
                "company_id": str(self.company.id),
                "opportunity_id": str(self.opportunity.id),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        created = GeneratedDocument.objects.get(title="Category Reference Result")
        summary = created.assembled_content["summary"]
        self.assertEqual(summary["source_document_count"], 2)
        self.assertIn("Sales Proposal Draft A", summary["source_document_titles"])
        self.assertIn("Sales Proposal Draft B", summary["source_document_titles"])
        self.assertNotIn("Company Overview Draft C", summary["source_document_titles"])

    def test_generation_center_includes_registered_reference_documents(self):
        template = DocumentTemplate.objects.create(
            name="Government Proposal",
            template_type=DocumentTemplate.TemplateType.GOVERNMENT_PROPOSAL,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Business Plan",
            block_type=DocumentBlock.BlockType.TEXT,
            content="",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="business,government",
        )

        reference_file = SimpleUploadedFile(
            "legacy-plan.pdf",
            b"legacy government proposal content",
            content_type="application/pdf",
        )
        ReferenceDocument.objects.create(
            title="Legacy Government Proposal",
            category=DocumentTemplate.TemplateType.GOVERNMENT_PROPOSAL,
            file_format=ReferenceDocument.FileFormat.PDF,
            source_file=reference_file,
            company=self.company,
            summary="legacy summary",
            extracted_text="legacy plan and market entry details",
            tags="business,government",
        )

        response = self.client.post(
            "/documents/generator/",
            {
                "title": "Government Category Reference",
                "template_id": str(template.id),
                "company_id": str(self.company.id),
                "opportunity_id": str(self.opportunity.id),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        created = GeneratedDocument.objects.get(title="Government Category Reference")
        summary = created.assembled_content["summary"]
        self.assertEqual(summary["reference_document_count"], 1)
        self.assertIn("Legacy Government Proposal", summary["reference_document_titles"])

    def test_generation_center_allows_blank_optional_relationships(self):
        template = DocumentTemplate.objects.create(
            name="Blank Optional Fields",
            template_type=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Company Overview",
            block_type=DocumentBlock.BlockType.TEXT,
            content="base overview",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )

        response = self.client.post(
            "/documents/generator/",
            {
                "title": "Blank Optional Generation",
                "template_id": str(template.id),
                "company_id": "",
                "opportunity_id": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        created = GeneratedDocument.objects.get(title="Blank Optional Generation")
        self.assertIsNone(created.company)
        self.assertIsNone(created.opportunity)
        self.assertTrue(created.assembled_content["preview_pages"])

    def test_generation_center_applies_prompt_to_first_html_preview(self):
        template = DocumentTemplate.objects.create(
            name="Prompt Driven Overview",
            template_type=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Company Overview",
            block_type=DocumentBlock.BlockType.TEXT,
            content="base overview",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )
        DocumentBlock.objects.create(
            template=template,
            title="Core Capabilities",
            block_type=DocumentBlock.BlockType.TEXT,
            content="capability content",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="capability,technology",
        )

        response = self.client.post(
            "/documents/generator/",
            {
                "title": "Latest Company Overview",
                "template_id": str(template.id),
                "generation_request": "Create the latest company overview in English with 10 pages.",
                "company_id": str(self.company.id),
                "opportunity_id": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        created = GeneratedDocument.objects.get(title="Latest Company Overview")
        self.assertEqual(created.assembled_content["generation_request"], "Create the latest company overview in English with 10 pages.")
        self.assertEqual(created.assembled_content["preview_meta"]["language"], "en")
        self.assertEqual(created.assembled_content["preview_meta"]["page_count"], 10)
        self.assertEqual(len(created.assembled_content["preview_pages"]), 10)
        version = DocumentVersionSnapshot.objects.get(document=created, version_number=1)
        self.assertEqual(version.source_event, DocumentVersionSnapshot.SourceEvent.INITIAL_GENERATION)
        self.assertTrue(version.rendered_html)

    def test_generation_center_builds_visual_preview_from_reference_documents(self):
        template = DocumentTemplate.objects.create(
            name="Visual Company Overview",
            template_type=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Company Overview",
            block_type=DocumentBlock.BlockType.TEXT,
            content="base company overview",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )
        DocumentBlock.objects.create(
            template=template,
            title="Representative References",
            block_type=DocumentBlock.BlockType.TEXT,
            content="base reference section",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="reference,case",
        )
        reference_file = SimpleUploadedFile(
            "visual-overview.pdf",
            b"visual overview reference",
            content_type="application/pdf",
        )
        ReferenceDocument.objects.create(
            title="Legacy Visual Company Deck",
            category=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
            file_format=ReferenceDocument.FileFormat.PDF,
            source_file=reference_file,
            company=self.company,
            summary="이미지 위주 회사소개 자료",
            extracted_text="company, overview, reference, field image assets",
            tags="company,overview,reference,case",
        )

        response = self.client.post(
            "/documents/generator/",
            {
                "title": "Visual First Overview",
                "template_id": str(template.id),
                "generation_request": "기존 보관 문서 활용 이미지 위주로 5장 짜리 만들어줘",
                "company_id": str(self.company.id),
                "opportunity_id": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        created = GeneratedDocument.objects.get(title="Visual First Overview")
        self.assertEqual(created.assembled_content["preview_meta"]["presentation_style"], "visual")
        self.assertEqual(created.assembled_content["preview_meta"]["page_count"], 5)
        self.assertTrue(any(page["visual_assets"] for page in created.assembled_content["preview_pages"]))
        self.assertTrue(
            any(
                asset["title"] == "Legacy Visual Company Deck"
                for page in created.assembled_content["preview_pages"]
                for asset in page["visual_assets"]
            )
        )

    def test_generated_document_detail_saves_revision_request_and_images(self):
        template = DocumentTemplate.objects.create(
            name="Revision Template",
            template_type=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Company Overview",
            block_type=DocumentBlock.BlockType.TEXT,
            content="initial overview",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )
        document = GeneratedDocument.objects.create(
            title="Revision Target",
            template=template,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )
        document.assembled_content = DocumentAssembler().build_payload(document)
        document.save(update_fields=["assembled_content"])

        image = SimpleUploadedFile(
            "revision-image.png",
            b"fake-image-bytes",
            content_type="image/png",
        )

        response = self.client.post(
            f"/documents/generated/{document.id}/",
            {
                "general_feedback": "Please make the second draft sharper.",
                "text_feedback": "Shorten the introduction.",
                "image_feedback": "Replace the hero image and add one field photo.",
                "block_feedback_0": "Use a more concise company introduction.",
                "additional_images": image,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        revision = DocumentRevisionRequest.objects.get(document=document)
        self.assertEqual(revision.request_round, 1)
        self.assertEqual(len(revision.block_feedback), 1)
        self.assertEqual(revision.block_feedback[0]["title"], "Company Overview")
        self.assertEqual(revision.assets.count(), 1)
        document.refresh_from_db()
        self.assertEqual(document.status, GeneratedDocument.Status.REVIEW)
        self.assertEqual(document.assembled_content["preview_meta"]["revision_count"], 1)
        self.assertTrue(document.assembled_content["preview_pages"])
        self.assertEqual(document.version_snapshots.count(), 1)
        snapshot = document.version_snapshots.first()
        self.assertEqual(snapshot.source_event, DocumentVersionSnapshot.SourceEvent.REVISION_REGENERATION)

    def test_generated_document_can_export_html_preview(self):
        template = DocumentTemplate.objects.create(
            name="Export Template",
            template_type=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Company Overview",
            block_type=DocumentBlock.BlockType.TEXT,
            content="export ready content",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )
        document = GeneratedDocument.objects.create(
            title="Export Ready Document",
            template=template,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )
        document.assembled_content = {
            **DocumentAssembler().build_payload(document),
            "generation_request": "Create an English company overview in 5 pages.",
        }
        document.assembled_content["preview_pages"] = [
            {
                "page_label": "Page 1",
                "theme_label": "Cover",
                "title": "Export Ready Document",
                "body": ["Preview body"],
                "bullets": ["Bullet 1"],
                "image_note": "Use a clean engineering visual.",
            }
        ]
        document.save(update_fields=["assembled_content"])

        response = self.client.get(f"/documents/generated/{document.id}/export/html/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")

    def test_manual_preview_regeneration_creates_version_snapshot(self):
        template = DocumentTemplate.objects.create(
            name="Manual Regen Template",
            template_type=DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
        )
        DocumentBlock.objects.create(
            template=template,
            title="Company Overview",
            block_type=DocumentBlock.BlockType.TEXT,
            content="manual regen content",
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            tags="company,overview",
        )
        document = GeneratedDocument.objects.create(
            title="Manual Regen Document",
            template=template,
            company=self.company,
            opportunity=self.opportunity,
            created_by=self.user,
        )
        document.assembled_content = DocumentAssembler().build_payload(document)
        document.save(update_fields=["assembled_content"])

        response = self.client.post(f"/documents/generated/{document.id}/assemble/", follow=True)

        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        snapshot = DocumentVersionSnapshot.objects.get(document=document)
        self.assertEqual(snapshot.source_event, DocumentVersionSnapshot.SourceEvent.MANUAL_REGENERATION)
