"""Interfaz web (Flask): la misma gestión de la CLI, con pantallas y botones.

Reutiliza tal cual la lógica de negocio de ``repositorio.py``, el envío de
correo de ``correo.py`` y la exportación de ``exportar.py`` — esta capa solo
traduce formularios/clicks a esas mismas llamadas. Pensada para correr en tu
propia computadora (``python app.py``) y abrirse en el navegador; si el día
de mañana hace falta que la usen varias personas desde la red, esta es la
capa que habría que ampliar (autenticación, base de datos compartida), no la
lógica de negocio.
"""

from __future__ import annotations

import csv
import io
import os

from flask import Flask, Response, flash, g, redirect, render_template, request, url_for

from . import catalogos, correo, exportar, repositorio as repo
from .db import RUTA_DB_POR_DEFECTO, conectar, inicializar
from .formato import etiqueta_dias, money, render_alertas_fragmento


def crear_app(ruta_db: str | None = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("GV_SECRET_KEY", "clave-de-desarrollo-no-usar-en-produccion")
    app.config["RUTA_DB"] = ruta_db or RUTA_DB_POR_DEFECTO

    con_inicial = conectar(app.config["RUTA_DB"])
    inicializar(con_inicial)
    con_inicial.close()

    def get_db():
        if "db" not in g:
            g.db = conectar(app.config["RUTA_DB"])
        return g.db

    @app.teardown_appcontext
    def cerrar_db(exception=None):
        con = g.pop("db", None)
        if con is not None:
            con.close()

    app.jinja_env.filters["money"] = money
    app.jinja_env.filters["dias"] = etiqueta_dias

    # ------------------------------------------------------------------- #
    # Tablero de alertas
    # ------------------------------------------------------------------- #

    @app.route("/")
    def index():
        con = get_db()
        dias = request.args.get("dias", 30, type=int)
        umbral_km = request.args.get("umbral_km", 1000, type=int)
        a = repo.calcular_alertas(con, dias=dias, umbral_km=umbral_km)
        return render_template(
            "index.html", dias=dias, umbral_km=umbral_km,
            fragmento=render_alertas_fragmento(a), correo_configurado=correo.configurado(),
        )

    @app.route("/alertas/enviar", methods=["POST"])
    def alertas_enviar():
        con = get_db()
        dias = request.form.get("dias", 30, type=int)
        umbral_km = request.form.get("umbral_km", 1000, type=int)
        a = repo.calcular_alertas(con, dias=dias, umbral_km=umbral_km)
        from .formato import render_alertas, render_alertas_html
        total = len(a["obligaciones"]) + len(a["mant_fecha"]) + len(a["mant_km"])
        try:
            destinatarios = correo.enviar_alertas(
                render_alertas(a), total, cuerpo_html=render_alertas_html(a))
            flash(f"Alertas enviadas a: {', '.join(destinatarios)}", "success")
        except correo.CorreoNoConfigurado as e:
            flash(f"No se pudo enviar el correo: {e}", "error")
        except Exception as e:  # errores de SMTP/red
            flash(f"Falló el envío de correo: {e}", "error")
        return redirect(url_for("index", dias=dias, umbral_km=umbral_km))

    # ------------------------------------------------------------------- #
    # Sucursales
    # ------------------------------------------------------------------- #

    @app.route("/sucursales", methods=["GET", "POST"])
    def sucursales():
        con = get_db()
        if request.method == "POST":
            repo.crear_sucursal(
                con, request.form["nombre"], request.form.get("ciudad") or None,
                request.form.get("estado") or None, request.form.get("responsable") or None,
                request.form.get("telefono") or None,
            )
            flash("Sucursal creada.", "success")
            return redirect(url_for("sucursales"))
        return render_template("sucursales.html", filas=repo.listar_sucursales(con))

    # ------------------------------------------------------------------- #
    # Vehículos
    # ------------------------------------------------------------------- #

    @app.route("/vehiculos", methods=["GET", "POST"])
    def vehiculos():
        con = get_db()
        if request.method == "POST":
            repo.crear_vehiculo(
                con, int(request.form["sucursal_id"]), request.form["tipo"],
                request.form["marca"], request.form["modelo"],
                int(request.form["anio"]) if request.form.get("anio") else None,
                request.form.get("placas") or None, request.form.get("num_serie") or None,
                int(request.form.get("km_actual") or 0), request.form.get("energia") or "combustion",
            )
            flash("Vehículo creado.", "success")
            return redirect(url_for("vehiculos"))
        sucursal_id = request.args.get("sucursal_id", type=int)
        return render_template(
            "vehiculos.html", filas=repo.listar_vehiculos(con, sucursal_id=sucursal_id),
            sucursales=repo.listar_sucursales(con), sucursal_id=sucursal_id,
            tipos=catalogos.TIPOS_VEHICULO, energias=catalogos.TIPOS_ENERGIA,
        )

    @app.route("/vehiculos/<int:vehiculo_id>/km", methods=["POST"])
    def vehiculo_km(vehiculo_id):
        con = get_db()
        repo.actualizar_km(con, vehiculo_id, int(request.form["km"]))
        flash("Odómetro actualizado.", "success")
        return redirect(url_for("vehiculos"))

    # ------------------------------------------------------------------- #
    # Conductores
    # ------------------------------------------------------------------- #

    @app.route("/conductores", methods=["GET", "POST"])
    def conductores():
        con = get_db()
        if request.method == "POST":
            vigencia = repo.parse_fecha(request.form["vigencia"]) if request.form.get("vigencia") else None
            repo.crear_conductor(
                con, request.form["nombre"],
                int(request.form["sucursal_id"]) if request.form.get("sucursal_id") else None,
                request.form.get("num_licencia") or None, request.form.get("tipo_licencia") or None,
                vigencia, request.form.get("telefono") or None,
            )
            flash("Conductor creado.", "success")
            return redirect(url_for("conductores"))
        return render_template(
            "conductores.html", filas=repo.listar_conductores(con), sucursales=repo.listar_sucursales(con))

    # ------------------------------------------------------------------- #
    # Mantenimientos
    # ------------------------------------------------------------------- #

    @app.route("/mantenimientos", methods=["GET", "POST"])
    def mantenimientos():
        con = get_db()
        if request.method == "POST":
            fecha = repo.parse_fecha(request.form["fecha"]) if request.form.get("fecha") else repo.hoy().isoformat()
            proximo_fecha = (
                repo.parse_fecha(request.form["proximo_fecha"]) if request.form.get("proximo_fecha") else None
            )
            repo.registrar_mantenimiento(
                con, int(request.form["vehiculo_id"]), request.form["tipo"], fecha,
                km=int(request.form["km"]) if request.form.get("km") else None,
                costo=float(request.form["costo"]) if request.form.get("costo") else None,
                taller=request.form.get("taller") or None, proximo_fecha=proximo_fecha,
                proximo_km=int(request.form["proximo_km"]) if request.form.get("proximo_km") else None,
                notas=request.form.get("notas") or None,
            )
            flash("Mantenimiento registrado.", "success")
            return redirect(url_for("mantenimientos"))
        vehiculo_id = request.args.get("vehiculo_id", type=int)
        return render_template(
            "mantenimientos.html", filas=repo.listar_mantenimientos(con, vehiculo_id=vehiculo_id),
            vehiculos=repo.listar_vehiculos(con), vehiculo_id=vehiculo_id,
            tipos_combustion=catalogos.TIPOS_MANTENIMIENTO_COMBUSTION,
            tipos_electrico=catalogos.TIPOS_MANTENIMIENTO_ELECTRICO,
        )

    # ------------------------------------------------------------------- #
    # Obligaciones (derechos, permisos, licencias)
    # ------------------------------------------------------------------- #

    @app.route("/obligaciones", methods=["GET", "POST"])
    def obligaciones():
        con = get_db()
        if request.method == "POST":
            vencimiento = repo.parse_fecha(request.form["fecha_vencimiento"])
            vehiculo_id = int(request.form["vehiculo_id"]) if request.form.get("vehiculo_id") else None
            conductor_id = int(request.form["conductor_id"]) if request.form.get("conductor_id") else None
            if vehiculo_id is None and conductor_id is None:
                flash("Indicá un vehículo o un conductor.", "error")
                return redirect(url_for("obligaciones"))
            repo.registrar_obligacion(
                con, request.form["tipo"], vencimiento, vehiculo_id=vehiculo_id, conductor_id=conductor_id,
                descripcion=request.form.get("descripcion") or None, periodo=request.form.get("periodo") or None,
                monto=float(request.form["monto"]) if request.form.get("monto") else None,
                pagado=bool(request.form.get("pagado")), notas=request.form.get("notas") or None,
            )
            flash("Registro creado.", "success")
            return redirect(url_for("obligaciones"))
        solo_pendientes = request.args.get("pendientes") == "1"
        return render_template(
            "obligaciones.html", filas=repo.listar_obligaciones(con, solo_pendientes=solo_pendientes),
            vehiculos=repo.listar_vehiculos(con), conductores=repo.listar_conductores(con),
            solo_pendientes=solo_pendientes,
            tipos_vehiculo=catalogos.TIPOS_OBLIGACION_VEHICULO,
            tipos_conductor=catalogos.TIPOS_OBLIGACION_CONDUCTOR,
        )

    @app.route("/obligaciones/<int:obligacion_id>/pagar", methods=["POST"])
    def obligacion_pagar(obligacion_id):
        con = get_db()
        if repo.marcar_pagada(con, obligacion_id):
            flash("Marcado como pagado.", "success")
        else:
            flash(f"No existe el registro id={obligacion_id}.", "error")
        return redirect(request.referrer or url_for("obligaciones"))

    # ------------------------------------------------------------------- #
    # Exportar / Correo
    # ------------------------------------------------------------------- #

    @app.route("/exportar")
    def exportar_pagina():
        cfg_ok = correo.configurado()
        return render_template(
            "exportar.html", rubros=exportar.RUBROS_ETIQUETAS, correo_configurado=cfg_ok,
            remitente=os.environ.get("GV_SMTP_FROM") or os.environ.get("GV_SMTP_USER", ""),
            destinatarios=os.environ.get("GV_SMTP_TO", ""),
        )

    @app.route("/exportar/<rubro>")
    def exportar_rubro(rubro):
        con = get_db()
        try:
            encabezados, filas = exportar.datos_por_rubro(con, rubro)
        except ValueError:
            flash(f"Rubro desconocido: {rubro}", "error")
            return redirect(url_for("exportar_pagina"))
        buf = io.StringIO()
        escritor = csv.writer(buf)
        escritor.writerow(encabezados)
        escritor.writerows(filas)
        return Response(
            "﻿" + buf.getvalue(), mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={exportar.nombre_por_defecto(rubro)}"},
        )

    @app.route("/correo/probar", methods=["POST"])
    def correo_probar():
        try:
            destinatarios = correo.enviar_prueba()
            flash(f"Correo de prueba enviado a: {', '.join(destinatarios)}", "success")
        except correo.CorreoNoConfigurado as e:
            flash(f"No se pudo enviar: {e}", "error")
        except Exception as e:  # errores de SMTP/red
            flash(f"Falló el envío: {e}", "error")
        return redirect(request.referrer or url_for("exportar_pagina"))

    return app
