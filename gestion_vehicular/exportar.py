"""Exportación de la información a CSV, separada por rubro.

Cada rubro se exporta a su propio archivo: los mantenimientos no se mezclan con
los permisos, ni las licencias con los vehículos. Los CSV se pueden abrir
directamente en Excel.
"""

from __future__ import annotations

import csv
from datetime import date

from . import repositorio as repo

# Rubros disponibles y su etiqueta legible (para la CLI y la interfaz web).
RUBROS_ETIQUETAS = {
    "sucursales": "Sucursales",
    "vehiculos": "Vehículos",
    "conductores": "Conductores",
    "mantenimientos": "Mantenimientos",
    "permisos": "Derechos y permisos (vehículos)",
    "licencias": "Licencias (conductores)",
}
RUBROS = list(RUBROS_ETIQUETAS)


def _sucursales(con):
    filas = repo.listar_sucursales(con)
    encabezados = ["id", "nombre", "ciudad", "estado", "responsable", "telefono"]
    return encabezados, [[f[c] for c in encabezados] for f in filas]


def _vehiculos(con):
    filas = repo.listar_vehiculos(con)
    encabezados = ["id", "sucursal", "tipo", "energia", "marca", "modelo", "anio",
                   "placas", "num_serie", "km_actual"]
    return encabezados, [[f[c] for c in encabezados] for f in filas]


def _conductores(con):
    filas = repo.listar_conductores(con)
    encabezados = ["id", "nombre", "sucursal", "num_licencia", "tipo_licencia",
                   "vigencia_licencia", "telefono"]
    return encabezados, [[f[c] for c in encabezados] for f in filas]


def _mantenimientos(con):
    filas = repo.listar_mantenimientos(con)
    encabezados = ["id", "vehiculo_id", "placas", "marca", "modelo", "tipo", "fecha",
                   "km", "costo", "taller", "proximo_fecha", "proximo_km", "notas"]
    return encabezados, [[f[c] for c in encabezados] for f in filas]


def _obligaciones(con, *, de_vehiculo: bool):
    """Permisos (obligaciones de vehículo) o licencias (obligaciones de conductor)."""
    filas = repo.listar_obligaciones(con)
    filas = [f for f in filas if (f["vehiculo_id"] is not None) == de_vehiculo]
    encabezados = ["id", "tipo", "placas" if de_vehiculo else "conductor", "sucursal",
                   "descripcion", "periodo", "fecha_vencimiento", "monto",
                   "pagado", "fecha_pago", "notas"]
    def valor(f, c):
        if c == "pagado":
            return "si" if f["pagado"] else "no"
        return f[c]
    return encabezados, [[valor(f, c) for c in encabezados] for f in filas]


def datos_por_rubro(con, rubro: str):
    """Devuelve (encabezados, filas) para el rubro pedido."""
    if rubro == "sucursales":
        return _sucursales(con)
    if rubro == "vehiculos":
        return _vehiculos(con)
    if rubro == "conductores":
        return _conductores(con)
    if rubro == "mantenimientos":
        return _mantenimientos(con)
    if rubro == "permisos":
        return _obligaciones(con, de_vehiculo=True)
    if rubro == "licencias":
        return _obligaciones(con, de_vehiculo=False)
    raise ValueError(f"Rubro desconocido: {rubro}. Opciones: {', '.join(RUBROS)}")


def escribir_csv(ruta: str, encabezados: list[str], filas: list[list]) -> None:
    with open(ruta, "w", newline="", encoding="utf-8-sig") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(encabezados)
        escritor.writerows(filas)


def nombre_por_defecto(rubro: str) -> str:
    return f"gv_{rubro}_{date.today().isoformat()}.csv"
