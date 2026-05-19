# Despliegue del Frontend en AWS S3 + CloudFront

## 1. Introducción

Este documento describe el proceso completo de despliegue del frontend de la plataforma AI Recruitment en AWS, utilizando **S3 (almacenamiento)** + **CloudFront (distribución CDN)** para servir contenido estático con HTTPS.

**Ventajas de esta arquitectura:**
- S3: Almacenamiento escalable y económico
- CloudFront: Red de distribución de contenidos (CDN) global
- HTTPS automático y gratuito
- Hosting de aplicaciones single-page (SPA)
- Pay-as-you-go: Solo pagas por lo que uses (~$5-10/mes típico)

---

## 2. Prerequisitos

- Cuenta AWS activa con billing habilitado
- Acceso a AWS Management Console (https://console.aws.amazon.com)
- Archivos del frontend listos (HTML, CSS, JS)

**Nota:** Este proceso se realiza completamente desde la consola web de AWS, sin necesidad de CLI local.

---

## 3. Paso 1: Crear el Bucket S3

### 3.1 Acceder a S3 Console

1. Abre https://console.aws.amazon.com/s3/
2. Click en **"Create bucket"**

### 3.2 Configurar el bucket

| Campo | Valor |
|-------|-------|
| **Bucket name** | `mi-recruitment-app-2026` (debe ser único globalmente) |
| **Region** | `eu-west-1` (Europa - Irlanda) |
| **Block Public Access** | Dejar default (lo cambiaremos después) |

3. Click **"Create bucket"**

**Resultado:** Bucket creado y visible en S3 Console.

---

## 4. Paso 2: Subir archivos del frontend

### 4.1 Archivos a subir

```
frontend/
├── index.html
├── styles.css
├── TESTING_GUIDE.js (opcional)
└── js/
    ├── app.js
    ├── config.js
    ├── mock-auth.js
    ├── api-client.js
    ├── router.js
    ├── utils.js
    └── pages/
        ├── home.js
        ├── job-detail.js
        ├── apply.js
        ├── hr-dashboard.js
        └── admin-dashboard.js
```

### 4.2 Subir archivos (Drag & Drop)

1. **S3 Console** → Click en tu bucket `mi-recruitment-app-2026`
2. Selecciona todos los archivos y la carpeta `js/` en tu PC
3. **Arrastra y suelta** en la ventana de S3 Console
4. Espera a que termine la carga

**Alternativa (si drag&drop no funciona):**
1. Click **"Upload"**
2. Click **"Add files"** → selecciona archivo
3. Click **"Upload"**
4. Repite para cada archivo

**Resultado:** Todos los archivos subidos a S3.

---

## 5. Paso 3: Configurar permisos públicos

### 5.1 Modificar block public access

1. **S3 Console** → Tu bucket → Tab **"Permissions"**
2. Encuentra **"Block public access (bucket settings)"**
3. Click **"Edit"**
4. **Desactiva todos los checkboxes:**
   - ☐ Block all public access
   - ☐ Ignore all public ACLs
   - ☐ Block public ACLs
   - ☐ Block public policies
   - ☐ Restrict public buckets
5. Click **"Save changes"**
6. Confirma escribiendo `confirm`

### 5.2 Agregar bucket policy

1. En la misma tab **"Permissions"**, baja a **"Bucket policy"**
2. Click **"Edit"**
3. Copia y pega la siguiente política (reemplaza el nombre del bucket):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::mi-recruitment-app-2026/*"
    }
  ]
}
```

4. Click **"Save"**

**Resultado:** Bucket es accesible públicamente.

---

## 6. Paso 4: Habilitar Static Website Hosting

### 6.1 Configurar hosting estático

1. **S3 Console** → Tu bucket → Tab **"Properties"**
2. Baja hasta **"Static website hosting"**
3. Click **"Edit"**
4. Selecciona **"Enable"**
5. **Index document:** `index.html`
6. **Error document:** `index.html` (importante para SPA routing)
7. Click **"Save changes"**

### 6.2 Obtener URL del endpoint

Copia la **URL del website endpoint** que aparece, ejemplo:
```
http://mi-recruitment-app-2026.s3-website-eu-west-1.amazonaws.com
```

**Nota:** Esta URL funciona pero es HTTP. Usaremos CloudFront para HTTPS.

**Resultado:** Website hosting habilitado en S3.

---

## 7. Paso 5: Crear distribución CloudFront (HTTPS)

### 7.1 Acceder a CloudFront Console

1. Abre https://console.aws.amazon.com/cloudfront/
2. Click **"Create distribution"**

### 7.2 Configurar origen

**Origin domain:**
- Selecciona tu bucket: `mi-recruitment-app-2026.s3.eu-west-1.amazonaws.com`
- ⚠️ **Importante:** SIN `-website-` en la URL

**Grant CloudFront access to origin:** `Yes`

### 7.3 Configurar comportamiento de caché

| Campo | Valor |
|-------|-------|
| **Viewer protocol policy** | `Redirect HTTP to HTTPS` |
| **Allowed HTTP methods** | `GET, HEAD` |
| **Cache policy** | `CachingOptimized` |

### 7.4 Configurar responses de error

En la sección **"Error pages"**, crea dos custom error responses:

**Error Response 1 (403):**
- HTTP error code: `403`
- Customize error response: ✓ YES
- Response page path: `/index.html`
- HTTP response code: `200`
- Click **"Create"**

**Error Response 2 (404):**
- HTTP error code: `404`
- Customize error response: ✓ YES
- Response page path: `/index.html`
- HTTP response code: `200`
- Click **"Create"**

**Nota:** Esto es crítico para que el SPA routing funcione correctamente.

### 7.5 Crear distribución

1. Click **"Create distribution"** (en Review and create)
2. **Espera 5-10 minutos** a que se despliegue

**Resultado:** Distribution con status "Enabled".

---

## 8. Paso 6: Obtener URL de acceso

### 8.1 Copiar domain name

1. **CloudFront Console** → **Distributions**
2. Encuentra `recruitment-app-distribution`
3. Verifica que Status sea **"Enabled"**
4. Copia el **"Domain name"** (ej: `d12345abcde.cloudfront.net`)

### 8.2 URLs disponibles

Después del despliegue tienes:

| Descripción | URL |
|------------|-----|
| S3 Website (HTTP) | `http://mi-recruitment-app-2026.s3-website-eu-west-1.amazonaws.com` |
| CloudFront (HTTPS) ⭐ | `https://d12345abcde.cloudfront.net` |

**Usa la URL de CloudFront** para acceso seguro.

---

## 9. Paso 7: Verificar y acceder

### 9.1 Probar el frontend

1. Abre en navegador: `https://d12345abcde.cloudfront.net`
2. Deberías ver:
   - ✓ Página de inicio con listado de ofertas
   - ✓ Header con navegación
   - ✓ Footer
   - ✓ Formulario de búsqueda funcional

### 9.2 Pruebas funcionales

1. **Autenticación:** Login con `admin@example.com` / `admin123`
2. **Navegación:** Muévete entre páginas sin errores
3. **Formularios:** Intenta rellenar forms
4. **Storage:** Abre console (F12) → Storage → localStorage
   - Deberías ver `ai_recruitment_auth` y `ai_recruitment_users`

---

## 10. Paso 8: Configurar backend URL

El frontend está desplegado, pero necesita conectar al backend.

### 10.1 Opción A: Backend en desarrollo local

```javascript
// Consola del navegador (F12)
apiClient.setBaseURL('http://localhost:8000');
window.location.reload();
```

### 10.2 Opción B: Editar config antes de desplegar

1. Edita `frontend/js/config.js`:

```javascript
API_BASE_URL: 'https://tu-backend-url.com'  // Cambiar aquí
```

2. Sube el archivo a S3
3. Invalida caché en CloudFront (siguiente sección)

### 10.3 Verificar conexión

```javascript
// Consola del navegador
await apiClient.healthCheck();
// Debería retornar: { message: "Backend funcionando correctamente" }
```

---

## 11. Actualizar archivos después del despliegue

### 11.1 Subir archivos actualizados

1. **S3 Console** → Tu bucket
2. Sube nuevamente los archivos modificados (Drag & drop o Upload)
3. Sobrescribe los existentes

### 11.2 Limpiar caché CloudFront

Para que se vean los cambios inmediatamente:

1. **CloudFront Console** → Tu distribución
2. Click en distribution name
3. Tab **"Invalidations"** → **"Create invalidation"**
4. **Object paths:** `/` (o `/*` para invalidar todo)
5. Click **"Create invalidation"**
6. Espera 1-2 minutos

**Resultado:** Cambios reflejados en tiempo real.

---

## 12. Monitoreo y costos

### 12.1 Monitorar uso

1. **CloudFront Console** → Tu distribución → **"Monitoring"**
2. Observa:
   - Requests (número de peticiones)
   - Data transferred (datos transferidos)
   - Bytes downloaded (bytes descargados)

### 12.2 Estimación de costos

**Precios típicos (mayo 2024):**
- S3: $0.023 por GB almacenado (primeros 50TB/mes)
- CloudFront: $0.085 por GB distribuido (primeros 10TB/mes)

**Ejemplo para aplicación pequeña:**
- 5 MB almacenados = ~$0.0001/mes
- 100 GB distribuidos/mes = ~$8.50/mes
- **Total estimado: ~$8-10/mes**

---

## 13. Troubleshooting

### Problema: Página en blanco

**Solución:**
1. Abre console (F12) → Network
2. ¿Hay errores 403 o 404?
3. Verifica que S3 bucket policy esté bien configurada
4. Crea invalidación en CloudFront

### Problema: Frontend carga pero no ve datos de API

**Solución:**
```javascript
// Consola (F12)
apiClient.setBaseURL('https://tu-backend-real.com');
location.reload();
```

### Problema: SPA routing no funciona

**Solución:**
- Verifica que error responses 403 y 404 estén configuradas en CloudFront
- Crua invalidación: `/`

### Problema: Cambios no aparecen

**Solución:**
1. Limpiar caché local: Ctrl+Shift+Delete
2. Crear invalidación en CloudFront
3. Esperar 5 minutos

---

## 14. Resumen de arquitectura

```
Usuario
  ↓
HTTPS
  ↓
CloudFront (CDN global)
  ↓
S3 Bucket (almacenamiento estático)
  ↓
index.html + CSS + JS
  ↓
SPA React-like (navegación cliente)
  ↓
Backend API (próximamente)
```

---

## 15. Checklist de despliegue

- [ ] Bucket S3 creado con nombre único
- [ ] Archivos frontend subidos (HTML, CSS, JS)
- [ ] Block public access desactivado
- [ ] Bucket policy configurada
- [ ] Static website hosting habilitado
- [ ] CloudFront distribution creada
- [ ] Error responses (403, 404) configuradas
- [ ] Distribution status: "Enabled"
- [ ] URL CloudFront funcional
- [ ] Frontend se ve correctamente
- [ ] Backend URL configurada
- [ ] API conectando correctamente

---

## 16. Documentación adicional

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [SPA Routing en CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/custom-error-pages.html)

---

## 17. Conclusión

El frontend de AI Recruitment Platform está ahora:

✅ Desplegado en infraestructura de producción (AWS)
✅ Servido a través de CDN global (CloudFront)
✅ Accesible con HTTPS seguro
✅ Listo para integración con backend
✅ Escalable automáticamente (pay-as-you-go)

**Próximas fases:**
1. Despliegue del backend (FastAPI + Amplify/Lambda)
2. Integración de autenticación real (AWS Cognito)
3. Procesamiento de CV con AgentCore
4. Análisis automático de candidatos

---

**Documento generado:** Mayo 2026
**Proyecto:** AI Recruitment Platform - TFG
**Versión:** 1.0
