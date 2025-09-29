# forum/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.conf import settings  # ✅ ต้องมี (ใช้กับ ThreadLike.user)

# ---------- upload paths ----------
def thread_image_upload(instance, filename):
    # media/threads/<user_id>/<filename>
    return f"threads/{instance.author_id}/{filename}"

def comment_image_upload(instance, filename):
    # media/comments/<user_id>/<filename>
    return f"comments/{instance.author_id}/{filename}"


# ---------- models ----------
class Category(models.Model):
    name  = models.CharField(max_length=100, unique=True)
    slug  = models.SlugField(unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "category"
            s = base
            i = 1
            while Category.objects.filter(slug=s).exclude(pk=self.pk).exists():
                s = f"{base}-{i}"
                i += 1
            self.slug = s
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Thread(models.Model):
    category   = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="threads")
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="threads")
    title      = models.CharField(max_length=160)
    content    = models.TextField()
    image      = models.ImageField(upload_to=thread_image_upload, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    @property
    def comment_count(self) -> int:
        """จำนวนคอมเมนต์ที่ยังไม่ถูกลบของกระทู้นี้"""
        return self.comments.filter(is_deleted=False).count()




    # ✅ เมธอดต้องอยู่ในคลาส (เยื้อง 4 ช่อง)
    @property
    def likes_count(self):
        return self.likes.count()

    def is_liked_by(self, user):
        return user.is_authenticated and self.likes.filter(user=user).exists()

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["category", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    # -------- tag_list (ชั่วคราว, set/get ได้) --------
    @property
    def tag_list(self):
        """
        คืนลิสต์แท็กจากแคชชั่วคราว (_tag_list) ถ้ามี
        ถ้าไม่มีจะพยายามอ่านจากฟิลด์ 'tags' (ถ้ามีใน DB) ไม่งั้นคืน []
        - จุดประสงค์หลัก: ให้ view ใส่ t.tag_list = [...] ได้โดยไม่ error
        """
        cached = getattr(self, "_tag_list", None)
        if cached is not None:
            return cached

        tags = getattr(self, "tags", "")
        if isinstance(tags, str) and tags.strip():
            return [s.strip() for s in tags.split(",") if s.strip()]
        return []

    @tag_list.setter
    def tag_list(self, value):
        self._tag_list = list(value) if value else []


class Comment(models.Model):
    thread     = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="comments")
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content    = models.TextField()
    image      = models.ImageField(upload_to=comment_image_upload, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.thread}"


class Report(models.Model):
    TARGET_CHOICES = (("thread", "Thread"), ("comment", "Comment"))
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES)
    target_id   = models.PositiveIntegerField()
    reporter    = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    reason      = models.CharField(max_length=255)
    status      = models.CharField(max_length=10, default="open")  # open|closed
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["target_type", "target_id", "status"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.target_type}:{self.target_id} by {self.reporter}"


class ThreadLike(models.Model):
    thread = models.ForeignKey('Thread', related_name='likes', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='thread_likes', on_delete=models.CASCADE)  # ✅ ใช้ settings.AUTH_USER_MODEL
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('thread', 'user')

    def __str__(self):
        return f'{self.user} ♥ {self.thread}'
