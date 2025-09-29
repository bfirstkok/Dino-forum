# forum/admin_urls.py
from django.urls import path
from . import admin_views as views

app_name = "adminpanel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # categories
    path("categories/", views.cat_list, name="cat_list"),
    path("categories/new/", views.cat_create, name="cat_create"),
    path("categories/<int:pk>/edit/", views.cat_edit, name="cat_edit"),
    path("categories/<int:pk>/delete/", views.cat_delete, name="cat_delete"),
    path("categories/<int:pk>/move/<str:direction>/", views.cat_move, name="cat_move"),

    # users
    path("users/", views.user_list, name="user_list"),
    path("users/<int:uid>/role/", views.user_role_toggle, name="user_role_toggle"),

    # reports
    path("reports/", views.report_list, name="report_list"),
    path("reports/<int:rid>/resolve/", views.report_resolve, name="report_resolve"),
    path("reports/<int:rid>/delete-target/", views.report_delete_target, name="report_delete_target"),
]
