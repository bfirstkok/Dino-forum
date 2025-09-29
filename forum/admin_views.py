# forum/admin_views.py
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db.models import (
    Q, Count, Case, When, Value, IntegerField, F, OuterRef, Subquery
)

from .models import Category, Thread, Comment, Report
from .forms import CategoryForm, UserRoleForm
from .views import TRENDING_CACHE_KEY

User = get_user_model()

# ให้เข้าได้เฉพาะ staff
is_staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff)

# ==================== Reports Center (รายการรายงาน) ====================

@staff_member_required
def admin_reports(request):
    q = (request.GET.get("q") or "").strip()

    # หา thread_id ให้ทุก report (ถ้าเป็น comment จะดึง thread_id ของคอมเมนต์นั้น)
    comment_thread_sq = (
        Comment.objects.filter(pk=OuterRef("target_id"))
        .values("thread_id")[:1]
    )

    qs = (
        Report.objects.select_related("reporter")
        .annotate(
            thread_id=Case(
                When(target_type="thread", then=F("target_id")),
                When(target_type="comment", then=Subquery(comment_thread_sq)),
                default=Value(None),
                output_field=IntegerField(),
            )
        )
        .order_by("-id")
    )

    if q:
        qs = qs.filter(
            Q(reason__icontains=q)
            | Q(target_type__icontains=q)
            | Q(target_id__icontains=q)
            | Q(reporter__username__icontains=q)
        )

    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))

    return render(
        request,
        "forum/admin_reports.html",
        {"page_obj": page_obj, "q": q},
    )

@staff_member_required
@require_POST
def report_resolve(request, rid: int):
    """ปิดรายงานโดยไม่ลบเป้าหมาย"""
    rep = get_object_or_404(Report, id=rid)
    if not rep.resolved:
        rep.resolved = True
        rep.save(update_fields=["resolved"])
        messages.success(request, "ปิดรายงานแล้ว")
    else:
        messages.info(request, "รายงานนี้ถูกปิดไว้แล้ว")
    return redirect(request.POST.get("next") or "adminpanel:report_list")

@staff_member_required
@require_POST
def report_delete_target(request, rid: int):
    """
    ลบ/ซ่อนเป้าหมายที่ถูกรายงาน:
      - thread  -> soft-delete (is_deleted=True) + ล้าง cache มาแรง
      - comment -> soft-delete + ล้าง cache ตัวนับคอมเมนต์ของ thread นั้น + ล้าง cache มาแรง
    ปิดรายงานโดยการลบแถวรายงาน (ไม่มีฟิลด์ resolved)
    """
    rep = get_object_or_404(Report, id=rid)

    msg = "ชนิดเป้าหมายไม่รองรับ"
    if rep.target_type == "thread":
        changed = Thread.objects.filter(pk=rep.target_id).update(is_deleted=True)
        cache.delete(TRENDING_CACHE_KEY)
        msg = "ลบกระทู้แล้ว" if changed else "ไม่พบกระทู้ (อาจถูกลบไปแล้ว)"

    elif rep.target_type == "comment":
        # หา thread_id ของคอมเมนต์เพื่อเคลียร์ cache ตัวนับให้ถูกกระทู้
        tid = Comment.objects.filter(pk=rep.target_id).values_list("thread_id", flat=True).first()
        changed = Comment.objects.filter(pk=rep.target_id).update(is_deleted=True)
        if tid:
            cache.delete(f"thread:{tid}:comment_count")
        cache.delete(TRENDING_CACHE_KEY)
        msg = "ลบคอมเมนต์แล้ว" if changed else "ไม่พบคอมเมนต์ (อาจถูกลบไปแล้ว)"

    # ปิดรายงานโดยลบแถวรายงานออก
    rep.delete()

    messages.success(request, msg)
    return redirect(request.POST.get("next") or "adminpanel:report_list")

# ==================== Dashboard ====================

@is_staff_required
def dashboard(request):
    now = timezone.now()
    week = now - timedelta(days=7)

    ctx = {
        "total_users": User.objects.count(),
        "new_users_7d": User.objects.filter(date_joined__gte=week).count(),

        "total_threads": Thread.objects.filter(is_deleted=False).count(),
        "threads_7d": Thread.objects.filter(is_deleted=False, created_at__gte=week).count(),

        # นับเฉพาะคอมเมนต์ที่ยังไม่ถูกลบ และอยู่ในกระทู้ที่ยังไม่ถูกลบ
        "total_comments": Comment.objects.filter(
            is_deleted=False, thread__is_deleted=False
        ).count(),
        "comments_7d": Comment.objects.filter(
            is_deleted=False, thread__is_deleted=False, created_at__gte=week
        ).count(),

        "reports_open": Report.objects.count(),
        "latest_threads": Thread.objects.filter(is_deleted=False).order_by("-created_at")[:5],
        "latest_reports": Report.objects.order_by("-id")[:5],
    }
    return render(request, "adminpanel/dashboard.html", ctx)

# ==================== Categories ====================

@is_staff_required
def cat_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Category.objects.all().order_by("order", "name")
    if q:
        qs = qs.filter(name__icontains=q)
    return render(request, "adminpanel/cat_list.html", {"items": qs, "q": q})

@is_staff_required
def cat_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "สร้างหมวดหมู่แล้ว")
        return redirect("adminpanel:cat_list")
    return render(request, "adminpanel/cat_form.html", {"form": form})

@is_staff_required
def cat_edit(request, pk):
    obj = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "บันทึกหมวดหมู่แล้ว")
        return redirect("adminpanel:cat_list")
    return render(request, "adminpanel/cat_form.html", {"form": form, "obj": obj})

@is_staff_required
def cat_delete(request, pk):
    obj = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "ลบหมวดหมู่แล้ว")
        return redirect("adminpanel:cat_list")
    return render(request, "adminpanel/cat_delete_confirm.html", {"obj": obj})

@is_staff_required
def cat_move(request, pk, direction: str):
    obj = get_object_or_404(Category, pk=pk)
    delta = -1 if direction == "up" else 1
    obj.order = (obj.order or 0) + delta
    obj.save(update_fields=["order"])
    return redirect("adminpanel:cat_list")

# ==================== Users & Roles ====================

@is_staff_required
def user_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = User.objects.all().order_by("-is_staff", "username")
    if q:
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
    return render(request, "adminpanel/user_list.html", {"items": qs, "q": q})

@is_staff_required
def user_role_toggle(request, uid):
    u = get_object_or_404(User, pk=uid)
    if request.method == "POST":
        form = UserRoleForm(request.POST, instance=u)
        if form.is_valid():
            form.save()
            messages.success(request, "อัปเดตสิทธิ์ผู้ใช้แล้ว")
            return redirect("adminpanel:user_list")
    else:
        form = UserRoleForm(instance=u)
    return render(request, "adminpanel/user_role_form.html", {"form": form, "target": u})
