# 🚨 Solución para Problemas en Streamlit Cloud

## 📋 Problemas Detectados:
1. ❌ "Supabase: No configurado" 
2. ❌ "Archivo credentials.json no encontrado"

## 🔧 Soluciones Paso a Paso

### PASO 1: Ejecutar SQL en Supabase ⚠️ CRÍTICO

**ANTES QUE NADA**, necesitas crear la tabla en Supabase:

1. Ve a: https://supabase.com/dashboard/projects/ktxmkdazgguqiubbalwj
2. Clic en **"SQL Editor"** (menú izquierdo)
3. Crea una **Nueva Query**
4. **Copia y pega todo el contenido** del archivo `simplified_database.sql`
5. **Ejecuta** haciendo clic en "Run" o Ctrl+Enter

**⚠️ Sin este paso, Supabase no funcionará**

### PASO 2: Verificar Secrets en Streamlit Cloud

1. Ve a tu app en Streamlit Cloud
2. **Settings** → **Secrets**
3. Asegúrate de que tengas exactamente esto:

```toml
SUPABASE_URL = "https://ktxmkdazgguqiubbalwj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0eG1rZGF6Z2d1cWl1YmJhbHdqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkwMDEwNDQsImV4cCI6MjA2NDU3NzA0NH0.wbbVT69NfHHhYWCslZ44o_P4vb6cGUXg41SwszmQSfw"
```

**⚠️ IMPORTANTE:**
- NO debe haber espacios al inicio o final
- NO debe haber comillas extra
- Debe ser exactamente como se muestra arriba

### PASO 3: Subir código actualizado

1. **Hacer commit** de los cambios:
```bash
git add .
git commit -m "fix: Modo cloud con datos de ejemplo y mejor debug"
git push origin main
```

2. **Esperar** a que Streamlit Cloud se actualice (1-2 minutos)

### PASO 4: Probar la aplicación

1. **Hacer login** con uno de estos usuarios:
   - admin / 09678916
   - jsato / SanManz12025  
   - rrepetto / SanManz22025

2. **Ir a la pestaña URL**

3. **Deberías ver**:
   - "🌐 Modo Streamlit Cloud Detectado"
   - "🗄️ Supabase: Configurado" en el sidebar

4. **Generar datos de ejemplo**:
   - Clic en "🎯 Generar Datos de Ejemplo"
   - Luego "🔍 Validar Estado de URLs"
   - Finalmente "📤 Enviar Datos Validados a Supabase"

## 🔍 Debug Adicional

Si aún no funciona, crea temporalmente este archivo `debug.py`:

```python
import streamlit as st

st.title("🔍 Debug Streamlit Cloud")

st.write("**Variables disponibles:**")
if hasattr(st, 'secrets') and st.secrets:
    st.write("✅ st.secrets funciona")
    st.write("Keys:", list(st.secrets.keys()))
    
    url = st.secrets.get("SUPABASE_URL", "❌ NO ENCONTRADA")
    key = st.secrets.get("SUPABASE_KEY", "❌ NO ENCONTRADA") 
    
    st.write("SUPABASE_URL:", "✅ OK" if url != "❌ NO ENCONTRADA" else url)
    st.write("SUPABASE_KEY:", "✅ OK" if key != "❌ NO ENCONTRADA" else key)
else:
    st.write("❌ st.secrets no disponible")

# Probar conexión
try:
    from supabase import create_client
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    
    if url and key:
        client = create_client(url, key)
        result = client.table('validated_urls').select('*').limit(1).execute()
        st.write("✅ Conexión Supabase OK")
    else:
        st.write("❌ Variables no configuradas")
except Exception as e:
    st.write("❌ Error:", str(e))
```

**Subir este debug.py y cambiar temporalmente Main file path a `debug.py`**

## 📞 Si sigue sin funcionar

**Compárteme:**
1. **Screenshot** del SQL Editor después de ejecutar el script
2. **Screenshot** de tus Secrets en Streamlit Cloud
3. **Screenshot** del debug.py funcionando

**Posibles causas adicionales:**
- La tabla no se creó correctamente
- Las credenciales tienen caracteres especiales
- Hay problemas de caché en Streamlit Cloud

## ✅ Resultado esperado

Al final deberías tener:
- ✅ Login funcionando
- ✅ "Supabase: Configurado" en sidebar  
- ✅ Modo demo funcionando con datos de ejemplo
- ✅ Validación de URLs funcionando
- ✅ Guardado en Supabase funcionando 