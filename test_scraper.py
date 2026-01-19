#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para el scraper de baloncesto
Crea un PDF de ejemplo para testear el parser sin necesidad de conexión
"""

import fitz  # PyMuPDF
from datetime import datetime
from pathlib import Path


def crear_pdf_prueba():
    """Crea un PDF de prueba con formato similar al real"""
    
    # Crear un nuevo documento PDF
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    
    # Contenido de ejemplo
    contenido = """
    FEDERACIÓN INSULAR DE BALONCESTO DE GRAN CANARIA
    HOJA DE JORNADA - TEMPORADA 2025/2026
    
    Sábado (10/01/2026)
    
    N.Part  Hora   Categoría           Local                    Visitante              Lugar
    ─────────────────────────────────────────────────────────────────────────────────────────
    101     18:30  Senior Masculino    CB Valsequillo          Gran Canaria B         Pabellón Municipal Valsequillo
    102     20:15  Senior Femenino     Telde A                 CB Valsequillo         Polideportivo de Telde
    
    Domingo (11/01/2026)
    
    103     11:00  Junior Masculino    CB Valsequillo          Arucas                 Pabellón Municipal Valsequillo
    104     12:30  Cadete Femenino     San Mateo               Valsequillo CF         Instalaciones San Mateo
    
    Martes (13/01/2026)
    
    105     19:00  Infantil Masculino  Valsequillo INF         Agüimes                Pabellón Municipal Valsequillo
    106     20:30  Senior Masculino    Las Palmas C            CB Valsequillo SM      Pabellón Paco Artiles
    
    Miércoles (14/01/2026)
    
    107     18:00  Alevín Femenino     Valsequillo ALV         Ingenio                Pabellón Municipal Valsequillo
    
    """
    
    # Añadir texto al PDF
    punto_insercion = fitz.Point(50, 50)
    fuente = "helv"
    tamaño_fuente = 10
    
    for linea in contenido.strip().split('\n'):
        page.insert_text(punto_insercion, linea, fontsize=tamaño_fuente, fontname=fuente)
        punto_insercion = fitz.Point(50, punto_insercion.y + 15)
    
    # Guardar el PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = Path(f"jornada_prueba_{timestamp}.pdf")
    doc.save(pdf_path)
    doc.close()
    
    print(f"✅ PDF de prueba creado: {pdf_path}")
    return pdf_path


def probar_scraper():
    """Prueba el scraper con el PDF de prueba"""
    from scraper_baloncesto import ScraperBaloncesto
    
    print("🏀 Creando PDF de prueba...")
    pdf_path = crear_pdf_prueba()
    
    print("\n📄 Procesando PDF...")
    scraper = ScraperBaloncesto()
    partidos = scraper.extraer_partidos_pdf(pdf_path)
    
    if partidos:
        print(f"\n✅ Se encontraron {len(partidos)} partidos de Valsequillo:")
        print("\n" + "="*100)
        for i, partido in enumerate(partidos, 1):
            print(f"\nPartido {i}:")
            print(f"  Día: {partido['dia']}")
            print(f"  Hora: {partido['hora']}")
            print(f"  Categoría: {partido['categoria']}")
            print(f"  Local: {partido['local']}")
            print(f"  Visitante: {partido['visitante']}")
            print(f"  Lugar: {partido['lugar']}")
        print("\n" + "="*100)
        
        print("\n📊 Generando Excel...")
        excel_path = scraper.generar_excel(partidos, "partidos_prueba.xlsx")
        print(f"✅ Excel generado: {excel_path}")
        
    else:
        print("❌ No se encontraron partidos")


if __name__ == "__main__":
    probar_scraper()
