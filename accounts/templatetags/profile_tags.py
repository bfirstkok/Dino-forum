from django import template

register = template.Library()

@register.filter
def display_name(user):
    """คืนชื่อที่แสดงของผู้ใช้ (fallback: ชื่อจริง > username)"""
    if not user:
        return ""
    prof = getattr(user, "profile", None)
    name = getattr(prof, "display_name", "") or user.get_full_name() or user.username
    return name
