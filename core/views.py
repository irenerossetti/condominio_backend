# --- imports (limpios) ---
import json
from django.db.models import Sum, Count, Q
from django.db.models import ProtectedError # 👈 AÑADE ESTE IMPORT ARRIBA
from django.db import IntegrityError # 👈 Añade este import al principio
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone 
from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status # 👈 AÑADE ESTE IMPORT ARRIBA
from rest_framework.parsers import MultiPartParser, FormParser # 👈 ASEGÚRATE DE QUE ESTÉ
from rest_framework.exceptions import PermissionDenied # 👈 Y ESTE TAMBIÉN

from .serializers import (
    ActivityLogSerializer, AdminUserWriteSerializer, CommonAreaSerializer,
    ExpenseTypeSerializer, FamilyMemberSerializer, FeeSerializer,
    MaintenanceRequestCommentSerializer, MaintenanceRequestSerializer,
    MeSerializer, NoticeCategorySerializer, NoticeSerializer,
    NotificationSerializer, MaintenanceRequestAttachmentSerializer,
    PaymentSerializer, PetSerializer, ProfileSerializer, ReservationSerializer,
    UnitSerializer, UserSerializer, UserWithProfileSerializer, VehicleSerializer
)
from .models import (
    ActivityLog, CommonArea, ExpenseType, FamilyMember, Fee, MaintenanceRequest,
    MaintenanceRequestComment, Notice, NoticeCategory, Notification,
    Payment, Pet, Profile, Reservation, Unit, Vehicle, MaintenanceRequestAttachment 
)
from .permissions import IsAdmin, IsOwnerOrAdmin
from rest_framework import serializers # Importar serializers para la excepción


User = get_user_model()

# --- Login ---
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        data = request.data
        identifier = (data.get("email") or data.get("username") or "").strip()
        password = (data.get("password") or "").strip()
        if not identifier or not password:
            return Response({"detail": "Faltan credenciales"}, status=400)

        user_lookup = {"email__iexact": identifier} if "@" in identifier else {"username__iexact": identifier}
        user_obj = User.objects.filter(**user_lookup).first()
        if not user_obj:
            return Response({"detail": "Credenciales inválidas"}, status=401)

        user = authenticate(request, username=user_obj.username, password=password)
        if not user:
            return Response({"detail": "Credenciales inválidas"}, status=401)
        
        ActivityLog.objects.create(user=user, action="USER_LOGIN_SUCCESS")
        refresh = RefreshToken.for_user(user)
        return Response({ "access": str(refresh.access_token), "refresh": str(refresh) })

class MeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        serializer = UserWithProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"])
    def update_profile(self, request):
        prof, _ = Profile.objects.get_or_create(user=request.user)
        ser = ProfileSerializer(prof, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related('profile', 'vehicles', 'pets', 'family_members').all().order_by("id")
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "email"]
    ordering = ["id"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AdminUserWriteSerializer
        return UserWithProfileSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {"detail": "No se puede eliminar. El usuario es propietario de una o más Unidades."},
                status=status.HTTP_400_BAD_REQUEST
            )  
    # 👇 AÑADE ESTA NUEVA FUNCIÓN DENTRO DE UserViewSet
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def staff_members(self, request):
        """
        Devuelve una lista de todos los usuarios con el rol de STAFF.
        Esto crea automáticamente el endpoint GET /api/users/staff_members/
        """
        staff_users = User.objects.filter(profile__role='STAFF').order_by('username')
        serializer = self.get_serializer(staff_users, many=True)
        return Response(serializer.data)      

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.select_related("owner").all().order_by("id")
    serializer_class = UnitSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["code", "tower", "number", "owner__username", "owner__email"]
    ordering_fields = ["id", "code", "tower", "number"]
    ordering = ["id"]

    def perform_update(self, serializer):
        unit = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action="UNIT_UPDATED",
            details=f"Se actualizó la unidad: {unit.code}"
        )

    def perform_destroy(self, instance):
        code = instance.code
        instance.delete()
        ActivityLog.objects.create(
            user=self.request.user,
            action="UNIT_DELETED",
            details=f"Se eliminó la unidad: {code}"
        )

class ExpenseTypeViewSet(viewsets.ModelViewSet):
    queryset = ExpenseType.objects.all().order_by("id")
    serializer_class = ExpenseTypeSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["id", "name", "amount_default"]

    def perform_create(self, serializer):
        expense_type = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action="EXPENSE_TYPE_CREATED",
            details=f"Se creó el tipo de expensa: '{expense_type.name}'"
        )
    
    def perform_update(self, serializer):
        expense_type = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action="EXPENSE_TYPE_UPDATED",
            details=f"Se actualizó el tipo de expensa: '{expense_type.name}'"
        )

    def perform_destroy(self, instance):
        name = instance.name
        instance.delete()
        ActivityLog.objects.create(
            user=self.request.user,
            action="EXPENSE_TYPE_DELETED",
            details=f"Se eliminó el tipo de expensa: '{name}'"
        )

