# --- imports (limpios) ---
import json
from django.db.models import Sum, Count
from django.contrib.auth import authenticate, get_user_model
from rest_framework import viewsets, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserSerializer, ProfileSerializer, MeSerializer,
    UserWithProfileSerializer, AdminUserWriteSerializer, UnitSerializer,
    ExpenseTypeSerializer, FeeSerializer, PaymentSerializer, NoticeSerializer, 
    CommonAreaSerializer, ReservationSerializer, MaintenanceRequestSerializer, ActivityLogSerializer,
    MaintenanceRequestCommentSerializer
)
from .models import (
    Profile, Unit, ExpenseType, Fee, Payment, Notice,
    CommonArea, Reservation, MaintenanceRequest, ActivityLog, MaintenanceRequestComment
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
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                return Response({"detail": "JSON inválido"}, status=400)

        identifier = (data.get("email") or data.get("username") or "").strip()
        password   = (data.get("password") or "").strip()
        if not identifier or not password:
            return Response({"detail": "Faltan datos"}, status=400)

        if "@" in identifier:
            user_obj = User.objects.filter(email__iexact=identifier).first()
            if not user_obj:
                return Response({"detail": "Credenciales inválidas"}, status=401)
            username = user_obj.get_username()
        else:
            username = identifier

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Credenciales inválidas"}, status=401)
        ActivityLog.objects.create(user=user, action="USER_LOGIN_SUCCESS")
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {"id": user.id, "username": user.get_username(), "email": user.email},
        }, status=200)

class MeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        u = request.user
        prof = getattr(u, "profile", None)
        payload = {
            **UserSerializer(u).data,
            "profile": ProfileSerializer(prof).data if prof else None,
        }
        return Response(MeSerializer(payload).data)

    @action(detail=False, methods=["patch"])
    def update_profile(self, request):
        prof, _ = Profile.objects.get_or_create(user=request.user)
        ser = ProfileSerializer(prof, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    @action(detail=False, methods=["get"])
    def fees(self, request):
        qs = Fee.objects.select_related("unit", "expense_type") \
                        .filter(unit__owner=request.user) \
                        .order_by("-issued_at")
        return Response(FeeSerializer(qs, many=True).data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["id", "username", "email", "date_joined"]
    ordering = ["id"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AdminUserWriteSerializer
        if self.action in ("list", "retrieve"):
            return UserWithProfileSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action="USER_CREATED",
            details=f"Se creó el usuario con ID: {user.id}"
        )

    def perform_destroy(self, instance):
        username = instance.username
        user_id = instance.id
        instance.delete()
        ActivityLog.objects.create(
            user=self.request.user,
            action="USER_DELETED",
            details=f"Se eliminó el usuario: {username} ({user_id})"
        )

    def perform_update(self, serializer):
        user = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action="USER_UPDATED",
            details=f"Se actualizó el usuario con ID: {user.id}"
        )

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


class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.select_related("created_by").all().order_by("-published_at")
    serializer_class = NoticeSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class FinanceReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Fee.objects.select_related("unit", "unit__owner", "expense_type")

        p_from = request.query_params.get("from")
        p_to   = request.query_params.get("to")
        owner  = request.query_params.get("owner")

        if p_from: qs = qs.filter(period__gte=p_from)
        if p_to:   qs = qs.filter(period__lte=p_to)

        if not is_admin(request.user):
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
    # --- ACCIÓN NUEVA PARA ADMINS ---
    @action(detail=True, methods=['patch'], permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        instance = self.get_object()
        new_status = request.data.get('status')
        old_status = instance.status

        # Valida que el estado sea uno de los permitidos
        valid_statuses = [choice[0] for choice in MaintenanceRequest.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'detail': 'Estado no válido.'}, status=400)

        instance.status = new_status
        instance.save(update_fields=['status'])
        
        # 👈 Nuevo: Registrar la actualización del estado
        ActivityLog.objects.create(
            user=request.user,
            action="MAINTENANCE_REQUEST_STATUS_UPDATED",
            details=f"Se actualizó el estado de la solicitud '{instance.title}' de '{old_status}' a '{new_status}'"
        )   
        return Response(self.get_serializer(instance).data)  
# Al final de core/views.py

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
        # Permite a los usuarios ver comentarios de sus propias solicitudes o a los admins ver todo
        user = self.request.user
        if not (user.is_staff or getattr(user.profile, 'role', 'RESIDENT') == 'ADMIN'):
            return self.queryset.filter(request__reported_by=user)
        return self.queryset
    
    def perform_create(self, serializer):
        # Asegura que el usuario solo pueda comentar en solicitudes existentes
        request_id = self.request.data.get('request')
        try:
            maintenance_request = MaintenanceRequest.objects.get(id=request_id)
        except MaintenanceRequest.DoesNotExist:
            raise serializers.ValidationError("Solicitud de mantenimiento no encontrada.")
            
        serializer.save(user=self.request.user, request=maintenance_request)