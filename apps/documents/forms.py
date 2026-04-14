from django import forms

from apps.documents.models import DocumentRevisionRequest, ReferenceDocument


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return [single_file_clean(data, initial)]


class ReferenceDocumentForm(forms.ModelForm):
    class Meta:
        model = ReferenceDocument
        fields = [
            "title",
            "category",
            "file_format",
            "source_file",
            "company",
            "opportunity",
            "summary",
            "extracted_text",
            "tags",
            "is_active",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
            "extracted_text": forms.Textarea(attrs={"rows": 8}),
        }


class DocumentRevisionRequestForm(forms.ModelForm):
    additional_images = MultipleImageField(
        required=False,
        widget=MultipleImageInput(
            attrs={
                "accept": "image/*",
                "multiple": True,
            }
        ),
    )

    class Meta:
        model = DocumentRevisionRequest
        fields = [
            "general_feedback",
            "text_feedback",
            "image_feedback",
        ]
        widgets = {
            "general_feedback": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "2차 생성 시 반영할 전체 요청사항을 적어주세요.",
                }
            ),
            "text_feedback": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "텍스트 톤, 문장 수정, 추가해야 할 메시지를 적어주세요.",
                }
            ),
            "image_feedback": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "수정할 이미지, 교체 방향, 새로 추가할 이미지를 적어주세요.",
                }
            ),
        }