class FeeViewSet(viewsets.ModelViewSet):
    queryset = Fee.objects.select_related("unit", "expense_type", "unit__owner").all()
    serializer_class = FeeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["period", "unit__code", "expense_type__name", "unit__owner__username"]
    ordering_fields = ["issued_at", "period", "amount"]
    ordering = ["-issued_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "1" and self.request.user.is_authenticated:
            qs = qs.filter(unit__owner=self.request.user)
        period = self.request.query_params.get("period")
        if period:
            qs = qs.filter(period=period)
        return qs

    @action(detail=False, methods=["post"], permission_classes=[IsAdmin])
    def issue(self, request):
        period = (request.data.get("period") or "").strip()
        if not period:
            return Response({"detail": "period requerido (YYYY-MM)"}, status=400)

        et_id = request.data.get("expense_type")
        amount_override = request.data.get("amount")

        units = Unit.objects.all()
        ets = ExpenseType.objects.filter(id=et_id) if et_id else ExpenseType.objects.filter(active=True)

        count = 0
        for u in units:
            for et in ets:
                defaults = {"amount": amount_override or et.amount_default}
                fee, created = Fee.objects.get_or_create(
                    unit=u, expense_type=et, period=period, defaults=defaults
                )
                if not created and amount_override:
                    fee.amount = amount_override
                    fee.save(update_fields=["amount"])
                count += 1
        ActivityLog.objects.create(
            user=request.user,
            action="FEES_ISSUED",
            details=f"Se emitieron {count} cuotas para el periodo {period}"
        )        
        return Response({"ok": True, "period": period, "count": count})

    @action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def pay(self, request, pk=None):
        fee = self.get_object()
        try:
            amount = float(request.data.get("amount"))
        except Exception:
            return Response({"detail": "amount inválido"}, status=400)
        method = request.data.get("method", "cash")
        note = request.data.get("note", "")

        p = Payment.objects.create(fee=fee, amount=amount, method=method, note=note)

        total = fee.payments.aggregate(total=Sum("amount"))["total"] or 0
        if float(total) >= float(fee.amount):
            fee.status = "PAID"
            fee.save(update_fields=["status"])
        
        ActivityLog.objects.create(
            user=request.user,
            action="FEE_PAID",
            details=f"Se registró un pago de {amount} para la cuota de {fee.unit.code} ({fee.period})"
        )
        return Response(PaymentSerializer(p).data, status=201)

# 👇 AÑADE ESTE NUEVO VIEWSET (puede ser antes de NoticeViewSet)
class NoticeCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para que los admins gestionen las categorías de los avisos.
    Los residentes solo pueden leerlas.
    """
    queryset = NoticeCategory.objects.all()
    serializer_class = NoticeCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        # Solo los admins pueden crear, editar o borrar categorías
        if self.action not in ('list', 'retrieve'):
            return [IsAdmin()]
        return super().get_permissions()
    
class NoticeViewSet(viewsets.ModelViewSet):
    serializer_class = NoticeSerializer

    def get_queryset(self):
        """
        Esta función ahora solo devuelve los avisos cuya fecha de publicación
        es menor o igual a la fecha y hora actual.
        """
        return Notice.objects.filter(
            publish_date__lte=timezone.now()
        ).select_related("created_by").order_by("-publish_date")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class FinanceReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # La forma correcta de verificar el permiso
        is_admin_check = IsAdmin()
        user_is_admin = is_admin_check.has_permission(request, self)

        qs = Fee.objects.select_related("unit", "unit__owner", "expense_type")

        p_from = request.query_params.get("from")
        p_to   = request.query_params.get("to")
        owner  = request.query_params.get("owner")

        if p_from: qs = qs.filter(period__gte=p_from)
        if p_to:   qs = qs.filter(period__lte=p_to)

        # Lógica corregida
        if not user_is_admin:
            qs = qs.filter(unit__owner=request.user)
        elif owner:
            qs = qs.filter(unit__owner_id=int(owner)) if owner.isdigit() \
                 else qs.filter(unit__owner__username=owner)

        overall_q = qs.aggregate(issued=Sum("amount"), paid=Sum("payments__amount"))
        issued = overall_q["issued"] or 0
        paid   = overall_q["paid"] or 0
        overall = {"issued": float(issued), "paid": float(paid), "outstanding": float(issued - paid)}

        by_period = list(
            qs.values("period").annotate(
                issued=Sum("amount"), paid=Sum("payments__amount"), count=Count("id")
            ).order_by("period")
        )
        for r in by_period:
            r["issued"] = float(r["issued"] or 0)
            r["paid"] = float(r["paid"] or 0)
            r["outstanding"] = float(r["issued"] - r["paid"])

        by_type = list(
            qs.values("expense_type__name").annotate(
                issued=Sum("amount"), paid=Sum("payments__amount"), count=Count("id")
            ).order_by("expense_type__name")
        )
        for r in by_type:
            r["type"] = r.pop("expense_type__name")
            r["issued"] = float(r["issued"] or 0)
            r["paid"] = float(r["paid"] or 0)
            r["outstanding"] = float(r["issued"] - r["paid"])

        return Response({
            "filters": {"from": p_from, "to": p_to, "owner": owner},
            "overall": overall,
            "by_period": by_period,
            "by_type": by_type,
        })

class CommonAreaViewSet(viewsets.ModelViewSet):
    queryset = CommonArea.objects.filter(is_active=True).order_by("name")
    serializer_class = CommonAreaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Todos pueden ver, solo admin modifica

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        common_area = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action="COMMON_AREA_CREATED",
            details=f"Se creó el área común: {common_area.name}"
        )

    def perform_update(self, serializer):
        common_area = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action="COMMON_AREA_UPDATED",
            details=f"Se actualizó el área común: {common_area.name}"
        )

    def perform_destroy(self, instance):
        name = instance.name
        instance.delete()
        ActivityLog.objects.create(
            user=self.request.user,
            action="COMMON_AREA_DELETED",
            details=f"Se eliminó el área común: {name}"
        )

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related("area", "user").all()
    serializer_class = ReservationSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        # Un admin ve todo, un residente solo lo suyo
        if self.request.user.profile.role == "ADMIN":
            return super().get_queryset().order_by("-start_time")
        return super().get_queryset().filter(user=self.request.user).order_by("-start_time")

    def perform_create(self, serializer):
        reservation = serializer.save(user=self.request.user)
        ActivityLog.objects.create(
            user=self.request.user,
            action="RESERVATION_CREATED",
            details=f"Se creó una reserva para '{reservation.area.name}' ({reservation.start_time.strftime('%Y-%m-%d %H:%M')})"
        )

    def perform_update(self, serializer):
        reservation = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action="RESERVATION_UPDATED",
            details=f"Se actualizó la reserva para '{reservation.area.name}'"
        )

    def perform_destroy(self, instance):
        area_name = instance.area.name
        start_time = instance.start_time
        instance.delete()
        ActivityLog.objects.create(
            user=self.request.user,
            action="RESERVATION_DELETED",
            details=f"Se eliminó la reserva de '{area_name}' ({start_time.strftime('%Y-%m-%d %H:%M')})"
        )
# En core/views.py
class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRequest.objects.all().order_by('-created_at')
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Si el usuario NO es admin, solo ve sus propias solicitudes
        if not (user.is_staff or getattr(user.profile, 'role', 'RESIDENT') == 'ADMIN'):
            return self.queryset.filter(reported_by=user)
        # Si es admin, ve todo
        return self.queryset

    def perform_create(self, serializer):
        maintenance_request = serializer.save(reported_by=self.request.user)
        ActivityLog.objects.create(
            user=self.request.user,
            action="MAINTENANCE_REQUEST_CREATED",
            details=f"Se creó la solicitud de mantenimiento: '{maintenance_request.title}'"
        )
        
        # --- LÓGICA DE NOTIFICACIÓN CORREGIDA ---
        admins = User.objects.filter(profile__role='ADMIN')
        for admin in admins:
            if admin != self.request.user: # No notificarse a uno mismo
                Notification.objects.create(
                    user=admin,
                    message=f"Nueva solicitud de {self.request.user.username}: '{maintenance_request.title}'",
                    link="/maintenance"
                )   

    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        instance = self.get_object()
        new_status = request.data.get('status')
        old_status_display = instance.get_status_display()

        valid_statuses = [choice[0] for choice in MaintenanceRequest.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'detail': 'Estado no válido.'}, status=400)

        instance.status = new_status
        fields_to_update = ['status']
        if new_status == 'COMPLETED':
            instance.completed_by = request.user
            instance.completed_at = timezone.now()
            fields_to_update.extend(['completed_by', 'completed_at'])
        instance.save(update_fields=fields_to_update)
        
        # Notificar al dueño del ticket sobre el cambio de estado
        if instance.reported_by != request.user:
            Notification.objects.create(
                user=instance.reported_by,
                message=f"El estado de tu solicitud '{instance.title}' cambió a: {instance.get_status_display()}",
                link="/maintenance"
            )
        
        ActivityLog.objects.create(
            user=request.user,
            action="MAINTENANCE_REQUEST_STATUS_UPDATED",
            details=f"Estado de '{instance.title}' cambiado de '{old_status_display}' a '{instance.get_status_display()}'"
        )
        return Response(self.get_serializer(instance).data)
    
class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Viewset para que los administradores vean el registro de actividad.
    Es de solo lectura.
    """
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'action', 'details']
    ordering_fields = ['timestamp']     

    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def create_custom(self, request):
        action = request.data.get('action')
        details = request.data.get('details')
        if not action:
            return Response({"detail": "El campo 'action' es requerido."}, status=400)
        
        log = ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
        )
        return Response(self.get_serializer(log).data, status=201)
    
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        ActivityLog.objects.create(user=user, action="USER_LOGOUT")
        return Response({"detail": "Sesión cerrada correctamente."})

