from __future__ import annotations

import re
from dataclasses import dataclass


DEFAULT_PAGE_COUNTS = {
    "company_overview": 8,
    "sales_proposal": 10,
    "government_proposal": 10,
    "demo_report": 6,
    "meeting_note": 5,
}


THEME_LIBRARY = {
    "company_overview": [
        "cover",
        "summary",
        "company",
        "capabilities",
        "solutions",
        "references",
        "workflow",
        "value",
        "roadmap",
        "closing",
    ],
    "sales_proposal": [
        "cover",
        "client_need",
        "problem",
        "solution",
        "architecture",
        "workflow",
        "references",
        "impact",
        "schedule",
        "closing",
    ],
    "government_proposal": [
        "cover",
        "need",
        "market",
        "technology_goal",
        "development_plan",
        "validation",
        "commercialization",
        "team",
        "budget",
        "closing",
    ],
    "demo_report": [
        "cover",
        "environment",
        "result",
        "insight",
        "actions",
        "closing",
    ],
    "meeting_note": [
        "cover",
        "agenda",
        "decisions",
        "actions",
        "closing",
    ],
}


THEME_TAGS = {
    "cover": set(),
    "summary": {"company", "overview", "capability"},
    "company": {"company", "overview"},
    "capabilities": {"capability", "technology"},
    "solutions": {"solution", "technology", "proposal"},
    "references": {"reference", "case", "demo", "result"},
    "workflow": {"workflow", "proposal", "business", "meeting", "action"},
    "value": {"effect", "business", "impact"},
    "roadmap": {"business", "government", "need"},
    "client_need": {"problem", "proposal", "need"},
    "problem": {"problem", "proposal"},
    "solution": {"solution", "proposal", "technology"},
    "architecture": {"technology", "solution"},
    "impact": {"effect", "proposal", "result"},
    "schedule": {"meeting", "action", "business"},
    "need": {"need", "government"},
    "market": {"business", "government"},
    "technology_goal": {"technology", "government"},
    "development_plan": {"technology", "business", "government"},
    "validation": {"demo", "result", "government"},
    "commercialization": {"business", "government"},
    "team": {"company", "capability"},
    "budget": {"business", "government"},
    "environment": {"demo", "overview"},
    "result": {"demo", "result", "effect"},
    "insight": {"demo", "improvement", "effect"},
    "actions": {"meeting", "action", "improvement"},
    "agenda": {"meeting", "purpose"},
    "decisions": {"meeting", "decision"},
}


THEME_LABELS = {
    "ko": {
        "cover": "표지",
        "summary": "요약",
        "company": "회사 개요",
        "capabilities": "핵심 역량",
        "solutions": "솔루션 구성",
        "references": "대표 실적",
        "workflow": "수행 방식",
        "value": "고객 가치",
        "roadmap": "확장 계획",
        "client_need": "고객 니즈",
        "problem": "문제 정의",
        "solution": "제안 솔루션",
        "architecture": "기술 구성",
        "impact": "기대 효과",
        "schedule": "추진 일정",
        "need": "과제 필요성",
        "market": "시장 및 적용처",
        "technology_goal": "기술 개발 목표",
        "development_plan": "개발 계획",
        "validation": "검증 계획",
        "commercialization": "사업화 계획",
        "team": "수행 조직",
        "budget": "자원 계획",
        "environment": "실증 환경",
        "result": "주요 결과",
        "insight": "시사점",
        "actions": "후속 액션",
        "agenda": "회의 개요",
        "decisions": "결정 사항",
        "closing": "마무리",
        "appendix": "부록",
    },
    "en": {
        "cover": "Cover",
        "summary": "Executive Summary",
        "company": "Company Overview",
        "capabilities": "Core Capabilities",
        "solutions": "Solution Portfolio",
        "references": "Representative References",
        "workflow": "Delivery Workflow",
        "value": "Customer Value",
        "roadmap": "Growth Roadmap",
        "client_need": "Client Needs",
        "problem": "Problem Definition",
        "solution": "Proposed Solution",
        "architecture": "Technical Architecture",
        "impact": "Expected Impact",
        "schedule": "Execution Schedule",
        "need": "Project Need",
        "market": "Market & Use Cases",
        "technology_goal": "Technical Goal",
        "development_plan": "Development Plan",
        "validation": "Validation Plan",
        "commercialization": "Commercialization Plan",
        "team": "Delivery Team",
        "budget": "Resource Plan",
        "environment": "Pilot Environment",
        "result": "Key Results",
        "insight": "Insights",
        "actions": "Next Actions",
        "agenda": "Meeting Overview",
        "decisions": "Decisions",
        "closing": "Closing",
        "appendix": "Appendix",
    },
}


