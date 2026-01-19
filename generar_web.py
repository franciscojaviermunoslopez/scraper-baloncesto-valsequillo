#!/usr/bin/env python3
"""
Genera una página web HTML estática con los próximos partidos
Para publicar en GitHub Pages
"""

import json
from pathlib import Path
from datetime import datetime

def generar_web_publica(partidos_definitivos=None, partidos_provisionales=None):
    """
    Genera index.html con diseño PREMIUM
    Muestra tanto definitivos como provisionales
    """
    
    # 1. Obtener datos
    if partidos_definitivos is None and partidos_provisionales is None:
        snapshot_path = Path("partidos_anteriores.json")
        partidos = []
        if snapshot_path.exists():
            try:
                with open(snapshot_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        partidos = json.loads(content)
            except:
                pass
        partidos_definitivos = [p for p in partidos if p.get('jornada_tipo') == 'DEFINITIVA']
        partidos_provisionales = [p for p in partidos if p.get('jornada_tipo') == 'PROVISIONAL']
    
    # Combinar ambos tipos
    partidos_def = partidos_definitivos if partidos_definitivos else []
    partidos_prov = partidos_provisionales if partidos_provisionales else []
    
    # Eliminar duplicados (un partido puede estar varias veces en la federación)
    # Usar combinación de día+hora+local+visitante como clave única
    partidos_unicos = {}
    for p in partidos_def + partidos_prov:
        # Crear clave única
        clave = f"{p.get('dia', '')}_{p.get('hora', '')}_{p.get('local', '')}_{p.get('visitante', '')}_{p.get('categoria', '')}"
        # Si ya existe, priorizar DEFINITIVA sobre PROVISIONAL
        if clave not in partidos_unicos:
            partidos_unicos[clave] = p
        else:
            # Si el nuevo es DEFINITIVA y el existente es PROVISIONAL, reemplazar
            if p.get('jornada_tipo') == 'DEFINITIVA' and partidos_unicos[clave].get('jornada_tipo') == 'PROVISIONAL':
                partidos_unicos[clave] = p
    
    todos_partidos = list(partidos_unicos.values())
    
    # Ordenar por fecha (más cercanos primero)
    def parsear_fecha(partido):
        """Convierte 'Viernes 09/01/26' a objeto datetime para ordenar"""
        try:
            dia_str = partido.get('dia', '')
            # Extraer solo la parte de fecha DD/MM/YY
            import re
            match = re.search(r'(\d{2})/(\d{2})/(\d{2})', dia_str)
            if match:
                dia, mes, anio = match.groups()
                # Asumir siglo 20XX
                from datetime import datetime
                return datetime(2000 + int(anio), int(mes), int(dia))
            return datetime(2099, 12, 31)  # Fecha muy lejana si no se puede parsear
        except:
            from datetime import datetime
            return datetime(2099, 12, 31)
    
    todos_partidos.sort(key=parsear_fecha)
    
    # Filtrar partidos que ya terminaron (más de 2 horas después del inicio)
    from datetime import datetime, timedelta
    import re
    
    partidos_vigentes = []
    ahora = datetime.now()
    
    for p in todos_partidos:
        try:
            # Parsear fecha y hora del partido
            match_fecha = re.search(r'(\d{2})/(\d{2})/(\d{2})', p.get('dia', ''))
            match_hora = re.search(r'(\d{1,2}):(\d{2})', p.get('hora', ''))
            
            if match_fecha and match_hora:
                dia, mes, anio = match_fecha.groups()
                hora, minuto = match_hora.groups()
                
                fecha_partido = datetime(2000 + int(anio), int(mes), int(dia), int(hora), int(minuto))
                # Añadir 2 horas buffer (un partido dura ~1.5-2h)
                fecha_fin_estimada = fecha_partido + timedelta(hours=2)
                
                # Solo mostrar si no ha terminado
                if ahora < fecha_fin_estimada:
                    partidos_vigentes.append(p)
            else:
                # Si no se puede parsear, incluirlo por seguridad
                partidos_vigentes.append(p)
        except:
            # Si hay error, incluir el partido
            partidos_vigentes.append(p)
    
    todos_partidos = partidos_vigentes
    
    # 2. Generar HTML con diseño mejorado
    html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CB Valsequillo - Próximos Partidos</title>
    <link rel="icon" type="image/png" href="logo_club.png">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #2D8B3C;
            --primary-dark: #1b5e25;
            --accent: #FF9800;
            --text-dark: #1a1a1a;
            --text-light: #f5f5f5;
            --bg-card: #ffffff;
            --shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Outfit', sans-serif;
            background-color: #f0f2f5;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* HEADER PREMIUM */
        header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
            border-bottom-left-radius: 30px;
            border-bottom-right-radius: 30px;
            box-shadow: 0 4px 20px rgba(45, 139, 60, 0.3);
            margin-bottom: 30px;
            position: relative;
            overflow: hidden;
        }
        
        /* Círculos decorativos fondo */
        header::before {
            content: '';
            position: absolute;
            top: -50px;
            left: -50px;
            width: 200px;
            height: 200px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
        }
        
        header::after {
            content: '';
            position: absolute;
            bottom: -30px;
            right: -30px;
            width: 150px;
            height: 150px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
        }
        
        .logo-container {
            width: 150px;
            height: 150px;
            background: transparent;
            border-radius: 50%;
            margin: 0 auto 15px;
            padding: 5px;
            box-shadow: none;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        .logo-img {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        h1 {
            font-weight: 800;
            font-size: 2.5em;
            margin-bottom: 5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .subtitle {
            font-weight: 300;
            font-size: 1.1em;
            opacity: 0.9;
        }

        /* GRID Partidos */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            width: 100%;
            flex-grow: 1;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        /* TARJETA PARTIDO */
        .card {
            background: var(--bg-card);
            border-radius: 20px;
            padding: 25px;
            box-shadow: var(--shadow);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-top: 5px solid transparent;
            position: relative;
            overflow: visible;
            
            /* Estado inicial: invisible y desplazada */
            opacity: 0;
            transform: translateY(30px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        /* Cuando la tarjeta es visible (añadido por JavaScript) */
        .card.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        .card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        
        .card.visible:hover {
            transform: translateY(-8px);
        }
        
        /* DESTACAR PARTIDOS DE VALSEQUILLO */
        .card.valsequillo-destacado {
            border-top-width: 7px;
            box-shadow: 0 10px 30px rgba(45, 139, 60, 0.3), 
                        0 0 0 3px rgba(45, 139, 60, 0.1);
        }
        
        .card.valsequillo-destacado.visible {
            animation: pulseGlow 3s ease-in-out infinite;
        }
        
        @keyframes pulseGlow {
            0%, 100% {
                box-shadow: 0 10px 30px rgba(45, 139, 60, 0.3), 
                           0 0 0 3px rgba(45, 139, 60, 0.1);
            }
            50% {
                box-shadow: 0 15px 35px rgba(45, 139, 60, 0.4), 
                           0 0 0 4px rgba(45, 139, 60, 0.2);
            }
        }
        
        .card.valsequillo-destacado:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 25px 50px rgba(45, 139, 60, 0.4),
                       0 0 0 4px rgba(45, 139, 60, 0.2);
        }
        
        .card.casa { border-top-color: var(--primary); }
        .card.fuera { border-top-color: var(--accent); }
        .card.provisional { border-top-color: #FF6B00; border-top-width: 6px; }
        
        .card-badge {
            position: absolute;
            top: 15px;
            right: 15px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge-casa { background: #e8f5e9; color: var(--primary); }
        .badge-fuera { background: #fff3e0; color: var(--accent); }
        .badge-provisional { background: #FFEACC; color: #FF6B00; animation: blink 2s ease-in-out infinite; }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .date-row {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .matchup {
            text-align: center;
            margin: 20px 0;
        }
        
        .team {
            font-size: 1.25em;
            font-weight: 700;
            color: var(--text-dark);
            line-height: 1.2;
        }
        
        .vs {
            font-size: 0.8em;
            color: #999;
            margin: 8px 0;
            font-weight: 600;
            letter-spacing: 1px;
        }
        
        .team-highlight { color: var(--primary); }
        
        .meta-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid #f0f0f0;
            padding-top: 15px;
            margin-top: 10px;
            font-size: 0.85em;
        }
        
        .category-tag {
            background: #f5f5f5;
            padding: 4px 10px;
            border-radius: 8px;
            color: #666;
            font-weight: 600;
        }
        
        .location-link {
            color: #555;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: color 0.2s;
        }
        
        .location-link:hover { color: var(--primary); text-decoration: underline; }
        
        /* FOOTER */
        footer {
            text-align: center;
            padding: 30px;
            color: #888;
            font-size: 0.9em;
            margin-top: auto;
        }
        
        /* BANNER PRÓXIMO PARTIDO */
        .next-match-banner {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(45, 139, 60, 0.3);
            display: flex;
            align-items: center;
            gap: 30px;
            color: white;
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }
        
        .countdown {
            background: rgba(255,255,255,0.2);
            border-radius: 15px;
            padding: 20px 30px;
            text-align: center;
            min-width: 180px;
            border: 2px solid rgba(255,255,255,0.3);
        }
        
        .countdown-emoji {
            font-size: 3em;
            display: block;
            margin-bottom: 10px;
            animation: bounce 1s ease infinite;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        .countdown-text {
            font-size: 1.5em;
            font-weight: 800;
            letter-spacing: 2px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .next-match-info {
            flex: 1;
        }
        
        .next-match-teams {
            font-size: 1.5em;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .vs-small {
            font-size: 0.7em;
            opacity: 0.8;
            font-weight: 400;
        }
        
        .next-match-details {
            font-size: 0.95em;
            opacity: 0.9;
        }
        
        @media (max-width: 768px) {
            .next-match-banner {
                flex-direction: column;
                gap: 20px;
                text-align: center;
            }
            
            .countdown {
                min-width: 100%;
            }
        }
        
        .empty-state {
            grid-column: 1 / -1;
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 20px;
            box-shadow: var(--shadow);
            color: #666;
        }

        .upload-hint {
            font-size: 0.8em; 
            margin-top: 5px; 
            color: rgba(255,255,255,0.7);
        }
        
        /* FILTROS */
        .filter-section {
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .filter-label {
            font-weight: 600;
            color: #666;
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .filter-btn {
            padding: 8px 20px;
            border: 2px solid #e0e0e0;
            background: white;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9em;
            transition: all 0.3s ease;
            color: #666;
        }
        
        .filter-btn:hover {
            border-color: var(--primary);
            color: var(--primary);
            transform: translateY(-2px);
        }
        
        .filter-btn.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .card.hidden {
            display: none;
        }
    </style>
</head>
<body>

    <header>
        <div class="logo-container">
            <!-- LOGO: Cambia 'logo.png' por tu archivo -->
            <img src="logo_club.png" alt="Logo Club" class="logo-img" onerror="this.src='https://cdn-icons-png.flaticon.com/512/33/33736.png'">
        </div>
        <h1>CB Valsequillo</h1>
        <p class="subtitle">Próximos Partidos Oficiales</p>
    </header>

    <script>
        // Script de filtrado por categoría y tipo
        document.addEventListener('DOMContentLoaded', function() {
            const filterBtns = document.querySelectorAll('.filter-btn');
            const cards = document.querySelectorAll('.card');
            
            filterBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    // Quitar active de todos los botones
                    filterBtns.forEach(b => b.classList.remove('active'));
                    // Añadir active al botón clickeado
                    this.classList.add('active');
                    
                    const category = this.getAttribute('data-category');
                    const type = this.getAttribute('data-type');
                    
                    cards.forEach(card => {
                        const cardCategory = card.getAttribute('data-category');
                        const cardType = card.getAttribute('data-type');
                        
                        let showCard = true;
                        
                        // Filtro por categoría
                        if (category !== 'all' && cardCategory !== category) {
                            showCard = false;
                        }
                        
                        // Filtro por tipo
                        if (type !== 'all' && cardType !== type) {
                            showCard = false;
                        }
                        
                        if (showCard) {
                            card.classList.remove('hidden');
                        } else {
                            card.classList.add('hidden');
                        }
                    });
                });
            });
            
            // Animación al scroll
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        // Opcional: dejar de observar después de animar
                        observer.unobserve(entry.target);
                    }
                });
            }, observerOptions);
            
            // Observar todas las tarjetas
            document.querySelectorAll('.card').forEach(card => {
                observer.observe(card);
            });
        });
    </script>
"""
    
    # Calcular próximo partido y días restantes
    proximo_partido = None
    dias_restantes = None
    
    if todos_partidos:
        from datetime import datetime, timedelta
        hoy = datetime.now()
        
        # Buscar el partido más cercano
        for p in todos_partidos:
            try:
                # Parsear fecha
                fecha_str = p.get('dia', '')
                import re
                match = re.search(r'(\d{1,2}/\d{1,2}/\d{2,4})', fecha_str)
                if match:
                    fecha_pura = match.group(1)
                    partes = fecha_pura.split('/')
                    if len(partes[2]) == 2:
                        partes[2] = "20" + partes[2]
                    
                    dia, mes, año = partes
                    fecha_partido = datetime(int(año), int(mes), int(dia))
                    
                    # Solo partidos futuros
                    if fecha_partido >= hoy.replace(hour=0, minute=0, second=0, microsecond=0):
                        if proximo_partido is None or fecha_partido < proximo_partido['fecha']:
                            proximo_partido = {
                                'fecha': fecha_partido,
                                'partido': p
                            }
            except:
                continue
        
        # Calcular días restantes desde inicio del día actual
        if proximo_partido:
            hoy_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
            dias_restantes = (proximo_partido['fecha'] - hoy_inicio).days
    
    # Añadir banner de próximo partido si existe
    if proximo_partido:
        p = proximo_partido['partido']
        
        # Texto según días restantes
        if dias_restantes == 0:
            texto_dias = "¡HOY!"
            emoji = "🔥"
        elif dias_restantes == 1:
            texto_dias = "MAÑANA"
            emoji = "⚡"
        else:
            texto_dias = f"EN {dias_restantes} DÍAS"
            emoji = "⏰"
        
        html += f"""
    <div class="container">
        <div class="next-match-banner">
            <div class="countdown">
                <span class="countdown-emoji">{emoji}</span>
                <span class="countdown-text">{texto_dias}</span>
            </div>
            <div class="next-match-info">
                <div class="next-match-teams">🏀 {p['local']} <span class="vs-small">vs</span> {p['visitante']}</div>
                <div class="next-match-details">
                    <span>🏆 {p.get('categoria', 'Sin categoría')}</span>
                    <span style="margin: 0 10px;">•</span>
                    <span>📅 {p['dia']}</span>
                    <span style="margin: 0 10px;">•</span>
                    <span>🕐 {p['hora']}</span>
                    <span style="margin: 0 10px;">•</span>
                    <span>📍 {p['lugar']}</span>
                </div>
            </div>
        </div>
    </div>
"""
    
    # Función para normalizar categorías (quitar códigos numéricos)
    def normalizar_categoria(cat):
        import re
        # Eliminar códigos numéricos del inicio (ej: "78270 Junior Masc S-B" -> "Junior Masc S-B")
        return re.sub(r'^\d+\s+', '', cat).strip()
    
    # Extraer categorías únicas NORMALIZADAS
    categorias = set()
    if todos_partidos:
        for p in todos_partidos:
            cat = p.get('categoria', 'Sin categoría')
            cat_normalizada = normalizar_categoria(cat)
            categorias.add(cat_normalizada)
            # Añadir categoría normalizada al partido para filtrado
            p['categoria_filtro'] = cat_normalizada
    
    # Generar botones de filtro si hay partidos
    if todos_partidos:
        categorias_ordenadas = sorted(list(categorias))
        html += """
    <div class="container">
        <div class="filter-section">
            <span class="filter-label">Filtrar por:</span>
            <div class="filter-buttons">
                <button class="filter-btn active" data-category="all" data-type="all">TODOS</button>
                <button class="filter-btn" data-category="all" data-type="DEFINITIVA">DEFINITIVOS</button>
                <button class="filter-btn" data-category="all" data-type="PROVISIONAL">PROVISIONALES</button>
"""
        for cat in categorias_ordenadas:
            html += f'                <button class="filter-btn" data-category="{cat}" data-type="all">{cat}</button>\n'
        
        html += """            </div>
        </div>
    </div>
"""
    
    html += """
    <div class="container">
        <div class="grid">
"""
    
    if not todos_partidos:
        html += """
        <div class="empty-state">
            <div style="font-size: 3em; margin-bottom: 20px;">🏀</div>
            <h3>No hay partidos programados</h3>
            <p>Vuelve a consultar el próximo lunes</p>
        </div>
        """
    else:
        for p in todos_partidos:
            es_provisional = p.get('jornada_tipo') == 'PROVISIONAL'
            es_casa = "valsequillo" in p.get('local', '').lower()
            es_visitante = "valsequillo" in p.get('visitante', '').lower()
            es_partido_valsequillo = es_casa or es_visitante
            
            # Clase de card según tipo y ubicación
            clases = []
            if es_provisional:
                clases.append("provisional")
                badge_class = "badge-provisional"
                badge_text = "⚠️ PROVISIONAL"
            else:
                if es_casa:
                    clases.append("casa")
                else:
                    clases.append("fuera")
                badge_class = "badge-casa" if es_casa else "badge-fuera"
                badge_text = "🏠 EN CASA" if es_casa else "✈️ VISITANTE"
            
            # Añadir clase destacado si juega Valsequillo
            if es_partido_valsequillo:
                clases.append("valsequillo-destacado")
            
            clase_card = " ".join(clases)
            
            # Limpiar nombres largos de equipos
            local = p['local'].replace("(35008832)", "").replace("(35008831)", "").strip()
            visitante = p['visitante'].replace("(35008832)", "").replace("(35008840)", "").strip()
            
            # Enlace a Google Maps para el lugar
            lugar_query = p['lugar'].replace(" ", "+")
            maps_url = f"https://www.google.com/maps/search/?api=1&query={lugar_query}"
            
            # Tipo de jornada para tooltip
            tipo_jornada = "DEFINITIVA" if not es_provisional else "PROVISIONAL"
            
            html += f"""
            <div class="card {clase_card}" data-category="{p.get('categoria_filtro', p['categoria'])}" data-type="{p.get('jornada_tipo', 'DEFINITIVA')}">
                <div class="card-badge {badge_class}">{badge_text}</div>
                
                <div class="date-row">
                    <span style="font-size: 1.2em;">📅</span>
                    <div>
                        <div style="color: var(--text-dark);">{p['dia']}</div>
                        <div style="color: var(--primary);">{p['hora']}</div>
                    </div>
                </div>
                
                <div class="matchup">
                    <div class="team {'team-highlight' if es_casa else ''}">{local}</div>
                    <div class="vs">VS</div>
                    <div class="team {'team-highlight' if not es_casa else ''}">{visitante}</div>
                </div>
                
                <div class="meta-info">
                    <span class="category-tag">{p['categoria']}</span>
                    <a href="{maps_url}" target="_blank" class="location-link">
                        📍 {p['lugar']}
                    </a>
                </div>
            </div>
            """

    # Obtener Calendar ID de variables de entorno o config
    import os
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID', '')
    
    # Generar enlace de suscripción al calendario
    if calendar_id:
        calendar_url = f"https://calendar.google.com/calendar/u/0?cid={calendar_id}"
    else:
        calendar_url = "https://calendar.google.com"
    
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    html += f"""
        </div>
    </div>

    <footer>
        <p>Actualizado automáticamente: {now}</p>
        <p style="font-size: 0.8em; margin-top: 10px;">
            <a href="{calendar_url}" target="_blank" style="color: var(--primary); text-decoration: none; font-weight: 600;">
                📅 Suscribirse al Calendario Oficial
            </a>
        </p>
    </footer>

</body>
</html>
"""
    
    # Guardar
    output_path = Path("docs/index.html")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(html, encoding='utf-8')
    
    # Copiar logo a docs/ si existe en la raíz
    logo_filename = "logo_club.png"
    logo_source = Path(logo_filename)
    if logo_source.exists():
        import shutil
        shutil.copy(logo_source, output_path.parent / logo_filename)
        print(f"✅ Logo copiado a docs/: {logo_filename}")
    
    print(f"✅ Web pública generada: {output_path}")
    print(f"   Partidos definitivos: {len(partidos_def)}")
    print(f"   Partidos provisionales: {len(partidos_prov)}")
    print(f"   Total partidos mostrados: {len(todos_partidos)}")

if __name__ == "__main__":
    generar_web_publica()
