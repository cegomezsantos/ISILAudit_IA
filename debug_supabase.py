import streamlit as st
from supabase import create_client
import json

st.title("🔍 Debug Supabase - ISILAudit IA")

st.write("## 1. Verificación de Secrets")

# Verificar si st.secrets está disponible
if hasattr(st, 'secrets') and st.secrets:
    st.success("✅ st.secrets está disponible")
    st.write("**Keys disponibles:**", list(st.secrets.keys()))
    
    # Verificar variables específicas
    url = st.secrets.get("SUPABASE_URL", "❌ NO ENCONTRADA")
    key = st.secrets.get("SUPABASE_KEY", "❌ NO ENCONTRADA")
    
    st.write("**SUPABASE_URL:**", "✅ Configurada" if url != "❌ NO ENCONTRADA" else url)
    st.write("**SUPABASE_KEY:**", "✅ Configurada" if key != "❌ NO ENCONTRADA" else key)
    
    if url != "❌ NO ENCONTRADA":
        st.write("**URL completa:**", url)
    
    if key != "❌ NO ENCONTRADA":
        st.write("**Key (primeros 20 chars):**", key[:20] + "...")
        
else:
    st.error("❌ st.secrets no está disponible")

st.write("## 2. Test de Conexión")

try:
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    
    if url and key:
        st.write("**Intentando crear cliente Supabase...**")
        client = create_client(url, key)
        st.success("✅ Cliente Supabase creado exitosamente")
        
        st.write("**Probando conexión con tabla validated_urls...**")
        result = client.table('validated_urls').select('*').limit(1).execute()
        st.success("✅ Conexión a tabla validated_urls exitosa")
        st.write("**Datos de prueba:**", result.data)
        
        st.write("**Probando inserción de datos de prueba...**")
        test_data = {
            'filename': 'test_debug.pptx',
            'slide_number': 1,
            'url': 'https://www.google.com',
            'url_domain': 'google.com',
            'location_context': 'Debug test',
            'text_context': 'Test context',
            'status': '200',
            'status_description': 'OK',
            'checked_at': '2024-01-01T00:00:00.000Z',
            'subfolder': 'DEBUG-TEST',
            'processed_by': 'debug_user',
        }
        
        insert_result = client.table('validated_urls').insert(test_data).execute()
        st.success("✅ Inserción de datos de prueba exitosa")
        st.write("**Resultado de inserción:**", insert_result.data)
        
    else:
        st.error("❌ Variables SUPABASE_URL o SUPABASE_KEY no configuradas")
        
except Exception as e:
    st.error(f"❌ Error en conexión: {str(e)}")
    st.write("**Tipo de error:**", type(e).__name__)
    st.write("**Detalle completo:**", str(e))

st.write("## 3. Información del Entorno")
st.write("**Streamlit version:**", st.__version__)

# Verificar si estamos en Streamlit Cloud
if hasattr(st, 'secrets'):
    st.write("**Entorno:** Streamlit Cloud")
else:
    st.write("**Entorno:** Local")

st.write("## 4. Estructura de la Tabla")
st.code("""
CREATE TABLE validated_urls (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    slide_number INTEGER NOT NULL DEFAULT 1,
    url TEXT NOT NULL,
    url_domain VARCHAR(255),
    location_context TEXT,
    text_context TEXT,
    status VARCHAR(100),
    status_description TEXT,
    checked_at TIMESTAMPTZ,
    subfolder VARCHAR(255),
    processed_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
""")

st.write("## 5. Instrucciones de Solución")
st.info("""
**Si ves errores:**

1. **Verificar que la tabla existe:** Ejecuta el SQL de `simplified_database.sql` en Supabase
2. **Verificar credenciales:** Asegúrate de que SUPABASE_URL y SUPABASE_KEY estén en Streamlit Secrets
3. **Verificar formato:** Las credenciales no deben tener espacios extra
4. **Verificar permisos:** La clave debe ser la "anon public key" de Supabase
""") 