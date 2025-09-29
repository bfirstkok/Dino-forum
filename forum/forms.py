from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError
import bleach

from .models import Category, Thread, Comment, Report

User = get_user_model()

# ----- Admin helper forms -----
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
        widgets = {"is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"})}
        labels = {"is_staff": "ให้สิทธิ์แอดมิน (is_staff)"}

# ----- Sanitizer -----
ALLOWED_TAGS = ["b", "i", "strong", "em", "u", "code", "br", "ul", "ol", "li", "p", "a"]
ALLOWED_ATTRS = {"a": ["href", "rel", "target"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

def sanitize_html(text: str) -> str:
    return bleach.clean(
        text or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

# ----- Thread form -----
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_CT = {"image/jpeg", "image/png", "image/webp", "image/gif"}

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ["category", "title", "content", "image"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
            # ช่วยกรองชนิดไฟล์ตั้งแต่ตอนเลือก
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp,image/gif"}
            ),
        }

    def clean_title(self):
        t = (self.cleaned_data.get("title") or "").strip()
        if not t:
            raise ValidationError("กรุณากรอกชื่อกระทู้")
        # ปล่อยเฉพาะตัวอักษรธรรมดา ไม่มีแท็ก
        return bleach.clean(t, tags=[], strip=True)

    def clean_content(self):
        return sanitize_html(self.cleaned_data.get("content", ""))

    def clean_image(self):
        f = self.cleaned_data.get("image")
        if not f:
            return f  # ไม่ได้อัปโหลดใหม่

        # ขนาดไฟล์
        if getattr(f, "size", 0) > MAX_IMAGE_BYTES:
            raise ValidationError("ไฟล์รูปต้องไม่เกิน 5MB")

        ctype = getattr(f, "content_type", None)
        if ctype in ALLOWED_CT:
            return f

        # ถ้า content_type ไม่แม่น (เช่น application/octet-stream) → ตรวจด้วย Pillow
        # ต้องคืนตำแหน่งไฟล์หลังตรวจ ไม่งั้น storage บางตัวจะบันทึกไม่ได้
        try:
            origin_pos = f.tell()
        except Exception:
            origin_pos = None

        try:
            try:
                f.seek(0)
            except Exception:
                pass
            img = Image.open(f)
            img.verify()  # ตรวจความเป็นภาพโดยไม่ต้องโหลดเต็ม
        except (UnidentifiedImageError, OSError):
            raise ValidationError("รองรับเฉพาะ JPEG/PNG/WEBP/GIF")
        finally:
            try:
                if origin_pos is not None:
                    f.seek(origin_pos)
            except Exception:
                pass

        return f

# ----- Comment form -----
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {"content": forms.Textarea(attrs={"class": "form-control", "rows": 3})}

    def clean_content(self):
        return sanitize_html(self.cleaned_data.get("content", ""))

# ----- Report form -----
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason"]
        widgets = {"reason": forms.TextInput(attrs={"class": "form-control"})}

    def clean_reason(self):
        return bleach.clean(self.cleaned_data.get("reason", ""), tags=[], strip=True)
