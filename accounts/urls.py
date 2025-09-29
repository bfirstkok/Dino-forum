# accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("me/", views.profile_me, name="profile_me"),
    path("edit/", views.profile_edit, name="profile_edit"),
    path("settings/", views.settings_home, name="settings_home"),
    path("devices/", views.devices_list, name="devices_list"),
    path("devices/<str:session_key>/revoke/", views.device_revoke, name="device_revoke"),
    path("<str:username>/", views.profile_detail, name="profile_detail"),
]
