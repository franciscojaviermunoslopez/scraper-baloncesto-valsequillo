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
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Optional
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScraperBaloncesto:
    """Scraper para extraer partidos de baloncesto de Valsequillo"""
    
    def __init__(self, url_base: str = "https://www.fibgrancanaria.com"):
        self.url_base = url_base
        self.url_jornadas = "https://www.fibgrancanaria.com/index.php/competicion/hojas-de-jornada"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def descargar_ultimo_pdf(self) -> Optional[Path]:
        """
        Accede a la página de hojas de jornada y descarga el PDF más reciente
        
        Returns:
            Path al archivo PDF descargado o None si falla
        """
        try:
            logger.info(f"Accediendo a {self.url_jornadas}")
            response = self.session.get(self.url_jornadas, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar enlaces de descarga usando el patrón de Phoca Download
            # Los enlaces tienen el formato: ?download=ID:nombre-archivo
            download_link = None
            
            # Buscar todos los enlaces que contengan el parámetro '?download='
            download_links = soup.find_all('a', href=re.compile(r'\?download=', re.I))
            
            if download_links:
                # Filtrar para obtener solo jornadas definitivas (más confiables)
                definitivas = [
                    link for link in download_links 
                    if 'definitiva' in link.get_text().lower()
                ]
                
                # Si hay definitivas, usar la primera; si no, usar el primer enlace disponible
                selected_link = definitivas[0] if definitivas else download_links[0]
                download_link = selected_link.get('href')
                titulo = selected_link.get_text().strip()
                
                logger.info(f"PDF seleccionado: {titulo}")
                logger.info(f"Enlace de descarga: {download_link}")
            
            if not download_link:
                logger.error("No se encontró ningún enlace de descarga en la página")
                return None
            
            # Normalizar URL
            if not download_link.startswith('http'):
                download_link = f"{self.url_base}{download_link}" if download_link.startswith('/') else f"{self.url_base}/{download_link}"
            
            # Descargar el PDF
            logger.info(f"Descargando PDF desde: {download_link}")
            pdf_response = self.session.get(download_link, timeout=30)
            pdf_response.raise_for_status()
            
            # Guardar el PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_path = Path(f"jornada_{timestamp}.pdf")
            pdf_path.write_bytes(pdf_response.content)
            
            logger.info(f"PDF descargado exitosamente: {pdf_path}")
            return pdf_path
            
        except requests.RequestException as e:
            logger.error(f"Error al descargar el PDF: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return None
    
    def extraer_partidos_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Extrae información de partidos del PDF usando PyMuPDF
        El PDF tiene formato multi-línea donde cada partido ocupa 4 líneas:
        Línea 1: Nº Part + Hora + Categoría
        Línea 2: Equipo Local (con código)
        Línea 3: Equipo Visitante (con código)
        Línea 4: Lugar
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Lista de diccionarios con información de partidos
        """
        partidos = []
        partidos_unicos = set()  # Para evitar duplicados
        dia_actual = None
        
        try:
            logger.info(f"Procesando PDF: {pdf_path}")
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Dividir en líneas
                lines = [line.strip() for line in text.split('\n')]
                
                # Días de la semana para detectar
                dias_semana = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
                
                i = 0
                while i < len(lines):
                    line = lines[i]
                    
                    if not line:
                        i += 1
                        continue
                    
                    # Detectar encabezados de día
                    line_lower = line.lower()
                    for dia in dias_semana:
                        if line_lower.startswith(dia) or (dia in line_lower and len(line) < 50):
                            # Verificar si no es parte de un partido
                            if not re.search(r'\d{1,2}:\d{2}', line):
                                dia_actual = line
                                logger.info(f"Día detectado: {dia_actual}")
                                break
                    
                    # Verificar si la línea actual o las siguientes 3 contienen "Valsequillo"
                    siguiente_4_lineas = lines[i:i+4]
                    contiene_valsequillo = any('valsequillo' in l.lower() for l in siguiente_4_lineas)
                    
                    if contiene_valsequillo:
                        # Intentar reconstruir el partido desde las próximas líneas
                        partido = self._parsear_partido_multilinea(lines, i, dia_actual)
                        if partido:
                            # Crear clave única para evitar duplicados (hora + local + visitante)
                            clave_unica = (partido['hora'], partido['local'].lower(), partido['visitante'].lower())
                            
                            if clave_unica not in partidos_unicos:
                                partidos.append(partido)
                                partidos_unicos.add(clave_unica)
                                logger.info(f"Partido encontrado: {partido}")
                            else:
                                logger.debug(f"Partido duplicado omitido: {partido}")
                            
                            i += 4  # Saltar las líneas ya procesadas
                            continue
                    
                    i += 1
            
            doc.close()
            logger.info(f"Total de partidos de Valsequillo encontrados: {len(partidos)}")
            return partidos
            
        except Exception as e:
            logger.error(f"Error al procesar el PDF: {e}")
            return []
    
    def _parsear_partido_multilinea(self, lines: List[str], start_idx: int, dia: Optional[str]) -> Optional[Dict]:
        """
        Parsea un partido que está en formato multi-línea:
        Línea start_idx: Nº Part + Hora + Categoría
        Línea start_idx+1: Equipo Local
        Línea start_idx+2: Equipo Visitante
        Línea start_idx+3: Lugar
        
        Args:
            lines: Lista completa de líneas
            start_idx: Índice de inicio del partido
            dia: Día de la semana
            
        Returns:
            Diccionario con información del partido o None
        """
        try:
            # Necesitamos encontrar la línea que tiene Nº + Hora + Categoría
            # Buscar hacia atrás y adelante desde start_idx
            
            linea_hora = None
            linea_local = None
            linea_visitante = None
            linea_lugar = None
            
            # Buscar en un rango de ±2 líneas la línea con hora
            for offset in range(-2, 3):
                idx = start_idx + offset
                if 0 <= idx < len(lines):
                    if re.search(r'\d{1,2}:\d{2}', lines[idx]):
                        linea_hora = lines[idx]
                        # Ahora las siguientes 3 líneas deben ser local, visitante, lugar
                        if idx + 3 < len(lines):
                            candidatos = [lines[idx+1], lines[idx+2], lines[idx+3]]
                            # Verificar que al menos una contenga "Valsequillo"
                            if any('valsequillo' in c.lower() for c in candidatos):
                                linea_local = lines[idx+1]
                                linea_visitante = lines[idx+2]
                                linea_lugar = lines[idx+3]
                                break
            
            if not linea_hora or not linea_local or not linea_visitante:
                return None
            
            # Parsear hora y categoría
            hora_match = re.search(r'\b(\d{1,2}:\d{2})\b', linea_hora)
            hora = hora_match.group(1) if hora_match else "Sin especificar"
            
            # Extraer categoría (después de la hora)
            if hora_match:
                despues_hora = linea_hora[hora_match.end():].strip()
                # La categoría es todo lo que queda después de eliminar el número de partido
                categoria = re.sub(r'^\d+\s*', '', despues_hora).strip()
            else:
                categoria = "Sin especificar"
            
            # Limpiar nombres de equipos (quitar códigos entre paréntesis)
            local = re.sub(r'\s*\([0-9]+\)\s*', '', linea_local).strip()
            visitante = re.sub(r'\s*\([0-9]+\)\s*', '', linea_visitante).strip()
            lugar = linea_lugar.strip() if linea_lugar else "Sin especificar"
            
            # Limpiar símbolos extraños
            local = re.sub(r'[&*]+\s*$', '', local).strip()
            visitante = re.sub(r'[&*]+\s*$', '', visitante).strip()
            
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
            logger.warning(f"Error al parsear partido multi-línea: {e}")
            return None
    
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
            
            # Renombrar columnas para mejor presentación
            df.columns = ['Día', 'Hora', 'Categoría', 'Equipo Local', 'Equipo Visitante', 'Pabellón/Lugar']
            
            # Guardar a Excel
            excel_path = Path(nombre_archivo)
            df.to_excel(excel_path, index=False, engine='openpyxl')
            
            logger.info(f"Excel generado exitosamente: {excel_path}")
            logger.info(f"Total de partidos exportados: {len(partidos)}")
            
            return excel_path
            
        except Exception as e:
            logger.error(f"Error al generar Excel: {e}")
            raise
    
    def generar_pdf(self, partidos: List[Dict]) -> Path:
        """
        Genera un archivo PDF con los partidos filtrados
        Formato de nombre: PARTIDOS_VALSEQUILLO_DD_MM.pdf
        
        Args:
            partidos: Lista de partidos
            
        Returns:
            Path al archivo PDF generado
        """
        try:
            # Generar nombre de archivo con formato DIA_MES
            now = datetime.now()
            nombre_archivo = f"PARTIDOS_VALSEQUILLO_{now.strftime('%d_%m')}.pdf"
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
            title = Paragraph("PARTIDOS DE VALSEQUILLO", title_style)
            elements.append(title)
            
            # Subtítulo con fecha de generación
            subtitle = Paragraph(
                f"Jornada - Generado el {now.strftime('%d/%m/%Y a las %H:%M')}",
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
    
    def ejecutar(self) -> Optional[Path]:
        """
        Ejecuta el proceso completo: descarga, extracción y generación de Excel
        
        Returns:
            Path al archivo PDF generado o None si falla
        """
        logger.info("=== Iniciando proceso de extracción de partidos ===")
        
        # 1. Descargar PDF
        pdf_path = self.descargar_ultimo_pdf()
        if not pdf_path:
            logger.error("No se pudo descargar el PDF")
            return None
        
        # 2. Extraer partidos
        partidos = self.extraer_partidos_pdf(pdf_path)
        if not partidos:
            logger.warning("No se encontraron partidos de Valsequillo")
            return None
        
        # 3. Generar Excel
        excel_path = self.generar_excel(partidos)
        logger.info(f"Archivo Excel: {excel_path}")
        
        # 4. Generar PDF
        pdf_partidos_path = self.generar_pdf(partidos)
        logger.info(f"Archivo PDF: {pdf_partidos_path}")
        
        logger.info("=== Proceso completado exitosamente ===")
        
        return pdf_partidos_path


def main():
    """Función principal"""
    try:
        scraper = ScraperBaloncesto()
        pdf_path = scraper.ejecutar()
        
        if pdf_path:
            print(f"\n✅ ¡Éxito! Partidos exportados a PDF: {pdf_path}")
            print(f"   (También se generó un archivo Excel)")
        else:
            print("\n❌ No se pudo completar el proceso")
            
    except Exception as e:
        logger.error(f"Error en la ejecución: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
