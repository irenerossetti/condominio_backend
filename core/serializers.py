from django.contrib.auth import get_user_model
from rest_framework import serializers

from django.db.models import Q
from django.db import transaction # 👈 Asegúrate de que este import esté al principio del archivo
from .models import (
    Profile, Unit, ExpenseType, Fee, Payment, Notice,
    CommonArea, Reservation, MaintenanceRequest, ActivityLog, MaintenanceRequestComment,
    Vehicle, Pet, FamilyMember, NoticeCategory, Notification, MaintenanceRequestAttachment  # <-- ¡Añadido aquí!
)
User = get_user_model()

# --- Serializers para modelos relacionados ---
class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = '__all__'

class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = '__all__'
# ---------------------------------------------
# --- Serializers Principales ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active", "is_staff", "date_joined"]

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["full_name", "phone", "role"]

class MeSerializer(serializers.Serializer):
    """Solo para componer la respuesta de /api/me/"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    profile = ProfileSerializer(allow_null=True)

class UserWithProfileSerializer(UserSerializer):
    profile = ProfileSerializer(read_only=True)
    vehicles = VehicleSerializer(many=True, read_only=True)
    pets = PetSerializer(many=True, read_only=True)
    family_members = FamilyMemberSerializer(many=True, read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["profile", "vehicles", "pets", "family_members"]


# 👇 REEMPLAZA TODA TU CLASE AdminUserWriteSerializer CON ESTO
class AdminUserWriteSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.ChoiceField(write_only=True, choices=Profile.ROLE_CHOICES, required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "full_name", "phone", "role", "is_active"]
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
        }

    @transaction.atomic
    def create(self, validated_data):
        profile_data = {
            "full_name": validated_data.pop("full_name", ""),
            "phone": validated_data.pop("phone", ""),
            "role": validated_data.pop("role", "RESIDENT"),
        }
        password = validated_data.pop("password", None)
        user_instance = User.objects.create_user(**validated_data, password=password)
        Profile.objects.create(user=user_instance, **profile_data)
        return user_instance

    @transaction.atomic
    def update(self, instance, validated_data):
        # Actualiza el modelo User
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        
        instance.save()

        # Actualiza o crea el modelo Profile
        profile_instance, _ = Profile.objects.get_or_create(user=instance)
        profile_instance.full_name = validated_data.get('full_name', profile_instance.full_name)
        profile_instance.phone = validated_data.get('phone', profile_instance.phone)
        profile_instance.role = validated_data.get('role', profile_instance.role)
        profile_instance.save()

        return instance

class UnitSerializer(serializers.ModelSerializer):
    owner_username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Unit
        fields = ["id", "code", "tower", "number", "owner", "owner_username"]
        read_only_fields = ["id"]

    def get_owner_username(self, obj):
        return getattr(obj.owner, "username", None)
    
class ExpenseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseType
        fields = ["id", "name", "amount_default", "active"]

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "paid_at", "method", "note"]

class FeeSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    owner_username = serializers.CharField(source="unit.owner.username", read_only=True)
    owner_id = serializers.IntegerField(source="unit.owner_id", read_only=True)
    expense_type_name = serializers.CharField(source="expense_type.name", read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Fee
        fields = [
            "id", "unit", "unit_code", "owner_username",
            "owner_id", "owner_username", 
            "expense_type", "expense_type_name",
            "period", "amount", "status", "issued_at", "due_date",
            "payments",
        ]
# 👇 AÑADE ESTE NUEVO SERIALIZADOR
class NoticeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeCategory
        fields = ["id", "name", "color"]

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'is_read', 'created_at', 'link']

# 👇 MODIFICA EL NoticeSerializer
class NoticeSerializer(serializers.ModelSerializer):
    # ... (el resto de tu NoticeSerializer se queda igual)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, allow_null=True)
    category_color = serializers.CharField(source="category.color", read_only=True, allow_null=True)

    class Meta:
        model = Notice
        # 👇 Añade 'category', 'category_name' y 'category_color' a la lista
        fields = [
            "id", "title", "body", "publish_date", "created_by", "created_by_username",
            "category", "category_name", "category_color"
        ]
        read_only_fields = ["id", "created_by", "created_by_username"]

class CommonAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonArea
        fields = ["id", "name", "description", "capacity", "is_active"]

# 👇 REEMPLAZA ESTA CLASE COMPLETA
class ReservationSerializer(serializers.ModelSerializer):
    area_name = serializers.CharField(source="area.name", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id", "area", "area_name", "user", "user_username",
            "start_time", "end_time", "notes", "created_at"
        ]
        read_only_fields = ["user", "created_at"]

    def validate(self, data):
        """
        Validación para prevenir el solapamiento de reservas (double-booking).
        """
        # Obtenemos los datos, usando los del objeto existente si es una actualización
        start_time = data.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = data.get('end_time', getattr(self.instance, 'end_time', None))
        area = data.get('area', getattr(self.instance, 'area', None))

        if not all([start_time, end_time, area]):
            # Si falta algún dato clave, dejamos que las validaciones por defecto se encarguen.
            return data

        if start_time >= end_time:
            raise serializers.ValidationError("La hora de finalización debe ser posterior a la hora de inicio.")

        # Lógica de comprobación de conflictos
        conflicting_reservations = Reservation.objects.filter(
            area=area,
            # El conflicto existe si:
            # 1. La nueva reserva empieza durante otra reserva.
            # 2. La nueva reserva termina durante otra reserva.
            # 3. La nueva reserva envuelve completamente a otra reserva.
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        # Si estamos actualizando, debemos excluir la propia reserva de la comprobación
        if self.instance:
            conflicting_reservations = conflicting_reservations.exclude(pk=self.instance.pk)

        if conflicting_reservations.exists():
            raise serializers.ValidationError(
                "Este horario ya está ocupado para el área seleccionada. Por favor, elige otro."
            )
            
        return data

class ActivityLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ActivityLog
        fields = ["id", "user", "user_username", "action", "timestamp", "details"]
        read_only_fields = ["id", "user", "user_username", "timestamp", "action", "details"]

# Mueve la definicion del serializador de comentarios antes de que se use
class MaintenanceRequestCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = MaintenanceRequestComment
        fields = ['id', 'request', 'user', 'user_username', 'body', 'created_at']
        read_only_fields = ['user', 'request']

# 👇 AÑADE ESTA NUEVA CLASE
class MaintenanceRequestAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequestAttachment
        fields = ['id', 'file', 'uploaded_at']

class MaintenanceRequestSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    reported_by_username = serializers.CharField(source="reported_by.username", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    completed_by_username = serializers.CharField(source="completed_by.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    comments = MaintenanceRequestCommentSerializer(many=True, read_only=True)
    
    # 👇 AÑADE ESTA LÍNEA para mostrar los archivos adjuntos
    attachments = MaintenanceRequestAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = '__all__' # fields = '__all__' ya incluye el nuevo campo 'attachments'
        read_only_fields = ['reported_by']
      