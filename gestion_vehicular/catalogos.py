"""Catálogos de referencia con terminología de México.

Son listas *sugeridas*: el sistema acepta cualquier texto en los campos "tipo",
pero estos catálogos alimentan la ayuda de la línea de comandos, los datos de
ejemplo y la validación suave (avisos, no errores). Editá estas listas para
adaptarlas a tu operación.
"""

# Tipos de vehículo de la flota (carrocería).
TIPOS_VEHICULO = ["sedan", "hatchback", "pickup"]

# Fuente de energía / tren motriz. Se separa del tipo de carrocería porque un
# mismo modelo puede ser de combustión, híbrido o eléctrico, y el mantenimiento
# cambia bastante. Hoy los eléctricos están solo en el Corporativo (central).
TIPOS_ENERGIA = ["combustion", "hibrido", "electrico"]

# Derechos, permisos y trámites que se pagan/renuevan por VEHÍCULO en México.
TIPOS_OBLIGACION_VEHICULO = {
    "tenencia": "Impuesto sobre tenencia o uso de vehículos (anual)",
    "refrendo": "Refrendo / derechos de control vehicular (anual)",
    "verificacion": "Verificación vehicular de emisiones (semestral)",
    "tarjeta_circulacion": "Tarjeta de circulación",
    "placas": "Alta / reposición de placas",
    "seguro": "Póliza de seguro del vehículo",
    "otro": "Otro derecho o permiso",
}

# Obligaciones asociadas a un CONDUCTOR.
TIPOS_OBLIGACION_CONDUCTOR = {
    "licencia": "Licencia de conducir",
}

# Tipos de mantenimiento de vehículos de combustión / híbridos
# (especialmente relevantes para pickups).
TIPOS_MANTENIMIENTO_COMBUSTION = {
    "afinacion": "Afinación mayor / servicio de agencia",
    "cambio_aceite": "Cambio de aceite y filtro",
    "llantas": "Cambio o rotación de llantas",
    "frenos": "Balatas / discos / sistema de frenos",
    "alineacion_balanceo": "Alineación y balanceo",
    "bateria": "Batería de arranque (12V)",
    "suspension": "Suspensión / amortiguadores",
    "clutch_transmision": "Clutch / transmisión",
    "revision_general": "Revisión / diagnóstico general",
    "otro": "Otro mantenimiento",
}

# Tipos de mantenimiento propios de vehículos ELÉCTRICOS (e híbridos enchufables).
# Preparan el terreno para la flota del Corporativo.
TIPOS_MANTENIMIENTO_ELECTRICO = {
    "bateria_hv": "Batería de alto voltaje (revisión / diagnóstico / SOH)",
    "refrigerante_bateria": "Refrigerante del paquete de baterías",
    "software": "Actualización de software / firmware",
    "frenos_regenerativos": "Frenos regenerativos / balatas (menor desgaste)",
    "cargador_puerto": "Cargador, puerto y cable de carga",
    "motor_inversor": "Motor eléctrico / inversor / reductor",
    "filtro_habitaculo": "Filtro de habitáculo (HVAC)",
    "revision_general": "Revisión / diagnóstico general",
    "otro": "Otro mantenimiento",
}

# Vista combinada (todos los tipos de mantenimiento conocidos).
TIPOS_MANTENIMIENTO = {**TIPOS_MANTENIMIENTO_COMBUSTION, **TIPOS_MANTENIMIENTO_ELECTRICO}


def tipos_mantenimiento_para(energia: str) -> dict:
    """Devuelve los tipos de mantenimiento sugeridos según la energía del vehículo."""
    if energia == "electrico":
        return TIPOS_MANTENIMIENTO_ELECTRICO
    if energia == "hibrido":
        return TIPOS_MANTENIMIENTO  # a un híbrido le aplican ambos mundos
    return TIPOS_MANTENIMIENTO_COMBUSTION


def descripcion_tipo_obligacion(tipo: str) -> str:
    """Devuelve la descripción legible de un tipo de obligación, o el tipo tal cual."""
    return (
        TIPOS_OBLIGACION_VEHICULO.get(tipo)
        or TIPOS_OBLIGACION_CONDUCTOR.get(tipo)
        or tipo
    )
