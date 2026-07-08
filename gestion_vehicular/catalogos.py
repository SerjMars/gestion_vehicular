"""Catálogos de referencia con terminología de México.

Son listas *sugeridas*: el sistema acepta cualquier texto en los campos "tipo",
pero estos catálogos alimentan la ayuda de la línea de comandos, los datos de
ejemplo y la validación suave (avisos, no errores). Editá estas listas para
adaptarlas a tu operación.
"""

# Tipos de vehículo de la flota.
TIPOS_VEHICULO = ["sedan", "hatchback", "pickup"]

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

# Tipos de mantenimiento más comunes (especialmente relevantes para pickups).
TIPOS_MANTENIMIENTO = {
    "afinacion": "Afinación mayor / servicio de agencia",
    "cambio_aceite": "Cambio de aceite y filtro",
    "llantas": "Cambio o rotación de llantas",
    "frenos": "Balatas / discos / sistema de frenos",
    "alineacion_balanceo": "Alineación y balanceo",
    "bateria": "Batería",
    "suspension": "Suspensión / amortiguadores",
    "clutch_transmision": "Clutch / transmisión",
    "revision_general": "Revisión / diagnóstico general",
    "otro": "Otro mantenimiento",
}


def descripcion_tipo_obligacion(tipo: str) -> str:
    """Devuelve la descripción legible de un tipo de obligación, o el tipo tal cual."""
    return (
        TIPOS_OBLIGACION_VEHICULO.get(tipo)
        or TIPOS_OBLIGACION_CONDUCTOR.get(tipo)
        or tipo
    )
