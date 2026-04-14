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
    "company_overview": ["cover", "summary", "company", "capabilities", "solutions", "references", "workflow", "value", "roadmap", "closing"],
    "sales_proposal": ["cover", "client_need", "problem", "solution", "architecture", "workflow", "references", "impact", "schedule", "closing"],
    "government_proposal": ["cover", "need", "market", "technology_goal", "development_plan", "validation", "commercialization", "team", "budget", "closing"],
    "demo_report": ["cover", "environment", "result", "insight", "actions", "closing"],
    "meeting_note": ["cover", "agenda", "decisions", "actions", "closing"],
}

VISUAL_THEME_LIBRARY = {
    "company_overview": ["cover", "company", "capabilities", "references", "closing"],
    "sales_proposal": ["cover", "client_need", "solution", "references", "impact", "closing"],
    "government_proposal": ["cover", "need", "technology_goal", "validation", "commercialization", "closing"],
    "demo_report": ["cover", "environment", "result", "insight", "closing"],
    "meeting_note": ["cover", "agenda", "decisions", "actions", "closing"],
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
        "cover": "표지", "summary": "요약", "company": "회사 개요", "capabilities": "핵심 역량", "solutions": "솔루션 구성",
        "references": "대표 실적", "workflow": "수행 방식", "value": "고객 가치", "roadmap": "확장 계획", "client_need": "고객 니즈",
        "problem": "문제 정의", "solution": "제안 솔루션", "architecture": "기술 구성", "impact": "기대 효과", "schedule": "추진 일정",
        "need": "과제 필요성", "market": "시장 및 적용처", "technology_goal": "기술 개발 목표", "development_plan": "개발 계획",
        "validation": "검증 계획", "commercialization": "사업화 계획", "team": "수행 조직", "budget": "자원 계획", "environment": "실증 환경",
        "result": "주요 결과", "insight": "시사점", "actions": "후속 액션", "agenda": "회의 개요", "decisions": "결정 사항", "closing": "마무리", "appendix": "부록",
    },
    "en": {
        "cover": "Cover", "summary": "Executive Summary", "company": "Company Overview", "capabilities": "Core Capabilities", "solutions": "Solution Portfolio",
        "references": "Representative References", "workflow": "Delivery Workflow", "value": "Customer Value", "roadmap": "Growth Roadmap", "client_need": "Client Needs",
        "problem": "Problem Definition", "solution": "Proposed Solution", "architecture": "Technical Architecture", "impact": "Expected Impact", "schedule": "Execution Schedule",
        "need": "Project Need", "market": "Market & Use Cases", "technology_goal": "Technical Goal", "development_plan": "Development Plan",
        "validation": "Validation Plan", "commercialization": "Commercialization Plan", "team": "Delivery Team", "budget": "Resource Plan", "environment": "Pilot Environment",
        "result": "Key Results", "insight": "Insights", "actions": "Next Actions", "agenda": "Meeting Overview", "decisions": "Decisions", "closing": "Closing", "appendix": "Appendix",
    },
}

VISUAL_KEYWORDS = ["이미지", "비주얼", "사진", "갤러리", "브로셔", "슬라이드", "image", "visual", "photo", "gallery", "brochure", "slide"]
LIBRARY_KEYWORDS = ["보관 문서", "기존 문서", "기존 보관 문서", "참조 문서", "legacy", "library", "reference document", "existing document"]


@dataclass
class GenerationIntent:
    raw_prompt: str
    language: str
    page_count: int
    audience: str
    visual_priority: bool
    use_library_assets: bool

    @property
    def language_label(self) -> str:
        return "English" if self.language == "en" else "한국어"

    @property
    def presentation_style(self) -> str:
        return "visual" if self.visual_priority else "standard"

    @property
    def presentation_style_label(self) -> str:
        return "이미지 중심" if self.visual_priority else "텍스트+비주얼 혼합"


