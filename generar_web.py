#!/usr/bin/env python3
"""
Genera una página web HTML estática con los próximos partidos
Para publicar en GitHub Pages
"""

import json
from pathlib import Path
from datetime import datetime

def generar_web_publica(partidos_definitivos=None):
    """
    Genera index.html con los próximos partidos
    
    Args:
        partidos_definitivos: Lista de partidos definitivos. Si es None, lee del snapshot.
    """
    
    # Si no se pasaron partidos, leer del snapshot
    if partidos_definitivos is None:
        snapshot_path = Path("partidos_anteriores.json")
        partidos = []
        
        if snapshot_path.exists():
            try:
                with open(snapshot_path, 'r', encoding='utf-8') as f:
                    contenido = f.read().strip()
                    if contenido:
                        partidos = json.loads(contenido)
                    else:
                        print("⚠️ Archivo JSON vacío, generando web sin partidos")
            except json.JSONDecodeError:
                print("⚠️ Error leyendo JSON, generando web sin partidos")
        else:
            print("⚠️ No se encontró snapshot, generando web sin partidos")
        
        # Filtrar solo definitivos
        partidos_def = [p for p in partidos if p.get('jornada_tipo') == 'DEFINITIVA']
    else:
        # Usar los partidos que se pasaron como parámetro
        partidos_def = partidos_definitivos
    
    # Generar HTML
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CB Valsequillo - Próximos Partidos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #2D8B3C 0%, #1a5225 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 40px 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        
        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .partidos-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .partido-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .partido-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        
        .partido-card.casa {
            border-left: 5px solid #2D8B3C;
        }
        
        .partido-card.fuera {
            border-left: 5px solid #FF9800;
        }
        
        .fecha {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.1em;
            color: #2D8B3C;
            font-weight: bold;
            margin-bottom: 15px;
        }
        
        .equipos {
            margin: 20px 0;
        }
        
        .equipo {
            font-size: 1.2em;
            padding: 10px;
            margin: 5px 0;
        }
        
        .equipo.local {
            background: #e8f5e9;
            border-radius: 8px;
            font-weight: bold;
        }
        
        .equipo.visitante {
            background: #f5f5f5;
            border-radius: 8px;
        }
        
        .vs {
            text-align: center;
            color: #666;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .info {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
            font-size: 0.9em;
            color: #666;
        }
        
        .categoria {
            background: #2D8B3C;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
        }
        
        .lugar {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
        }
        
        .badge.casa {
            background: #e8f5e9;
            color: #2D8B3C;
        }
        
        .badge.fuera {
            background: #fff3e0;
            color: #FF9800;
        }
        
        footer {
            text-align: center;
            color: white;
            padding: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .actualizado {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 2em;
            }
            
            .partidos-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏀 CB Valsequillo</h1>
            <p class="subtitle">Roque Grande - Próximos Partidos</p>
        </header>
        
        <div class="partidos-grid">
"""
    
    if not partidos_def:
        html += """
            <div style="grid-column: 1/-1; text-align: center; color: white; font-size: 1.5em; padding: 50px;">
                <p>📅 No hay partidos definitivos programados en este momento</p>
                <p style="font-size: 0.8em; margin-top: 20px; opacity: 0.8;">Esta página se actualiza automáticamente cada día</p>
            </div>
        """
    else:
        for p in partidos_def:
            es_casa = "valsequillo" in p['local'].lower()
            clase_card = "casa" if es_casa else "fuera"
            badge_text = "🏠 En Casa" if es_casa else "✈️ Fuera"
            badge_class = "casa" if es_casa else "fuera"
            
            html += f"""
            <div class="partido-card {clase_card}">
                <div class="fecha">
                    <span>📅</span>
                    <span>{p['dia']}</span>
                    <span style="margin-left: auto;">🕐 {p['hora']}</span>
                </div>
                
                <span class="badge {badge_class}">{badge_text}</span>
                
                <div class="equipos">
                    <div class="equipo local">{p['local']}</div>
                    <div class="vs">VS</div>
                    <div class="equipo visitante">{p['visitante']}</div>
                </div>
                
                <div class="info">
                    <span class="categoria">{p['categoria']}</span>
                    <span class="lugar">📍 {p['lugar']}</span>
                </div>
            </div>
            """
    
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    html += f"""
        </div>
        
        <footer>
            <p><strong>Club de Baloncesto Valsequillo</strong></p>
            <p class="actualizado">Última actualización: {now}</p>
            <p style="margin-top: 15px; font-size: 0.85em;">
                📅 <a href="https://calendar.google.com" style="color: white;">Añadir al calendario</a> | 
                📧 Actualizaciones automáticas cada día
            </p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Guardar
    output_path = Path("docs/index.html")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(html, encoding='utf-8')
    
    print(f"✅ Web pública generada: {output_path}")
    print(f"   Total partidos mostrados: {len(partidos_def)}")

if __name__ == "__main__":
    generar_web_publica()
