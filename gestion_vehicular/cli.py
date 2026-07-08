"""Interfaz de línea de comandos.

Estructura general:  ``gv <entidad> <acción> [opciones]``

Ejemplos rápidos:
    python gv.py init
    python gv.py seed                      # carga datos de ejemplo
    python gv.py alertas                   # tablero: qué vence pronto
    python gv.py vehiculo list
    python gv.py obligacion pagar --id 3
"""

from __future__ import annotations

import argparse
import sqlite3
import sys

from . import catalogos, repositorio as repo
from .db import RUTA_DB_POR_DEFECTO, conectar, inicializar
from .formato import money, tabla


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #

def cmd_init(con, args):
    inicializar(con)
    print(f"Base de datos lista en: {args.db or RUTA_DB_POR_DEFECTO}")


def cmd_seed(con, args):
    inicializar(con)
    from .seed import cargar_datos_ejemplo
    cargar_datos_ejemplo(con)
    print("Datos de ejemplo cargados. Probá:  python gv.py alertas")


# ---- Sucursales ---- #

def cmd_sucursal_add(con, args):
    sid = repo.crear_sucursal(con, args.nombre, args.ciudad, args.estado,
                              args.responsable, args.telefono)
    print(f"Sucursal creada (id={sid}): {args.nombre}")


def cmd_sucursal_list(con, args):
    filas = repo.listar_sucursales(con)
    print(tabla(
        ["ID", "Nombre", "Ciudad", "Estado", "Responsable", "Teléfono"],
        [[f["id"], f["nombre"], f["ciudad"], f["estado"], f["responsable"], f["telefono"]]
         for f in filas],
    ))


# ---- Vehículos ---- #

def cmd_vehiculo_add(con, args):
    if args.tipo not in catalogos.TIPOS_VEHICULO:
        print(f"Aviso: tipo '{args.tipo}' no está en {catalogos.TIPOS_VEHICULO}.", file=sys.stderr)
    vid = repo.crear_vehiculo(con, args.sucursal, args.tipo, args.marca, args.modelo,
                              args.anio, args.placas, args.serie, args.km)
    print(f"Vehículo creado (id={vid}): {args.marca} {args.modelo} [{args.placas or 's/placas'}]")


def cmd_vehiculo_list(con, args):
    filas = repo.listar_vehiculos(con, sucursal_id=args.sucursal)
    print(tabla(
        ["ID", "Sucursal", "Tipo", "Marca", "Modelo", "Año", "Placas", "Km"],
        [[f["id"], f["sucursal"], f["tipo"], f["marca"], f["modelo"], f["anio"],
          f["placas"], f["km_actual"]] for f in filas],
    ))


def cmd_vehiculo_km(con, args):
    if repo.obtener_vehiculo(con, args.id) is None:
        print(f"No existe el vehículo id={args.id}", file=sys.stderr)
        return 1
    repo.actualizar_km(con, args.id, args.km)
    print(f"Odómetro del vehículo {args.id} actualizado a {args.km:,} km.")


# ---- Conductores ---- #

def cmd_conductor_add(con, args):
    vig = repo.parse_fecha(args.vigencia) if args.vigencia else None
    cid = repo.crear_conductor(con, args.nombre, args.sucursal, args.licencia,
                               args.tipo, vig, args.telefono)
    print(f"Conductor creado (id={cid}): {args.nombre}")


def cmd_conductor_list(con, args):
    filas = repo.listar_conductores(con)
    print(tabla(
        ["ID", "Nombre", "Sucursal", "Licencia", "Tipo", "Vigencia", "Teléfono"],
        [[f["id"], f["nombre"], f["sucursal"], f["num_licencia"], f["tipo_licencia"],
          f["vigencia_licencia"], f["telefono"]] for f in filas],
    ))


# ---- Mantenimientos ---- #

def cmd_mant_add(con, args):
    if repo.obtener_vehiculo(con, args.vehiculo) is None:
        print(f"No existe el vehículo id={args.vehiculo}", file=sys.stderr)
        return 1
    fecha = repo.parse_fecha(args.fecha) if args.fecha else repo.hoy().isoformat()
    prox_fecha = repo.parse_fecha(args.proximo_fecha) if args.proximo_fecha else None
    mid = repo.registrar_mantenimiento(
        con, args.vehiculo, args.tipo, fecha, km=args.km, costo=args.costo,
        taller=args.taller, proximo_fecha=prox_fecha, proximo_km=args.proximo_km,
        notas=args.notas,
    )
    print(f"Mantenimiento registrado (id={mid}) para vehículo {args.vehiculo}.")


def cmd_mant_list(con, args):
    filas = repo.listar_mantenimientos(con, vehiculo_id=args.vehiculo)
    print(tabla(
        ["ID", "Veh", "Placas", "Tipo", "Fecha", "Km", "Costo", "Próx.fecha", "Próx.km", "Taller"],
        [[f["id"], f["vehiculo_id"], f["placas"], f["tipo"], f["fecha"], f["km"],
          money(f["costo"]), f["proximo_fecha"], f["proximo_km"], f["taller"]] for f in filas],
    ))