class DocumentPreviewBuilder:
    def enrich_payload(self, document, payload: dict, generation_request: str = "", revision_requests=None) -> dict:
        revision_requests = list(revision_requests or [])
        source_documents = list(payload.get("source_documents", []))
        reference_documents = list(payload.get("reference_documents", []))
        intent = self._parse_intent(document, payload, generation_request, revision_requests)
        revision_assets = self._collect_revision_assets(revision_requests)
        payload["generation_request"] = generation_request
        payload["preview_pages"] = self._build_pages(
            document,
            payload,
            intent,
            revision_requests,
            source_documents,
            reference_documents,
            revision_assets,
        )
        payload["preview_meta"] = {
            "language": intent.language,
            "language_label": intent.language_label,
            "page_count": len(payload["preview_pages"]),
            "audience": intent.audience,
            "request": generation_request,
            "revision_count": len(revision_requests),
            "last_revision_round": revision_requests[0].request_round if revision_requests else 0,
            "presentation_style": intent.presentation_style,
            "presentation_style_label": intent.presentation_style_label,
            "source_document_count": len(source_documents),
            "reference_document_count": len(reference_documents),
            "revision_asset_count": len(revision_assets),
        }
        return payload

    def _parse_intent(self, document, payload: dict, generation_request: str, revision_requests) -> GenerationIntent:
        combined = " ".join(filter(None, [generation_request] + [
            " ".join(filter(None, [revision.general_feedback, revision.text_feedback, revision.image_feedback]))
            for revision in revision_requests
        ])).lower()
        page_matches = re.findall(r"(\d+)\s*(?:page|pages|페이지|장)", combined)
        page_count = int(page_matches[-1]) if page_matches else DEFAULT_PAGE_COUNTS.get(document.template.template_type, 8)
        page_count = max(4, min(page_count, 20))
        language = "en" if any(keyword in combined for keyword in ["영문", "english", "in english", "english version"]) else "ko"
        audience = "investor" if any(keyword in combined for keyword in ["investor", "투자", "ir"]) else "client" if any(keyword in combined for keyword in ["proposal", "client", "고객", "제안"]) else "general"
        visual_priority = any(keyword in combined for keyword in VISUAL_KEYWORDS)
        use_library_assets = bool(payload.get("reference_documents")) and any(keyword in combined for keyword in LIBRARY_KEYWORDS + VISUAL_KEYWORDS)
        return GenerationIntent(generation_request, language, page_count, audience, visual_priority, use_library_assets)

    def _collect_revision_assets(self, revision_requests) -> list[dict]:
        items = []
        for revision in revision_requests:
            for asset in revision.assets.all():
                items.append({"title": asset.original_name or "uploaded-image", "summary": asset.note or "사용자 업로드 이미지", "badge": "업로드 이미지", "asset_type": "uploaded", "file_url": asset.image_file.url if asset.image_file else "", "file_format_label": "Image"})
        return items

    def _build_pages(self, document, payload: dict, intent: GenerationIntent, revision_requests, source_documents: list[dict], reference_documents: list[dict], revision_assets: list[dict]) -> list[dict]:
        blocks = payload.get("blocks", [])
        latest_general = revision_requests[0].general_feedback.strip() if revision_requests else ""
        latest_text = revision_requests[0].text_feedback.strip() if revision_requests else ""
        latest_image = revision_requests[0].image_feedback.strip() if revision_requests else ""
        block_overrides = {}
        if revision_requests:
            for item in revision_requests[0].block_feedback:
                block_overrides[item.get("title", "")] = item.get("requested_change", "")
        company_name = document.company.name if document.company else "Uptec"
        theme_ids = self._select_themes(document.template.template_type, intent)
        pages = []
        for index, theme_id in enumerate(theme_ids, start=1):
            matched_blocks = self._match_blocks(theme_id, blocks)
            visual_assets = self._select_visual_assets(
                theme_id,
                intent,
                matched_blocks,
                source_documents,
                reference_documents,
                revision_assets,
                index,
            )
            body = [self._theme_sentence(theme_id, intent.language, company_name, document.template.template_type)]
            override_text = next((block_overrides.get(block.get("title", "")) for block in matched_blocks if block_overrides.get(block.get("title", ""))), "")
            if override_text:
                body.append(override_text)
            elif matched_blocks:
                body.append(self._summarize_blocks(matched_blocks, intent.language, short=intent.visual_priority))
            request_summary = self._request_summary(intent.language, latest_general, latest_text)
            if request_summary and theme_id in {"cover", "summary", "references", "closing", "appendix"}:
                body.append(request_summary)
            pages.append({
                "page_number": index,
                "page_label": self._page_label(intent.language, index),
                "title": document.title if theme_id == "cover" else THEME_LABELS[intent.language].get(theme_id, theme_id.title()),
                "theme_label": THEME_LABELS[intent.language].get(theme_id, THEME_LABELS[intent.language]["appendix"]),
                "body": [item for item in body if item][: 2 if intent.visual_priority else 3],
                "bullets": self._page_bullets(intent.language, company_name, matched_blocks, latest_general, visual_assets, theme_id),
                "image_note": latest_image or self._default_image_note(intent.language, company_name, intent.visual_priority),
                "source_titles": [block.get("title", "") for block in matched_blocks[:3]],
                "layout_style": "gallery" if intent.visual_priority and theme_id in {"cover", "references"} else "split" if intent.visual_priority or visual_assets else "text",
                "visual_assets": visual_assets,
                "is_visual": intent.visual_priority or bool(visual_assets),
                "asset_summary": self._asset_summary(intent.language, visual_assets, source_documents, reference_documents),
            })
        return pages

    def _select_themes(self, template_type: str, intent: GenerationIntent) -> list[str]:
        base = VISUAL_THEME_LIBRARY.get(template_type, THEME_LIBRARY["company_overview"]) if intent.visual_priority else THEME_LIBRARY.get(template_type, THEME_LIBRARY["company_overview"])
        if intent.page_count <= len(base):
            return base[: intent.page_count]
        return base + ["appendix"] * (intent.page_count - len(base))

    def _match_blocks(self, theme_id: str, blocks: list[dict]) -> list[dict]:
        tags = THEME_TAGS.get(theme_id, set())
        if not tags:
            return blocks[:2]
        matched = []
        for block in blocks:
            block_tags = {tag.strip().lower() for tag in (block.get("tags") or "").split(",") if tag.strip()}
            if block_tags.intersection(tags):
                matched.append(block)
        return matched or blocks[:2]

    def _select_visual_assets(self, theme_id: str, intent: GenerationIntent, matched_blocks: list[dict], source_documents: list[dict], reference_documents: list[dict], revision_assets: list[dict], page_number: int) -> list[dict]:
        assets = []
        if revision_assets:
            assets.extend(self._rotate(revision_assets, page_number - 1, 2 if intent.visual_priority else 1))
        tags = THEME_TAGS.get(theme_id, set())
        reference_pool = []
        for item in reference_documents:
            item_tags = {tag.strip().lower() for tag in (item.get("tags") or "").split(",") if tag.strip()}
            if not tags or item_tags.intersection(tags) or intent.use_library_assets:
                reference_pool.append({
                    "title": item.get("title") or "기존 문서",
                    "summary": self._truncate(item.get("summary") or item.get("extracted_text") or "", 120),
                    "badge": "보관 문서",
                    "asset_type": "reference",
                    "file_url": self._preview_url(item.get("source_file_url") or ""),
                    "file_format_label": item.get("file_format_label") or item.get("file_format") or "",
                })
        if reference_pool:
            assets.extend(self._rotate(reference_pool, page_number - 1, 3 if intent.visual_priority else 1))
        source_pool = [{
            "title": item.get("title") or "기존 생성 문서",
            "summary": self._truncate(" · ".join(filter(None, [item.get("template_name") or "", item.get("company_name") or "", item.get("opportunity_title") or ""])), 120),
            "badge": "기존 생성 문서",
            "asset_type": "generated",
            "file_url": "",
            "file_format_label": item.get("template_name") or "",
        } for item in source_documents]
        if not reference_pool and source_pool:
            assets.extend(self._rotate(source_pool, page_number - 1, 2 if intent.visual_priority else 1))
        if not assets:
            assets = [{
                "title": block.get("title", "승인 블록"),
                "summary": self._truncate(block.get("content", ""), 120),
                "badge": "승인 블록",
                "asset_type": "block",
                "file_url": "",
                "file_format_label": block.get("type", "text"),
            } for block in matched_blocks[: 2 if intent.visual_priority else 1]]
        return assets[: 3 if intent.visual_priority else 2]

    def _preview_url(self, file_url: str) -> str:
        return file_url if file_url.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")) else ""

    def _theme_sentence(self, theme_id: str, language: str, company_name: str, template_type: str) -> str:
        label = {"company_overview": {"ko": "회사소개서", "en": "company overview"}, "sales_proposal": {"ko": "제안서", "en": "proposal"}, "government_proposal": {"ko": "정부과제 문서", "en": "government proposal"}, "demo_report": {"ko": "실증 보고서", "en": "demo report"}, "meeting_note": {"ko": "회의록", "en": "meeting note"}}.get(template_type, {"ko": "문서", "en": "document"})[language]
        if language == "en":
            if theme_id == "cover":
                return f"This is the HTML preview for the latest {company_name} {label}, organized from the request and reference assets."
            return f"This page summarizes the {THEME_LABELS['en'].get(theme_id, theme_id.title())} story in a review-ready slide format."
        if theme_id == "cover":
            return f"{company_name} {label} 초안입니다. 요청사항과 참조 자산을 반영한 HTML 미리보기입니다."
        return f"이 페이지는 {THEME_LABELS['ko'].get(theme_id, theme_id)} 내용을 슬라이드형 구조로 재정리한 초안입니다."

    def _summarize_blocks(self, matched_blocks: list[dict], language: str, short: bool = False) -> str:
        titles = ", ".join(block.get("title", "") for block in matched_blocks[:3] if block.get("title"))
        contents = re.sub(r"\s+", " ", " ".join((block.get("content", "") or "").strip() for block in matched_blocks[:2])).strip()
        contents = self._truncate(contents, 140 if short else 220)
        if language == "en":
            return f"Reference sections: {titles}. {contents}" if contents else f"Reference sections: {titles}."
        return f"참조 섹션: {titles}. {contents}" if contents else f"참조 섹션: {titles}."

    def _page_bullets(self, language: str, company_name: str, matched_blocks: list[dict], general_feedback: str, visual_assets: list[dict], theme_id: str) -> list[str]:
        section_bullets = [block.get("title", "") for block in matched_blocks[:2] if block.get("title")]
        asset_bullet = visual_assets[0]["title"] if visual_assets else ""
        if language == "en":
            bullets = [f"Focused narrative for {company_name}", f"Section theme: {THEME_LABELS['en'].get(theme_id, theme_id.title())}", "Prepared for HTML review before export"]
            if section_bullets:
                bullets = [f"Reference section: {item}" for item in section_bullets]
            if asset_bullet:
                bullets.append(f"Visual source: {asset_bullet}")
            if general_feedback:
                bullets[-1] = f"Reviewer direction: {self._truncate(general_feedback, 80)}"
            return bullets[:3]
        bullets = [f"{company_name} 중심 메시지 반영", f"페이지 주제: {THEME_LABELS['ko'].get(theme_id, theme_id)}", "HTML 검토 후 수정 반영을 위한 페이지"]
        if section_bullets:
            bullets = [f"참조 섹션: {item}" for item in section_bullets]
        if asset_bullet:
            bullets.append(f"활용 자산: {asset_bullet}")
        if general_feedback:
            bullets[-1] = f"현재 검토 요청: {self._truncate(general_feedback, 80)}"
        return bullets[:3]

    def _default_image_note(self, language: str, company_name: str, visual_priority: bool) -> str:
        if language == "en":
            return f"Recommended visual treatment: use archived references and field imagery to strengthen {company_name}'s credibility." if visual_priority else f"Suggested image: add a clean supporting visual that reinforces {company_name}'s field and engineering credibility."
        return f"추천 이미지: 보관 문서의 대표 장표나 현장 사진을 전면 배치해 {company_name}의 엔지니어링 신뢰감을 강화해주세요." if visual_priority else f"추천 이미지: 엔지니어링/현장 중심 비주얼을 배치해 {company_name}의 신뢰감을 강화해주세요."

    def _request_summary(self, language: str, general_feedback: str, text_feedback: str) -> str:
        combined = self._truncate(" ".join(filter(None, [general_feedback, text_feedback])).strip(), 160)
        if not combined:
            return ""
        return f"Reviewer note applied to this draft: {combined}" if language == "en" else f"현재 반영 요청 메모: {combined}"

    def _asset_summary(self, language: str, visual_assets: list[dict], source_documents: list[dict], reference_documents: list[dict]) -> str:
        if not visual_assets:
            return ""
        return (
            f"Visual sources prepared: {len(visual_assets)} items from uploaded assets, archived references, or earlier generated documents."
            if language == "en"
            else f"시각 자산 준비: 현재 페이지용 자산 {len(visual_assets)}건, 기존 생성 문서 {len(source_documents)}건, 보관 문서 {len(reference_documents)}건."
        )

    def _page_label(self, language: str, page_number: int) -> str:
        return f"Page {page_number}" if language == "en" else f"{page_number}페이지"

    def _rotate(self, items: list[dict], start: int, size: int) -> list[dict]:
        if not items:
            return []
        rotated = items[start:] + items[:start]
        return rotated[:size]

    def _truncate(self, value: str, limit: int) -> str:
        value = re.sub(r"\s+", " ", (value or "").strip())
        return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"