class PageAccessLogView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        page_name = request.data.get('page_name')
        if not page_name:
            return Response({"detail": "El nombre de la página es requerido."}, status=400)
            
        ActivityLog.objects.create(
            user=request.user,
            action="PAGE_ACCESS",
            details=f"Accedió a la página: {page_name}"
        )
        return Response({"status": "Registro de acceso a página exitoso."}, status=201)
    
class MaintenanceRequestCommentViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRequestComment.objects.all()
    serializer_class = MaintenanceRequestCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not (user.is_staff or getattr(user.profile, 'role', 'RESIDENT') == 'ADMIN'):
            return self.queryset.filter(request__reported_by=user)
        return self.queryset
    
    def perform_create(self, serializer):
        request_id = self.request.data.get('request')
        try:
            maintenance_request = MaintenanceRequest.objects.get(id=request_id)
        except MaintenanceRequest.DoesNotExist:
            raise serializers.ValidationError("Solicitud de mantenimiento no encontrada.")
        comment = serializer.save(user=self.request.user, request=maintenance_request)
        request_owner = comment.request.reported_by
        assigned_worker = comment.request.assigned_to
        commenter = self.request.user
        if commenter == request_owner:
            if assigned_worker and assigned_worker != commenter:
                Notification.objects.create(
                    user=assigned_worker,
                    message=f"{commenter.username} comentó en una tarea asignada.",
                    link="/maintenance"
                )
            else:
                admins = User.objects.filter(profile__role='ADMIN')
                for admin in admins:
                    if admin != commenter:
                        Notification.objects.create(
                            user=admin,
                            message=f"{commenter.username} comentó en '{comment.request.title}'.",
                            link="/maintenance"
                        )
        else:
            if request_owner != commenter:
                Notification.objects.create(
                    user=request_owner,
                    message=f"{commenter.username} comentó en tu solicitud: '{comment.request.title}'",
                    link="/maintenance"
                )


class DashboardStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        user_count = User.objects.count()
        unit_count = Unit.objects.count()

        pending_fees = Fee.objects.filter(status__in=["ISSUED", "OVERDUE"]).aggregate(total=Sum('amount'))['total'] or 0

        open_requests = MaintenanceRequest.objects.filter(status__in=["PENDING", "IN_PROGRESS"]).count()

        stats = {
            "total_users": user_count,
            "active_units": unit_count,
            "pending_fees_total": float(pending_fees),
            "open_maintenance_requests": open_requests,
        }
        return Response(stats)

## --- NUEVOS VIEWSETS ---
class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAdmin]
    def create(self, request, *args, **kwargs):
        try: return super().create(request, *args, **kwargs)
        except IntegrityError: return Response({"detail": "Ya existe un vehículo con esta placa."}, status=status.HTTP_400_BAD_REQUEST)

class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
    permission_classes = [IsAdmin]

class FamilyMemberViewSet(viewsets.ModelViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer
    permission_classes = [IsAdmin]

# 👇 Añade este nuevo ViewSet
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

# --- 👇 AÑADE ESTA CLASE COMPLETA AL FINAL ---
class MaintenanceRequestAttachmentViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRequestAttachment.objects.all()
    serializer_class = MaintenanceRequestAttachmentSerializer
    # Le decimos a la vista que puede manejar la subida de archivos
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated] # Solo usuarios logueados pueden subir

    def perform_create(self, serializer):
        # Asegurarnos que el usuario que sube el archivo sea el que reportó
        # la solicitud o un administrador.
        request_id = self.request.data.get('request')
        maintenance_request = MaintenanceRequest.objects.get(id=request_id)
        user = self.request.user

        if maintenance_request.reported_by != user and not (user.is_staff or getattr(user.profile, 'role', '') == 'ADMIN'):
            raise PermissionDenied("No tienes permiso para adjuntar archivos a esta solicitud.")
        
        serializer.save()


