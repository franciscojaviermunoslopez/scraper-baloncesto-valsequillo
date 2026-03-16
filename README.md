# 🏀 Scraper Automático de Partidos de Valsequillo

Script automatizado para extraer partidos de baloncesto de Valsequillo desde la Federación Insular de Baloncesto de Gran Canaria.

## 🚀 Características

- ✅ **Web Scraping Automático**: Descarga el PDF más reciente de hojas de jornada
- ✅ **Procesamiento Inteligente**: Extrae y parsea información de partidos del PDF
- ✅ **Filtrado por Equipo**: Identifica automáticamente partidos de Valsequillo
- ✅ **Detección de Fechas**: Reconoce el día de la semana de cada partido
- ✅ **Exportación a Excel**: Genera archivos Excel listos para usar
- ✅ **Ejecución Automática**: GitHub Actions ejecuta el script semanalmente
- ✅ **Manejo de Errores**: Logs detallados y recuperación ante fallos

## 📋 Requisitos

### Instalación Local

```bash
# 1. Clonar o descargar este repositorio
git clone <tu-repo>
cd PRUEBA\ PDF

# 2. Instalar Python 3.8 o superior
# Descargar desde: https://www.python.org/downloads/

# 3. Instalar dependencias
pip install -r requirements.txt
```

## 🎯 Uso

### Ejecución Manual

```bash
python scraper_baloncesto.py
```

El script generará:
- `jornada_YYYYMMDD_HHMMSS.pdf` - El PDF descargado
- `partidos_valsequillo_YYYYMMDD_HHMMSS.xlsx` - Excel con los partidos filtrados

### Ejecución Automática (GitHub Actions)

#### Configuración Inicial:

1. **Sube este código a un repositorio de GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Scraper de partidos"
   git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
   git push -u origin main
   ```

2. **Activa GitHub Actions**:
   - Ve a tu repositorio en GitHub
   - Ve a la pestaña "Actions"
   - Haz clic en "I understand my workflows, go ahead and enable them"

3. **Configura permisos de escritura** (si quieres que haga commits automáticos):
   - Settings → Actions → General
   - En "Workflow permissions" selecciona "Read and write permissions"
   - Guarda los cambios

#### El workflow se ejecutará:

- 🕐 **Automáticamente**: Todos los lunes a las 8:00 AM (UTC)
- 🔘 **Manualmente**: Ve a Actions → "Scraper Automático de Partidos" → "Run workflow"

#### Descargar Resultados:

1. Ve a la pestaña "Actions" de tu repositorio
2. Haz clic en la ejecución más reciente
3. En "Artifacts" descarga `partidos-valsequillo-X`

## 📊 Formato de Salida Excel

El archivo Excel generado contiene las siguientes columnas:

| Día | Hora | Categoría | Equipo Local | Equipo Visitante | Pabellón/Lugar |
|-----|------|-----------|--------------|------------------|----------------|
| Sábado (10/01/26) | 18:30 | Senior Masculino | Valsequillo | CB Gran Canaria | Pabellón Municipal |

## 🛠️ Estructura del Proyecto

```
PRUEBA PDF/
├── scraper_baloncesto.py      # Script principal
├── requirements.txt            # Dependencias Python
├── README.md                   # Esta documentación
└── .github/
    └── workflows/
        └── scraper_automatico.yml  # Configuración de GitHub Actions
```

## 🔧 Personalización

### Cambiar la frecuencia de ejecución automática

Edita `.github/workflows/scraper_automatico.yml`:

```yaml
schedule:
  - cron: '0 8 * * 1'  # Formato: minuto hora día-mes mes día-semana
```

Ejemplos:
- `'0 8 * * 1'` - Lunes a las 8:00 AM
- `'0 20 * * 5'` - Viernes a las 8:00 PM
- `'0 9 * * 1,4'` - Lunes y jueves a las 9:00 AM
- `'0 10 * * *'` - Todos los días a las 10:00 AM

### Filtrar por otro equipo

En `scraper_baloncesto.py`, modifica la línea:

```python
if 'valsequillo' in line.lower():
```

Por:

```python
if 'tu_equipo' in line.lower():
```

## 🐛 Solución de Problemas

### Error: "No se encontró ningún enlace de descarga"

La estructura de la web puede haber cambiado. Revisa:
1. Que la URL `https://fibgc.es/hojas-de-jornada/` sea correcta
2. Los selectores en el método `descargar_ultimo_pdf()`

### Error: "No se encontraron partidos"

Verifica:
1. Que el PDF contenga la palabra "Valsequillo"
2. El formato del PDF en el método `extraer_partidos_pdf()`

### Ver logs detallados

Los logs se muestran en la consola. Para guardarlos en archivo:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
```

## 📝 Notas Importantes

- ⚠️ **Scraping Ético**: El script respeta los términos de uso y no sobrecarga el servidor
- 🔒 **Privacidad**: No se almacenan datos personales
- 🌐 **Conectividad**: Requiere conexión a Internet para funcionar
- 📅 **Actualidad**: Los PDFs deben estar disponibles en la web de FIBGC

## 🤝 Contribuciones

Si encuentras un bug o quieres mejorar el script:
1. Abre un Issue
2. Envía un Pull Request

## 📄 Licencia

MIT License - libre para uso personal y comercial

---

**¡Disfruta de tu scraper en "antigravedad"! 🚀**
