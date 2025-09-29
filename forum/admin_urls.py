# forum/admin_urls.py
from django.urls import path
from . import admin_views, views

# helper: เลือก view ตามชื่อจาก admin_views ถ้าไม่มีค่อยไป views
def pick(name, alt=None):
    if hasattr(admin_views, name):
        return getattr(admin_views, name)
    if hasattr(views, name):
        return getattr(views, name)
    # เผื่อชื่อสำรอง เช่น admin_reports / report_list
    if alt:
        alts = (alt,) if isinstance(alt, str) else tuple(alt)
        for n in alts:
            if hasattr(admin_views, n):
                return getattr(admin_views, n)
            if hasattr(views, n):
                return getattr(views, n)
    raise AttributeError(f"Neither admin_views nor views defines '{name}'")

app_name = "adminpanel"

urlpatterns = [
    # dashboard
    path("", pick("dashboard"), name="dashboard"),

    # categories
    path("categories/", pick("cat_list"), name="cat_list"),
    path("categories/new/", pick("cat_create"), name="cat_create"),
    path("categories/<int:pk>/edit/", pick("cat_edit"), name="cat_edit"),
    path("categories/<int:pk>/delete/", pick("cat_delete"), name="cat_delete"),
    path("categories/<int:pk>/move/<str:direction>/", pick("cat_move"), name="cat_move"),

    # threads (admin)
    path("threads/", pick("admin_threads"), name="admin_threads"),
    path("threads/bulk/", pick("admin_threads_bulk"), name="admin_threads_bulk"),
    path(
        "threads/<int:thread_id>/toggle-delete/",
        pick("admin_thread_toggle_delete"),
        name="admin_thread_toggle_delete",
    ),

    # users
    path("users/", pick("user_list"), name="user_list"),
    path("users/<int:uid>/role/", pick("user_role_toggle"), name="user_role_toggle"),

    # reports (ใช้ชื่อสำรองได้: admin_reports หรือ report_list)
    path("reports/", pick("admin_reports", alt="report_list"), name="admin_reports"),
    path("reports/", pick("admin_reports", alt="report_list"), name="report_list"),  # ← ชื่อสำรอง
    path("reports/<int:rid>/resolve/", pick("report_resolve"), name="report_resolve"),
    path("reports/<int:rid>/delete-target/", pick("report_delete_target"), name="report_delete_target"),
    path("reports/<int:rid>/delete-target/", admin_views.report_delete_target, name="report_delete_target"),

    
]
