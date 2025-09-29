from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static   # <<< เพิ่มอันนี้
from django.core.files.storage import default_storage  # <-- เพิ่ม
import os
import uuid


def avatar_upload(instance: "Profile", filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return f"avatars/user_{instance.user_id}/{uuid.uuid4().hex}{ext}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload, blank=True, null=True)
    bio = models.CharField(max_length=280, blank=True)
    social_link = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.display_name or self.user.username

    @property
    def avatar_url(self) -> str:
        """
        คืน URL รูปโปรไฟล์:
        - ถ้าฟิลด์ avatar มีค่าและไฟล์มีอยู่จริง -> ใช้ไฟล์นั้น
        - ถ้าไฟล์ไม่มี/หาย -> ใช้รูป default ใน static
        """
        name = getattr(self.avatar, "name", "")
        if name and default_storage.exists(name):
            return self.avatar.url
        return static("img/avatar-default.png")
