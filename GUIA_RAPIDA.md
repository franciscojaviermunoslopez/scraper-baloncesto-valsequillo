# 🚀 Guía Rápida de Instalación

## ⚡ Inicio Rápido (3 pasos)

### 1️⃣ Instalar Python
- Descarga Python 3.8+ desde [python.org](https://www.python.org/downloads/)
- ✅ Durante la instalación, marca "Add Python to PATH"

### 2️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3️⃣ Ejecutar
```bash
# Prueba local (sin Internet)
python test_scraper.py

# Ejecución real
python scraper_baloncesto.py
```

---

## 🔧 Opciones de Ejecución

### Opción A: Manual Local
**Ventajas:** Control total, ejecución inmediata  
**Desventajas:** Requiere ejecutar manualmente

```bash
python scraper_baloncesto.py
```

### Opción B: GitHub Actions (Recomendado) 🌟
**Ventajas:** 100% automático, no requiere tu ordenador  
**Desventajas:** Requiere configurar GitHub

#### Pasos para GitHub Actions:

1. **Crear repositorio en GitHub:**
   - Ve a [github.com](https://github.com)
   - Clic en "New repository"
   - Nombre: `scraper-baloncesto-valsequillo`
   - Tipo: Puede ser privado o público

2. **Subir el código:**
   ```bash
   cd "c:\Users\fmunoz\Downloads\PRUEBA PDF"
   git init
   git add .
   git commit -m "🏀 Scraper de partidos Valsequillo"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/scraper-baloncesto-valsequillo.git
   git push -u origin main
   ```

3. **Activar Actions:**
   - Ve a tu repo → pestaña "Actions"
   - Clic en "I understand..."
   - ✅ Se ejecutará automáticamente cada lunes

4. **Descargar resultados:**
   - Actions → última ejecución → Artifacts → Download

### Opción C: Tarea Programada Windows
**Ventajas:** No requiere GitHub, ejecución local automática  
**Desventajas:** Tu PC debe estar encendido

#### Crear tarea programada:

1. Abre "Programador de tareas" (Task Scheduler)
2. Clic en "Crear tarea básica"
3. Nombre: "Scraper Baloncesto"
4. Desencadenador: Semanal → Lunes 8:00
5. Acción: Iniciar programa
   - Programa: `python`
   - Argumentos: `scraper_baloncesto.py`
   - Directorio: `c:\Users\fmunoz\Downloads\PRUEBA PDF`

---

## 📧 Recibir Resultados por Email (Bonus)

Si quieres recibir el Excel automáticamente por email:

### Modificar `scraper_baloncesto.py`:

Añade al final del archivo, antes de `if __name__ == "__main__"`:

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def enviar_email(excel_path: Path):
    """Envía el Excel por email"""
    # Configuración de Gmail (crea una contraseña de aplicación)
    remitente = "tu_email@gmail.com"
    contraseña = "tu_contraseña_app"
    destinatario = "tu_email@gmail.com"
    
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = destinatario
    msg['Subject'] = f"🏀 Partidos Valsequillo - {datetime.now().strftime('%d/%m/%Y')}"
    
    # Adjuntar archivo
    with open(excel_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={excel_path.name}')
        msg.attach(part)
    
    # Enviar
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(remitente, contraseña)
        server.send_message(msg)
    
    logger.info(f"Email enviado a {destinatario}")

# En la función ejecutar(), después de generar el Excel:
if excel_path:
    enviar_email(excel_path)  # ← Añade esta línea
```

**⚠️ Nota:** Para Gmail, necesitas crear una [contraseña de aplicación](https://myaccount.google.com/apppasswords)

---

## 🐛 Problemas Comunes

### "ModuleNotFoundError: No module named 'X'"
```bash
pip install -r requirements.txt --upgrade
```

### "SSL Error" al descargar PDF
```python
# En scraper_baloncesto.py, añade:
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

### El PDF tiene un formato diferente
El script intenta detectar automáticamente, pero si falla:
1. Abre un Issue en GitHub con el PDF
2. O ajusta los patrones en `_parsear_linea_partido()`

---

## 📊 Ver Resultados

### En Excel:
```bash
start partidos_prueba.xlsx  # Windows
```

### En terminal:
```bash
python -c "import pandas; print(pandas.read_excel('partidos_prueba.xlsx'))"
```

---

## 🎯 Próximos Pasos

1. ✅ Prueba local con `python test_scraper.py`
2. ✅ Configura GitHub Actions para automatización completa
3. ✅ (Opcional) Configura email para recibir resultados
4. 🎉 ¡Disfruta de tu scraper en "antigravedad"!

---

**¿Necesitas ayuda?** Abre un Issue en el repositorio o consulta el README.md completo.
