# 📅 Configuración de Google Calendar Compartido

## ¿Qué conseguirás?
Un calendario público del CB Valsequillo que se actualiza automáticamente cada lunes. Cualquier persona con el enlace puede suscribirse y recibir actualizaciones en su móvil sin hacer nada.

---

## 🛠️ Configuración Inicial (Solo una vez)

### Paso 1: Crear Proyecto en Google Cloud
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto llamado "CB Valsequillo Scraper"
3. Selecciona el proyecto

### Paso 2: Habilitar Google Calendar API
1. En el menú lateral → **APIs y servicios** → **Biblioteca**
2. Busca "Google Calendar API"
3. Haz clic en **HABILITAR**

### Paso 3: Crear Credenciales (Service Account)
1. Ve a **APIs y servicios** → **Credenciales**
2. Haz clic en **+ CREAR CREDENCIALES** → **Cuenta de servicio**
3. Nombre: `valsequillo-calendar-bot`
4. Haz clic en **CREAR Y CONTINUAR**
5. Rol: **Editor** (o "Calendar Event Editor" si está disponible)
6. Haz clic en **LISTO**

### Paso 4: Descargar Clave JSON
1. En la lista de Cuentas de servicio, haz clic en la que acabas de crear
2. Ve a la pestaña **CLAVES**
3. **AGREGAR CLAVE** → **Crear clave nueva** → **JSON**
4. Se descargará un archivo `.json` (guárdalo seguro)

### Paso 5: Crear Google Calendar Público
1. Abre [Google Calendar](https://calendar.google.com)
2. En "Otros calendarios" → **+** → **Crear calendario**
3. Nombre: `CB Valsequillo - Partidos`
4. Haz clic en **Crear calendario**
5. Ve a **Configuración del calendario**
6. Copia el **ID del calendario** (ej: `abc123@group.calendar.google.com`)
7. En **Permisos de acceso**, marca **Hacer disponible públicamente**

### Paso 6: Dar acceso al Service Account
1. En Configuración del calendario → **Compartir con usuarios y grupos en particular**
2. Añade el email de tu service account (lo encontrarás en el archivo JSON, campo `client_email`)
3. Permisos: **Hacer cambios en los eventos**
4. **Enviar**

### Paso 7: Añadir Secretos a GitHub
1. Ve a tu repositorio en GitHub
2. **Settings** → **Secrets and variables** → **Actions**
3. Añade estos secretos:

   - **GOOGLE_CALENDAR_ID**: `abc123@group.calendar.google.com` (el ID que copiaste)
   - **GOOGLE_CREDENTIALS_JSON**: Pega TODO el contenido del archivo JSON descargado

---

## 🚀 Uso

Una vez configurado:
1. El script automáticamente **sincroniza los partidos** al calendario cada lunes
2. **Borra eventos antiguos** (partidos ya jugados)
3. **Añade nuevos eventos** con alarmas

### Compartir el Calendario
Cualquiera puede suscribirse con este enlace:
```
https://calendar.google.com/calendar/u/0?cid=TU_CALENDAR_ID_AQUI
```

O buscar "CB Valsequillo - Partidos" en Google Calendar.

---

## 🔧 Código (Ya incluido en scraper_baloncesto.py)

El método `sincronizar_google_calendar()` se encarga de todo automáticamente.

---

## ⚠️ Seguridad
- **NUNCA** subas el archivo JSON a Git (ya está en .gitignore)
- Las credenciales están seguras en GitHub Secrets
- Solo el service account tiene acceso al calendario
