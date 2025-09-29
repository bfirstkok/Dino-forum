from django.urls import path
from . import views

app_name = "forum"

urlpatterns = [
    path("", views.home, name="home"),

    path("threads/new/", views.thread_create, name="thread_create"),
    path("threads/<int:thread_id>/", views.thread_detail, name="thread_detail"),
    path("threads/<int:thread_id>/edit/", views.thread_edit, name="thread_edit"),
    path("threads/<int:thread_id>/delete/", views.thread_delete, name="thread_delete"),
    path("threads/<int:thread_id>/like/", views.thread_like_toggle, name="thread_like_toggle"),

    path("report/<str:target_type>/<int:target_id>/", views.report_create, name="report_create"),

    # เส้นทางแผงจัดการ (อย่าใช้ /admin/ เพราะชน Django Admin)
    path("staff/threads/", views.admin_threads, name="admin_threads"),
    path("staff/threads/bulk/", views.admin_threads_bulk, name="admin_threads_bulk"),
    path("staff/threads/<int:thread_id>/toggle-delete/",
         views.admin_thread_toggle_delete, name="admin_thread_toggle_delete"),

    path("comments/<int:pk>/edit/", views.comment_edit, name="comment_edit"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
]