# ---- Obligaciones ---- #

def cmd_obl_add(con, args):
    if args.vehiculo is None and args.conductor is None:
        print("Indicá --vehiculo o --conductor.", file=sys.stderr)
        return 1
    venc = repo.parse_fecha(args.vencimiento)
    oid = repo.registrar_obligacion(
        con, args.tipo, venc, vehiculo_id=args.vehiculo, conductor_id=args.conductor,
        descripcion=args.descripcion, periodo=args.periodo, monto=args.monto,
        pagado=args.pagado, notas=args.notas,
    )
    print(f"Obligación registrada (id={oid}): {args.tipo} vence {venc}.")


def cmd_obl_list(con, args):
    filas = repo.listar_obligaciones(con, solo_pendientes=args.pendientes)
    def objetivo(f):
        return f["placas"] or f["conductor"] or "-"
    print(tabla(
        ["ID", "Tipo", "Aplica a", "Sucursal", "Periodo", "Vence", "Monto", "Pagado"],
        [[f["id"], f["tipo"], objetivo(f), f["sucursal"], f["periodo"],
          f["fecha_vencimiento"], money(f["monto"]), "sí" if f["pagado"] else "no"]
         for f in filas],
    ))


def cmd_obl_pagar(con, args):
    fecha = repo.parse_fecha(args.fecha) if args.fecha else None
    if repo.marcar_pagada(con, args.id, fecha):
        print(f"Obligación {args.id} marcada como pagada.")
    else:
        print(f"No existe la obligación id={args.id}", file=sys.stderr)
        return 1


# ---- Tablero de alertas ---- #

def _etiqueta_dias(d: int) -> str:
    if d < 0:
        return f"VENCIDO hace {-d} d"
    if d == 0:
        return "vence HOY"
    return f"en {d} d"


def cmd_alertas(con, args):
    a = repo.calcular_alertas(con, dias=args.dias, umbral_km=args.umbral_km)

    print("=" * 72)
    print(f" TABLERO DE ALERTAS  —  horizonte {a['dias']} días / {a['umbral_km']:,} km")
    print("=" * 72)

    print("\n▸ DERECHOS, PERMISOS Y LICENCIAS (pendientes de pago/renovación)")
    print(tabla(
        ["ID", "Tipo", "Aplica a", "Sucursal", "Vence", "Estado", "Monto"],
        [[o["id"], o["tipo"], o["placas"] or o["conductor"] or "-", o["sucursal"],
          o["fecha_vencimiento"], _etiqueta_dias(o["dias_restantes"]), money(o["monto"])]
         for o in a["obligaciones"]],
    ))

    print("\n▸ MANTENIMIENTOS PRÓXIMOS (por fecha)")
    print(tabla(
        ["Veh", "Placas", "Vehículo", "Sucursal", "Tipo", "Próx.fecha", "Estado"],
        [[m["vehiculo_id"], m["placas"], f"{m['marca']} {m['modelo']}", m["sucursal"],
          m["tipo"], m["proximo_fecha"], _etiqueta_dias(m["dias_restantes"])]
         for m in a["mant_fecha"]],
    ))

    print("\n▸ MANTENIMIENTOS PRÓXIMOS (por kilometraje)")
    print(tabla(
        ["Veh", "Placas", "Vehículo", "Sucursal", "Tipo", "Km actual", "Próx.km", "Faltan"],
        [[m["vehiculo_id"], m["placas"], f"{m['marca']} {m['modelo']}", m["sucursal"],
          m["tipo"], f"{m['km_actual']:,}", f"{m['proximo_km']:,}",
          ("VENCIDO" if m["km_restantes"] < 0 else f"{m['km_restantes']:,} km")]
         for m in a["mant_km"]],
    ))

    total = len(a["obligaciones"]) + len(a["mant_fecha"]) + len(a["mant_km"])
    print("\n" + "-" * 72)
    print(f" {total} punto(s) requieren atención." if total else " Todo al día. ✓")
    print("-" * 72)


# --------------------------------------------------------------------------- #
# Definición del parser
# --------------------------------------------------------------------------- #

