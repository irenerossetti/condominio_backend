# config/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core import views as v

router = DefaultRouter()
router.register(r"me", v.MeViewSet, basename="me")
router.register(r"users", v.UserViewSet)
router.register(r"units", v.UnitViewSet)   
router.register(r"expense-types", v.ExpenseTypeViewSet)
router.register(r"fees", v.FeeViewSet)
router.register(r"notices", v.NoticeViewSet)


urlpatterns = [
    path("admin/", admin.site.urls),

    # Login propio
    path("api/auth/login/", v.LoginView.as_view()),

    # Opcional: endpoints de SimpleJWT (útiles para pruebas)
    path("api/auth/token/", TokenObtainPairView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/reports/finance/", v.FinanceReportView.as_view()),  # <-- NUEVO
    # Rutas de DRF y apps
    path("api/", include(router.urls)),
  #  path("api/", include("todos.urls")),
]
