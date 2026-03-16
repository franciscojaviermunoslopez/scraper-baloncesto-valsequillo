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
