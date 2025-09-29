from django import forms
from django.contrib.auth.models import User
from .models import Profile
from PIL import Image
import bleach


# สมัครสมาชิก (เก็บรหัสผ่านแบบ hash)
class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean_username(self):
        return bleach.clean(self.cleaned_data.get("username", ""), tags=[], strip=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # hash password
        if commit:
            user.save()
        return user


# แก้โปรไฟล์
class ProfileForm(forms.ModelForm):
    display_name = forms.CharField(
        max_length=150,
        required=False,  # ถ้าจะบังคับ ให้เปลี่ยนเป็น True
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ชื่อที่จะแสดง (ไม่ใช่ username)"
        }),
        label="ชื่อที่แสดง",
    )

    class Meta:
        model = Profile
        fields = ["display_name", "avatar", "bio", "social_link"]
        widgets = {
            "bio": forms.TextInput(attrs={"class": "form-control", "placeholder": "เขียนแนะนำตัวสั้น ๆ"}),
            "social_link": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean_display_name(self):
        name = (self.cleaned_data.get("display_name") or "").strip()
        return bleach.clean(name, tags=[], strip=True)

    def clean_bio(self):
        return bleach.clean(self.cleaned_data.get("bio", ""), tags=[], strip=True)

    def clean_social_link(self):
        url = (self.cleaned_data.get("social_link") or "").strip()
        if url and not (url.startswith("http://") or url.startswith("https://")):
            raise forms.ValidationError("ลิงก์ต้องขึ้นต้นด้วย http:// หรือ https://")
        return bleach.clean(url, tags=[], strip=True)

    def clean_avatar(self):
        f = self.cleaned_data.get("avatar")
        if not f:
            return f

        # 1) ขนาดไฟล์
        if f.size > 2 * 1024 * 1024:
            raise forms.ValidationError("ไฟล์รูปต้องไม่เกิน 2MB")

        # 2) MIME ที่อนุญาต (เผื่อเบราว์เซอร์บางตัวใช้ชนิดย่อย)
        allowed_mime = {
            "image/jpeg", "image/jpg", "image/pjpeg",
            "image/png", "image/x-png",
            "image/webp",
        }
        ctype = (getattr(f, "content_type", "") or "").lower()

        # 3) ถ้า MIME ไม่เข้าเงื่อนไข ให้ตรวจด้วย Pillow ว่าเป็นรูปจริง
        if ctype not in allowed_mime:
            try:
                img = Image.open(f)
                img.verify()   # ตรวจว่าเป็นไฟล์รูปจริง
                f.seek(0)      # ย้อน pointer หลัง verify
                if (img.format or "").upper() not in {"JPEG", "PNG", "WEBP"}:
                    raise forms.ValidationError("รองรับเฉพาะ JPEG/PNG/WEBP")
            except Exception:
                raise forms.ValidationError("ไฟล์รูปภาพไม่ถูกต้อง หรือไม่รองรับ")

        return f
