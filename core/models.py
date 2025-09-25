from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Profile(models.Model):
    ROLE_CHOICES = [("ADMIN", "Administrador"), ("RESIDENT", "Residente"), ("STAFF", "Personal")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="RESIDENT")
    def __str__(self): return f"{self.full_name or self.user.username} ({self.role})"

class Unit(models.Model):
    code = models.CharField(max_length=30, unique=True)   # p.ej. T1-302
    tower = models.CharField(max_length=30)
    number = models.CharField(max_length=30)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="units")
    def __str__(self): return self.code

class ExpenseType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    amount_default = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Fee(models.Model):
    STATUS = [("ISSUED", "Emitida"), ("PAID", "Pagada"), ("OVERDUE", "Vencida")]
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="fees")
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.PROTECT)
    period = models.CharField(max_length=7)  # YYYY-MM (p.ej. 2025-09)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=8, choices=STATUS, default="ISSUED")
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("unit", "expense_type", "period")

    def __str__(self): return f"{self.unit} {self.period} {self.expense_type}"

class Payment(models.Model):
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=30, default="cash")
    note = models.TextField(blank=True)

class Notice(models.Model):
    title = models.CharField(max_length=120)
    body = models.TextField()
    published_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta: ordering = ["-published_at"]

# ... al final de core/models.py

class CommonArea(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Reservation(models.Model):
    area = models.ForeignKey(CommonArea, on_delete=models.CASCADE, related_name="reservations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.area.name} - {self.user.username} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"
    
# ... al final de core/models.py

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pendiente"),
        ("IN_PROGRESS", "En Progreso"),
        ("COMPLETED", "Completado"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_requests")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="maintenance_requests")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title