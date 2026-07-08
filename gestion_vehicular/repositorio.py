"""Acceso a datos y lógica de negocio.

Estas funciones son la "API interna" del sistema: reciben una conexión y datos
simples, y devuelven filas o identificadores. No imprimen nada ni saben de la
línea de comandos, por lo que una futura app web (Flask/FastAPI) puede llamarlas
tal cual.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime

# --------------------------------------------------------------------------- #
# Utilidades de fecha
# --------------------------------------------------------------------------- #

FORMATO_FECHA = "%Y-%m-%d"


def parse_fecha(texto: str) -> str:
    """Valida y normaliza una fecha en formato YYYY-MM-DD. Lanza ValueError si es inválida."""
    return datetime.strptime(texto.strip(), FORMATO_FECHA).date().isoformat()


def hoy() -> date:
    return date.today()


def dias_hasta(fecha_iso: str, referencia: date | None = None) -> int:
    """Días desde hoy (o ``referencia``) hasta ``fecha_iso``. Negativo si ya pasó."""
    referencia = referencia or hoy()
    objetivo = datetime.strptime(fecha_iso, FORMATO_FECHA).date()
    return (objetivo - referencia).days


# --------------------------------------------------------------------------- #
# Sucursales
# --------------------------------------------------------------------------- #

def crear_sucursal(con, nombre, ciudad=None, estado=None, responsable=None, telefono=None) -> int:
    cur = con.execute(
        "INSERT INTO sucursales (nombre, ciudad, estado, responsable, telefono) "
        "VALUES (?, ?, ?, ?, ?)",
        (nombre, ciudad, estado, responsable, telefono),
    )
    con.commit()
    return cur.lastrowid


def listar_sucursales(con) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM sucursales ORDER BY nombre").fetchall()


def obtener_sucursal(con, sucursal_id) -> sqlite3.Row | None:
    return con.execute("SELECT * FROM sucursales WHERE id = ?", (sucursal_id,)).fetchone()


# --------------------------------------------------------------------------- #
# Vehículos
# --------------------------------------------------------------------------- #

def crear_vehiculo(con, sucursal_id, tipo, marca, modelo, anio=None,
                   placas=None, num_serie=None, km_actual=0, energia="combustion") -> int:
    cur = con.execute(
        "INSERT INTO vehiculos (sucursal_id, tipo, marca, modelo, anio, placas, "
        "num_serie, km_actual, energia) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (sucursal_id, tipo, marca, modelo, anio, placas, num_serie, km_actual, energia),
    )
    con.commit()
    return cur.lastrowid


def listar_vehiculos(con, sucursal_id=None, solo_activos=True) -> list[sqlite3.Row]:
    sql = (
        "SELECT v.*, s.nombre AS sucursal "
        "FROM vehiculos v JOIN sucursales s ON s.id = v.sucursal_id"
    )
    condiciones, params = [], []
    if sucursal_id is not None:
        condiciones.append("v.sucursal_id = ?")
        params.append(sucursal_id)
    if solo_activos:
        condiciones.append("v.activo = 1")
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " ORDER BY s.nombre, v.tipo, v.marca"
    return con.execute(sql, params).fetchall()


def obtener_vehiculo(con, vehiculo_id) -> sqlite3.Row | None:
    return con.execute(
        "SELECT v.*, s.nombre AS sucursal "
        "FROM vehiculos v JOIN sucursales s ON s.id = v.sucursal_id "
        "WHERE v.id = ?",
        (vehiculo_id,),
    ).fetchone()


def actualizar_km(con, vehiculo_id, km_actual) -> None:
    con.execute("UPDATE vehiculos SET km_actual = ? WHERE id = ?", (km_actual, vehiculo_id))
    con.commit()


# --------------------------------------------------------------------------- #
# Conductores
# --------------------------------------------------------------------------- #

def crear_conductor(con, nombre, sucursal_id=None, num_licencia=None,
                    tipo_licencia=None, vigencia_licencia=None, telefono=None) -> int:
    cur = con.execute(
        "INSERT INTO conductores (nombre, sucursal_id, num_licencia, tipo_licencia, "
        "vigencia_licencia, telefono) VALUES (?, ?, ?, ?, ?, ?)",
        (nombre, sucursal_id, num_licencia, tipo_licencia, vigencia_licencia, telefono),
    )
    con.commit()
    return cur.lastrowid


def listar_conductores(con, solo_activos=True) -> list[sqlite3.Row]:
    sql = (
        "SELECT c.*, s.nombre AS sucursal "
        "FROM conductores c LEFT JOIN sucursales s ON s.id = c.sucursal_id"
    )
    if solo_activos:
        sql += " WHERE c.activo = 1"
    sql += " ORDER BY c.nombre"
    return con.execute(sql).fetchall()


# --------------------------------------------------------------------------- #
# Mantenimientos
# --------------------------------------------------------------------------- #

def registrar_mantenimiento(con, vehiculo_id, tipo, fecha, km=None, costo=None,
                            taller=None, proximo_fecha=None, proximo_km=None,
                            notas=None, actualizar_km_vehiculo=True) -> int:
    cur = con.execute(
        "INSERT INTO mantenimientos (vehiculo_id, tipo, fecha, km, costo, taller, "
        "proximo_fecha, proximo_km, notas) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (vehiculo_id, tipo, fecha, km, costo, taller, proximo_fecha, proximo_km, notas),
    )
    # Si el mantenimiento reporta un km mayor al registrado, adelantamos el odómetro.
    if actualizar_km_vehiculo and km is not None:
        veh = obtener_vehiculo(con, vehiculo_id)
        if veh is not None and km > (veh["km_actual"] or 0):
            con.execute("UPDATE vehiculos SET km_actual = ? WHERE id = ?", (km, vehiculo_id))
    con.commit()
    return cur.lastrowid


def listar_mantenimientos(con, vehiculo_id=None) -> list[sqlite3.Row]:
    sql = (
        "SELECT m.*, v.placas, v.marca, v.modelo "
        "FROM mantenimientos m JOIN vehiculos v ON v.id = m.vehiculo_id"
    )
    params = []
    if vehiculo_id is not None:
        sql += " WHERE m.vehiculo_id = ?"
        params.append(vehiculo_id)
    sql += " ORDER BY m.fecha DESC"
    return con.execute(sql, params).fetchall()


# --------------------------------------------------------------------------- #
# Obligaciones (derechos, permisos, tenencia, verificación, seguro, licencias)
# --------------------------------------------------------------------------- #

def registrar_obligacion(con, tipo, fecha_vencimiento, vehiculo_id=None,
                         conductor_id=None, descripcion=None, periodo=None,
                         monto=None, pagado=False, fecha_pago=None, notas=None) -> int:
    if vehiculo_id is None and conductor_id is None:
        raise ValueError("La obligación debe referenciar un vehículo o un conductor.")
    cur = con.execute(
        "INSERT INTO obligaciones (vehiculo_id, conductor_id, tipo, descripcion, "
        "periodo, fecha_vencimiento, monto, pagado, fecha_pago, notas) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (vehiculo_id, conductor_id, tipo, descripcion, periodo, fecha_vencimiento,
         monto, 1 if pagado else 0, fecha_pago, notas),
    )
    con.commit()
    return cur.lastrowid


def marcar_pagada(con, obligacion_id, fecha_pago=None) -> bool:
    fecha_pago = fecha_pago or hoy().isoformat()
    cur = con.execute(
        "UPDATE obligaciones SET pagado = 1, fecha_pago = ? WHERE id = ?",
        (fecha_pago, obligacion_id),
    )
    con.commit()
    return cur.rowcount > 0


def listar_obligaciones(con, solo_pendientes=False) -> list[sqlite3.Row]:
    sql = """
        SELECT o.*,
               v.placas, v.marca, v.modelo,
               c.nombre AS conductor,
               COALESCE(sv.nombre, sc.nombre) AS sucursal
        FROM obligaciones o
        LEFT JOIN vehiculos   v  ON v.id = o.vehiculo_id
        LEFT JOIN sucursales  sv ON sv.id = v.sucursal_id
        LEFT JOIN conductores c  ON c.id = o.conductor_id
        LEFT JOIN sucursales  sc ON sc.id = c.sucursal_id
    """
    if solo_pendientes:
        sql += " WHERE o.pagado = 0"
    sql += " ORDER BY o.fecha_vencimiento"
    return con.execute(sql).fetchall()


# --------------------------------------------------------------------------- #
# Cálculo de alertas / tablero
# --------------------------------------------------------------------------- #

def calcular_alertas(con, dias=30, umbral_km=1000) -> dict:
    """Devuelve un diccionario con todo lo que requiere atención.

    - ``obligaciones``: derechos/permisos/licencias no pagados, vencidos o que
      vencen dentro de ``dias``. Cada fila incluye ``dias_restantes``.
    - ``mant_fecha``: mantenimientos cuyo próximo servicio por fecha cae dentro
      de ``dias`` (o ya pasó).
    - ``mant_km``: vehículos cuyo próximo servicio por kilometraje está a menos
      de ``umbral_km`` km (o ya se pasó), según el odómetro actual.
    """
    referencia = hoy()

    # --- Obligaciones pendientes que vencen pronto o ya vencieron ---
    obligaciones = []
    for fila in listar_obligaciones(con, solo_pendientes=True):
        d = dias_hasta(fila["fecha_vencimiento"], referencia)
        if d <= dias:
            registro = dict(fila)
            registro["dias_restantes"] = d
            obligaciones.append(registro)
    obligaciones.sort(key=lambda r: r["dias_restantes"])

    # --- Mantenimientos por fecha próxima ---
    # Tomamos, por vehículo, el mantenimiento con la próxima fecha más cercana.
    filas_fecha = con.execute(
        """
        SELECT m.*, v.placas, v.marca, v.modelo, v.energia, s.nombre AS sucursal
        FROM mantenimientos m
        JOIN vehiculos v  ON v.id = m.vehiculo_id
        JOIN sucursales s ON s.id = v.sucursal_id
        WHERE m.proximo_fecha IS NOT NULL AND v.activo = 1
        """
    ).fetchall()
    mant_fecha = []
    for fila in filas_fecha:
        d = dias_hasta(fila["proximo_fecha"], referencia)
        if d <= dias:
            registro = dict(fila)
            registro["dias_restantes"] = d
            mant_fecha.append(registro)
    mant_fecha.sort(key=lambda r: r["dias_restantes"])

    # --- Mantenimientos por kilometraje ---
    filas_km = con.execute(
        """
        SELECT m.*, v.placas, v.marca, v.modelo, v.energia, v.km_actual, s.nombre AS sucursal
        FROM mantenimientos m
        JOIN vehiculos v  ON v.id = m.vehiculo_id
        JOIN sucursales s ON s.id = v.sucursal_id
        WHERE m.proximo_km IS NOT NULL AND v.activo = 1
        """
    ).fetchall()
    mant_km = []
    for fila in filas_km:
        km_restantes = fila["proximo_km"] - (fila["km_actual"] or 0)
        if km_restantes <= umbral_km:
            registro = dict(fila)
            registro["km_restantes"] = km_restantes
            mant_km.append(registro)
    mant_km.sort(key=lambda r: r["km_restantes"])

    return {
        "obligaciones": obligaciones,
        "mant_fecha": mant_fecha,
        "mant_km": mant_km,
        "dias": dias,
        "umbral_km": umbral_km,
    }
