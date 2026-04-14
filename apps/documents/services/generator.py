from apps.documents.models import DocumentBlock, GeneratedDocument


class DocumentAssembler:
    """
    Initial service layer for building approved document content from blocks.
    This MVP returns structured JSON that can later feed DOCX/PPTX generators.
    """

    def build_payload(self, document: GeneratedDocument) -> dict:
        approved_blocks = DocumentBlock.objects.filter(
            template=document.template,
            approval_status=DocumentBlock.ApprovalStatus.APPROVED,
        ).order_by("title")
        return {
            "document_id": document.id,
            "title": document.title,
            "template": document.template.name,
            "company": document.company.name if document.company else "",
            "opportunity": document.opportunity.title if document.opportunity else "",
            "blocks": [
                {
                    "title": block.title,
                    "type": block.block_type,
                    "content": block.content,
                    "tags": block.tags,
                }
                for block in approved_blocks
            ],
        }
