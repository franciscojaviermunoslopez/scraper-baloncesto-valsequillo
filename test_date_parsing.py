import re

def test_logic():
    # Simulamos el texto tal cual salió en tu log anterior
    raw_lines = [
        "Línea 60: Nº  Part",
        "Línea 61: Hora",
        "Línea 62: Categoría",
        "Línea 63: Local",
        "Línea 64: Visitante",
        "Línea 65: Lugar",
        "Viernes",           # Línea i
        "(16/01/26)",        # Línea i+1
        "81270",
        "Sen Masc 2ª F G-B",
        "Vito Valsequillo (35008831)"
    ]
    
    lines = [l.strip() for l in raw_lines]
    
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_actual = "Desconocido"
    
    print("--- Testeando lógica del Scraper ---")
    
    for i, line in enumerate(lines):
        for d in dias_semana:
            # Condición del scraper
            if d in line and len(line) < 40:
                print(f"\nDetectado día '{d}' en línea: '{line}'")
                
                # Lógica actual del scraper
                match_fecha = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', line)
                
                if not match_fecha:
                    print(f"   ❌ No hay fecha en la misma línea.")
                    if i + 1 < len(lines):
                        line_next = lines[i+1]
                        print(f"   👀 Mirando siguiente línea: '{line_next}'")
                        match_fecha = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', line_next)
                
                if match_fecha:
                    dia_actual = f"{d} {match_fecha.group(1)}"
                    print(f"   ✅ ¡FECHA ENCONTRADA! dia_actual = {dia_actual}")
                else:
                    dia_actual = d
                    print(f"   ⚠️ Fecha no encontrada. dia_actual = {dia_actual}")
                break
                
        if "valsequillo" in line.lower():
            print(f"\n🏀 Partido encontrado con fecha: {dia_actual}")

if __name__ == "__main__":
    test_logic()
