from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.crm.models import Company, Opportunity
from apps.documents.models import DocumentBlock, DocumentTemplate, GeneratedDocument, ReferenceDocument
from apps.documents.services.generator import DocumentAssembler
from apps.knowledge.models import Certification, Patent, Reference, Technology


class Command(BaseCommand):
    help = "Seed sample data for the Uptec document-centric ERP MVP."

    def handle(self, *args, **options):
        user_model = get_user_model()
        admin_user, _ = user_model.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.email = "admin@example.com"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.set_password("admin1234!")
        admin_user.save()

        company, _ = Company.objects.get_or_create(
            name="한국남부발전",
            defaults={
                "industry": "발전",
                "summary": "재생에너지와 전력 인프라 안정화 관련 제안 대상 고객사",
            },
        )

        opportunity, _ = Opportunity.objects.get_or_create(
            title="전력구 이상감지 통합 제안",
            company=company,
            defaults={
                "stage": Opportunity.Stage.PROPOSAL,
                "customer_need": "전력구 화재 전조와 진동 이상을 조기 감지하고 보고서까지 자동화하는 체계가 필요",
                "probability": 60,
                "owner": admin_user,
                "next_action": "비교 생성으로 고객 맞춤 제안서 초안 작성",
            },
        )

        technology, _ = Technology.objects.get_or_create(
            name="DFOS 기반 전력구 이상 감지",
            defaults={
                "category": "인프라 안전",
                "description": "광섬유 기반 장거리 연속 감시와 이벤트 판별 기술",
                "approved_summary": "전력구와 지중 인프라 구간의 이상 징후를 연속 감지하는 업텍 핵심 기술",
            },
        )

        reference, _ = Reference.objects.get_or_create(
            title="지중 인프라 광섬유 감시 실증",
            defaults={
                "client": company,
                "summary": "지중 인프라 환경에서 광섬유 감시와 이벤트 판별 실증 수행",
                "impact": "실증 결과를 기반으로 고객 맞춤 제안서와 회사소개서 확장 가능",
                "is_public": True,
            },
        )
        reference.technologies.add(technology)

        Patent.objects.get_or_create(
            title="광섬유 기반 인프라 이상 감지 방법",
            defaults={
                "status": "출원",
                "summary": "연속 센싱 데이터를 기반으로 이벤트를 분류하는 특허 자산",
            },
        )

        Certification.objects.get_or_create(
            name="GS 인증 1등급",
            defaults={
                "issuer": "TTA",
                "summary": "AI 영상 분석 서버 관련 인증 자산 예시",
            },
        )

        templates = [
            (
                "표준 회사소개서",
                DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
                "업텍 기본 회사소개서 템플릿",
                [
                    ("업텍 소개", "업텍은 전력계통 해석과 인프라 안전 실증 역량을 결합해 고객 맞춤 문서를 빠르게 생성합니다.", "company,overview"),
                    ("핵심 역량", "전력계통 해석, DFOS 기반 감시, 실증 운영, 문서 자동화 역량을 보유하고 있습니다.", "capability,technology"),
                    ("대표 실적", "지중 인프라 광섬유 감시 실증 및 전력 인프라 안정화 제안 수행 경험을 보유하고 있습니다.", "reference,case"),
                ],
            ),
            (
                "표준 영업 제안서",
                DocumentTemplate.TemplateType.SALES_PROPOSAL,
                "고객 맞춤 영업 제안서 템플릿",
                [
                    ("고객 문제 정의", "전력구 및 지중 인프라의 이상 징후를 조기 감지하고 이를 문서화해 즉시 의사결정에 활용할 수 있어야 합니다.", "problem,proposal"),
                    ("제안 솔루션", "업텍은 DFOS 기반 감시와 문서 자동화를 결합해 현장 운영과 보고 체계를 동시에 제안합니다.", "solution,proposal"),
                    ("기대 효과", "조기 경보, 대응 시간 단축, 보고 품질 표준화, 고객 맞춤 확장성을 제공합니다.", "effect,proposal"),
                ],
            ),
            (
                "표준 정부과제 문서",
                DocumentTemplate.TemplateType.GOVERNMENT_PROPOSAL,
                "정부과제 제안서 기본 템플릿",
                [
                    ("과제 필요성", "전력 인프라 안전과 디지털 문서 자동화 수요가 동시에 확대되고 있습니다.", "need,government"),
                    ("기술 개발 내용", "센싱 데이터 해석, 이상 이벤트 판별, 표준 문서 자동화 기술을 통합 개발합니다.", "technology,government"),
                    ("사업화 계획", "발전사, 공공기관, 산업단지 대상으로 단계적 확산을 추진합니다.", "business,government"),
                ],
            ),
            (
                "표준 실증 보고서",
                DocumentTemplate.TemplateType.DEMO_REPORT,
                "실증 결과 요약 보고서 템플릿",
                [
                    ("실증 개요", "현장 환경, 적용 구간, 감시 대상 이벤트를 정리합니다.", "demo,overview"),
                    ("주요 결과", "감지 정확도, 이상 이벤트 탐지 사례, 운영 효과를 요약합니다.", "demo,result"),
                    ("향후 개선 과제", "현장 확대, 데이터 누적, 알고리즘 고도화 계획을 정리합니다.", "demo,improvement"),
                ],
            ),
            (
                "표준 회의록",
                DocumentTemplate.TemplateType.MEETING_NOTE,
                "회의 요약 및 실행항목 템플릿",
                [
                    ("회의 목적", "회의 배경과 주요 안건을 정리합니다.", "meeting,purpose"),
                    ("결정 사항", "합의된 의사결정과 책임자를 정리합니다.", "meeting,decision"),
                    ("후속 액션", "다음 일정과 산출물을 정리합니다.", "meeting,action"),
                ],
            ),
        ]

        created_templates = {}
        for template_name, template_type, description, blocks in templates:
            template, _ = DocumentTemplate.objects.get_or_create(
                name=template_name,
                defaults={
                    "template_type": template_type,
                    "description": description,
                },
            )
            created_templates[template_name] = template

            for title, content, tags in blocks:
                block, _ = DocumentBlock.objects.get_or_create(
                    template=template,
                    title=title,
                    defaults={
                        "block_type": DocumentBlock.BlockType.TEXT,
                        "content": content,
                        "approval_status": DocumentBlock.ApprovalStatus.APPROVED,
                        "tags": tags,
                    },
                )
                block.technologies.add(technology)
                block.references.add(reference)

        created_documents = [
            ("한국남부발전_회사소개서_초안", "표준 회사소개서"),
            ("업텍_국문_회사소개서_보강본", "표준 회사소개서"),
            ("한국남부발전_전력구_제안서_초안", "표준 영업 제안서"),
            ("전력구_운영개선_제안서_보강본", "표준 영업 제안서"),
            ("전력구_실증결과_초안", "표준 실증 보고서"),
        ]

        assembler = DocumentAssembler()
        for title, template_name in created_documents:
            document, _ = GeneratedDocument.objects.get_or_create(
                title=title,
                template=created_templates[template_name],
                company=company,
                opportunity=opportunity,
                defaults={
                    "created_by": admin_user,
                    "status": GeneratedDocument.Status.DRAFT,
                },
            )
            document.assembled_content = assembler.build_payload(document)
            document.save(update_fields=["assembled_content", "updated_at"])

        reference_seed = [
            (
                "남부발전 기존 제안서 PDF",
                DocumentTemplate.TemplateType.SALES_PROPOSAL,
                ReferenceDocument.FileFormat.PDF,
                "legacy_sales_proposal.pdf",
                "기존 영업 제안서의 핵심 요약",
                "고객 문제 정의, 제안 솔루션, 기대 효과, 수행 실적을 포함한 기존 제안서 내용",
                "problem,proposal,solution,effect",
            ),
            (
                "업텍 회사소개 발표자료",
                DocumentTemplate.TemplateType.COMPANY_OVERVIEW,
                ReferenceDocument.FileFormat.PPTX,
                "uptec_company_overview.pptx",
                "회사소개 발표자료 요약",
                "업텍 소개, 핵심 역량, 대표 실적을 담은 기존 회사소개 자료",
                "company,overview,capability,reference",
            ),
        ]

        for title, category, file_format, file_name, summary, extracted_text, tags in reference_seed:
            reference_document, created = ReferenceDocument.objects.get_or_create(
                title=title,
                defaults={
                    "category": category,
                    "file_format": file_format,
                    "company": company,
                    "opportunity": opportunity,
                    "uploaded_by": admin_user,
                    "summary": summary,
                    "extracted_text": extracted_text,
                    "tags": tags,
                    "is_active": True,
                },
            )
            if created or not reference_document.source_file:
                reference_document.source_file.save(
                    file_name,
                    ContentFile(summary + "\n" + extracted_text),
                    save=False,
                )
            reference_document.category = category
            reference_document.file_format = file_format
            reference_document.company = company
            reference_document.opportunity = opportunity
            reference_document.uploaded_by = admin_user
            reference_document.summary = summary
            reference_document.extracted_text = extracted_text
            reference_document.tags = tags
            reference_document.is_active = True
            reference_document.save()

        self.stdout.write(self.style.SUCCESS("Seed data created."))
        self.stdout.write("Admin user: admin / admin1234!")
