# forum/views.py
from datetime import timedelta
import re
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, F, IntegerField, Value, Case, When, BooleanField
from django.db.models.functions import Coalesce

# --- Fallback สำหรับกรณีไม่มี django-ratelimit (เช่นบน Python 3.13) ---
try:
    from ratelimit.decorators import ratelimit
except Exception:  # pragma: no cover
    def ratelimit(*args, **kwargs):
        def _wrap(fn):
            return fn
        return _wrap

from .models import Category, Thread, Comment, Report, ThreadLike
from .forms import ThreadForm, CommentForm, ReportForm

# ===================== Constants =====================
TRENDING_CACHE_KEY = "home:trending:top5"

# ===================== Helpers (DRY) =====================

@ratelimit(key="ip", rate="10/m", method=["POST"], block=True)
@login_required
def report_create(request, target_type, target_id):
    if target_type not in ("thread", "comment"):
        return HttpResponseForbidden("invalid target")

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.target_type = target_type
            r.target_id = int(target_id)
            r.reporter = request.user
            r.save()
            messages.success(request, "ส่งรายงานเรียบร้อย")
            return redirect("forum:home")
    else:
        form = ReportForm()

    return render(
        request,
        "forum/report_form.html",
        {"form": form, "target_type": target_type, "target_id": target_id},
    )


def _thread_base_qs():
    return (
        Thread.objects
        .filter(is_deleted=False)
        .select_related("author", "category")
    )

def _with_comment_count(qs):
    # นับเฉพาะคอมเมนต์ที่ยังไม่ถูกลบ → alias: live_comment_count
    return qs.annotate(
        live_comment_count=Count("comments", filter=Q(comments__is_deleted=False)),
    )

def _with_like_count(qs):
    return qs.annotate(like_count=Count("likes", distinct=True))

def _extract_tags_from(thread):
    tag_re = re.compile(r"#([\wก-๙/+\-]+)")
    tags = []
    if thread.category_id:
        tags.append(thread.category.name)
    for field in (thread.title, thread.content):
        if field:
            tags.extend(tag_re.findall(field))
    clean, seen = [], set()
    for x in tags:
        if x and x not in seen:
            seen.add(x)
            clean.append(x)
    return clean

# ===================== Admin: จัดการกระทู้ =====================

def _annotate_counts(qs):
    # ตั้งชื่อไม่ชน property ในโมเดล
    return qs.annotate(
        live_comment_count=Count("comments", filter=Q(comments__is_deleted=False))
    )

@staff_member_required
def admin_threads(request):
    q      = (request.GET.get("q") or "").strip()
    cat    = (request.GET.get("cat") or "").strip()
    status = (request.GET.get("status") or "active").strip()  # active|deleted|all
    order  = (request.GET.get("order") or "-created_at").strip()

    qs = Thread.objects.select_related("author", "category")

    if status == "active":
        qs = qs.filter(is_deleted=False)
    elif status == "deleted":
        qs = qs.filter(is_deleted=True)

    if cat:
        qs = qs.filter(category_id=cat)

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(author__username__icontains=q)
        )

    qs = _annotate_counts(qs)

    order_map = {
        "-created_at": "-created_at",
        "created_at": "created_at",
        "-comment_count": "-live_comment_count",
    }
    qs = qs.order_by(order_map.get(order, "-created_at"))

    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))

    return render(request, "forum/admin_threads.html", {
        "cats": Category.objects.all(),
        "page_obj": page_obj,
        "q": q, "cat": cat, "status": status, "order": order,
    })

@staff_member_required
@require_POST
def admin_thread_toggle_delete(request, thread_id: int):
    updated = Thread.objects.filter(id=thread_id).update(
        is_deleted=Case(
            When(is_deleted=True, then=Value(False)),
            default=Value(True),
            output_field=BooleanField(),
        )
    )
    if updated:
        cache.delete(TRENDING_CACHE_KEY)  # << เพิ่ม
        messages.success(request, "อัปเดตสถานะกระทู้เรียบร้อย")
    else:
        messages.error(request, "ไม่พบกระทู้ที่ต้องการ")
    return redirect(request.POST.get("next") or "forum:admin_threads")

