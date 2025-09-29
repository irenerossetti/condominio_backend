from django.db import models

class Unidad(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    piso = models.CharField(max_length=50, blank=True, null=True)
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    alicuota = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "unidades"
        ordering = ["codigo"]
    def __str__(self): return self.codigo

class Residente(models.Model):
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, related_name="residentes")
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    es_propietario = models.BooleanField(default=True)
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "residentes"
        indexes = [models.Index(fields=["unidad"])]

class Cuota(models.Model):
    nombre = models.CharField(max_length=200)
    monto_base = models.DecimalField(max_digits=12, decimal_places=2)
    aplica_alicuota = models.BooleanField(default=True)
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "cuotas"

class Movimiento(models.Model):
    TIPO = (("cargo", "cargo"), ("pago", "pago"))
    unidad = models.ForeignKey(Unidad, on_delete=models.CASCADE, related_name="movimientos")
    periodo = models.DateField()
    tipo = models.CharField(max_length=5, choices=TIPO)
    concepto = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    medio_pago = models.CharField(max_length=100, blank=True, null=True)
    referencia = models.CharField(max_length=100, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "movimientos"
        indexes = [models.Index(fields=["unidad", "periodo"])]
        constraints = [
            models.UniqueConstraint(
                fields=["unidad", "periodo", "concepto"],
                condition=models.Q(tipo="cargo"),
                name="uniq_cargo_mes",
            )
        ]
