"""Datos de ejemplo: 6 sucursales a nivel nacional con su flota.

Las fechas se calculan en relación a HOY para que el tablero de alertas muestre
casos representativos (vencidos, por vencer y al día). Ideal para probar sin
capturar datos manualmente:  ``python gv.py seed && python gv.py alertas``.
"""

from __future__ import annotations

from datetime import date, timedelta

from . import repositorio as repo


def _f(dias: int) -> str:
    """Fecha ISO a ``dias`` de hoy (negativo = pasado)."""
    return (date.today() + timedelta(days=dias)).isoformat()


def cargar_datos_ejemplo(con) -> None:
    # Evitamos duplicar si ya se corrió seed.
    if repo.listar_sucursales(con):
        print("Ya hay sucursales cargadas; se omite el seed.")
        return

    # --- 6 sucursales nacionales ---
    sucursales = [
        ("Matriz CDMX", "Ciudad de México", "CDMX", "Laura Mendoza", "55-1000-0001"),
        ("Guadalajara", "Guadalajara", "Jalisco", "Carlos Ruiz", "33-1000-0002"),
        ("Monterrey", "Monterrey", "Nuevo León", "Ana Torres", "81-1000-0003"),
        ("Puebla", "Puebla", "Puebla", "Jorge Salas", "22-1000-0004"),
        ("Mérida", "Mérida", "Yucatán", "Diana Poot", "99-1000-0005"),
        ("Tijuana", "Tijuana", "Baja California", "Raúl Beltrán", "66-1000-0006"),
    ]
    ids_suc = [repo.crear_sucursal(con, *s) for s in sucursales]

    # --- Flota: cada sucursal tiene al menos una pickup ---
    # (sucursal_idx, tipo, marca, modelo, anio, placas, km_actual)
    flota = [
        (0, "pickup",    "Toyota",     "Hilux",   2022, "ABC-11-01", 78000),
        (0, "sedan",     "Nissan",     "Versa",   2021, "ABC-11-02", 62000),
        (0, "hatchback", "Chevrolet",  "Aveo",    2023, "ABC-11-03", 30000),
        (1, "pickup",    "Ford",       "Ranger",  2020, "DEF-22-01", 110000),
        (1, "sedan",     "Volkswagen", "Jetta",   2022, "DEF-22-02", 54000),
        (2, "pickup",    "RAM",        "1500",    2021, "GHI-33-01", 95000),
        (2, "pickup",    "Nissan",     "Frontier",2023, "GHI-33-02", 41000),
        (2, "hatchback", "Kia",        "Rio",     2022, "GHI-33-03", 48000),
        (3, "pickup",    "Toyota",     "Tacoma",  2019, "JKL-44-01", 132000),
        (4, "pickup",    "Chevrolet",  "S10",     2022, "MNO-55-01", 67000),
        (4, "sedan",     "Honda",      "City",    2023, "MNO-55-02", 25000),
        (5, "pickup",    "Ford",       "F-150",   2021, "PQR-66-01", 88000),
        (5, "hatchback", "Mazda",      "2",       2022, "PQR-66-02", 39000),
    ]
    ids_veh = []
    for idx, tipo, marca, modelo, anio, placas, km in flota:
        ids_veh.append(repo.crear_vehiculo(
            con, ids_suc[idx], tipo, marca, modelo, anio, placas, km_actual=km))

    # --- Conductores (uno por sucursal, con licencia) ---
    conductores = [
        ("Miguel Ángel Cruz", 0, "LIC-CDMX-0011", "B", _f(45)),
        ("Fernanda López",    1, "LIC-JAL-0022",  "B", _f(-10)),   # licencia vencida
        ("Héctor Ramírez",    2, "LIC-NL-0033",   "C", _f(200)),
        ("Sofía Herrera",     3, "LIC-PUE-0044",  "B", _f(15)),    # por vencer
        ("Luis Canul",        4, "LIC-YUC-0055",  "B", _f(365)),
        ("Marisol Vega",      5, "LIC-BC-0066",   "C", _f(5)),     # por vencer
    ]
    ids_cond = []
    for nombre, idx, lic, tipo, vig in conductores:
        ids_cond.append(repo.crear_conductor(
            con, nombre, ids_suc[idx], lic, tipo, vig))

    # --- Mantenimientos (con próximo servicio por fecha y/o km) ---
    # (veh_idx, tipo, fecha, km, costo, taller, prox_fecha, prox_km)
    mantenimientos = [
        (0, "cambio_aceite", _f(-160), 73000, 1800, "Taller Matriz", _f(20),  83000),  # km cerca
        (0, "frenos",        _f(-90),  75000, 4200, "Taller Matriz", None,     None),
        (3, "afinacion",     _f(-200), 100000, 7800, "Ford GDL",     _f(-5),   115000), # fecha vencida
        (5, "cambio_aceite", _f(-100), 50000,  1900, "VW Center",    _f(60),   64000),
        (8, "llantas",       _f(-30),  130000, 9600, "Llantera Sur", None,     138000), # km cerca
        (11,"cambio_aceite", _f(-80),  85000,  2100, "Ford Tijuana", _f(10),   93000),  # fecha cerca
    ]
    for vidx, tipo, fecha, km, costo, taller, pf, pk in mantenimientos:
        repo.registrar_mantenimiento(
            con, ids_veh[vidx], tipo, fecha, km=km, costo=costo, taller=taller,
            proximo_fecha=pf, proximo_km=pk)

    # --- Obligaciones vehiculares (tenencia, verificación, seguro...) ---
    # (veh_idx, tipo, periodo, vencimiento, monto, pagado)
    obligaciones = [
        (0, "tenencia",     "2026", _f(-20), 5200,  False),  # vencida
        (0, "verificacion", "2026-1er sem.", _f(12), 620,   False),  # por vencer
        (0, "seguro",       "2026", _f(90),  14500, True),
        (3, "verificacion", "2026-1er sem.", _f(-8), 620,   False),  # vencida
        (5, "tenencia",     "2026", _f(25),  6100,  False),  # por vencer
        (6, "seguro",       "2026", _f(3),   13200, False),  # por vencer
        (8, "tenencia",     "2026", _f(120), 4800,  False),  # lejano (no alerta)
        (11,"verificacion", "2026-1er sem.", _f(18), 640,   False),  # por vencer
    ]
    for vidx, tipo, periodo, venc, monto, pagado in obligaciones:
        repo.registrar_obligacion(
            con, tipo, venc, vehiculo_id=ids_veh[vidx], periodo=periodo,
            monto=monto, pagado=pagado,
            descripcion=None)

    # --- Licencias como obligación del conductor (renovación) ---
    for cid, (_, _, _, _, vig) in zip(ids_cond, conductores):
        repo.registrar_obligacion(
            con, "licencia", vig, conductor_id=cid, periodo="renovación",
            descripcion="Renovación de licencia de conducir")

    print(f"Cargadas {len(sucursales)} sucursales, {len(flota)} vehículos, "
          f"{len(conductores)} conductores.")
