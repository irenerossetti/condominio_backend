from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

# --- FUNCIÓN AUXILIAR (definida al principio) ---
def maintenance_attachment_path(instance, filename):
    return f'maintenance/{instance.request_id}/{filename}'

# --- MODELOS DE LA APLICACIÓN ---

class Profile(models.Model):
    ROLE_CHOICES = [("ADMIN", "Administrador"), ("RESIDENT", "Residente"), ("STAFF", "Personal")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="RESIDENT")
    def __str__(self): return f"{self.full_name or self.user.username} ({self.role})"

class Unit(models.Model):
    code = models.CharField(max_length=30, unique=True)
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
    period = models.CharField(max_length=7)
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

class NoticeCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#888888", help_text="Color en formato hexadecimal, ej. #FF5733")
    def __str__(self): return self.name
    class Meta:
        ordering = ["name"]

class Notice(models.Model):
    title = models.CharField(max_length=120)
    body = models.TextField()
    publish_date = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    category = models.ForeignKey(NoticeCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="notices")
    class Meta:
        ordering = ["-publish_date"]

class CommonArea(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Reservation(models.Model):
    area = models.ForeignKey(CommonArea, on_delete=models.CASCADE, related_name="reservations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reservations")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.area.name} - {self.user.username} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [("PENDING", "Pendiente"), ("IN_PROGRESS", "En Progreso"), ("COMPLETED", "Completado")]
    PRIORITY_CHOICES = [("BAJA", "Baja"), ("MEDIA", "Media"), ("ALTA", "Alta"), ("URGENTE", "Urgente")]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="MEDIA", verbose_name="Prioridad")
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_requests")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="maintenance_requests")
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_maintenance_requests")
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="completed_maintenance_requests")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de finalización")
    def __str__(self): return self.title

class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
    def __str__(self): return f'{self.user.username} - {self.action} at {self.timestamp.strftime("%Y-%m-%d %H:%M")}'

class MaintenanceRequestComment(models.Model):
    request = models.ForeignKey('MaintenanceRequest', on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='maintenance_comments')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    def __str__(self): return f"Comentario de {self.user.username} en solicitud {self.request.id}"

class Vehicle(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vehicles")
    plate = models.CharField(max_length=20, default='', help_text="Placa del vehículo")
    brand = models.CharField(max_length=50, blank=True, help_text="Marca (ej. Toyota)")
    # 👇 LA COMILLA FALTANTE ESTABA AQUÍ
    model = models.CharField(max_length=50, blank=True, help_text="Modelo (ej. Corolla)")
    color = models.CharField(max_length=30, blank=True)
    def __str__(self): return f"{self.plate} ({self.owner.username})"

class Pet(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pets")
    name = models.CharField(max_length=100, default='')
    species = models.CharField(max_length=50, blank=True, help_text="Especie (ej. Perro, Gato)")
    breed = models.CharField(max_length=50, blank=True, help_text="Raza (ej. Labrador)")
    def __str__(self): return f"{self.name} ({self.owner.username})"

class FamilyMember(models.Model):
    resident = models.ForeignKey(User, on_delete=models.CASCADE, related_name="family_members")
    full_name = models.CharField(max_length=200, blank=True, default='')
    relationship = models.CharField(max_length=50, blank=True, default='', help_text="Parentesco (ej. Esposo/a, Hijo/a)")
    phone = models.CharField(max_length=30, blank=True)
    def __str__(self): return f"{self.full_name} ({self.relationship} de {self.resident.username})"

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True, help_text="URL a la que debe dirigir la notificación")
    class Meta:
        ordering = ['-created_at']
    def __str__(self): return f"Notificación para {self.user.username}: {self.message}"

class MaintenanceRequestAttachment(models.Model):
    request = models.ForeignKey(MaintenanceRequest, on_delete=models.CASCADE, related_name='attachments')
    file = models.ImageField(upload_to=maintenance_attachment_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Adjunto para la solicitud {self.request.id}"