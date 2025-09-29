# forum/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Comment

@receiver([post_save, post_delete], sender=Comment)
def invalidate_comment_count(sender, instance, **kwargs):
    # ลบแคชตัวนับคอมเมนต์ของกระทู้ที่เกี่ยวข้อง
    cache.delete(f"thread:{instance.thread_id}:comment_count")
