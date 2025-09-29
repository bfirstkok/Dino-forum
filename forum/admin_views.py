# forum/admin_views.py
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Category, Thread, Comment, Report
from .forms import CategoryForm, UserRoleForm

User = get_user_model()

# ให้เข้าได้เฉพาะ staff
is_staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff)

# ========== Dashboard ==========
@is_staff_required
def dashboard(request):
    now = timezone.now()
    week = now - timedelta(days=7)
    ctx = {
        "total_users": User.objects.count(),
        "new_users_7d": User.objects.filter(date_joined__gte=week).count(),
        "total_threads": Thread.objects.filter(is_deleted=False).count(),
        "threads_7d": Thread.objects.filter(is_deleted=False, created_at__gte=week).count(),
        "total_comments": Comment.objects.filter(is_deleted=False).count(),
        "comments_7d": Comment.objects.filter(is_deleted=False, created_at__gte=week).count(),
        # วิธีง่ายสุด: ใช้ลบแถวเมื่อ resolve → รายงานค้าง = จำนวนแถว
        "reports_open": Report.objects.count(),
        "latest_threads": Thread.objects.filter(is_deleted=False).order_by("-created_at")[:5],
        "latest_reports": Report.objects.order_by("-id")[:5],
    }
    return render(request, "adminpanel/dashboard.html", ctx)

# ========== Categories ==========
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

# ========== Users & Roles ==========
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

# ========== Reports Center ==========
@is_staff_required
def report_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Report.objects.all().order_by("-id")
    if q:
        qs = qs.filter(Q(reason__icontains=q) | Q(target_type__icontains=q))
    return render(request, "adminpanel/report_list.html", {"items": qs, "q": q})

@is_staff_required
def report_resolve(request, rid):
    r = get_object_or_404(Report, pk=rid)
    if request.method == "POST":
        r.delete()  # ปิดรายงานแบบลบแถว (ง่ายสุด)
        messages.success(request, "ปิดรายงานแล้ว")
    return redirect("adminpanel:report_list")

@is_staff_required
def report_delete_target(request, rid):
    r = get_object_or_404(Report, pk=rid)
    if r.target_type == "thread":
        t = get_object_or_404(Thread, pk=r.target_id)
        if hasattr(t, "is_deleted"):
            if not t.is_deleted:
                t.is_deleted = True
                t.save(update_fields=["is_deleted"])
        else:
            t.delete()
    elif r.target_type == "comment":
        c = get_object_or_404(Comment, pk=r.target_id)
        if hasattr(c, "is_deleted"):
            if not c.is_deleted:
                c.is_deleted = True
                c.save(update_fields=["is_deleted"])
        else:
            c.delete()
    r.delete()  # ปิดรายงาน
    messages.success(request, "ลบเป้าหมายและปิดรายงานแล้ว")
    return redirect("adminpanel:report_list")
