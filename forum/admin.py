from django.contrib import admin
from .models import Category, Thread, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    ordering = ("order", "name")
    # ไม่ให้กรอก slug เอง ให้ระบบสร้างให้
    fields = ("name", "order")          # หรือใช้ exclude = ("slug",)

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "created_at", "is_deleted")
    list_filter = ("category", "is_deleted")
    search_fields = ("title", "content")

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("thread", "author", "created_at", "is_deleted")
from .models import Category, Thread, Comment, Report
# … ของเดิม …
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("target_type", "target_id", "reporter", "status", "created_at")
    list_filter = ("status", "target_type")
    search_fields = ("reason",)
