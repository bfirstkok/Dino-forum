# accounts/views.py
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from allauth.account.views import LoginView, SignupView, LogoutView
from django.apps import apps
from django.core.paginator import Paginator

from forum.models import Thread
from .models import Profile
from .forms import ProfileForm, SignupForm

User = get_user_model()


# ----------------------- Auth Views -----------------------

class MyLoginView(LoginView):
    template_name = "accounts/login.html"

class MySignupView(SignupView):
    template_name = "accounts/signup.html"

class MyLogoutView(LogoutView):
    template_name = "accounts/logout.html"


# ----------------------- Helpers -----------------------

def _thread_base_qs():
    qs = Thread.objects.all().select_related("author", "category")
    # กรอง soft-delete ถ้ามี
    if "is_deleted" in {f.name for f in Thread._meta.get_fields()}:
        qs = qs.filter(is_deleted=False)
    # (ถ้ามี status และคุณใช้) qs = qs.filter(status="published")
    return qs

def _with_live_comment_count(qs):
    """annotate นับเฉพาะคอมเมนต์ที่ยังไม่ถูกลบ → alias: live_comment_count"""
    return qs.annotate(
        live_comment_count=Count("comments", filter=Q(comments__is_deleted=False))
    )


# ----------------------- โปรไฟล์ -----------------------

@login_required
def profile_me(request):
    return redirect("accounts:profile_detail", username=request.user.username)


def profile_detail(request, username):
    owner = get_object_or_404(User, username=username)
    profile = getattr(owner, "profile", None)
    joined = owner.date_joined

    tab = request.GET.get("tab", "overview")
    page_number = request.GET.get("page", 1)

    # กระทู้ที่เจ้าของตั้งเอง
    threads_qs = (
        _with_live_comment_count(
            _thread_base_qs().filter(author=owner)
        )
        .order_by("-created_at")
    )

    # กระทู้ที่เจ้าของเคยไปตอบ (เอาเฉพาะที่คอมเมนต์ยังไม่ถูกลบ)
    replied_qs = (
        _with_live_comment_count(
            _thread_base_qs().filter(
                Q(comments__author=owner) & Q(comments__is_deleted=False)
            ).distinct()
        )
        .order_by("-created_at")
    )

    ctx = {
        "owner": owner,
        "profile": profile,
        "joined": joined,
        "tab": tab,
        "threads_count": threads_qs.count(),
        "replies_count": replied_qs.count(),
    }

    if tab == "threads":
        ctx["page_obj"] = Paginator(threads_qs, 10).get_page(page_number)
    elif tab == "replies":
        ctx["page_obj"] = Paginator(replied_qs, 10).get_page(page_number)
    else:  # overview
        ctx["threads_recent"] = list(threads_qs[:5])
        ctx["replied_recent"] = list(replied_qs[:5])

    return render(request, "accounts/profile_detail.html", ctx)


# ----------------------- แก้ไขโปรไฟล์ / สมัครสมาชิก -----------------------

@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_email = request.POST.get("email", "").strip()
            if new_email and new_email != request.user.email:
                request.user.email = new_email
                request.user.save(update_fields=["email"])

            form.save()
            messages.success(request, "บันทึกโปรไฟล์เรียบร้อยแล้ว")
            return redirect("accounts:profile_detail", username=request.user.username)
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/edit_profile.html", {"form": form, "profile": profile})


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile_detail", username=request.user.username)

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("forum:home")
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


# ----------------------- Settings -----------------------

@login_required
def settings_home(request):
    return render(
        request,
        "accounts/settings_home.html",
        {"has_social": apps.is_installed("allauth.socialaccount")},
    )


@login_required
def devices_list(request):
    sessions = []
    qs = Session.objects.filter(expire_date__gte=timezone.now()).order_by("-expire_date")
    for s in qs:
        data = s.get_decoded()
        if data.get("_auth_user_id") == str(request.user.id):
            sessions.append({
                "key": s.session_key,
                "expire": s.expire_date,
                "ip": data.get("ip"),
                "ua": data.get("ua"),
                "login_at": data.get("login_at"),
                "is_current": (s.session_key == request.session.session_key),
            })
    return render(request, "accounts/settings_devices.html", {"sessions": sessions})


@login_required
def device_revoke(request, session_key: str):
    if request.method != "POST":
        return HttpResponseForbidden("POST only")
    s = get_object_or_404(Session, session_key=session_key)
    data = s.get_decoded()
    if data.get("_auth_user_id") != str(request.user.id):
        return HttpResponseForbidden("Not yours")
    s.delete()
    messages.success(request, "ยกเลิกอุปกรณ์เรียบร้อยแล้ว")
    return redirect("accounts:devices_list")
