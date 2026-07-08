"""Ayudas de presentación en consola (tablas y dinero).

Sin dependencias externas: si más adelante querés colores o exportar a Excel,
este es el único módulo que habría que tocar.
"""

from __future__ import annotations


def money(valor) -> str:
    """Formatea un monto como pesos mexicanos. Devuelve '-' si es None."""
    if valor is None:
        return "-"
    return f"${valor:,.2f}"


def tabla(encabezados: list[str], filas: list[list]) -> str:
    """Arma una tabla de texto alineada por columnas."""
    if not filas:
        return "  (sin registros)"
    columnas = [str(h) for h in encabezados]
    celdas = [[("" if c is None else str(c)) for c in fila] for fila in filas]
    anchos = [len(h) for h in columnas]
    for fila in celdas:
        for i, c in enumerate(fila):
            anchos[i] = max(anchos[i], len(c))

    def linea(valores):
        return "  ".join(v.ljust(anchos[i]) for i, v in enumerate(valores))

    separador = "  ".join("-" * a for a in anchos)
    salida = [linea(columnas), separador]
    salida.extend(linea(fila) for fila in celdas)
    return "\n".join(salida)


def etiqueta_dias(d: int) -> str:
    """Traduce 'días restantes' a una etiqueta legible."""
    if d < 0:
        return f"VENCIDO hace {-d} d"
    if d == 0:
        return "vence HOY"
    return f"en {d} d"


def render_alertas(a: dict) -> str:
    """Arma el tablero de alertas como texto (reutilizable en consola y correo)."""
    lineas = []
    lineas.append("=" * 72)
    lineas.append(f" TABLERO DE ALERTAS  —  horizonte {a['dias']} días / {a['umbral_km']:,} km")
    lineas.append("=" * 72)

    lineas.append("\n▸ DERECHOS, PERMISOS Y LICENCIAS (pendientes de pago/renovación)")
    lineas.append(tabla(
        ["ID", "Tipo", "Aplica a", "Sucursal", "Vence", "Estado", "Monto"],
        [[o["id"], o["tipo"], o["placas"] or o["conductor"] or "-", o["sucursal"],
          o["fecha_vencimiento"], etiqueta_dias(o["dias_restantes"]), money(o["monto"])]
         for o in a["obligaciones"]],
    ))

    lineas.append("\n▸ MANTENIMIENTOS PRÓXIMOS (por fecha)")
    lineas.append(tabla(
        ["Veh", "Placas", "Vehículo", "Energía", "Sucursal", "Tipo", "Próx.fecha", "Estado"],
        [[m["vehiculo_id"], m["placas"], f"{m['marca']} {m['modelo']}", m["energia"],
          m["sucursal"], m["tipo"], m["proximo_fecha"], etiqueta_dias(m["dias_restantes"])]
         for m in a["mant_fecha"]],
    ))

    lineas.append("\n▸ MANTENIMIENTOS PRÓXIMOS (por kilometraje)")
    lineas.append(tabla(
        ["Veh", "Placas", "Vehículo", "Energía", "Sucursal", "Tipo", "Km actual", "Próx.km", "Faltan"],
        [[m["vehiculo_id"], m["placas"], f"{m['marca']} {m['modelo']}", m["energia"],
          m["sucursal"], m["tipo"], f"{m['km_actual']:,}", f"{m['proximo_km']:,}",
          ("VENCIDO" if m["km_restantes"] < 0 else f"{m['km_restantes']:,} km")]
         for m in a["mant_km"]],
    ))

    total = len(a["obligaciones"]) + len(a["mant_fecha"]) + len(a["mant_km"])
    lineas.append("\n" + "-" * 72)
    lineas.append(f" {total} punto(s) requieren atención." if total else " Todo al día. ✓")
    lineas.append("-" * 72)
    return "\n".join(lineas)
