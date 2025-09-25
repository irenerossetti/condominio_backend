from django.contrib import admin
from .models import Profile, Unit, ExpenseType, Fee, Payment, Notice
from .models import MaintenanceRequest # <-- Añadir

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

# ... al inicio del archivo, modifica la línea de importación de models
from .models import (
    Profile, Unit, ExpenseType, Fee, Payment, Notice,
    CommonArea, Reservation  # <-- Añade CommonArea y Reservation
)

# ... (Aquí van los @admin.register que ya tenías) ...

# ... Añade estas clases al final del archivo
@admin.register(CommonArea)
class CommonAreaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "capacity", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "area", "user", "start_time", "end_time")
    list_filter = ("area",)
    search_fields = ("user__username", "notes")

@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'unit', 'reported_by', 'created_at')
    list_filter = ('status', 'unit')    