THEME_SENTENCES = {
    "ko": {
        "cover": "{company_name} {document_label} 초안입니다. 요청사항과 참조 자산을 반영한 HTML 미리보기입니다.",
        "summary": "{company_name}의 핵심 역량과 적용 분야를 한눈에 이해할 수 있도록 문서 구조를 재정렬했습니다.",
        "company": "{company_name}은 전력 인프라와 현장 운영 이슈를 구조화해 설명하는 데 강점을 가진 팀입니다.",
        "capabilities": "계통 해석, DFOS 기반 감시, 현장 실증, 보고 문서 자동화를 연결한 수행 역량을 중심으로 정리했습니다.",
        "solutions": "고객 문제를 해결하는 서비스 묶음과 전달 방식이 한 페이지 안에서 이해되도록 구성했습니다.",
        "references": "대표 수행 사례와 참조 문서를 바탕으로 신뢰성을 보여주는 흐름으로 배치했습니다.",
        "workflow": "분석, 설계, 실증, 보고까지 이어지는 실행 프로세스를 문서 흐름에 맞춰 정리했습니다.",
        "value": "운영 효율, 의사결정 속도, 현장 대응력을 높이는 고객 가치를 중심으로 표현했습니다.",
        "roadmap": "다음 적용 단계와 확장 가능성을 보여줄 수 있도록 정리했습니다.",
        "client_need": "고객이 겪는 운영 문제와 의사결정 지연 요인을 먼저 짚어주는 구조입니다.",
        "problem": "현재 방식의 한계와 개선이 필요한 포인트를 명확하게 설명하는 페이지입니다.",
        "solution": "제안 솔루션의 핵심 구조와 기대 적용 방식을 요약했습니다.",
        "architecture": "기술 요소와 데이터 흐름이 한 번에 이해되도록 기술 구조를 정리했습니다.",
        "impact": "도입 시 기대할 수 있는 운영 및 사업 효과를 정리했습니다.",
        "schedule": "단계별 추진 계획과 검토 포인트를 요약했습니다.",
        "need": "과제 수행의 배경과 필요성을 정책 및 현장 관점에서 정리했습니다.",
        "market": "적용 가능 시장과 확장 분야를 함께 설명하는 페이지입니다.",
        "technology_goal": "개발하고자 하는 기술의 목표 수준과 차별 요소를 정리했습니다.",
        "development_plan": "개발, 검증, 고도화 단계를 기준으로 계획을 구성했습니다.",
        "validation": "실증 또는 시험을 통해 확인해야 할 핵심 포인트를 정리했습니다.",
        "commercialization": "후속 적용처와 수익화 가능성을 연결해 설명합니다.",
        "team": "수행 조직과 역할 분담을 문서 수준에서 정리했습니다.",
        "budget": "필요 자원과 집행 방향을 한눈에 이해할 수 있도록 구성했습니다.",
        "environment": "실증 환경과 적용 조건을 설명하는 페이지입니다.",
        "result": "실증 또는 수행 결과의 핵심 포인트를 요약했습니다.",
        "insight": "검토 과정에서 얻은 시사점과 개선 방향을 정리했습니다.",
        "actions": "후속 일정과 실행 항목을 정리했습니다.",
        "agenda": "회의 목적과 범위를 빠르게 이해할 수 있도록 구성했습니다.",
        "decisions": "결정된 사항과 책임 주체를 정리하는 페이지입니다.",
        "closing": "문서 전체 메시지를 짧게 정리하고 다음 액션을 연결하는 마지막 페이지입니다.",
        "appendix": "보조 설명과 추가 참고 내용을 담는 페이지입니다.",
    },
    "en": {
        "cover": "This is the HTML preview for the {company_name} {document_label}, generated from the latest request and reference assets.",
        "summary": "This page reframes the overall message so a reviewer can understand the core value and narrative quickly.",
        "company": "{company_name} is positioned as a focused deep-tech team that explains power and infrastructure work in a structured way.",
        "capabilities": "The draft highlights capabilities across grid studies, DFOS-based monitoring, field execution, and documentation workflow.",
        "solutions": "The solution portfolio is arranged so the reader can understand what the team delivers and how it fits the client need.",
        "references": "This page is designed to build trust by connecting the draft with representative references and supporting assets.",
        "workflow": "The delivery workflow explains how analysis, design, validation, and reporting move forward as one process.",
        "value": "The narrative focuses on customer value such as faster decisions, clearer reporting, and stronger field execution.",
        "roadmap": "This page shows how the current offer can expand into follow-on execution and broader deployment.",
        "client_need": "This page frames the client's need first so the rest of the document reads as a direct response.",
        "problem": "The problem definition page clarifies where the current process is slow, fragmented, or risky.",
        "solution": "The proposed solution page outlines the structure of the offer and how it will be applied.",
        "architecture": "The technical architecture page shows the main components and how they connect in practice.",
        "impact": "This page translates the proposal into measurable impact for operations and business outcomes.",
        "schedule": "The execution schedule summarizes the main phases, milestones, and review points.",
        "need": "This page explains why the project matters from both an operational and policy perspective.",
        "market": "The market page connects the technology to real deployment scenarios and growth paths.",
        "technology_goal": "The technical goal page clarifies what the team aims to achieve and why it matters.",
        "development_plan": "The development plan maps the work into staged development and validation steps.",
        "validation": "The validation page explains how the team will prove feasibility and readiness.",
        "commercialization": "The commercialization page links the project to rollout and business opportunities.",
        "team": "This page explains who delivers the work and how responsibilities are structured.",
        "budget": "The resource plan provides a simple view of the required effort and execution direction.",
        "environment": "This page outlines the pilot environment and the operating conditions involved.",
        "result": "The key results page summarizes the main outcomes and evidence points.",
        "insight": "This page captures the main lessons and the implications for the next iteration.",
        "actions": "The next actions page turns the discussion into concrete follow-up steps.",
        "agenda": "This page gives a quick overview of the meeting purpose and scope.",
        "decisions": "This page records the decisions that should remain visible after the meeting.",
        "closing": "The closing page summarizes the message and points clearly to the next step.",
        "appendix": "This appendix page captures extra supporting detail for reviewers.",
    },
}


