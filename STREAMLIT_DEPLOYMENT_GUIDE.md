# 🚀 Guía de Despliegue Seguro en Streamlit Cloud

## 📋 Preparación antes del despliegue

### 1. Verificar archivos sensibles
Antes de subir a GitHub, asegúrate de que estos archivos estén en `.gitignore`:

```
# Archivos sensibles - NO SUBIR A GITHUB
credentials.json
token.json
.streamlit/secrets.toml

# Archivos temporales
*.pyc
__pycache__/
.env
*.log
```

### 2. Crear archivo de ejemplo para secrets
Crea `.streamlit/secrets.toml.example`:

```toml
# Configuración de secretos para ISILAudit IA
# IMPORTANTE: Duplicar este archivo como secrets.toml y configurar con datos reales

SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-clave-anonima-aqui"

# Credenciales de Google Drive (opcional para producción)
# GOOGLE_CREDENTIALS = '{"type": "service_account", ...}'
```

### 3. Actualizar requirements.txt
Asegúrate de que tu `requirements.txt` esté actualizado:

```txt
streamlit>=1.28.0
google-auth>=2.22.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.100.0
supabase>=1.0.0
pandas>=2.0.0
python-pptx>=0.6.21
requests>=2.31.0
```

## 🔧 Pasos para el despliegue

### Paso 1: Preparar repositorio GitHub

1. **Verificar `.gitignore`**:
```bash
# En tu terminal local
cat .gitignore
```

2. **Hacer commit de cambios**:
```bash
git add .
git commit -m "feat: Sistema de login y base de datos simplificada"
git push origin main
```

### Paso 2: Configurar Streamlit Cloud

1. **Ir a [share.streamlit.io](https://share.streamlit.io)**

2. **Conectar con GitHub** y seleccionar tu repositorio

3. **Configurar la aplicación**:
   - **Repository**: `tu-usuario/ISILAudit_IA`
   - **Branch**: `main`
   - **Main file path**: `app.py`

### Paso 3: Configurar Secrets de manera segura

En Streamlit Cloud, ve a **Settings > Secrets** y agrega:

```toml
# Configuración de Supabase
SUPABASE_URL = "<TU_SUPABASE_URL>"
SUPABASE_KEY = "<TU_SUPABASE_KEY>"

# Configuración adicional de seguridad (opcional)
SESSION_SECRET = "tu-clave-secreta-para-sesiones"
```
Reemplaza los valores entre `<...>` con las credenciales de tu proyecto.

### Paso 4: Ejecutar SQL en Supabase

1. **Ir a tu proyecto Supabase**: https://supabase.com/dashboard/projects/<tu-proyecto>

2. **Ir a SQL Editor**

3. **Ejecutar el script** `simplified_database.sql`:
```sql
-- Copia y pega todo el contenido del archivo simplified_database.sql
-- Este script:
-- - Borra las tablas anteriores
-- - Crea la nueva tabla validated_urls
-- - Configura índices y políticas de seguridad
```

4. **Verificar la creación**:
```sql
-- Verificar que la tabla fue creada
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'validated_urls';
```

### Paso 5: Verificar despliegue

1. **Esperar a que termine el despliegue** (1-3 minutos)

2. **Probar la aplicación**:
   - Login con uno de los usuarios: `admin`, `jsato`, `rrepetto`
   - Verificar conexión a Supabase
   - Probar funcionalidad básica

## 🔒 Consideraciones de seguridad

### Variables de entorno seguras

✅ **CORRECTO** - En Streamlit Secrets:
```toml
SUPABASE_URL = "https://proyecto.supabase.co"
SUPABASE_KEY = "clave-publica-anonima"
```

❌ **INCORRECTO** - En código:
```python
# NUNCA hacer esto
SUPABASE_URL = "https://proyecto.supabase.co"
```

### Usuarios y contraseñas

**Actualizar contraseñas en producción**:
```python
# En app.py - cambiar por contraseñas más seguras
USERS = {
    "admin": "contraseña-segura-admin-2024",
    "jsato": "contraseña-segura-jsato-2024", 
    "rrepetto": "contraseña-segura-rrepetto-2024"
}
```

### Políticas de base de datos

Las políticas RLS (Row Level Security) están configuradas para:
- Solo usuarios autenticados pueden acceder
- Cada usuario ve solo sus datos procesados

## 🚨 Solución de problemas comunes

### Error: "No module named 'pptx_analyzer'"
```python
# En app.py, verificar que el import tenga fallback:
try:
    from pptx_analyzer import PPTXURLExtractor
except ImportError:
    # Usar datos de ejemplo si no está disponible
    pass
```

### Error de conexión a Supabase
1. Verificar que las URLs no tengan espacios en blanco
2. Verificar que la clave sea la "anon public key"
3. Revisar que RLS esté configurado correctamente

### Error de autenticación Google Drive
- En producción, usar Service Account en lugar de OAuth
- Configurar credenciales en Streamlit Secrets

## 📊 Monitoreo post-despliegue

### Logs de aplicación
```bash
# En Streamlit Cloud, ir a Settings > Logs
# Monitorear errores y uso
```

### Métricas de Supabase
```sql
-- Consultar uso de la tabla
SELECT 
    processed_by,
    COUNT(*) as urls_processed,
    MAX(created_at) as last_activity
FROM validated_urls 
GROUP BY processed_by;
```

### Verificación de funcionalidades
- [ ] Login funciona correctamente
- [ ] Conexión a Google Drive
- [ ] Extracción de URLs
- [ ] Validación de URLs
- [ ] Guardado en Supabase
- [ ] Descarga de CSV

## 🔄 Actualizaciones futuras

Para actualizar la aplicación:

1. **Hacer cambios localmente**
2. **Commit y push a GitHub**:
```bash
git add .
git commit -m "feat: nueva funcionalidad"
git push origin main
```
3. **Streamlit Cloud se actualiza automáticamente**

## 📞 Soporte

Si encuentras problemas:
1. Revisar logs en Streamlit Cloud
2. Verificar estado de Supabase
3. Comprobar configuración de secrets
4. Revisar políticas de base de datos

---

**✅ Lista de verificación final:**
- [ ] Archivo secrets.toml no está en GitHub
- [ ] Variables de entorno configuradas en Streamlit
- [ ] Base de datos actualizada con nuevo SQL
- [ ] Aplicación desplegada y funcionando
- [ ] Login probado con todos los usuarios
- [ ] Funcionalidad de URLs probada
- [ ] Conexión a Supabase verificada 