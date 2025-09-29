from django import forms
from .models import Thread, Comment, Report
import bleach
from django.contrib.auth import get_user_model
from .models import Category

User = get_user_model()


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "ชื่อหมวด"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["is_staff"]
        widgets = {
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"})
        }
        labels = {"is_staff": "ให้สิทธิ์แอดมิน (is_staff)"}

ALLOWED_TAGS = ["b","i","strong","em","u","code","br","ul","ol","li","p","a"]
ALLOWED_ATTRS = {"a": ["href","rel","target"]}
ALLOWED_PROTOCOLS = ["http","https","mailto"]

def sanitize_html(text: str) -> str:
    return bleach.clean(text or "", tags=ALLOWED_TAGS,
                        attributes=ALLOWED_ATTRS, protocols=ALLOWED_PROTOCOLS, strip=True)

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ["category", "title", "content", "image"]  # ← เพิ่ม image
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
        }

    def clean_title(self):
        t = self.cleaned_data.get("title", "").strip()
        if not t:
            raise forms.ValidationError("กรุณากรอกชื่อกระทู้")
        return bleach.clean(t, tags=[], strip=True)

    def clean_content(self):
        return sanitize_html(self.cleaned_data.get("content", ""))
        
    def clean_image(self):
        f = self.cleaned_data.get("image")
        if not f:
            return f
        ok = {"image/jpeg","image/png","image/webp","image/gif"}
        if getattr(f, "content_type", "") not in ok:
            raise forms.ValidationError("รองรับเฉพาะ JPEG/PNG/WEBP/GIF")
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("ไฟล์รูปต้องไม่เกิน 5MB")
        return f

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_content(self):
        return sanitize_html(self.cleaned_data.get("content", ""))

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason"]
        widgets = {
            "reason": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_reason(self):
        return bleach.clean(self.cleaned_data.get("reason", ""), tags=[], strip=True)
