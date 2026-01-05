# 🤖 Guía de Configuración - GitHub Actions

## 📋 Requisitos Previos

1. ✅ Tener una cuenta de GitHub (si no tienes, crea una gratis en [github.com](https://github.com))
2. ✅ Tener Git instalado en tu PC

### Verificar Git
```bash
git --version
```

Si no tienes Git, descárgalo de: https://git-scm.com/downloads

---

## 🚀 Configuración en 5 Pasos

### **Paso 1: Crear Repositorio en GitHub**

1. Ve a [github.com](https://github.com) e inicia sesión
2. Haz clic en el botón verde **"New"** (esquina superior derecha)
3. Rellena:
   - **Repository name**: `scraper-baloncesto-valsequillo`
   - **Description**: `Scraper automático de partidos del CB Valsequillo`
   - **Visibilidad**: Elige **Private** (privado) o **Public** (público)
   - ✅ **NO** marques "Add a README file"
4. Haz clic en **"Create repository"**

---

### **Paso 2: Configurar Git en tu PC** (solo primera vez)

Abre PowerShell o CMD y ejecuta:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu_email@ejemplo.com"
```

*(Usa el mismo email de tu cuenta de GitHub)*

---

### **Paso 3: Subir el Código a GitHub**

Abre PowerShell en la carpeta del proyecto y ejecuta estos comandos **uno por uno**:

```bash
# 1. Ir a la carpeta del proyecto
cd "c:\Users\fmunoz\Downloads\PRUEBA PDF"

# 2. Inicializar Git
git init

# 3. Añadir todos los archivos
git add .

# 4. Crear el primer commit
git commit -m "🏀 Scraper automático de partidos Valsequillo"

# 5. Renombrar la rama a 'main'
git branch -M main

# 6. Conectar con GitHub (REEMPLAZA TU_USUARIO con tu nombre de usuario de GitHub)
git remote add origin https://github.com/TU_USUARIO/scraper-baloncesto-valsequillo.git

# 7. Subir el código
git push -u origin main
```

**⚠️ IMPORTANTE:** En el paso 6, reemplaza `TU_USUARIO` con tu nombre de usuario real de GitHub.

**Ejemplo:**
Si tu usuario es `juanperez`, el comando sería:
```bash
git remote add origin https://github.com/juanperez/scraper-baloncesto-valsequillo.git
```

---

### **Paso 4: Activar GitHub Actions**

1. Ve a tu repositorio en GitHub
2. Haz clic en la pestaña **"Actions"**
3. Si aparece un botón verde, haz clic en **"I understand my workflows, go ahead and enable them"**
4. Verás el workflow **"Scraper Automático de Partidos"**

---

### **Paso 5: Configurar Permisos (Opcional)**

Si quieres que GitHub Actions haga commits automáticos de los PDFs:

1. Ve a tu repositorio → **Settings** → **Actions** → **General**
2. En "Workflow permissions":
   - Selecciona **"Read and write permissions"**
   - Marca la casilla **"Allow GitHub Actions to create and approve pull requests"**
3. Haz clic en **"Save"**

---

## ✅ ¡Ya Está Configurado!

### 🕐 ¿Cuándo se ejecuta?

**Automáticamente:**
- Todos los **lunes a las 8:00 AM** (hora UTC = 9:00 AM hora de Canarias)

**Manualmente:**
1. Ve a tu repo → pestaña **"Actions"**
2. Selecciona **"Scraper Automático de Partidos"**
3. Haz clic en **"Run workflow"** → **"Run workflow"**

---

## 📥 ¿Cómo Descargar los Resultados?

### Opción 1: Artifacts (Archivos Temporales)

1. Ve a **Actions** en tu repositorio
2. Haz clic en la ejecución más reciente (aparece con ✅ verde)
3. Baja hasta **"Artifacts"**
4. Haz clic en **`partidos-valsequillo-X`** para descargar
5. Descomprime el ZIP y tendrás:
   - `PARTIDOS_VALSEQUILLO_DD_MM.pdf`
   - `partidos_valsequillo_*.xlsx`
   - `jornada_*.pdf` (PDF original descargado)

**⚠️ Nota:** Los artifacts se borran automáticamente después de 30 días.

### Opción 2: Commits Automáticos (si activaste write permissions)

Si configuraste los permisos de escritura, los PDFs se guardarán directamente en el repositorio.

---

## 🎯 Ejemplos de Uso

### Ver historial de ejecuciones
```
Repositorio → Actions → Ver lista de ejecuciones
```

### Ejecutar manualmente
```
Actions → Scraper Automático de Partidos → Run workflow
```

### Descargar última jornada
```
Actions → Última ejecución → Artifacts → Download
```

---

## 🔧 Personalización

### Cambiar el horario de ejecución

Edita `.github/workflows/scraper_automatico.yml`:

```yaml
schedule:
  - cron: '0 8 * * 1'  # Lunes 8:00 AM
```

**Ejemplos:**
- `'0 20 * * 5'` - Viernes 8:00 PM
- `'0 9 * * 1,4'` - Lunes y Jueves 9:00 AM
- `'0 10 * * *'` - Todos los días 10:00 AM

Después de editar:
```bash
git add .github/workflows/scraper_automatico.yml
git commit -m "Cambiar horario de ejecución"
git push
```

---

## ❓ Solución de Problemas

### Error: "remote: Repository not found"
- Verifica que pusiste bien tu nombre de usuario
- Asegúrate de que el repositorio existe en GitHub

### Error: "Authentication failed"
- GitHub te pedirá usuario y contraseña
- **Importante:** En lugar de tu contraseña, usa un **Personal Access Token**
- Crea uno en: GitHub → Settings → Developer settings → Personal access tokens → Generate new token

### El workflow no se ejecuta
- Verifica que esté activado en Actions
- Comprueba que el archivo `.github/workflows/scraper_automatico.yml` existe
- Revisa los permisos del repositorio

### Los artifacts no aparecen
- Espera a que la ejecución termine (✅ verde)
- Verifica que no haya errores en los logs
- Los artifacts tienen 30 días de caducidad

---

## 🎊 ¡Disfruta de tu Scraper Automático!

Ahora cada lunes tendrás automáticamente:
- 📄 PDF profesional con el logo del club
- 📊 Excel con todos los partidos
- 💚 Todo con los colores corporativos de Valsequillo

**¿Necesitas ayuda?** Revisa los logs en la pestaña Actions de tu repositorio.

---

**Última actualización:** 05/01/2026  
**Modo:** Antigravedad Total Activado 🚀🏀
