# accounts/templatetags/online.py
from django import template
from django.core.cache import cache
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils import timezone

register = template.Library()

@register.filter
def is_online(user):
    return bool(user and cache.get(f"online:{user.pk}"))

@register.simple_tag
def online_users():
    now = timezone.now()
    ids = set()
    for s in Session.objects.filter(expire_date__gte=now):
        data = s.get_decoded()
        uid = data.get("_auth_user_id")
        if uid and cache.get(f"online:{uid}"):
            ids.add(int(uid))
    User = get_user_model()
    return User.objects.select_related("profile").filter(id__in=ids)

@register.simple_tag
def all_users(limit=None, order="-date_joined"):
    User = get_user_model()
    qs = User.objects.select_related("profile").order_by(order)
    return qs[:int(limit)] if limit else qs
