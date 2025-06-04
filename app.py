import streamlit as st
import os
import io
import zipfile
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from pptx import Presentation
import re
from urllib.parse import urlparse
import tempfile
import json
import requests
import time
from supabase import create_client, Client
from datetime import datetime
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Configuración de usuarios
USERS = {
    "admin": "09678916",
    "jsato": "SanManz12025", 
    "rrepetto": "SanManz22025"
}

def login_screen():
    """Pantalla de login simple"""
    st.set_page_config(
        page_title="ISILAudit IA - Login",
        page_icon="🔐",
        layout="centered"
    )
    
    # CSS personalizado para el login
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
    .login-title {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Título principal
    st.markdown("<h1 class='login-title'>🏭 ISILAudit IA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #666;'>Iniciar Sesión</h3>", unsafe_allow_html=True)
    
    # Contenedor del login
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Formulario de login
            with st.form("login_form"):
                usuario = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
                password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit_button = st.form_submit_button("🔐 Iniciar Sesión", use_container_width=True)
                
                if submit_button:
                    if usuario in USERS and USERS[usuario] == password:
                        st.session_state.authenticated = True
                        st.session_state.current_user = usuario
                        st.success("✅ ¡Login exitoso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
                        time.sleep(2)
                        st.rerun()
    
    # Información adicional
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; font-size: 0.8em;'>
        <p>🔒 Sistema de Auditoría Inteligente</p>
        <p>Para soporte técnico, contacta al administrador</p>
    </div>
    """, unsafe_allow_html=True)

def check_authentication():
    """Verificar si el usuario está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_screen()
        st.stop()

def logout():
    """Cerrar sesión"""
    st.session_state.authenticated = False
    if 'current_user' in st.session_state:
        del st.session_state.current_user
    st.rerun()

# Configuración de Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Configuración de Supabase
try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
except Exception as e:
    SUPABASE_URL = ""
    SUPABASE_KEY = ""

class GoogleDriveManager:
    def __init__(self):
        self.service = None
        self.credentials = None
    
    def authenticate(self):
        """Autenticación con Service Account desde Streamlit Secrets"""
        try:
            # Verificar si tenemos credenciales de Service Account en secrets
            if hasattr(st, 'secrets') and 'GOOGLE_CREDENTIALS' in st.secrets:
                st.info("🔍 Intentando autenticar con Service Account...")
                
                # Usar credenciales desde Streamlit Secrets (Service Account)
                credentials_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
                creds = service_account.Credentials.from_service_account_info(
                    credentials_info, scopes=SCOPES
                )
                self.credentials = creds
                
                # Crear el servicio de Google Drive
                self.service = build('drive', 'v3', credentials=creds)
                
                # Verificar que la conexión funcione
                results = self.service.files().list(pageSize=1).execute()
                
                st.success("✅ Conexión con Google Drive establecida (Service Account)")
                return True
                
            elif os.path.exists(CREDENTIALS_FILE):
                st.info("🔍 Intentando autenticar con OAuth local...")
                
                # Fallback para desarrollo local con OAuth
                creds = None
                
                # Cargar token existente si existe
                if os.path.exists(TOKEN_FILE):
                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                
                # Si no hay credenciales válidas disponibles, permitir al usuario autenticarse
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                        
                        # Usar run_local_server para autenticación automática
                        try:
                            creds = flow.run_local_server(port=8080, open_browser=True)
                        except Exception as e:
                            st.error(f"❌ Error en autenticación: {str(e)}")
                            st.info("💡 Asegúrate de que el puerto 8080 esté disponible")
                            return False
                    
                    # Guardar las credenciales para la próxima ejecución
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                
                # Crear el servicio de Google Drive
                self.service = build('drive', 'v3', credentials=creds)
                self.credentials = creds
                
                # Verificar que la conexión funcione
                results = self.service.files().list(pageSize=1).execute()
                
                st.success("✅ Conexión con Google Drive establecida (OAuth local)")
                return True
            else:
                st.error("❌ No se encontraron credenciales de Google Drive")
                st.info("💡 Para producción: Configura GOOGLE_CREDENTIALS en Streamlit Secrets")
                st.info("💡 Para desarrollo: Coloca credentials.json en la carpeta del proyecto")
                return False
            
        except Exception as e:
            st.error(f"❌ Error al conectar con Google Drive: {str(e)}")
            st.error(f"🔍 Detalle del error: {type(e).__name__}")
            return False

def main():
    # Verificar autenticación antes de mostrar la aplicación
    check_authentication()
    
    # Configuración de la página
    st.set_page_config(
        page_title="ISILAudit IA",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header con información del usuario y logout
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🏭 ISILAudit IA")
    
    with col2:
        st.write(f"👤 Usuario: **{st.session_state.current_user}**")
    
    with col3:
        if st.button("🚪 Cerrar Sesión", type="secondary"):
            logout()
    
    st.markdown("---")
    
    # Mostrar estado de Supabase
    if SUPABASE_URL and SUPABASE_KEY:
        st.sidebar.success(f"🗄️ Supabase: Configurado")
        st.sidebar.write(f"URL: {SUPABASE_URL[:30]}...")
    else:
        st.sidebar.error("🗄️ Supabase: No configurado")
        st.sidebar.write("Configura las credenciales en secrets.toml")
    
    # Crear las pestañas
    tab_names = [
        "URL", "Plantillas", "Bibliografía", "Imágenes", 
        "Archivos", "Redacción", "Secuencia", "Videos", "Datos"
    ]
    
    tabs = st.tabs(tab_names)
    
    # Pestaña URL (principal)
    with tabs[0]:
        st.header("🔗 Análisis de URLs en Presentaciones")
        
        # Verificar disponibilidad de Google Drive
        has_google_credentials = (
            (hasattr(st, 'secrets') and 'GOOGLE_CREDENTIALS' in st.secrets) or 
            os.path.exists(CREDENTIALS_FILE)
        )
        
        if has_google_credentials:
            # Modo completo - con Google Drive
            st.success("📁 **Google Drive configurado correctamente**")
            
            # Inicializar el manager de Google Drive
            if 'drive_manager' not in st.session_state:
                st.session_state.drive_manager = GoogleDriveManager()
            
            # Botón de conexión a Google Drive
            connect_button = st.button("🔌 Conectar con Google Drive", type="primary")
            
            if connect_button:
                with st.spinner("🔐 Autenticando con Google Drive..."):
                    st.session_state.connected = st.session_state.drive_manager.authenticate()
            
            # Mostrar estado de conexión
            if st.session_state.get('connected', False):
                st.success("📁 Conectado a Google Drive exitosamente")
            else:
                st.info("👆 Haz clic en 'Conectar con Google Drive' para comenzar")
        
        else:
            # Modo demo - sin Google Drive
            st.info("🌐 **Modo Demo - Sin Google Drive**")
            st.warning("📁 Google Drive no está configurado")
            
            st.markdown("""
            ### 🔧 Para usar Google Drive:
            
            **En Streamlit Cloud:**
            1. Configura `GOOGLE_CREDENTIALS` en **Settings → Secrets**
            2. Usar Service Account JSON completo
            
            **En desarrollo local:**
            1. Coloca `credentials.json` en la carpeta del proyecto
            
            ### 🧪 **Modo Demo**
            Mientras tanto, puedes probar la funcionalidad con datos de ejemplo:
            """)
            
            if st.button("🎯 Generar Datos de Ejemplo", type="primary"):
                st.success("✅ Datos de ejemplo generados")
                
                # Generar URLs de ejemplo
                sample_urls = [
                    {
                        'filename': 'demo_presentation.pptx',
                        'slide': 1,
                        'url': 'https://www.google.com',
                        'location': 'Diapositiva 1 - Texto',
                        'context': 'Google Search',
                        'subfolder': '12345-SESION01',
                        'domain': 'google.com'
                    },
                    {
                        'filename': 'demo_presentation.pptx',
                        'slide': 2,
                        'url': 'https://www.github.com',
                        'location': 'Diapositiva 2 - Hipervínculo',
                        'context': 'GitHub Repository',
                        'subfolder': '12345-SESION01',
                        'domain': 'github.com'
                    }
                ]
                
                # Mostrar tabla
                df = pd.DataFrame(sample_urls)
                st.dataframe(df[['filename', 'slide', 'url', 'context']], use_container_width=True)
    
    # Pestañas vacías (2-9)
    for i in range(1, 9):
        with tabs[i]:
            st.header(f"🚧 {tab_names[i]}")
            st.info("Esta sección estará disponible próximamente.")

if __name__ == "__main__":
    main() 