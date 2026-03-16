from scraper_baloncesto import ScraperBaloncesto
import logging
import fitz  # PyMuPDF

# Configurar logging
logging.basicConfig(level=logging.INFO)

def debug_blocks():
    scraper = ScraperBaloncesto()
    pdfs = scraper.descargar_pdfs_recientes()
    
    if not pdfs: return

    for pdf_info in pdfs:
        # Solo analizar la provisional que es la conflictiva
        if 'Provisional' not in pdf_info['titulo']:
            continue
            
        pdf_path = pdf_info['path']
        print(f"\n📄 Analizando BLOQUES de: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        page = doc[0] # Solo pagina 1
        
        blocks = page.get_text("blocks")
        # Blocks format: (x0, y0, x1, y1, text, block_no, block_type)
        
        print(f"Total bloques encontrados: {len(blocks)}")
        
        # Filtrar bloques con Valsequillo
        for b in blocks:
            text = b[4].strip()
            if "Valsequillo" in text or "VALSEQUILLO" in text:
                print(f"\n🎯 BLOQUE VALSEQUILLO ENCONTRADO:")
                print(f"   Texto: {text}")
                print(f"   Coords: ({b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f})")
                
                # Buscar bloques cercanos (misma altura Y)
                y_center = (b[1] + b[3]) / 2
                print("   🧩 Bloques cercanos (misma fila):")
                
                for other in blocks:
                    if other == b: continue
                    other_y_center = (other[1] + other[3]) / 2
                    
                    # Si están alineados verticalmente (con tolerancia de 10px)
                    if abs(y_center - other_y_center) < 15:
                         print(f"      -> {other[4].strip().replace('\n', ' ')}")

if __name__ == "__main__":
    debug_blocks()
