from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import MyLoginView, MySignupView, MyLogoutView


urlpatterns = [
    path("admin/", admin.site.urls),

    # โปรไฟล์ของเรา (namespace accounts)
    path("u/", include(("accounts.urls", "accounts"), namespace="accounts")),

    # ✅ override allauth ให้ใช้ template ใน templates/accounts/
    path("accounts/login/",  MyLoginView.as_view(),  name="account_login"),
    path("accounts/signup/", MySignupView.as_view(), name="account_signup"),
    path("accounts/logout/", MyLogoutView.as_view(), name="account_logout"),

    # ที่เหลือของ allauth
    path("accounts/", include("allauth.urls")),

    # forum
    path("", include(("forum.urls", "forum"), namespace="forum")),
    path("adminpanel/", include(("forum.admin_urls", "adminpanel"), namespace="adminpanel")),

    # adminpanel
    path("adminpanel/", include(("forum.admin_urls", "adminpanel"), namespace="adminpanel")),

    path("adminpanel/", include("forum.admin_urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
