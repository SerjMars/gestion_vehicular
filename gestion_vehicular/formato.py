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
