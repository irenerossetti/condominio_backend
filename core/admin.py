from django.contrib import admin
from .models import Profile, Unit, ExpenseType, Fee, Payment, Notice

@admin.register(ExpenseType)
class ExpenseTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "amount_default", "active")
    search_fields = ("name",)
    list_filter = ("active",)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "tower", "number", "owner")
    search_fields = ("code", "tower", "number", "owner__username")

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ("id", "unit", "expense_type", "period", "amount", "status", "issued_at", "due_date")
    list_filter = ("status", "period", "expense_type")
    search_fields = ("unit__code", "unit__owner__username")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "fee", "amount", "paid_at", "method")
    list_filter = ("method",)
    search_fields = ("fee__unit__code",)

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "published_at", "created_by")
    search_fields = ("title", "body")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "full_name", "phone", "role")
    list_filter = ("role",)
    search_fields = ("full_name", "user__username", "user__email")
