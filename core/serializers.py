from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Profile, Unit, ExpenseType, Fee, Payment, Notice,
    CommonArea, Reservation, MaintenanceRequest, ActivityLog, MaintenanceRequestComment
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "is_active", "is_staff", "date_joined",
        ]
        read_only_fields = ["id", "is_staff", "date_joined"]

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
    profile = ProfileSerializer(read_only=True, allow_null=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["profile"]

class AdminUserWriteSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role = serializers.ChoiceField(write_only=True, choices=Profile.ROLE_CHOICES, required=False)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=6)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "password",
            "first_name", "last_name", "is_active",
            "full_name", "phone", "role",
        ]
        read_only_fields = ["id"]

    def create(self, validated):
        profile_data = {k: validated.pop(k, None) for k in ("full_name", "phone", "role")}
        password = validated.pop("password", None)

        user = User(**validated)
        user.set_password(password or User.objects.make_random_password())
        user.save()

        defaults = {k: v for k, v in profile_data.items() if v is not None}
        if defaults:
            Profile.objects.update_or_create(user=user, defaults=defaults)
        return user

    def update(self, instance, validated):
        profile_data = {k: validated.pop(k, None) for k in ("full_name", "phone", "role")}
        password = validated.pop("password", None)

        for k, v in validated.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()

        if any(v is not None for v in profile_data.values()):
            prof, _ = Profile.objects.get_or_create(user=instance)
            for k, v in profile_data.items():
                if v is not None:
                    setattr(prof, k, v)
            prof.save()
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

class NoticeSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Notice
        fields = ["id", "title", "body", "published_at", "created_by", "created_by_username"]
        read_only_fields = ["id", "published_at", "created_by", "created_by_username"]

class CommonAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonArea
        fields = ["id", "name", "description", "capacity", "is_active"]

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

class MaintenanceRequestSerializer(serializers.ModelSerializer):
    unit_code = serializers.CharField(source="unit.code", read_only=True)
    reported_by_username = serializers.CharField(source="reported_by.username", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    completed_by_username = serializers.CharField(source="completed_by.username", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    comments = MaintenanceRequestCommentSerializer(many=True, read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = '__all__'
        read_only_fields = ['reported_by']