@staff_member_required
@require_POST
def admin_threads_bulk(request):
    ids = request.POST.getlist("ids")
    action = request.POST.get("action")
    if not ids:
        messages.warning(request, "ยังไม่ได้เลือกกระทู้")
        return redirect(request.POST.get("next") or "forum:admin_threads")

    qs = Thread.objects.filter(id__in=ids)
    if action == "delete":
        n = qs.update(is_deleted=True)
    elif action == "restore":
        n = qs.update(is_deleted=False)
    else:
        messages.warning(request, "ไม่รู้จักคำสั่งที่ส่งมา")
        return redirect(request.POST.get("next") or "forum:admin_threads")

    cache.delete(TRENDING_CACHE_KEY)  # << เพิ่ม
    messages.success(request, f"อัปเดต {n} กระทู้แล้ว")
    return redirect(request.POST.get("next") or "forum:admin_threads")

# ===================== Public Views =====================

def home(request):
    # ลิสต์หลัก
    qs = _with_like_count(_with_comment_count(_thread_base_qs())).order_by("-created_at")

    # ค้นหา/กรองหมวด
    q = (request.GET.get("q") or "").strip()
    cat = (request.GET.get("cat") or "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(author__username__icontains=q)
        )
    if cat:
        qs = qs.filter(category_id=cat)

    # เพจจิเนชัน
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # หมวดทั้งหมด (สำหรับ dropdown)
    cats = Category.objects.all().only("id", "name").order_by("order", "name")

    # กำลังมาแรง (7 วัน) — คิด score = คอมเมนต์*2 + ไลก์, แคช 5 นาที
    week_ago = timezone.now() - timedelta(days=7)
    trending = cache.get(TRENDING_CACHE_KEY)
    if trending is None:
        trending_qs = (
            _with_like_count(
                _with_comment_count(
                    _thread_base_qs().filter(created_at__gte=week_ago)
                )
            )
            .annotate(
                score=Coalesce(F("live_comment_count"), Value(0), output_field=IntegerField()) * 2
                     + Coalesce(F("like_count"), Value(0), output_field=IntegerField())
            )
            .order_by("-score", "-created_at")[:5]
        )
        trending = list(trending_qs)
        cache.set(TRENDING_CACHE_KEY, trending, 300)  # 5 นาที

    # เติม tag_list ให้ลิสต์ที่จะแสดงจริง ๆ
    threads = list(page_obj.object_list)
    for t in threads + trending:
        t.tag_list = _extract_tags_from(t)[:5]

    # liked flags
    if request.user.is_authenticated and threads:
        liked_ids = set(
            ThreadLike.objects
            .filter(user=request.user, thread_id__in=[th.id for th in threads])
            .values_list("thread_id", flat=True)
        )
    else:
        liked_ids = set()
    for t in threads:
        t.liked = t.id in liked_ids

    # หมวดหมู่ยอดนิยม (นับจำนวนเธรดที่ไม่ถูกลบ)
    top_cats = (
        Category.objects
        .annotate(thread_count=Count("threads", filter=Q(threads__is_deleted=False)))
        .order_by("-thread_count", "order", "name")[:10]
    )

    return render(
        request,
        "forum/thread_list.html",
        {
            "threads": threads,
            "page_obj": page_obj,
            "cats": cats,
            "q": q,
            "cat": cat,
            "trending": trending,
            "top_cats": top_cats,
        },
    )

@ratelimit(key="ip", rate="10/m", block=True)
@login_required
def thread_create(request):
    if request.method == "POST":
        form = ThreadForm(request.POST, request.FILES)
        if form.is_valid():
            t = form.save(commit=False)
            t.author = request.user
            t.save()
            cache.delete(TRENDING_CACHE_KEY)  # อัปเดตมาแรง
            return redirect("forum:thread_detail", thread_id=t.id)
    else:
        form = ThreadForm()
    return render(request, "forum/thread_form.html", {"form": form})

