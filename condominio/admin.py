from django.contrib import admin
from django.db.models import Sum, Case, When, F, Value, DecimalField
from .models import Unidad, Residente, Cuota, Movimiento

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ("codigo", "piso", "alicuota", "activo", "saldo_actual")
    search_fields = ("codigo", "piso")
    list_filter = ("activo",)

    def saldo_actual(self, obj):
        agg = obj.movimientos.aggregate(
            cargos=Sum(Case(When(tipo="cargo", then=F("monto")), default=Value(0), output_field=DecimalField())),
            pagos =Sum(Case(When(tipo="pago",  then=F("monto")), default=Value(0), output_field=DecimalField())),
        )
        return (agg["cargos"] or 0) - (agg["pagos"] or 0)
    saldo_actual.short_description = "Saldo"

@admin.register(Residente)
class ResidenteAdmin(admin.ModelAdmin):
    list_display = ("nombre","unidad","es_propietario","fecha_desde","fecha_hasta")
    search_fields = ("nombre","email","telefono")
    list_filter = ("es_propietario",)

@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ("nombre","monto_base","aplica_alicuota","vigente_desde","vigente_hasta")
    search_fields = ("nombre",)
    list_filter = ("aplica_alicuota",)

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("unidad","periodo","tipo","concepto","monto","medio_pago","referencia","fecha")
    search_fields = ("unidad__codigo","concepto","referencia")
    list_filter = ("tipo","periodo","medio_pago")
