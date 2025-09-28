# config/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core import views as v
from django.conf import settings # 👈 Importa settings
from django.conf.urls.static import static # 👈 Importa static

router = DefaultRouter()
router.register(r"me", v.MeViewSet, basename="me")
router.register(r"users", v.UserViewSet)
router.register(r"units", v.UnitViewSet)   
router.register(r"expense-types", v.ExpenseTypeViewSet)
router.register(r"fees", v.FeeViewSet)
router.register(r"notices", v.NoticeViewSet, basename="notice")
router.register(r"notice-categories", v.NoticeCategoryViewSet, basename="noticecategory")
router.register(r"common-areas", v.CommonAreaViewSet)
router.register(r"reservations", v.ReservationViewSet)
router.register(r"maintenance-requests", v.MaintenanceRequestViewSet)
# En config/urls.py, dentro de los registros del router
router.register(r"activity-logs", v.ActivityLogViewSet, basename="activitylog")
router.register(r"maintenance-request-comments", v.MaintenanceRequestCommentViewSet)
router.register(r"vehicles", v.VehicleViewSet, basename="vehicle")
router.register(r"pets", v.PetViewSet, basename="pet")
router.register(r"family-members", v.FamilyMemberViewSet, basename="familymember")
router.register(r"notifications", v.NotificationViewSet, basename="notification")
router.register(r"maintenance-attachments", v.MaintenanceRequestAttachmentViewSet, basename="maintenanceattachment")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Login propio
    path("api/auth/login/", v.LoginView.as_view()),
    path("api/auth/logout/", v.LogoutView.as_view(), name='auth-logout'), # 👈 Nueva línea
    path("api/log/page-access/", v.PageAccessLogView.as_view(), name='page-access-log'), # 👈 Nueva ruta
    # Opcional: endpoints de SimpleJWT (útiles para pruebas)
    path("api/auth/token/", TokenObtainPairView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/reports/finance/", v.FinanceReportView.as_view()),  # <-- NUEVO
    # Rutas de DRF y apps
    path("api/reports/dashboard-stats/", v.DashboardStatsView.as_view()),

    path("api/", include(router.urls)),
    path("api/", include("core.urls")),
  #  path("api/", include("todos.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)