# 📧 Guía de Configuración - Email Automático

## 🎯 ¿Qué hace esto?

Cada lunes a las 8:00 AM recibirás un **email automático** con:
- ✅ El PDF de partidos adjunto
- ✅ Un mensaje bonito con los colores del club
- ✅ Sin tener que hacer nada

---

## 🔐 Configuración de Secrets en GitHub

Para enviar emails, necesitas configurar 3 "secretos" en GitHub:

### **Paso 1: Obtener Contraseña de Aplicación de Gmail**

#### Si usas Gmail:

1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. En el menú izquierdo, haz clic en **"Seguridad"**
3. Busca **"Verificación en dos pasos"** y actívala (si no la tienes)
4. Una vez activada, busca **"Contraseñas de aplicaciones"**
5. Haz clic en **"Contraseñas de aplicaciones"**
6. En "Seleccionar app", elige **"Correo"**
7. En "Seleccionar dispositivo", elige **"Otro"** y escribe: `GitHub Actions`
8. Haz clic en **"Generar"**
9. **COPIA** la contraseña de 16 caracteres que aparece (algo como: `abcd efgh ijkl mnop`)
10. ⚠️ **Guárdala en un lugar seguro**, no la volverás a ver

#### Si usas otro email (Outlook, Yahoo, etc.):

- **Outlook/Hotmail**: 
  - Servidor: `smtp-mail.outlook.com`
  - Puerto: `587`
  - Crea una contraseña de aplicación en: https://account.live.com/proofs/AppPassword

- **Yahoo**:
  - Servidor: `smtp.mail.yahoo.com`
  - Puerto: `587`
  - Crea una contraseña de aplicación en tu configuración de seguridad

---

### **Paso 2: Configurar Secrets en GitHub**

1. Ve a tu repositorio en GitHub
2. Haz clic en **"Settings"** (⚙️)
3. En el menú izquierdo, haz clic en **"Secrets and variables"** → **"Actions"**
4. Haz clic en **"New repository secret"** (botón verde)

Crea **3 secrets** uno por uno:

#### Secret 1: EMAIL_USERNAME
- **Name**: `EMAIL_USERNAME`
- **Value**: Tu email completo (ejemplo: `tu_email@gmail.com`)
- Haz clic en **"Add secret"**

#### Secret 2: EMAIL_PASSWORD
- **Name**: `EMAIL_PASSWORD`
- **Value**: La contraseña de aplicación que copiaste (los 16 caracteres)
- Haz clic en **"Add secret"**

#### Secret 3: EMAIL_TO
- **Name**: `EMAIL_TO`
- **Value**: El email donde quieres recibir los partidos (puede ser el mismo u otro)
- Haz clic en **"Add secret"**

---

### **Paso 3: Verificar Configuración**

Deberías ver 3 secrets:
```
EMAIL_USERNAME
EMAIL_PASSWORD
EMAIL_TO
```

⚠️ **Importante**: Los valores de los secrets NO se pueden ver después de crearlos (por seguridad). Si te equivocaste, simplemente bórralo y créalo de nuevo.

---

## ✅ ¡Ya está configurado!

### 🕐 ¿Cuándo recibiré el email?

**Automáticamente:**
- Todos los **lunes a las 9:00 AM** (hora de Canarias)

**También puedes probarlo manualmente:**
1. Ve a tu repo → **Actions**
2. Selecciona **"Scraper Automático de Partidos"**
3. Haz clic en **"Run workflow"** → **"Run workflow"**
4. Espera ~2 minutos
5. ¡Recibirás el email!

---

## 📧 ¿Cómo se verá el email?

**Asunto:**
```
🏀 Partidos Valsequillo - #123
```

**Cuerpo del email:**
```
🏀 Partidos del CB Valsequillo

Hola,

Te adjunto el PDF con los próximos partidos de Valsequillo.

Generado automáticamente: 2026-01-05

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Club de Baloncesto Valsequillo - Roque Grande

Este email se envía automáticamente cada lunes.
```

**Adjunto:**
- `PARTIDOS_VALSEQUILLO_05_01.pdf` 📎

---

## 🔧 Personalizar el Email

Si quieres cambiar el mensaje del email, edita `.github/workflows/scraper_automatico.yml`:

```yaml
html_body: |
  <h2>🏀 Tus partidos están listos</h2>
  <p>¡Hola!</p>
  <p>Aquí tienes los partidos de esta semana.</p>
```

Después:
```bash
git add .github/workflows/scraper_automatico.yml
git commit -m "Personalizar email"
git push
```

---

## 📱 Cambiar el Email de Destino

Si quieres enviar a otro email (o a varios):

### Opción 1: Cambiar el Secret
1. GitHub → Settings → Secrets → EMAIL_TO
2. Update secret
3. Pon el nuevo email (o varios separados por coma: `email1@gmail.com, email2@gmail.com`)

### Opción 2: Enviar a múltiples personas
Edita el workflow:
```yaml
to: email1@gmail.com, email2@gmail.com, email3@gmail.com
```

---

## ❓ Solución de Problemas

### Error: "Invalid credentials"
- Verifica que EMAIL_USERNAME y EMAIL_PASSWORD sean correctos
- Asegúrate de usar la **contraseña de aplicación**, NO tu contraseña normal
- Si usas Gmail, verifica que la verificación en dos pasos esté activa

### No recibo el email
- Revisa la carpeta de **SPAM/Correo no deseado**
- Verifica que EMAIL_TO tenga el email correcto
- Comprueba los logs en Actions para ver si hay errores

### El email llega sin adjunto
- Verifica que el PDF se generó correctamente en los logs
- Comprueba que el step "Obtener nombre del PDF" funcionó

### Quiero usar otro servidor SMTP
Edita el workflow:
```yaml
server_address: smtp.tu-servidor.com
server_port: 587
```

---

## 🎊 ¡Disfruta de tus Emails Automáticos!

Ahora cada lunes:
1. ⏰ 8:00 AM - GitHub ejecuta el scraper
2. 📄 Genera el PDF con el logo del club
3. 📧 Te envía el email con el PDF adjunto
4. 📱 Recibes la notificación en tu móvil

**Todo sin tocar tu ordenador** 🚀

---

## 🔒 Seguridad

- ✅ Las contraseñas están cifradas en GitHub Secrets
- ✅ Nadie puede ver tus secrets (ni tú después de crearlos)
- ✅ Se usa una contraseña de aplicación, no tu contraseña real
- ✅ Puedes revocar el acceso en cualquier momento

---

**Última actualización:** 05/01/2026  
**Modo:** Email Automático Activado 📧🏀
