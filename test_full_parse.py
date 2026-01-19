import re

def parsear_simulacion():
    # Simulamos las líneas problemáticas copiadas de tus logs
    lines = [
        "HOJA DE JORNADA",
        # ... (bloque Viernes) ...
        "Viernes",
        "(16/01/26)",
        "Sen Masc 2ª F G-B",
        "Vito Valsequillo (35008831)", # PARTIDO 1 (Viernes)
        "Asigna Esbisoni Naranja (35023912)",
        "Sábado", # Cambio de día
        "81381",  # Basura entre medio
        "Cad Masc S-B",
        "Ecoener CB Castillo & (35003808)", # Local (bien)
        "Clínica Dental Virmident Valsequillo  (35008840)", # PARTIDO 2 (Sábado) - Visitante
        "Cdad Dep Vicente del Bosque", # Lugar
        "Junior Masc S-B",
        "Aqualia Ingenio (35002661)3)", # Local (CON BASURA AL FINAL '3)')
        "Valsequillo (35008832)nt Valsequillo (35008840)", # PARTIDO 3 - Visitante (DOBLADO)
        "Pab Pedro Padilla"
    ]
    
    print(f"Total líneas: {len(lines)}")
    
    patron_codigo = re.compile(r'\(\d+\)$') # ESTE ES EL CULPABLE PROBABLE (el $ exige final de línea)
    dias_semana = ['Viernes', 'Sábado']
    dia_actual = "Desconocido"
    
    partidos = []

    for i, line in enumerate(lines):
        # Actualización fecha
        for d in dias_semana:
            if d in line:
                dia_actual = d
                break
        
        if "valsequillo" in line.lower():
            print(f"\n🔍 Valsequillo encontrado en línea {i}: {line}")
            print(f"   Día actual: {dia_actual}")
            
            linea_ant = lines[i-1] if i>0 else ""
            linea_sig = lines[i+1] if i<len(lines)-1 else ""
            
            print(f"   Ant: {linea_ant}")
            print(f"   Sig: {linea_sig}")
            
            es_equipo = bool(patron_codigo.search(line))
            print(f"   ¿Es equipo (tiene código al final)? {es_equipo}")
            
            if not es_equipo:
                print("   ❌ Ignorado (no parece equipo válido)")
                continue

            local = "???"
            visitante = "???"
            
            # Chequeos de código
            # NOTA: Aquí está el fallo, si linea_ant tiene basura al final, search(regex+$) fallará
            if patron_codigo.search(linea_sig):
                print("   -> Detectado como LOCAL (siguiente tiene código)")
                local = line
                visitante = linea_sig
            elif patron_codigo.search(linea_ant):
                 print("   -> Detectado como VISITANTE (anterior tiene código)")
                 local = linea_ant
                 visitante = line
            else:
                 print("   ⚠️ NO SE DETECTA RIVAL (Codigos no coinciden)")
                 print(f"      Ant has code? {bool(patron_codigo.search(linea_ant))}")
                 # Forzamos lógica por defecto
                 local = line
                 visitante = linea_sig
            
            print(f"   ✅ PARTIDO: {local} vs {visitante}")

if __name__ == "__main__":
    parsear_simulacion()
