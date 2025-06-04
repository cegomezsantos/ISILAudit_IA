import streamlit as st
import json

st.title("🔍 Debug Google Drive Credentials")

st.header("1. Verificar disponibilidad de st.secrets")
if hasattr(st, 'secrets'):
    st.success("✅ st.secrets está disponible")
    
    # Mostrar todas las keys disponibles
    try:
        available_keys = list(st.secrets.keys())
        st.write("**Keys disponibles en secrets:**", available_keys)
    except Exception as e:
        st.error(f"Error al leer keys: {e}")
    
    st.header("2. Verificar GOOGLE_CREDENTIALS específicamente")
    
    # Verificar si existe la key
    if 'GOOGLE_CREDENTIALS' in st.secrets:
        st.success("✅ GOOGLE_CREDENTIALS existe en secrets")
        
        # Obtener el valor
        try:
            credentials_raw = st.secrets["GOOGLE_CREDENTIALS"]
            st.write("**Tipo de dato:**", type(credentials_raw))
            st.write("**Longitud:**", len(str(credentials_raw)))
            
            # Mostrar primeros y últimos caracteres (sin exponer datos sensibles)
            cred_str = str(credentials_raw)
            st.write("**Primeros 50 caracteres:**", repr(cred_str[:50]))
            st.write("**Últimos 50 caracteres:**", repr(cred_str[-50:]))
            
            st.header("3. Intentar parsear JSON")
            try:
                credentials_dict = json.loads(credentials_raw)
                st.success("✅ JSON parseado correctamente")
                st.write("**Keys en el JSON:**", list(credentials_dict.keys()))
                
                # Verificar campos obligatorios
                required_fields = ["type", "project_id", "private_key", "client_email"]
                missing_fields = [field for field in required_fields if field not in credentials_dict]
                
                if not missing_fields:
                    st.success("✅ Todos los campos obligatorios están presentes")
                else:
                    st.error(f"❌ Campos faltantes: {missing_fields}")
                
                # Verificar que sea service account
                if credentials_dict.get("type") == "service_account":
                    st.success("✅ Tipo correcto: service_account")
                else:
                    st.error(f"❌ Tipo incorrecto: {credentials_dict.get('type')}")
                
            except json.JSONDecodeError as e:
                st.error(f"❌ Error al parsear JSON: {e}")
                st.write("**Posibles problemas:**")
                st.write("- Caracteres de escape incorrectos (\\n vs \\\\n)")
                st.write("- Comillas mal cerradas")
                st.write("- Formato JSON inválido")
                
                # Sugerir corrección
                st.header("4. Formato correcto esperado")
                st.code('''
GOOGLE_CREDENTIALS = \'\'\'
{
  "type": "service_account",
  "project_id": "agente-101",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMII...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "islaudit-streamlit@agente-101.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/islaudit-streamlit%40agente-101.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
\'\'\'
                ''')
            
        except Exception as e:
            st.error(f"❌ Error al acceder a GOOGLE_CREDENTIALS: {e}")
    
    else:
        st.error("❌ GOOGLE_CREDENTIALS NO existe en secrets")
        st.write("**Asegúrate de:**")
        st.write("1. Usar exactamente el nombre 'GOOGLE_CREDENTIALS'")
        st.write("2. Usar comillas triples '''")
        st.write("3. Escapar correctamente los caracteres \\n como \\\\n")

else:
    st.error("❌ st.secrets no está disponible")

st.header("5. Test de importación")
try:
    from google.oauth2 import service_account
    st.success("✅ google.oauth2.service_account importado correctamente")
except ImportError as e:
    st.error(f"❌ Error al importar google.oauth2.service_account: {e}")

st.header("6. Verificar otras dependencias")
try:
    import json
    st.success("✅ json disponible")
except:
    st.error("❌ json no disponible")

st.markdown("---")
st.info("📋 **Copia el resultado de este debug y compártelo para ayudarte a resolver el problema**") 