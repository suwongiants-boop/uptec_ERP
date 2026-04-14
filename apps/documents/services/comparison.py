from __future__ import annotations

from dataclasses import dataclass

from apps.documents.models import DocumentBlock, GeneratedDocument, ReferenceDocument
from apps.documents.services.generator import DocumentAssembler


@dataclass
class SourceBlock:
    document_id: int
    document_title: str
    template_name: str
    title: str
    block_type: str
    content: str
    tags: str

    @property
    def normalized_title(self) -> str:
        return normalize_text(self.title)

    @property
    def tag_set(self) -> set[str]:
        return {tag.strip().lower() for tag in self.tags.split(",") if tag.strip()}


def normalize_text(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


class ComparisonDocumentGenerator:
    def build_payload(
        self,
        document: GeneratedDocument,
        source_documents: list[GeneratedDocument],
        reference_documents: list[ReferenceDocument] | None = None,
    ) -> dict:
        reference_documents = reference_documents or []
        target_blocks = list(
            DocumentBlock.objects.filter(
                template=document.template,
                approval_status=DocumentBlock.ApprovalStatus.APPROVED,
            ).order_by("title")
        )
        source_blocks = self._collect_source_blocks(source_documents, reference_documents)

        block_payloads = []
        reused_count = 0
        generated_count = 0

        for block in target_blocks:
            matched = self._find_match(block, source_blocks)
            if matched:
                reused_count += 1
                block_payloads.append(
                    {
                        "title": block.title,
                        "type": block.block_type,
                        "tags": block.tags,
                        "decision": "reuse",
                        "decision_label": "재사용",
                        "reason": "동일 제목 또는 유사 태그를 가진 기존 문서를 재사용합니다.",
                        "source_document": matched.document_title,
                        "source_template": matched.template_name,
                        "content": matched.content,
                    }
                )
            else:
                generated_count += 1
                block_payloads.append(
                    {
                        "title": block.title,
                        "type": block.block_type,
                        "tags": block.tags,
                        "decision": "generate",
                        "decision_label": "신규 생성",
                        "reason": "재사용 가능한 동일 섹션이 없어 새로 작성해야 합니다.",
                        "source_document": "",
                        "source_template": "",
                        "content": self._draft_missing_block(
                            document,
                            block,
                            source_documents,
                            reference_documents,
                        ),
                    }
                )

        return {
            "generation_mode": "category_reference_generate",
            "summary": {
                "target_template": document.template.name,
                "target_template_type": document.template.get_template_type_display(),
                "source_document_count": len(source_documents),
                "source_document_titles": [doc.title for doc in source_documents],
                "reference_document_count": len(reference_documents),
                "reference_document_titles": [doc.title for doc in reference_documents],
                "reused_block_count": reused_count,
                "generated_block_count": generated_count,
            },
            "blocks": block_payloads,
        }

    def _collect_source_blocks(
        self,
        source_documents: list[GeneratedDocument],
        reference_documents: list[ReferenceDocument],
    ) -> list[SourceBlock]:
        assembler = DocumentAssembler()
        collected: list[SourceBlock] = []

        for document in source_documents:
            payload = document.assembled_content or assembler.build_payload(document)
            for block in payload.get("blocks", []):
                collected.append(
                    SourceBlock(
                        document_id=document.id,
                        document_title=document.title,
                        template_name=document.template.name,
                        title=block.get("title", ""),
                        block_type=block.get("type", "text"),
                        content=block.get("content", ""),
                        tags=block.get("tags", ""),
                    )
                )

        for document in reference_documents:
            content = document.extracted_text.strip() or document.summary.strip()
            if not content:
                continue
            collected.append(
                SourceBlock(
                    document_id=document.id,
                    document_title=document.title,
                    template_name=document.get_category_display(),
                    title=document.title,
                    block_type=document.file_format,
                    content=content,
                    tags=document.tags,
                )
            )
        return collected

    def _find_match(self, target_block: DocumentBlock, source_blocks: list[SourceBlock]) -> SourceBlock | None:
        target_title = normalize_text(target_block.title)
        target_tags = {tag.strip().lower() for tag in target_block.tags.split(",") if tag.strip()}

        for source in source_blocks:
            if source.normalized_title and source.normalized_title == target_title:
                return source

        if target_tags:
            for source in source_blocks:
                if source.tag_set.intersection(target_tags):
                    return source

        return None

    def _draft_missing_block(
        self,
        document: GeneratedDocument,
        block: DocumentBlock,
        source_documents: list[GeneratedDocument],
        reference_documents: list[ReferenceDocument],
    ) -> str:
        company_name = document.company.name if document.company else "대상 고객"
        source_titles = ", ".join(doc.title for doc in source_documents) if source_documents else "참조 문서 없음"
        reference_titles = ", ".join(doc.title for doc in reference_documents) if reference_documents else "등록된 기존 문서 없음"
        return (
            f"{company_name} 기준으로 '{block.title}' 섹션은 신규 생성이 필요합니다. "
            f"현재 선택된 기존 문서({source_titles})에서 직접 재사용할 항목을 찾지 못했으므로 "
            f"등록된 기존 문서({reference_titles})를 참고해 "
            f"{document.template.get_template_type_display()} 목적에 맞게 새로 작성해야 합니다."
        )
