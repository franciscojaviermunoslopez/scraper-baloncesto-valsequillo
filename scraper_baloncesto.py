#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de extracción automática de partidos de Valsequillo
Federación Insular de Baloncesto de Gran Canaria
"""

import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import pandas as pd
import re
import ssl
import csv
import logging # Restaurado
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo # Para zona horaria Canarias
from pathlib import Path
from typing import List, Dict, Optional
import urllib3
from ics import Calendar, Event
from ics.alarm import DisplayAlarm  # Para recordatorios
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ScraperBaloncesto:
    """Scraper para extraer partidos de baloncesto de Valsequillo"""
    
    def __init__(self, url_base: str = "https://www.fibgrancanaria.com"):
        self.url_base = url_base
        self.url_jornadas = "https://www.fibgrancanaria.com/index.php/competicion/hojas-de-jornada"
        self.session = requests.Session()
        
        # Headers mejorados para compatibilidad con servidores
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Configuración SSL más permisiva para servidores con certificados antiguos
        import ssl
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def descargar_pdfs_recientes(self) -> List[Dict]:
        """
        Descarga las jornadas más recientes (definitivas y provisionales)
        CON REINTENTOS automáticos si la web está caída.
        
        Returns:
            Lista de diccionarios con info de PDFs descargados
        """
        max_intentos = 3
        tiempo_espera = 5  # segundos
        
        for intento in range(1, max_intentos + 1):
            try:
                logger.info(f"Accediendo a {self.url_jornadas} (Intento {intento}/{max_intentos})")
                response = self.session.get(self.url_jornadas, timeout=60, verify=False)  # Aumentado a 60s
                response.raise_for_status()
                
                # Si llegamos aquí, la conexión fue exitosa
                break
                
            except Exception as e:
                logger.warning(f"Intento {intento} falló: {e}")
                
                if intento < max_intentos:
                    logger.info(f"Reintentando en {tiempo_espera} segundos...")
                    time.sleep(tiempo_espera)
                    tiempo_espera *= 2  # Backoff exponencial (5s, 10s, 20s)
                else:
                    logger.error("Error al descargar los PDFs después de todos los reintentos")
                    return []
        
        try:
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar enlaces de descarga usando el patrón de Phoca Download
            # Los enlaces tienen el formato: ?download=ID:nombre-archivo
            download_link = None
            
            # Buscar todos los enlaces que contengan el parámetro '?download='
            download_links = soup.find_all('a', href=re.compile(r'\?download=', re.I))
            
            if not download_links:
                logger.error("No se encontró ningún enlace de descarga en la página")
                return []
            
            # Filtrar para obtener definitivas Y provisionales (las 3 jornadas más recientes)
            jornadas_recientes = []
            for link in download_links[:15]:  # Ampliar búsqueda a 15
                texto = link.get_text().lower()
                logger.info(f"Analizando enlace: {link.get_text().strip()}")
                
                # Ignorar Minibasket
                if 'minibasket' in texto or 'preminibasket' in texto:
                    logger.info("   -> Ignorado (Minibasket)")
                    continue
                
                if 'jornada' in texto and ('definitiva' in texto or 'provisional' in texto):
                    jornadas_recientes.append({
                        'link': link,
                        'href': link.get('href'),
                        'titulo': link.get_text().strip(),
                        'tipo': 'DEFINITIVA' if 'definitiva' in texto else 'PROVISIONAL'
                    })
            
            # Filtrar para quedarnos con la versión MÁS RECIENTE de cada jornada
            # Ejemplo: Si hay "Jornada 14 DEFINITIVA 2" y "Jornada 14 DEFINITIVA 3", solo cogemos la 3
            jornadas_unicas = {}
            
            for j in jornadas_recientes:
                # Extraer número de jornada (ej: "Jornada 14 (05-11 Ene) DEFINITIVA 3" -> "14-DEFINITIVA")
                # O si no tiene número: "Jornada DEFINITIVA" -> "0-DEFINITIVA"
                match = re.search(r'Jornada\s+(\d+)?\s*.*?(DEFINITIVA|PROVISIONAL)', j['titulo'], re.IGNORECASE)
                if match:
                    num_jornada = match.group(1) if match.group(1) else "0"  # Si no hay número, usar "0"
                    tipo = match.group(2).upper()
                    clave = f"{num_jornada}-{tipo}"
                    
                    # Si ya existe, comparar versiones y quedarnos con la más reciente
                    # (Las jornadas están ordenadas de más nueva a más vieja en la web)
                    if clave not in jornadas_unicas:
                        jornadas_unicas[clave] = j
            
            # Convertir de vuelta a lista y tomar las 3 más recientes
            jornadas_a_procesar = list(jornadas_unicas.values())[:3]
            
            if not jornadas_a_procesar:
                logger.error("No se encontraron jornadas definitivas ni provisionales")
                return []
            
            logger.info(f"Se encontraron {len(jornadas_a_procesar)} jornadas para procesar:")
            for j in jornadas_a_procesar:
                logger.info(f"  - {j['titulo']} ({j['tipo']})")
            
            # Descargar y procesar TODAS las jornadas encontradas
            pdfs_descargados = []
            for jornada in jornadas_a_procesar:
                download_link = jornada['href']
                
                # Normalizar URL
                if not download_link.startswith('http'):
                    download_link = f"{self.url_base}{download_link}" if download_link.startswith('/') else f"{self.url_base}/{download_link}"
                
                try:
                    # Descargar el PDF
                    logger.info(f"Descargando: {jornada['titulo']}")
                    pdf_response = self.session.get(download_link, timeout=30, verify=False)
                    pdf_response.raise_for_status()
                    
                    # Guardar el PDF
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    tipo_sufijo = jornada['tipo'].lower()
                    pdf_path = Path(f"jornada_{tipo_sufijo}_{timestamp}.pdf")
                    pdf_path.write_bytes(pdf_response.content)
                    
                    # Validar que sea realmente un PDF (no un HTML de error/login)
                    if not pdf_response.content.startswith(b'%PDF'):
                        logger.warning(f"⚠️ El archivo descargado NO es un PDF válido (posible redirect o login). Descartando: {jornada['titulo']}")
                        pdf_path.unlink()  # Borrar el archivo basura
                        continue
                    
                    pdfs_descargados.append({
                        'path': pdf_path,
                        'tipo': jornada['tipo'],
                        'titulo': jornada['titulo']
                    })
                    
                    logger.info(f"PDF descargado: {pdf_path}")
                    
                except Exception as e:
                    logger.warning(f"Error al descargar {jornada['titulo']}: {e}")
                    continue
            
            if not pdfs_descargados:
                logger.error("No se pudo descargar ningún PDF")
                return []
            
            logger.info(f"Total de PDFs descargados: {len(pdfs_descargados)}")
            return pdfs_descargados
            
        except requests.RequestException as e:
            logger.error(f"Error al descargar los PDFs: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return []
    
    def descargar_ultimo_pdf(self) -> Optional[Path]:
        """
        Método legacy - mantener compatibilidad
        Descarga el primer PDF y retorna su ruta
        """
        pdfs = self.descargar_pdfs_recientes()
        return pdfs[0]['path'] if pdfs else None
            
    def extraer_partidos_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Extrae información de partidos del PDF usando PyMuPDF
        El PDF tiene formato multi-línea donde cada partido ocupa 4 líneas:
        Línea 1: Nº Part + Hora + Categoría
        Línea 2: Equipo Local (con código)
        Extrae información de partidos del PDF usando heurísticas de texto.
        Busca 'Valsequillo' y deduce el contexto (rival, categoría, lugar) basado en la estructura.
        """
        partidos = []
        try:
            doc = fitz.open(pdf_path)
            
            # Patrón para detectar códigos de equipo: (35xxxxxx) o similar
            # Quitamos el $ para permitir basura al final de la línea
            patron_codigo = re.compile(r'\(\d+\)')
            
            for num_pagina, page in enumerate(doc):
                text = page.get_text()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                
                # Intentar extraer rango de fechas del título de la jornada
                # Ej: "JORNADA 15 (12-18 Ene)" o "05-11 Ene"
                fecha_inicio_jornada = None
                mes_jornada = None
                year_jornada = datetime.now().year
                
                # Buscar en las primeras 20 líneas
                for line in lines[:20]:
                    # Patrón: (DD-DD Mes) o DD-DD Mes
                    match_rango = re.search(r'(\d{1,2})-(\d{1,2})\s+(Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)', line, re.IGNORECASE)
                    if match_rango:
                        dia_inicio = int(match_rango.group(1))
                        mes_texto = match_rango.group(3).capitalize()
                        mes_jornada = mes_texto
                        
                        # Convertir mes texto a número
                        meses = {'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6,
                                'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12}
                        mes_num = meses.get(mes_texto, 1)
                        
                        # Ajustar año si es necesario (si estamos en dic y la jornada es ene del año siguiente)
                        if datetime.now().month == 12 and mes_num == 1:
                            year_jornada = datetime.now().year + 1
                        
                        fecha_inicio_jornada = datetime(year_jornada, mes_num, dia_inicio)
                        logger.debug(f"Fecha inicio jornada detectada: {fecha_inicio_jornada.strftime('%d/%m/%Y')}")
                        break
                
                # Detectar día de la semana en la página
                dia_actual = "Desconocido"
                dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                dia_semana_a_numero = {'Lunes': 0, 'Martes': 1, 'Miércoles': 2, 'Jueves': 3, 
                                      'Viernes': 4, 'Sábado': 5, 'Domingo': 6}
                
                # Buscar Valsequillo
                for i, line in enumerate(lines):
                    # Actualizar día si encontramos uno en la línea
                    for d in dias_semana:
                        # Verificamos que la línea sea principalmente el día
                        if d in line and len(line) < 40:
                            # Opción 1: Buscar fecha en la misma línea o siguientes
                            match_fecha = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', line)
                            
                            # 2. Si no está, buscar en las lineas SIGUIENTES (hasta 3)
                            if not match_fecha:
                                for offset in range(1, 4):
                                    if i + offset < len(lines):
                                        line_next = lines[i+offset]
                                        match_fecha = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', line_next)
                                        if match_fecha:
                                            break
                            
                            # Opción 2: Si NO encontramos fecha pero SÍ tenemos fecha_inicio_jornada, calcular
                            if not match_fecha and fecha_inicio_jornada:
                                dia_semana_num = dia_semana_a_numero.get(d)
                                if dia_semana_num is not None:
                                    # Calcular cuántos días hay desde fecha_inicio_jornada hasta este día
                                    dias_diferencia = (dia_semana_num - fecha_inicio_jornada.weekday()) % 7
                                    fecha_calculada = fecha_inicio_jornada + timedelta(days=dias_diferencia)
                                    dia_actual = f"{d} {fecha_calculada.strftime('%d/%m/%y')}"
                                    logger.debug(f"Fecha CALCULADA para {d}: {fecha_calculada.strftime('%d/%m/%y')}")
                                else:
                                    dia_actual = d
                                    logger.warning(f"Fecha NO detectada ni calculada para {d}")
                            elif match_fecha:
                                dia_actual = f"{d} {match_fecha.group(1)}" # Ej: "Viernes 16/01/26"
                                logger.debug(f"Fecha detectada para {d}: {match_fecha.group(1)}")
                            else:
                                dia_actual = d
                                logger.warning(f"Fecha NO detectada para día {d} (Usando solo nombre día)")
                            break

                    if "valsequillo" in line.lower():
                        logger.debug(f"Encontrado Valsequillo en línea {i}: {line}")
                        
                        # Es posible que sea el "Lugar" (IES Valsequillo)
                        # Si es Lugar, el partido ya debería haber sido procesado por el equipo, 
                        # pero si el equipo NO tiene "Valsequillo" en el nombre (raro), lo ignoramos.
                        # Generalmente queremos encontrar el EQUIPO Valsequillo.
                        # IES Valsequillo no tiene código (xxxx) al final.
                        es_equipo = bool(patron_codigo.search(line))
                        
                        if not es_equipo:
                            # Puede ser el lugar. Verificamos si ya procesamos este partido
                            # O simplemente lo ignoramos porque buscamos el nombre del equipo
                            continue

                        # Analizar contexto
                        categoria = "Desconocida"
                        local = "Desconocido"
                        visitante = "Desconocido"
                        lugar = "Desconocido"
                        hora = "00:00"
                        
                        # Mirar línea anterior y siguiente para decidir si somos Local o Visitante
                        linea_ant = lines[i-1] if i > 0 else ""
                        linea_sig = lines[i+1] if i < len(lines)-1 else ""
                        
                        es_local = False
                        
                        # Si la línea siguiente tiene código, entonces somos Local
                        if patron_codigo.search(linea_sig):
                            es_local = True
                            local = line
                            visitante = linea_sig
                            lugar = lines[i+2] if i < len(lines)-2 else "Desconocido"
                            categoria_raw = linea_ant
                        
                        # Si la línea anterior tiene código, entonces somos Visitante
                        elif patron_codigo.search(linea_ant):
                            es_local = False
                            local = linea_ant
                            visitante = line
                            lugar = linea_sig
                            categoria_raw = lines[i-2] if i > 1 else "Desconocido"
                            
                        else:
                            # Caso difícil. Asumir Local por defecto si no hay pistas
                            logger.warning(f"No se pudo determinar si es local o visitante: {line}")
                            local = line
                            visitante = linea_sig # Asumimos siguiente es rival
                            lugar = lines[i+2] if i < len(lines)-2 else "Desconocido"
                            categoria_raw = linea_ant

                        # Limpiar categoría y extraer hora
                        # A veces la categoría tiene basura pegada o la hora
                        # Buscar patrón de hora HH:MM
                        match_hora = re.search(r'(\d{2}:\d{2})', categoria_raw)
                        if match_hora:
                            hora = match_hora.group(1)
                            categoria = categoria_raw.replace(hora, "").strip()
                        else:
                            # Buscar hora en líneas muy cercanas hacia arriba (hasta 5 líneas)
                            for k in range(1, 6):
                                if i-k >= 0:
                                    possible_hora = lines[i-k]
                                    match_hora = re.search(r'(\d{2}:\d{2})', possible_hora)
                                    if match_hora:
                                        hora = match_hora.group(1)
                                        # Si encontramos la hora muy arriba, la categoría es probable que sea la línea justo encima del Local
                                        if categoria == "Desconocida":
                                            categoria = categoria_raw
                                        break
                            if categoria == "Desconocida":
                                categoria = categoria_raw

                        # Limpieza final
                        if len(categoria) > 50: categoria = categoria[:50] + "..."
                        
                        # Añadir partido
                        partido = {
                            'dia': dia_actual,
                            'hora': hora,
                            'categoria': categoria,
                            'local': local,
                            'visitante': visitante,
                            'lugar': lugar,
                            'origen': f"Página {num_pagina+1}"
                        }
                        
                        # Evitar duplicados (mismo equipo y hora)
                        clave = f"{dia_actual}_{hora}_{local}_{visitante}"
                        duplicado = False
                        for p in partidos:
                            k = f"{p['dia']}_{p['hora']}_{p['local']}_{p['visitante']}"
                            if k == clave:
                                duplicado = True
                                break
                        
                        if not duplicado:
                            partidos.append(partido)
                            logger.info(f"Partido encontrado: {local} vs {visitante} ({dia_actual} {hora})")

            return partidos
            
        except Exception as e:
            logger.error(f"Error al extraer partidos del PDF {pdf_path}: {e}")
            return []
    
    def _parsear_linea_tabla(self, line: str, dia: Optional[str]) -> Optional[Dict]:
        """
        Parsea una línea de formato tabular del PDF de FIBGC
        Formato: Nº Part | Hora | Categoría | Local | Visitante | Lugar
        Ejemplo: "78270 18:30 Junior Masc S-B Valsequillo (35008832) CB Telde (35002857) IES Valsequillo"
        
        Args:
            line: Línea de texto a parsear
            dia: Día de la semana del partido
            
        Returns:
            Diccionario con información del partido o None
        """
        try:
            # Buscar el patrón de hora (formato HH:MM)
            hora_match = re.search(r'\b(\d{1,2}:\d{2})\b', line)
            if not hora_match:
                return None
            
            hora = hora_match.group(1)
            hora_pos = hora_match.start()
            
            # Dividir la línea en partes basándose en la posición de la hora
            # Antes de la hora: Nº Partido
            # Después de la hora: Categoría | Local | Visitante | Lugar
            
            parte_despues_hora = line[hora_match.end():].strip()
            
            # Extraer categoría (siguiente palabra(s) después de la hora)
            # Patrones comunes: "Junior Masc S-B", "Sen Masc 2ª F G-B", "Cadete Femenino"
            categoria_match = re.match(r'^([A-Za-zª.\-\s]+(?:Masc|Fem|Masculino|Femenino|S-[AB]|G-[AB]|F\s*G-[AB]))', parte_despues_hora, re.I)
            
            if categoria_match:
                categoria = categoria_match.group(1).strip()
                despues_categoria = parte_despues_hora[categoria_match.end():].strip()
            else:
                categoria = "Sin especificar"
                despues_categoria = parte_despues_hora
            
            # Ahora debemos separar: Local | Visitante | Lugar
            # Los equipos suelen tener códigos entre paréntesis, ej: "(35008832)"
            # Eliminar códigos para facilitar el parseo
            linea_sin_codigos = re.sub(r'\([0-9]+\)', '', despues_categoria)
            
            # Buscar el lugar (última parte, suele ser "Pab...", "IES...", "Col...", "Pol...", etc.)
            lugar_match = re.search(r'\b((?:Pab|IES|Col|Pol|CEIP|Comp\s*Dep|Inst\s*Dep|Obispo|Canterbury|Rodriguez|Pabel)[^\d]*?)$', linea_sin_codigos, re.I)
            
            if lugar_match:
                lugar = lugar_match.group(1).strip()
                # Remover el lugar de la línea
                linea_equipos = linea_sin_codigos[:lugar_match.start()].strip()
            else:
                lugar = "Sin especificar"
                linea_equipos = linea_sin_codigos
            
            # Separar local y visitante
            # Intentar split por múltiples espacios o patrones comunes
            equipos_partes = re.split(r'\s{2,}', linea_equipos.strip())
            
            if len(equipos_partes) >= 2:
                local = equipos_partes[0].strip()
                visitante = equipos_partes[1].strip()
            elif len(equipos_partes) == 1:
                # Intentar split por palabras clave o conteo de palabras
                palabras = linea_equipos.split()
                mitad = len(palabras) // 2
                local = ' '.join(palabras[:mitad]).strip()
                visitante = ' '.join(palabras[mitad:]).strip()
            else:
                local = "Sin especificar"
                visitante = "Sin especificar"
            
            # Limpiar nombres de equipos (eliminar símbolos extraños, múltiples espacios)
            local = re.sub(r'\s+', ' ', local).strip()
            visitante = re.sub(r'\s+', ' ', visitante).strip()
            local = re.sub(r'[&*]+$', '', local).strip()
            visitante = re.sub(r'[&*]+$', '', visitante).strip()
            
            partido = {
                'dia': dia if dia else 'Sin especificar',
                'hora': hora,
                'categoria': categoria,
                'local': local,
                'visitante': visitante,
                'lugar': lugar
            }
            
            return partido
            
        except Exception as e:
            logger.warning(f"Error al parsear línea tabla: {e} | Línea: {line}")
            return None
    
    def _parsear_linea_partido(self, line: str, dia: Optional[str], 
                               all_lines: List[str], line_idx: int) -> Optional[Dict]:
        """
        Parsea una línea que contiene información de un partido
        
        Args:
            line: Línea de texto a parsear
            dia: Día de la semana del partido
            all_lines: Todas las líneas del documento
            line_idx: Índice de la línea actual
            
        Returns:
            Diccionario con información del partido o None
        """
        try:
            # Patrón para hora (ej: "18:30", "19:00")
            hora_match = re.search(r'\b(\d{1,2}:\d{2})\b', line)
            
            # Intentar extraer información con diferentes estrategias
            # Estrategia 1: Línea completa con formato tabular
            # Formato esperado: N.Part | Hora | Categoría | Local | Visitante | Lugar
            
            partido = {
                'dia': dia if dia else 'Sin especificar',
                'hora': hora_match.group(1) if hora_match else 'Sin especificar',
                'categoria': self._extraer_categoria(line, all_lines, line_idx),
                'local': '',
                'visitante': '',
                'lugar': self._extraer_lugar(line, all_lines, line_idx)
            }
            
            # Identificar cuál equipo es Valsequillo y cuál es el rival
            palabras = line.split()
            valsequillo_idx = -1
            for i, palabra in enumerate(palabras):
                if 'valsequillo' in palabra.lower():
                    valsequillo_idx = i
                    break
            
            if valsequillo_idx >= 0:
                # Intentar determinar local y visitante
                # Suele haber formato: "Equipo1 - Equipo2" o "Equipo1 vs Equipo2"
                if ' - ' in line or ' vs ' in line:
                    separador = ' - ' if ' - ' in line else ' vs '
                    partes = line.split(separador)
                    if len(partes) >= 2:
                        partido['local'] = partes[0].strip()
                        partido['visitante'] = partes[1].strip()
                else:
                    # Extraer los equipos basándose en la posición de Valsequillo
                    # Esto es heurístico y puede necesitar ajuste según el formato real
                    partido['local'] = 'Valsequillo' if valsequillo_idx < len(palabras) / 2 else self._extraer_equipo(line, excluir='valsequillo')
                    partido['visitante'] = self._extraer_equipo(line, excluir='valsequillo') if valsequillo_idx < len(palabras) / 2 else 'Valsequillo'
            
            # Validar que tengamos información mínima
            if partido['hora'] != 'Sin especificar' or \
               partido['local'] or partido['visitante']:
                return partido
            
            return None
            
        except Exception as e:
            logger.warning(f"Error al parsear línea: {e}")
            return None
    
    def _extraer_categoria(self, line: str, all_lines: List[str], line_idx: int) -> str:
        """Extrae la categoría del partido"""
        # Buscar patrones comunes de categoría
        categorias_comunes = [
            r'senior', r'junior', r'cadete', r'infantil', r'alevín', 
            r'benjamín', r'minibasket', r'masculin[oa]', r'femenin[oa]',
            r'\bsm\b', r'\bsf\b', r'\bjm\b', r'\bjf\b'
        ]
        
        for patron in categorias_comunes:
            match = re.search(patron, line, re.I)
            if match:
                return match.group(0)
        
        # Buscar en líneas cercanas
        for offset in [-1, 1, -2, 2]:
            idx = line_idx + offset
            if 0 <= idx < len(all_lines):
                for patron in categorias_comunes:
                    match = re.search(patron, all_lines[idx], re.I)
                    if match:
                        return match.group(0)
        
        return 'Sin especificar'
    
    def _extraer_lugar(self, line: str, all_lines: List[str], line_idx: int) -> str:
        """Extrae el lugar/pabellón del partido"""
        # Buscar patrones de lugar
        lugar_patterns = [
            r'pabellon\s+[\w\s]+',
            r'polideportivo\s+[\w\s]+',
            r'instalaciones\s+[\w\s]+'
        ]
        
        for patron in lugar_patterns:
            match = re.search(patron, line, re.I)
            if match:
                return match.group(0).strip()
        
        # Si no se encuentra en la línea actual, buscar en las cercanas
        for offset in [1, 2, -1]:
            idx = line_idx + offset
            if 0 <= idx < len(all_lines):
                for patron in lugar_patterns:
                    match = re.search(patron, all_lines[idx], re.I)
                    if match:
                        return match.group(0).strip()
        
        return 'Sin especificar'
    
    def _extraer_equipo(self, line: str, excluir: str = '') -> str:
        """Extrae el nombre del equipo rival (que no sea Valsequillo)"""
        # Eliminar números, horas, y palabras comunes
        palabras_ignorar = ['vs', 'contra', 'vs.', '-', 'pabellón', 'polideportivo']
        
        palabras = line.split()
        equipo_palabras = []
        
        for palabra in palabras:
            palabra_lower = palabra.lower()
            if excluir and excluir in palabra_lower:
                continue
            if palabra_lower in palabras_ignorar:
                continue
            if re.match(r'^\d+:\d+$', palabra):  # Hora
                continue
            if re.match(r'^\d+$', palabra):  # Números sueltos
                continue
            
            equipo_palabras.append(palabra)
        
        return ' '.join(equipo_palabras[:3]) if equipo_palabras else 'Sin especificar'
    
    def generar_excel(self, partidos: List[Dict], nombre_archivo: str = None) -> Path:
        """
        Genera un archivo Excel con los partidos filtrados
        
        Args:
            partidos: Lista de partidos
            nombre_archivo: Nombre del archivo (opcional)
            
        Returns:
            Path al archivo Excel generado
        """
        try:
            if not nombre_archivo:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nombre_archivo = f"partidos_valsequillo_{timestamp}.xlsx"
            
            # Crear DataFrame
            df = pd.DataFrame(partidos)
            
            # Asegurar que existan las columnas esperadas y en el orden correcto
            # Si existe jornada_tipo, incluirla
            columnas = ['dia', 'hora', 'categoria', 'local', 'visitante', 'lugar']
            nombres_columnas = ['Día', 'Hora', 'Categoría', 'Equipo Local', 'Equipo Visitante', 'Pabellón/Lugar']
            
            if 'jornada_tipo' in df.columns:
                columnas.insert(0, 'jornada_tipo')
                nombres_columnas.insert(0, 'Tipo Jornada')
            
            # Seleccionar y reordenar columnas
            df = df[columnas]
            df.columns = nombres_columnas
            
            # Guardar a Excel
            excel_path = Path(nombre_archivo)
            df.to_excel(excel_path, index=False, engine='openpyxl')
            
            logger.info(f"Excel generado exitosamente: {excel_path}")
            logger.info(f"Total de partidos exportados: {len(partidos)}")
            
            return excel_path
            
        except Exception as e:
            logger.error(f"Error al generar Excel: {e}")
            raise
    
    def generar_pdf(self, partidos: List[Dict], tipo_jornada: str = "") -> Path:
        """
        Genera un archivo PDF con los partidos filtrados
        
        Args:
            partidos: Lista de partidos
            tipo_jornada: Tipo de jornada (DEFINITIVA o PROVISIONAL) para el nombre del archivo
            
        Returns:
            Path al archivo PDF generado
        """
        try:
            now = datetime.now()
            # Nombre del archivo incluye el tipo si se especifica
            sufijo_tipo = f"_{tipo_jornada}" if tipo_jornada else ""
            nombre_archivo = f"PARTIDOS_VALSEQUILLO{sufijo_tipo}_{now.strftime('%d_%m')}.pdf"
            pdf_path = Path(nombre_archivo)
            
            # Crear el documento PDF en orientación horizontal (landscape)
            doc = SimpleDocTemplate(
                str(pdf_path),
                pagesize=landscape(A4),
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Contenedor de elementos
            elements = []
            
            # Colores corporativos del CB Valsequillo
            verde_valsequillo = colors.HexColor('#2D8B3C')  # Verde corporativo
            negro_valsequillo = colors.HexColor('#1A1A1A')  # Negro corporativo
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=verde_valsequillo,  # Verde corporativo
                spaceAfter=10,
                alignment=1,  # Centrado
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#555555'),
                spaceAfter=20,
                alignment=1  # Centrado
            )
            
            # Estilos para celdas
            cell_style = ParagraphStyle(
                'CellText',
                parent=styles['Normal'],
                fontSize=9,
                leading=11,
                wordWrap='LTR'
            )
            
            cell_valsequillo_style = ParagraphStyle(
                'CellValsequillo',
                parent=styles['Normal'],
                fontSize=9,
                leading=11,
                textColor=verde_valsequillo,  # Verde corporativo
                fontName='Helvetica-Bold',
                wordWrap='LTR'
            )
            
            # Logo del club (si existe) - Mejorado con mejor calidad y centrado
            # Primero intenta usar la versión HQ, si no existe usa la original
            logo_path = Path('logo_valsequillo_hq.png')
            if not logo_path.exists():
                logo_path = Path('logo_valsequillo.png')
                
            if logo_path.exists():
                try:
                    # Usar tamaño más grande y mantener proporción (logo es casi cuadrado)
                    logo_img = Image(str(logo_path), width=4*cm, height=4*cm, kind='proportional')
                    logo_img.hAlign = 'CENTER'  # Centrar horizontalmente
                    
                    # Crear una tabla de 1 celda solo para centrar el logo
                    logo_table = Table([[logo_img]], colWidths=[landscape(A4)[0] - 3*cm])
                    logo_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                    ]))
                    
                    elements.append(logo_table)
                    elements.append(Spacer(1, 0.4*cm))
                except Exception as e:
                    logger.warning(f"No se pudo cargar el logo: {e}")
            
            # Título
            titulo_texto = f"PARTIDOS DE VALSEQUILLO {tipo_jornada}" if tipo_jornada else "PARTIDOS DE VALSEQUILLO"
            title = Paragraph(titulo_texto, title_style)
            elements.append(title)
            
            # Subtítulo con fecha de generación
            # Contar cuántos son definitivas y cuántos provisionales
            definitivas_count = sum(1 for p in partidos if p.get('jornada_tipo') == 'DEFINITIVA')
            provisionales_count = sum(1 for p in partidos if p.get('jornada_tipo') == 'PROVISIONAL')
            
            tipos_texto = []
            if definitivas_count > 0:
                tipos_texto.append(f"{definitivas_count} definitiva{'s' if definitivas_count > 1 else ''}")
            if provisionales_count > 0:
                tipos_texto.append(f"{provisionales_count} provisional{'es' if provisionales_count > 1 else ''}")
            
            jornadas_info = " + ".join(tipos_texto) if tipos_texto else "Jornadas"
            
            subtitle = Paragraph(
                f"{jornadas_info} - Generado el {now.strftime('%d/%m/%Y a las %H:%M')}",
                subtitle_style
            )
            elements.append(subtitle)
            elements.append(Spacer(1, 0.3*cm))
            
            # Preparar datos para la tabla con Paragraphs para word wrap
            # Encabezados
            header_style = ParagraphStyle(
                'Header',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.whitesmoke,
                fontName='Helvetica-Bold',
                alignment=1,
                leading=12
            )
            
            data = [[
                Paragraph('Día', header_style),
                Paragraph('Hora', header_style),
                Paragraph('Categoría', header_style),
                Paragraph('Equipo Local', header_style),
                Paragraph('Equipo Visitante', header_style),
                Paragraph('Pabellón/Lugar', header_style)
            ]]
            
            # Datos de partidos usando Paragraph para permitir word wrap
            for partido in partidos:
                # Determinar si es Valsequillo y aplicar estilo
                local_es_valsequillo = 'valsequillo' in partido['local'].lower()
                visitante_es_valsequillo = 'valsequillo' in partido['visitante'].lower()
                
                local_style = cell_valsequillo_style if local_es_valsequillo else cell_style
                visitante_style = cell_valsequillo_style if visitante_es_valsequillo else cell_style
                
                row = [
                    Paragraph(partido['dia'], cell_style),
                    Paragraph(partido['hora'], cell_style),
                    Paragraph(partido['categoria'], cell_style),
                    Paragraph(partido['local'], local_style),
                    Paragraph(partido['visitante'], visitante_style),
                    Paragraph(partido['lugar'], cell_style)
                ]
                data.append(row)
            
            # Crear tabla con anchos ajustados
            table = Table(data, colWidths=[
                3.2*cm,   # Día
                1.5*cm,   # Hora
                3.2*cm,   # Categoría
                5.5*cm,   # Equipo Local
                5.5*cm,   # Equipo Visitante
                4.5*cm    # Pabellón/Lugar
            ])
            
            # Estilo de la tabla
            table.setStyle(TableStyle([
                # Encabezado con color corporativo verde
                ('BACKGROUND', (0, 0), (-1, 0), verde_valsequillo),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                
                # Datos
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (1, -1), 'CENTER'),  # Día y Hora centrados
                ('ALIGN', (2, 1), (-1, -1), 'LEFT'),   # Resto alineado a izquierda
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('LEFTPADDING', (0, 1), (-1, -1), 5),
                ('RIGHTPADDING', (0, 1), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alineación vertical al centro
                
                # Bordes y líneas
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 2, verde_valsequillo),  # Línea verde corporativa
                
                # Alternar colores de filas
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
            ]))
            
            elements.append(table)
            
            # Pie de página con información
            elements.append(Spacer(1, 0.8*cm))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                alignment=1
            )
            footer = Paragraph(
                f"<b>Total de partidos: {len(partidos)}</b> | Federación Insular de Baloncesto de Gran Canaria",
                footer_style
            )
            elements.append(footer)
            
            # Construir PDF
            doc.build(elements)
            
            logger.info(f"PDF generado exitosamente: {pdf_path}")
            logger.info(f"Total de partidos exportados a PDF: {len(partidos)}")
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error al generar PDF: {e}")
            raise

    def generar_calendario(self, partidos: List[Dict], tipo_jornada: str = "") -> Optional[Path]:
        """
        Genera un archivo de calendario (.ics) para importar en móviles/Outlook
        """
        try:
            c = Calendar()
            c.creator = "CB Valsequillo Scraper <scraper@valsequillo.com>"
            count = 0
            
            for p in partidos:
                # Intentar construir fecha y hora de inicio
                fecha_str = p.get('dia', '')
                hora_str = p.get('hora', '00:00')
                
                # Extraer DD/MM/YY de "Viernes 16/01/26"
                match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', fecha_str)
                if match:
                    fecha_pura = match.group(1)
                    # Normalizar año (si viene 26 convertir a 2026)
                    partes = fecha_pura.split('/')
                    if len(partes[2]) == 2:
                        partes[2] = "20" + partes[2]
                        fecha_pura = "/".join(partes)
                    
                    fecha_hora_str = f"{fecha_pura} {hora_str}"
                    try:
                        # Parsear fecha
                        # Convertir a datetime con zona horaria de Canarias
                        inicio_naive = datetime.strptime(fecha_hora_str, "%d/%m/%Y %H:%M")
                        inicio = inicio_naive.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                        
                        # Crear Evento
                        e = Event()
                        e.name = f"🏀 {p['local']} vs {p['visitante']}"
                        e.begin = inicio
                        e.duration = timedelta(hours=1, minutes=45) # Duración estimada partido
                        e.location = p['lugar']
                        e.description = f"Categoría: {p['categoria']}\nJornada: {tipo_jornada}\nOrigen: {p.get('origen','')}"
                        # Añadir UID único (importante para iOS)
                        e.uid = f"{inicio.strftime('%Y%m%d%H%M')}-{p['local'][:10].replace(' ', '')}-valsequillo@scraper.local"
                        
                        # Añadir ALERTAS/RECORDATORIOS
                        # Recordatorio 1 día antes
                        e.alarms.append(DisplayAlarm(trigger=timedelta(days=-1), display_text="🏀 Partido mañana!"))
                        # Recordatorio 2 horas antes
                        e.alarms.append(DisplayAlarm(trigger=timedelta(hours=-2), display_text="🏀 Partido en 2 horas"))
                        
                        c.events.add(e)
                        count += 1
                        logger.debug(f"Evento añadido al calendario: {e.name} ({fecha_hora_str})")
                        
                    except ValueError as ve:
                        logger.warning(f"Error de valor al crear evento calendario: {ve}")
                        continue
                    except Exception as ex:
                        logger.error(f"Error inesperado al crear evento: {ex}")
                        continue
                else:
                    logger.warning(f"CALENDARIO: Partido sin fecha exacta (solo '{fecha_str}'), se omite: {p['local']}")
            
            if count > 0:
                sufijo_tipo = f"_{tipo_jornada}" if tipo_jornada else ""
                now = datetime.now()
                nombre_archivo = f"PARTIDOS_VALSEQUILLO{sufijo_tipo}_{now.strftime('%d_%m')}.ics"
                path_ics = Path(nombre_archivo)
                
                with open(path_ics, 'w', encoding='utf-8') as f:
                    f.writelines(c.serialize_iter())
                
                logger.info(f"Calendario generado con {count} eventos: {path_ics}")
                return path_ics
            
            return None

        except Exception as e:
            logger.error(f"Error generando calendario: {e}")
            return None
    
    def generar_preview_email(self, partidos_definitivos: List[Dict], partidos_provisionales: List[Dict], cambios: List[Dict] = None) -> Optional[Path]:
        """
        Genera un preview HTML de los partidos para incluir en el email
        """
        try:
            html = """
            <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
                <h2 style="color: #2D8B3C; border-bottom: 3px solid #2D8B3C; padding-bottom: 10px;">
                    🏀 Próximos Partidos de Valsequillo
                </h2>
            """
            
            # Mostrar cambios si hay
            if cambios:
                html += f"""
                <div style="background-color: #fff3cd; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0;">
                    <h3 style="color: #ff6f00; margin-top: 0;">⚠️ CAMBIOS DETECTADOS ({len(cambios)})</h3>
                    <p style="margin: 5px 0;">La federación ha modificado estos partidos desde la última vez:</p>
                    <ul style="margin: 10px 0;">
                """
                for cambio in cambios:
                    html += f"<li><strong>{cambio['local']} vs {cambio['visitante']}</strong><br>"
                    for c in cambio['cambios']:
                        html += f"&nbsp;&nbsp;• {c}<br>"
                    html += "</li>"
                html += """
                    </ul>
                    <p style="color: #666; font-size: 12px; margin-top: 10px;">Actualiza tu calendario con el nuevo archivo .ics adjunto.</p>
                </div>
                """
            
            # Función auxiliar para generar tabla
            def generar_tabla(partidos, titulo, color):
                if not partidos:
                    return ""
                
                tabla_html = f"""
                <h3 style="color: {color}; margin-top: 20px;">{titulo}</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background-color: {color}; color: white;">
                            <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Día/Hora</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Categoría</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Partido</th>
                            <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Lugar</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for p in partidos:
                    # Resaltar si jugamos en casa
                    estilo_fila = ""
                    if "valsequillo" in p['local'].lower():
                        estilo_fila = "background-color: #e8f5e9;"  # Verde claro
                        icono_casa = "🏠 "
                    else:
                        icono_casa = "✈️ "
                    
                    tabla_html += f"""
                    <tr style="{estilo_fila}">
                        <td style="padding: 8px; border: 1px solid #ddd;">{icono_casa}<strong>{p['dia']}</strong><br>{p['hora']}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">{p['categoria']}</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">
                            <strong>{p['local']}</strong><br>
                            vs<br>
                            <strong>{p['visitante']}</strong>
                        </td>
                        <td style="padding: 8px; border: 1px solid #ddd; font-size: 12px;">{p['lugar']}</td>
                    </tr>
                    """
                
                tabla_html += """
                    </tbody>
                </table>
                """
                return tabla_html
            
            # Añadir tabla definitivos
            html += generar_tabla(partidos_definitivos, "📋 Jornada Definitiva", "#2D8B3C")
            
            # Añadir tabla provisionales
            html += generar_tabla(partidos_provisionales, "📝 Jornada Provisional", "#FF9800")
            
            html += """
                <p style="color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px;">
                    💡 <strong>Leyenda:</strong><br>
                    🏠 = Partido en casa (Valsequillo juega como local)<br>
                    ✈️ = Partido fuera (Valsequillo visita)<br><br>
                    📎 Descarga el calendario (.ics) adjunto para añadir estos partidos a tu móvil automáticamente.
                </p>
            </div>
            """
            
            # Guardar a archivo
            preview_path = Path("email_preview.html")
            preview_path.write_text(html, encoding='utf-8')
            logger.info(f"Preview de email generado: {preview_path}")
            
            return preview_path
            
        except Exception as e:
            logger.error(f"Error generando preview de email: {e}")
            return None
    
    def detectar_cambios(self, partidos_actuales: List[Dict]) -> List[Dict]:
        """
        Compara los partidos actuales con los de la semana anterior.
        Detecta cambios en fecha, hora o lugar.
        
        Returns:
            Lista de cambios detectados
        """
        cambios = []
        snapshot_path = Path("partidos_anteriores.json")
        
        try:
            # Leer snapshot anterior
            partidos_anteriores = []
            if snapshot_path.exists():
                import json
                with open(snapshot_path, 'r', encoding='utf-8') as f:
                    partidos_anteriores = json.load(f)
            
            # Crear diccionario de partidos anteriores por clave única
            # Clave: "LOCAL vs VISITANTE - CATEGORIA"
            partidos_ant_dict = {}
            for p in partidos_anteriores:
                clave = f"{p['local']} vs {p['visitante']} - {p['categoria']}"
                partidos_ant_dict[clave] = p
            
            # Comparar con actuales
            for p_actual in partidos_actuales:
                clave = f"{p_actual['local']} vs {p_actual['visitante']} - {p_actual['categoria']}"
                
                if clave in partidos_ant_dict:
                    p_anterior = partidos_ant_dict[clave]
                    
                    # Verificar cambios
                    cambios_partido = []
                    
                    if p_actual['dia'] != p_anterior['dia']:
                        cambios_partido.append(f"Día: {p_anterior['dia']} → {p_actual['dia']}")
                    
                    if p_actual['hora'] != p_anterior['hora']:
                        cambios_partido.append(f"Hora: {p_anterior['hora']} → {p_actual['hora']}")
                    
                    if p_actual['lugar'] != p_anterior['lugar']:
                        cambios_partido.append(f"Lugar: {p_anterior['lugar']} → {p_actual['lugar']}")
                    
                    if cambios_partido:
                        cambios.append({
                            'partido': clave,
                            'local': p_actual['local'],
                            'visitante': p_actual['visitante'],
                            'cambios': cambios_partido
                        })
            
            # Guardar snapshot actual para la próxima vez
            import json
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(partidos_actuales, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Cambios detectados: {len(cambios)}")
            return cambios
            
        except Exception as e:
            logger.error(f"Error detectando cambios: {e}")
            return []
    
    def sincronizar_google_calendar(self, partidos: List[Dict]) -> bool:
        """
        Sincroniza los partidos con Google Calendar compartido.
        Requiere variables de entorno:
        - GOOGLE_CALENDAR_ID
        - GOOGLE_CREDENTIALS_JSON
        
        Returns:
            True si tuvo éxito, False si falló
        """
        try:
            import os
            import json
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # Leer variables de entorno
            calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            
            if not calendar_id or not creds_json:
                logger.info("Google Calendar no configurado (variables de entorno faltantes). Saltando sincronización.")
                return False
            
            # Autenticar
            credentials_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # 1. Limpiar eventos antiguos (partidos ya jugados)
            now = datetime.now(ZoneInfo("Atlantic/Canary")).isoformat()
            
            # Listar eventos futuros con nuestro marcador
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime',
                q='CB Valsequillo'  # Buscar solo nuestros eventos
            ).execute()
            
            existing_events = events_result.get('items', [])
            
            # Borrar todos los eventos existentes (para reemplazarlos con los actualizados)
            for event in existing_events:
                try:
                    service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
                    logger.debug(f"Evento eliminado: {event.get('summary', 'Sin título')}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar evento: {e}")
            
            # 2. Añadir nuevos eventos
            count = 0
            for p in partidos:
                # Parsear fecha y hora
                fecha_str = p.get('dia', '')
                hora_str = p.get('hora', '00:00')
                
                match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', fecha_str)
                if match:
                    fecha_pura = match.group(1)
                    partes = fecha_pura.split('/')
                    if len(partes[2]) == 2:
                        partes[2] = "20" + partes[2]
                        fecha_pura = "/".join(partes)
                    
                    fecha_hora_str = f"{fecha_pura} {hora_str}"
                    try:
                        inicio_naive = datetime.strptime(fecha_hora_str, "%d/%m/%Y %H:%M")
                        inicio = inicio_naive.replace(tzinfo=ZoneInfo("Atlantic/Canary"))
                        
                        # Crear evento
                        event = {
                            'summary': f"🏀 {p['local']} vs {p['visitante']}",
                            'location': p['lugar'],
                            'description': f"Categoría: {p['categoria']}\nCompetición: CB Valsequillo\n\nCalendario actualizado automáticamente cada lunes.",
                            'start': {
                                'dateTime': inicio.isoformat(),
                                'timeZone': 'Atlantic/Canary',
                            },
                            'end': {
                                'dateTime': (inicio + timedelta(hours=1, minutes=45)).isoformat(),
                                'timeZone': 'Atlantic/Canary',
                            },
                            'reminders': {
                                'useDefault': False,
                                'overrides': [
                                    {'method': 'popup', 'minutes': 24 * 60},  # 1 día antes
                                    {'method': 'popup', 'minutes': 120},       # 2 horas antes
                                ],
                            },
                        }
                        
                        service.events().insert(calendarId=calendar_id, body=event).execute()
                        count += 1
                        logger.debug(f"Evento añadido a Google Calendar: {event['summary']}")
                        
                    except ValueError as ve:
                        logger.warning(f"Error parseando fecha para Google Calendar: {ve}")
                        continue
            
            logger.info(f"✅ Google Calendar sincronizado: {count} eventos añadidos")
            return True
            
        except Exception as e:
            logger.error(f"Error sincronizando con Google Calendar: {e}")
            return False
    
    def ejecutar(self) -> List[Path]:
        """
        Ejecuta el proceso completo: descarga múltiples jornadas, extracción y generación de PDFs independientes
        
        Returns:
            Lista de paths de los archivos PDF generados
        """
        logger.info("=== Iniciando proceso de extracción de partidos ===")
        
        # 1. Descargar PDFs recientes (definitivas y provisionales)
        pdfs_descargados = self.descargar_pdfs_recientes()
        if not pdfs_descargados:
            logger.error("No se pudo descargar ningún PDF")
            return []
        
        # 2. Extraer partidos de TODOS los PDFs
        todos_los_partidos = []
        for pdf_info in pdfs_descargados:
            pdf_path = pdf_info['path']
            tipo = pdf_info['tipo']
            logger.info(f"Procesando {tipo}: {pdf_path}")
            
            partidos = self.extraer_partidos_pdf(pdf_path)
            
            # Marcar los partidos con el tipo de jornada
            for partido in partidos:
                partido['jornada_tipo'] = tipo
            
            todos_los_partidos.extend(partidos)
        
        if not todos_los_partidos:
            logger.warning("No se encontraron partidos de Valsequillo en ninguna jornada")
            return []
        
        logger.info(f"Total de partidos de Valsequillo encontrados: {len(todos_los_partidos)}")
        
        # 3. Generar Excel con todos los partidos (para tener un registro completo)
        excel_path = self.generar_excel(todos_los_partidos)
        logger.info(f"Archivo Excel global: {excel_path}")
        
        # 3.5. Detectar cambios respecto a la semana anterior
        cambios_detectados = self.detectar_cambios(todos_los_partidos)
        if cambios_detectados:
            logger.warning(f"⚠️ Se detectaron {len(cambios_detectados)} cambios en partidos!")
            for cambio in cambios_detectados:
                logger.warning(f"  - {cambio['partido']}: {', '.join(cambio['cambios'])}")
        
        # 4. Separar y generar PDFs independientes
        pdfs_generados = []
        
        # Filtrar por tipo
        partidos_definitivos = [p for p in todos_los_partidos if p.get('jornada_tipo') == 'DEFINITIVA']
        partidos_provisionales = [p for p in todos_los_partidos if p.get('jornada_tipo') == 'PROVISIONAL']
        
        # Generar PDF Definitiva
        if partidos_definitivos:
            logger.info(f"Generando PDF Definitiva ({len(partidos_definitivos)} partidos)...")
            pdf_def = self.generar_pdf(partidos_definitivos, "DEFINITIVA")
            pdfs_generados.append(pdf_def)
            logger.info(f" PDF Definitiva: {pdf_def}")
            
            # Generar Calendario Definitiva
            ics_def = self.generar_calendario(partidos_definitivos, "DEFINITIVA")
            if ics_def: 
                pdfs_generados.append(ics_def)
                logger.info(f" ICS Calendario: {ics_def}")
        
        # Generar PDF Provisional
        if partidos_provisionales:
            logger.info(f"Generando PDF Provisional ({len(partidos_provisionales)} partidos)...")
            pdf_prov = self.generar_pdf(partidos_provisionales, "PROVISIONAL")
            pdfs_generados.append(pdf_prov)
            logger.info(f" PDF Provisional: {pdf_prov}")
            
            # Generar Calendario Provisional
            ics_prov = self.generar_calendario(partidos_provisionales, "PROVISIONAL")
            if ics_prov: 
                pdfs_generados.append(ics_prov)
                logger.info(f" ICS Calendario: {ics_prov}")
            
        # 4.5. Sincronizar con Google Calendar (solo partidos DEFINITIVOS)
        if partidos_definitivos:
            self.sincronizar_google_calendar(partidos_definitivos)
        
        # 5. Generar preview HTML para el email (incluyendo cambios si los hay)
        preview_email = self.generar_preview_email(partidos_definitivos, partidos_provisionales, cambios_detectados)
        if preview_email:
            pdfs_generados.append(preview_email)
            
        logger.info("=== Proceso completado exitosamente ===")
        
        return pdfs_generados


def main():
    """Función principal"""
    try:
        scraper = ScraperBaloncesto()
        pdfs_generados = scraper.ejecutar()
        
        if pdfs_generados:
            print(f"\n✅ ¡Éxito! Se generaron {len(pdfs_generados)} archivos PDF:")
            for pdf in pdfs_generados:
                print(f"   📄 {pdf}")
            print(f"   (También se generó un archivo Excel global)")
        else:
            print("\n❌ No se pudo completar el proceso")
            
    except Exception as e:
        logger.error(f"Error en la ejecución: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
