"""Ayudas de presentación: tablas de consola y el tablero en HTML para correo.

Sin dependencias externas: si más adelante querés exportar a Excel o cambiar el
diseño del correo, este es el único módulo que habría que tocar.
"""

from __future__ import annotations

import html as _html

# Colores según urgencia, usados tanto en el HTML del correo como de referencia
# para una futura interfaz web (mismo criterio en los dos lugares).
COLOR_VENCIDO = "#b91c1c"    # rojo   — ya venció
COLOR_URGENTE = "#c2410c"    # naranja — vence en ≤7 días / queda poco kilometraje
COLOR_PROXIMO = "#a16207"    # ámbar  — dentro del horizonte, pero sin apuro
FONDO_VENCIDO = "#fee2e2"
FONDO_URGENTE = "#ffedd5"
FONDO_PROXIMO = "#fef9c3"


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


def _color_por_dias(d: int) -> tuple[str, str]:
    """(color de texto, color de fondo) según los días restantes."""
    if d < 0:
        return COLOR_VENCIDO, FONDO_VENCIDO
    if d <= 7:
        return COLOR_URGENTE, FONDO_URGENTE
    return COLOR_PROXIMO, FONDO_PROXIMO


def _color_por_km(km_restantes: int, umbral_km: int) -> tuple[str, str]:
    """(color de texto, color de fondo) según el kilometraje restante."""
    if km_restantes < 0:
        return COLOR_VENCIDO, FONDO_VENCIDO
    if km_restantes <= umbral_km / 3:
        return COLOR_URGENTE, FONDO_URGENTE
    return COLOR_PROXIMO, FONDO_PROXIMO


def _esc(valor) -> str:
    return _html.escape("" if valor is None else str(valor))


def _tabla_html(encabezados: list[str], filas: list[list], colores: list[tuple[str, str]] | None = None) -> str:
    """Tabla HTML con estilos inline (necesario para que se vea bien en clientes de correo)."""
    if not filas:
        return '<p style="color:#6b7280;font-style:italic;margin:4px 0 16px;">Sin registros.</p>'

    ths = "".join(
        f'<th style="text-align:left;padding:6px 10px;background:#f3f4f6;'
        f'border-bottom:2px solid #d1d5db;font-size:13px;color:#374151;">{_esc(h)}</th>'
        for h in encabezados
    )
    filas_html = []
    for i, fila in enumerate(filas):
        color_texto, color_fondo = colores[i] if colores else ("#1f2937", "#ffffff")
        tds = "".join(
            f'<td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;'
            f'font-size:13px;color:{color_texto};">{_esc(c)}</td>'
            for c in fila
        )
        filas_html.append(f'<tr style="background:{color_fondo};">{tds}</tr>')

    return (
        '<table cellpadding="0" cellspacing="0" style="border-collapse:collapse;width:100%;'
        'margin-bottom:20px;font-family:Arial,Helvetica,sans-serif;">'
        f"<thead><tr>{ths}</tr></thead><tbody>{''.join(filas_html)}</tbody></table>"
    )


def render_alertas_fragmento(a: dict) -> str:
    """Arma el tablero de alertas como un fragmento HTML (sin <html>/<body>).

    Rojo = vencido, naranja = urgente (≤7 días o poco kilometraje restante),
    ámbar = dentro del horizonte configurado pero sin apuro inmediato. Lo usan
    tanto el correo (envuelto por :func:`render_alertas_html`) como la página
    web del tablero, para no duplicar el armado de las tablas.
    """
    obligaciones, mant_fecha, mant_km = a["obligaciones"], a["mant_fecha"], a["mant_km"]
    umbral_km = a["umbral_km"]

    colores_obl = [_color_por_dias(o["dias_restantes"]) for o in obligaciones]
    filas_obl = [
        [o["id"], o["tipo"], o["placas"] or o["conductor"] or "-", o["sucursal"],
         o["fecha_vencimiento"], etiqueta_dias(o["dias_restantes"]), money(o["monto"])]
        for o in obligaciones
    ]

    colores_mf = [_color_por_dias(m["dias_restantes"]) for m in mant_fecha]
    filas_mf = [
        [m["vehiculo_id"], m["placas"], f"{m['marca']} {m['modelo']}", m["energia"],
         m["sucursal"], m["tipo"], m["proximo_fecha"], etiqueta_dias(m["dias_restantes"])]
        for m in mant_fecha
    ]

    colores_mk = [_color_por_km(m["km_restantes"], umbral_km) for m in mant_km]
    filas_mk = [
        [m["vehiculo_id"], m["placas"], f"{m['marca']} {m['modelo']}", m["energia"],
         m["sucursal"], m["tipo"], f"{m['km_actual']:,}", f"{m['proximo_km']:,}",
         ("VENCIDO" if m["km_restantes"] < 0 else f"{m['km_restantes']:,} km")]
        for m in mant_km
    ]

    total = len(obligaciones) + len(mant_fecha) + len(mant_km)
    resumen = (
        f'<p style="font-size:15px;color:#111827;margin:0;"><strong>{total}</strong> '
        'punto(s) requieren atención.</p>'
        if total else
        '<p style="font-size:15px;color:#166534;margin:0;">✓ Todo al día.</p>'
    )

    return f"""\
  <h2 style="margin:0 0 4px;color:#111827;">Tablero de alertas — Flota</h2>
  <p style="margin:0 0 20px;color:#6b7280;font-size:13px;">
    Horizonte: {a['dias']} días · Umbral de mantenimiento: {a['umbral_km']:,} km
  </p>

  <h3 style="color:#111827;font-size:15px;margin:24px 0 8px;">Derechos, permisos y licencias</h3>
  {_tabla_html(["ID", "Tipo", "Aplica a", "Sucursal", "Vence", "Estado", "Monto"], filas_obl, colores_obl)}

  <h3 style="color:#111827;font-size:15px;margin:24px 0 8px;">Mantenimientos próximos (por fecha)</h3>
  {_tabla_html(["Veh", "Placas", "Vehículo", "Energía", "Sucursal", "Tipo", "Próx. fecha", "Estado"], filas_mf, colores_mf)}

  <h3 style="color:#111827;font-size:15px;margin:24px 0 8px;">Mantenimientos próximos (por kilometraje)</h3>
  {_tabla_html(["Veh", "Placas", "Vehículo", "Energía", "Sucursal", "Tipo", "Km actual", "Próx. km", "Faltan"], filas_mk, colores_mk)}

  <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
  {resumen}
  <p style="font-size:11px;color:#9ca3af;margin-top:16px;">
    Leyenda:
    <span style="color:{COLOR_VENCIDO};">■ vencido</span> ·
    <span style="color:{COLOR_URGENTE};">■ urgente (≤7 días o poco kilometraje)</span> ·
    <span style="color:{COLOR_PROXIMO};">■ próximo</span>
  </p>
"""


def render_alertas_html(a: dict) -> str:
    """Documento HTML completo del tablero de alertas, para enviarlo por correo."""
    return f"""\
<!doctype html>
<html>
<body style="margin:0;padding:0;background:#f9fafb;">
<div style="max-width:820px;margin:0 auto;padding:24px;font-family:Arial,Helvetica,sans-serif;">
{render_alertas_fragmento(a)}
</div>
</body>
</html>
"""
