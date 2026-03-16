from scraper_baloncesto import ScraperBaloncesto
import logging
from pathlib import Path
import fitz  # PyMuPDF

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_pdf_content():
    scraper = ScraperBaloncesto()
    
    # 1. Descargar PDFs recientes
    print("\n🔍 1. Descargando PDFs...")
    pdfs = scraper.descargar_pdfs_recientes()
    
    if not pdfs:
        print("❌ No se descargaron PDFs")
        return

    # 2. Analizar TODOS los PDFs
    for pdf_info in pdfs:
        pdf_path = pdf_info['path']
        print(f"\n📄 Analizando: {pdf_path} ({pdf_info['titulo']})")
        
        doc = fitz.open(pdf_path)
        found_valsequillo = False
        
        print(f"   🔎 Buscando 'Valsequillo' en {pdf_info['titulo']}...")
        for i, page in enumerate(doc):
            text = page.get_text()
            if "Valsequillo" in text or "VALSEQUILLO" in text:
                found_valsequillo = True
                print(f"   ✅ ENCONTRADO en página {i+1}")
                
                # Mostrar contexto
                lines = text.split('\n')
                for j, line in enumerate(lines):
                    if "valsequillo" in line.lower():
                        # Mostrar contexto amplio (10 líneas antes y después) para entender la estructura
                        start_line = max(0, j - 10)
                        end_line = min(len(lines), j + 10)
                        
                        print(f"\n      --- CONTEXTO BLOQUE PARTIDO ---")
                        for k in range(start_line, end_line):
                            prefix = ">>" if k == j else "  "
                            print(f"      {prefix} Línea {k}: {lines[k].strip()}")
                        print("      -------------------------------")
        
        if not found_valsequillo:
            print("\n❌ 'Valsequillo' NO aparece en el texto extraído.")
        else:
            print("\n✅ El texto 'Valsequillo' existe en este PDF.")

if __name__ == "__main__":
    debug_pdf_content()
