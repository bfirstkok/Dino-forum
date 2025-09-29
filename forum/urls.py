# forum/urls.py
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

    # เพิ่มตรงนี้
    path("comments/<int:pk>/edit/", views.comment_edit, name="comment_edit"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
]