@ratelimit(key="ip", rate="20/m", method=["POST"], block=True)
def thread_detail(request, thread_id):
    # ดึงกระทู้โดยไม่กรองสถานะก่อน
    thread = get_object_or_404(Thread, pk=thread_id)

    # ถ้ากระทู้ถูกลบ ให้เปิดดูได้เฉพาะ staff/superuser
    if thread.is_deleted and not (request.user.is_staff or request.user.is_superuser):
        raise Http404("No Thread matches the given query.")

    tags = _extract_tags_from(thread)[:6]

    # ฟอร์มคอมเมนต์
    comment_form = CommentForm()
    if request.method == "POST" and request.user.is_authenticated:
        comment_form = CommentForm(request.POST, request.FILES)
        if comment_form.is_valid():
            c = comment_form.save(commit=False)
            c.thread = thread
            c.author = request.user
            c.save()
            cache.delete(f"thread:{thread.id}:comment_count")
            cache.delete(TRENDING_CACHE_KEY)  # คอมเมนต์กระทบคะแนนมาแรง
            return redirect("forum:thread_detail", thread_id=thread.id)

    # โหลด/นับคอมเมนต์ (แคช 60s)
    cache_key = f"thread:{thread_id}:comment_count"
    comment_count = cache.get(cache_key)
    if comment_count is None:
        comment_count = Comment.objects.filter(thread=thread, is_deleted=False).count()
        cache.set(cache_key, comment_count, 60)
    thread.live_comment_count = comment_count  # safe (ไม่ชน property)

    comments_qs = (
        Comment.objects
        .filter(thread=thread, is_deleted=False)
        .select_related("author")
        .order_by("created_at")
    )

    likes_count = ThreadLike.objects.filter(thread=thread).count()
    liked = request.user.is_authenticated and ThreadLike.objects.filter(
        thread=thread, user=request.user
    ).exists()

    return render(
        request,
        "forum/thread_detail.html",
        {
            "thread": thread,
            "tags": tags,
            "comment_form": comment_form,
            "comment_count": comment_count,
            "comments": comments_qs,
            "likes_count": likes_count,
            "liked": liked,
        },
    )

@ratelimit(key="ip", rate="30/m", method=["POST"], block=True)
@login_required
def thread_edit(request, thread_id: int):
    thread = get_object_or_404(Thread, id=thread_id)

    # ให้ staff/superuser แก้ไขได้เสมอ
    if not (request.user.is_staff or request.user.is_superuser or request.user.id == thread.author_id):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์แก้ไขในกระทู้นี้")

    if request.method == "POST":
        form = ThreadForm(request.POST, request.FILES, instance=thread)
        if form.is_valid():
            form.save()
            messages.success(request, "บันทึกการแก้ไขกระทู้แล้ว")
            return redirect("forum:thread_detail", thread_id=thread.id)
    else:
        form = ThreadForm(instance=thread)

    return render(request, "forum/thread_form.html", {"form": form, "thread": thread})

@ratelimit(key="ip", rate="15/m", method=["POST"], block=True)
@login_required
def thread_delete(request, thread_id: int):
    thread = get_object_or_404(Thread, id=thread_id)

    if not (request.user.is_staff or request.user.is_superuser or request.user.id == thread.author_id):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบกระทู้นี้")

    if request.method == "POST":
        # soft-delete
        thread.is_deleted = True
        thread.save(update_fields=["is_deleted"])
        messages.success(request, "ลบกระทู้แล้ว")
        return redirect("forum:home")

    # ป้องกัน GET ตรง ๆ
    return redirect("forum:thread_detail", thread_id=thread.id)

@require_POST
@login_required
def thread_like_toggle(request, thread_id):
    thread = get_object_or_404(Thread, pk=thread_id, is_deleted=False)

    like_qs = ThreadLike.objects.filter(thread=thread, user=request.user)
    if like_qs.exists():
        like_qs.delete()
    else:
        ThreadLike.objects.create(thread=thread, user=request.user)

    cache.delete(TRENDING_CACHE_KEY)  # ไลก์กระทบคะแนนมาแรง

    next_url = request.POST.get("next") or reverse(
        "forum:thread_detail", kwargs={"thread_id": thread.id}
    )
    return redirect(next_url)

@login_required
def comment_edit(request, pk: int):
    c = get_object_or_404(Comment, pk=pk)
    if not (request.user.is_staff or request.user.is_superuser or request.user.id == c.author_id):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์แก้ไขความคิดเห็นนี้")

    form = CommentForm(request.POST or None, request.FILES or None, instance=c)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "แก้ไขความคิดเห็นแล้ว")
        cache.delete(f"thread:{c.thread_id}:comment_count")
        cache.delete(TRENDING_CACHE_KEY)
        return redirect("forum:thread_detail", thread_id=c.thread_id)

    return render(request, "forum/comment_form.html", {"form": form, "comment": c})

@login_required
def comment_delete(request, pk: int):
    c = get_object_or_404(Comment, pk=pk)
    if not (request.user.is_staff or request.user.is_superuser or request.user.id == c.author_id):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบความคิดเห็นนี้")
    if request.method == "POST":
        c.is_deleted = True
        c.save(update_fields=["is_deleted"])
        messages.success(request, "ลบความคิดเห็นแล้ว")
        # ล้างแคช มาแรง + ตัวนับคอมเมนต์
        cache.delete(TRENDING_CACHE_KEY)
        cache.delete(f"thread:{c.thread_id}:comment_count")
    return redirect("forum:thread_detail", thread_id=c.thread_id)
