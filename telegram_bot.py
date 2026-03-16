#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot de Telegram para CB Valsequillo — La Agenda del Finde
Envía resumen semanal de partidos al grupo de Telegram.
"""

import glob
import json
import logging
import os
import re
import sys

import fitz  # PyMuPDF
import requests

logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


def pdf_a_imagen(ruta_pdf: str) -> bytes:
    """
    Renderiza la primera página del PDF como PNG en memoria.
    Usa escala 2x (fitz.Matrix(2,2)) para ~144 DPI efectivos.
    Retorna los bytes PNG. No escribe ficheros temporales.
    """
    doc = fitz.open(ruta_pdf)
    try:
        page = doc[0]
        matriz = fitz.Matrix(2, 2)
        pixmap = page.get_pixmap(matrix=matriz)
        return pixmap.tobytes("png")
    finally:
        doc.close()


_ABREV_DIA = {
    "Lunes": "Lun", "Martes": "Mar", "Miércoles": "Mié",
    "Jueves": "Jue", "Viernes": "Vie", "Sábado": "Sáb", "Domingo": "Dom",
}


def _limpiar_nombre(nombre: str) -> str:
    """Elimina el código federativo entre paréntesis: 'Club (35000000)' → 'Club'."""
    return re.sub(r'\s*\(\d+\)\s*$', '', nombre).strip()


def _formatear_partido(p: dict) -> str:
    """Devuelve una línea formateada para un partido."""
    dia_partes = p["dia"].split()          # ["Sábado", "21/03/26"]
    dia_semana = _ABREV_DIA.get(dia_partes[0], dia_partes[0])
    fecha = dia_partes[1][:5]              # "21/03" (sin año)
    hora = p["hora"]
    local = _limpiar_nombre(p["local"])
    visitante = _limpiar_nombre(p["visitante"])
    lugar = p["lugar"]
    return f"• {dia_semana} {fecha} {hora}h | {local} vs {visitante} | {lugar}"


def formatear_mensaje(partidos: list, hay_cambios: bool) -> str:
    """
    Construye el texto del mensaje de Telegram.
    Respeta el límite de 1024 caracteres (caption de sendPhoto).
    """
    if not partidos:
        return "🏀 CB Valsequillo — No hay partidos próximos programados."

    definitivos = [p for p in partidos if p.get("jornada_tipo") == "DEFINITIVA"]
    provisionales = [p for p in partidos if p.get("jornada_tipo") == "PROVISIONAL"]

    lineas = ["🏀 La Agenda del Finde - CB Valsequillo", ""]

    if definitivos:
        lineas.append("📅 JORNADA DEFINITIVA:")
        for p in definitivos:
            lineas.append(_formatear_partido(p))
        lineas.append("")

    if provisionales:
        lineas.append("📅 PROVISIONAL (puede cambiar):")
        for p in provisionales:
            lineas.append(_formatear_partido(p))
        lineas.append("")

    if hay_cambios:
        lineas.append("⚠️ Cambios detectados — revisa el calendario actualizado.")

    texto = "\n".join(lineas).rstrip()

    if len(texto) > 1024:
        texto = texto[:1023] + "…"

    return texto