@dataclass
class GenerationIntent:
    raw_prompt: str
    language: str
    page_count: int
    audience: str

    @property
    def language_label(self) -> str:
        return "English" if self.language == "en" else "한국어"


class DocumentPreviewBuilder:
    def enrich_payload(
        self,
        document,
        payload: dict,
        generation_request: str = "",
        revision_requests=None,
    ) -> dict:
        revision_requests = list(revision_requests or [])
        intent = self._parse_intent(document, generation_request, revision_requests)
        pages = self._build_pages(document, payload, intent, revision_requests)
        preview_meta = {
            "language": intent.language,
            "language_label": intent.language_label,
            "page_count": len(pages),
            "audience": intent.audience,
            "request": generation_request,
            "revision_count": len(revision_requests),
            "last_revision_round": revision_requests[0].request_round if revision_requests else 0,
        }
        payload["generation_request"] = generation_request
        payload["preview_pages"] = pages
        payload["preview_meta"] = preview_meta
        return payload

    def _parse_intent(self, document, generation_request: str, revision_requests) -> GenerationIntent:
        combined_text = " ".join(
            filter(
                None,
                [
                    generation_request,
                    *[
                        " ".join(
                            filter(
                                None,
                                [
                                    revision.general_feedback,
                                    revision.text_feedback,
                                    revision.image_feedback,
                                ],
                            )
                        )
                        for revision in revision_requests
                    ],
                ],
            )
        )
        normalized = combined_text.lower()
        page_matches = re.findall(r"(\d+)\s*(?:page|pages|페이지|장)", normalized)
        page_count = int(page_matches[-1]) if page_matches else DEFAULT_PAGE_COUNTS.get(document.template.template_type, 8)
        page_count = max(4, min(page_count, 20))

        language = "ko"
        if any(keyword in normalized for keyword in ["영문", "english", "in english", "english version"]):
            language = "en"
        elif any(keyword in normalized for keyword in ["국문", "한글", "korean"]):
            language = "ko"

        audience = "general"
        if any(keyword in normalized for keyword in ["investor", "투자", "ir"]):
            audience = "investor"
        elif any(keyword in normalized for keyword in ["proposal", "client", "고객", "제안"]):
            audience = "client"

        return GenerationIntent(
            raw_prompt=generation_request,
            language=language,
            page_count=page_count,
            audience=audience,
        )

    def _build_pages(self, document, payload: dict, intent: GenerationIntent, revision_requests) -> list[dict]:
        blocks = payload.get("blocks", [])
        block_overrides = {}
        latest_image_feedback = ""
        latest_general_feedback = ""
        latest_text_feedback = ""

        if revision_requests:
            latest = revision_requests[0]
            latest_image_feedback = latest.image_feedback.strip()
            latest_general_feedback = latest.general_feedback.strip()
            latest_text_feedback = latest.text_feedback.strip()
            for item in latest.block_feedback:
                block_overrides[item.get("title", "")] = item.get("requested_change", "")

        company_name = document.company.name if document.company else "Uptec"
        document_label = self._document_label(document.template.template_type, intent.language)
        theme_ids = self._select_themes(document.template.template_type, intent.page_count)

        pages = []
        for index, theme_id in enumerate(theme_ids, start=1):
            matched_blocks = self._match_blocks(theme_id, blocks)
            page_title = self._page_title(theme_id, intent.language, document.title, company_name, index)
            body = self._page_body(
                theme_id=theme_id,
                intent=intent,
                company_name=company_name,
                document_label=document_label,
                matched_blocks=matched_blocks,
                block_overrides=block_overrides,
                general_feedback=latest_general_feedback,
                text_feedback=latest_text_feedback,
            )
            bullets = self._page_bullets(theme_id, intent.language, matched_blocks, company_name, latest_general_feedback)
            image_note = latest_image_feedback or self._default_image_note(theme_id, intent.language, company_name)

            pages.append(
                {
                    "page_number": index,
                    "page_label": self._page_label(intent.language, index),
                    "title": page_title,
                    "theme_label": THEME_LABELS[intent.language].get(theme_id, THEME_LABELS[intent.language]["appendix"]),
                    "body": body,
                    "bullets": bullets,
                    "image_note": image_note,
                    "source_titles": [block.get("title", "") for block in matched_blocks[:3]],
                }
            )
        return pages

    def _select_themes(self, template_type: str, page_count: int) -> list[str]:
        base_themes = THEME_LIBRARY.get(template_type, THEME_LIBRARY["company_overview"])
        if page_count <= len(base_themes):
            return base_themes[:page_count]
        extra = ["appendix"] * (page_count - len(base_themes))
        return base_themes + extra

    def _match_blocks(self, theme_id: str, blocks: list[dict]) -> list[dict]:
        target_tags = THEME_TAGS.get(theme_id, set())
        if not target_tags:
            return blocks[:2]

        matched = []
        for block in blocks:
            block_tags = {tag.strip().lower() for tag in (block.get("tags") or "").split(",") if tag.strip()}
            if block_tags.intersection(target_tags):
                matched.append(block)
        return matched or blocks[:2]

    def _page_title(self, theme_id: str, language: str, document_title: str, company_name: str, page_number: int) -> str:
        if theme_id == "cover":
            if language == "en":
                return document_title or f"{company_name} Company Overview"
            return document_title or f"{company_name} 문서 초안"
        if theme_id == "appendix":
            return f"{THEME_LABELS[language]['appendix']} {page_number}"
        return THEME_LABELS[language].get(theme_id, theme_id.title())

    def _page_body(
        self,
        theme_id: str,
        intent: GenerationIntent,
        company_name: str,
        document_label: str,
        matched_blocks: list[dict],
        block_overrides: dict[str, str],
        general_feedback: str,
        text_feedback: str,
    ) -> list[str]:
        language = intent.language
        sentence = THEME_SENTENCES[language].get(theme_id, THEME_SENTENCES[language]["appendix"]).format(
            company_name=company_name,
            document_label=document_label,
        )
        body = [sentence]

        override_texts = [
            block_overrides.get(block.get("title", ""))
            for block in matched_blocks
            if block_overrides.get(block.get("title", ""))
        ]
        if override_texts:
            body.append(override_texts[-1])
        elif matched_blocks:
            body.append(self._summarize_blocks(matched_blocks, language, company_name))

        request_summary = self._request_summary(language, general_feedback, text_feedback)
        if request_summary and theme_id in {"cover", "summary", "value", "closing", "appendix"}:
            body.append(request_summary)

        return [item for item in body if item]

    def _page_bullets(
        self,
        theme_id: str,
        language: str,
        matched_blocks: list[dict],
        company_name: str,
        general_feedback: str,
    ) -> list[str]:
        bullet_titles = [block.get("title", "") for block in matched_blocks[:3] if block.get("title")]
        if language == "en":
            base = [
                f"Focused narrative for {company_name}",
                f"Section theme: {THEME_LABELS['en'].get(theme_id, 'Appendix')}",
                "Prepared as an HTML review draft before document export",
            ]
            if bullet_titles:
                base = [f"Reference topic: {title}" for title in bullet_titles]
                while len(base) < 3:
                    base.append("Structured for review, revision, and final export")
            if general_feedback:
                base[-1] = f"Current reviewer direction: {general_feedback[:80]}"
            return base[:3]

        base = [
            f"{company_name} 중심 메시지 반영",
            f"페이지 주제: {THEME_LABELS['ko'].get(theme_id, '부록')}",
            "검토 후 수정과 최종 출력까지 이어지는 초안 구조",
        ]
        if bullet_titles:
            base = [f"참조 섹션: {title}" for title in bullet_titles]
            while len(base) < 3:
                base.append("HTML 검토 후 수정 반영을 위한 페이지")
        if general_feedback:
            base[-1] = f"현재 검토 요청: {general_feedback[:80]}"
        return base[:3]

    def _default_image_note(self, theme_id: str, language: str, company_name: str) -> str:
        if language == "en":
            return (
                f"Suggested image: add a clean supporting visual for the '{THEME_LABELS['en'].get(theme_id, 'Appendix')}' "
                f"page that reinforces {company_name}'s engineering and field-delivery credibility."
            )
        return (
            f"추천 이미지: '{THEME_LABELS['ko'].get(theme_id, '부록')}' 페이지에 맞는 엔지니어링/현장 중심 비주얼을 배치해 "
            f"{company_name}의 신뢰감을 강화해주세요."
        )

    def _summarize_blocks(self, matched_blocks: list[dict], language: str, company_name: str) -> str:
        titles = ", ".join(block.get("title", "") for block in matched_blocks[:3] if block.get("title"))
        contents = " ".join((block.get("content", "") or "").strip() for block in matched_blocks[:2]).strip()
        contents = re.sub(r"\s+", " ", contents)
        contents = contents[:240]
        if language == "en":
            if contents:
                return f"This draft pulls from approved content around {titles}. {contents}"
            return f"This page is built from approved sections such as {titles}, reorganized for clearer review and presentation."
        if contents:
            return f"이 페이지는 {titles} 관련 승인 블록을 기준으로 정리했습니다. {contents}"
        return f"이 페이지는 {titles} 관련 승인 블록을 기준으로 다시 구성한 초안입니다."

    def _request_summary(self, language: str, general_feedback: str, text_feedback: str) -> str:
        combined = " ".join(filter(None, [general_feedback, text_feedback])).strip()
        if not combined:
            return ""
        combined = combined[:160]
        if language == "en":
            return f"Reviewer note applied to this draft: {combined}"
        return f"현재 반영 요청 메모: {combined}"

    def _document_label(self, template_type: str, language: str) -> str:
        labels = {
            "company_overview": {"ko": "회사소개서", "en": "company overview"},
            "sales_proposal": {"ko": "제안서", "en": "proposal"},
            "government_proposal": {"ko": "정부과제 문서", "en": "government proposal"},
            "demo_report": {"ko": "실증 보고서", "en": "demo report"},
            "meeting_note": {"ko": "회의록", "en": "meeting note"},
        }
        return labels.get(template_type, labels["company_overview"])[language]

    def _page_label(self, language: str, page_number: int) -> str:
        if language == "en":
            return f"Page {page_number}"
        return f"{page_number}페이지"
