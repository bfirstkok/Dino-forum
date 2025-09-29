# accounts/middleware.py
from django.utils import timezone
from django.core.cache import cache

ONLINE_TIMEOUT = 300  # 5 นาที

class OnlineNowMiddleware:
    """
    ติ๊กหัวใจให้ผู้ใช้ที่กำลัง active ทุกครั้งที่มี request
    เก็บลง cache คีย์: online:<user_id> มีอายุ 5 นาที
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            # เก็บ timestamp ก็ได้ แต่สำหรับเช็ค "ออนไลน์ไหม" เอาค่า True ก็พอ
            cache.set(f"online:{user.pk}", True, ONLINE_TIMEOUT)
        return response