def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gv",
        description="Gestión de mantenimientos, derechos, permisos y licencias de la flota.",
    )
    p.add_argument("--db", help="Ruta a la base de datos SQLite (por defecto ~/gestion_vehicular.db).")
    sub = p.add_subparsers(dest="comando", required=True)

    # init / seed / alertas
    sub.add_parser("init", help="Crea la base de datos y las tablas.").set_defaults(func=cmd_init)
    sub.add_parser("seed", help="Carga datos de ejemplo (6 sucursales con flota).").set_defaults(func=cmd_seed)

    pa = sub.add_parser("alertas", help="Tablero: qué vence pronto (derechos, permisos, mantenimientos).")
    pa.add_argument("--dias", type=int, default=30, help="Horizonte de alerta en días (default 30).")
    pa.add_argument("--umbral-km", type=int, default=1000, help="Umbral de km para mantenimiento (default 1000).")
    pa.set_defaults(func=cmd_alertas)

    # sucursal
    ps = sub.add_parser("sucursal", help="Alta y listado de sucursales.").add_subparsers(dest="accion", required=True)
    a = ps.add_parser("add")
    a.add_argument("nombre")
    a.add_argument("--ciudad"); a.add_argument("--estado")
    a.add_argument("--responsable"); a.add_argument("--telefono")
    a.set_defaults(func=cmd_sucursal_add)
    ps.add_parser("list").set_defaults(func=cmd_sucursal_list)

    # vehiculo
    pv = sub.add_parser("vehiculo", help="Alta, listado y actualización de kilometraje.").add_subparsers(dest="accion", required=True)
    a = pv.add_parser("add")
    a.add_argument("--sucursal", type=int, required=True)
    a.add_argument("--tipo", required=True, help=f"{'|'.join(catalogos.TIPOS_VEHICULO)}")
    a.add_argument("--marca", required=True); a.add_argument("--modelo", required=True)
    a.add_argument("--anio", type=int); a.add_argument("--placas")
    a.add_argument("--serie", help="NIV / número de serie"); a.add_argument("--km", type=int, default=0)
    a.set_defaults(func=cmd_vehiculo_add)
    a = pv.add_parser("list")
    a.add_argument("--sucursal", type=int, help="Filtrar por sucursal.")
    a.set_defaults(func=cmd_vehiculo_list)
    a = pv.add_parser("km", help="Actualiza el odómetro de un vehículo.")
    a.add_argument("--id", type=int, required=True); a.add_argument("--km", type=int, required=True)
    a.set_defaults(func=cmd_vehiculo_km)

    # conductor
    pc = sub.add_parser("conductor", help="Alta y listado de conductores.").add_subparsers(dest="accion", required=True)
    a = pc.add_parser("add")
    a.add_argument("nombre")
    a.add_argument("--sucursal", type=int); a.add_argument("--licencia")
    a.add_argument("--tipo", help="Tipo/categoría de licencia."); a.add_argument("--vigencia", help="YYYY-MM-DD")
    a.add_argument("--telefono")
    a.set_defaults(func=cmd_conductor_add)
    pc.add_parser("list").set_defaults(func=cmd_conductor_list)

    # mantenimiento
    pm = sub.add_parser("mantenimiento", help="Registro e historial de mantenimientos.").add_subparsers(dest="accion", required=True)
    a = pm.add_parser("add")
    a.add_argument("--vehiculo", type=int, required=True)
    a.add_argument("--tipo", required=True, help=f"ej. {', '.join(list(catalogos.TIPOS_MANTENIMIENTO)[:4])}...")
    a.add_argument("--fecha", help="YYYY-MM-DD (default hoy)")
    a.add_argument("--km", type=int); a.add_argument("--costo", type=float); a.add_argument("--taller")
    a.add_argument("--proximo-fecha", help="Próximo servicio sugerido (YYYY-MM-DD)")
    a.add_argument("--proximo-km", type=int, help="Próximo servicio sugerido (km)")
    a.add_argument("--notas")
    a.set_defaults(func=cmd_mant_add)
    a = pm.add_parser("list")
    a.add_argument("--vehiculo", type=int, help="Filtrar por vehículo.")
    a.set_defaults(func=cmd_mant_list)

    # obligacion
    po = sub.add_parser("obligacion", help="Derechos, permisos, tenencia, verificación, seguro y licencias.").add_subparsers(dest="accion", required=True)
    a = po.add_parser("add")
    a.add_argument("--tipo", required=True, help="tenencia|verificacion|refrendo|seguro|licencia|...")
    a.add_argument("--vencimiento", required=True, help="YYYY-MM-DD")
    a.add_argument("--vehiculo", type=int, help="ID del vehículo (para derechos/permisos).")
    a.add_argument("--conductor", type=int, help="ID del conductor (para licencias).")
    a.add_argument("--descripcion"); a.add_argument("--periodo", help='ej. "2026" o "2026-1er sem."')
    a.add_argument("--monto", type=float)
    a.add_argument("--pagado", action="store_true"); a.add_argument("--notas")
    a.set_defaults(func=cmd_obl_add)
    a = po.add_parser("list")
    a.add_argument("--pendientes", action="store_true", help="Solo las no pagadas.")
    a.set_defaults(func=cmd_obl_list)
    a = po.add_parser("pagar")
    a.add_argument("--id", type=int, required=True); a.add_argument("--fecha", help="Fecha de pago (default hoy).")
    a.set_defaults(func=cmd_obl_pagar)

    return p


def main(argv=None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    con = conectar(args.db)
    try:
        resultado = args.func(con, args)
        return resultado or 0
    except (ValueError, sqlite3.IntegrityError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
