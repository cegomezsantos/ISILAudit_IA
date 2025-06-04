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
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'  # tu archivo JSON

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
                # Eliminar mensajes de debug
                credentials_raw = st.secrets["GOOGLE_CREDENTIALS"]
                # Manejar tanto string JSON como AttrDict
                if isinstance(credentials_raw, dict) or hasattr(credentials_raw, '__dict__'):
                    credentials_info = dict(credentials_raw)
                else:
                    credentials_info = json.loads(credentials_raw)
                creds = service_account.Credentials.from_service_account_info(
                    credentials_info, scopes=SCOPES
                )
                self.credentials = creds
                self.service = build('drive', 'v3', credentials=creds)
                # Verificar que la conexión funcione
                self.service.files().list(pageSize=1).execute()
                st.success("✅ Conexión con Google Drive establecida (Service Account)")
                return True
            elif os.path.exists(SERVICE_ACCOUNT_FILE):
                creds = service_account.Credentials.from_service_account_file(
                    SERVICE_ACCOUNT_FILE, scopes=SCOPES
                )
                self.credentials = creds
                self.service = build('drive', 'v3', credentials=creds)
                self.service.files().list(pageSize=1).execute()
                st.success("✅ Conexión con Google Drive establecida (Service Account)")
                return True
            else:
                st.error("❌ No se encontraron credenciales de Google Drive")
                st.info("💡 Para producción: Configura GOOGLE_CREDENTIALS en Streamlit Secrets")
                st.info("💡 Para desarrollo: Coloca service_account.json en la carpeta del proyecto")
                return False
        except Exception as e:
            st.error(f"❌ Error al conectar con Google Drive: {str(e)}")
            st.error(f"🔍 Detalle del error: {type(e).__name__}")
            if "JSON" in str(e) or "Malformed" in str(e):
                st.error("🚨 **Problema con formato JSON de credenciales**")
                st.info("💡 **Soluciones:**")
                st.write("1. Asegúrate de usar comillas triples '''")
                st.write("2. Verificar que todos los \\n sean \\\\n")
                st.write("3. JSON debe estar en una sola línea sin espacios")
                st.code("""
GOOGLE_CREDENTIALS = '''{"type": "service_account", "project_id": "agente-101", ...}'''
""")
            return False
    
    def get_folders(self):
        """Obtener TODAS las carpetas de la raíz de Google Drive"""
        try:
            if not self.service:
                return []
            
            # Buscar TODAS las carpetas en la raíz (parents in 'root')
            query = "mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                pageSize=1000,  # Aumentar para obtener todas las carpetas
                fields="nextPageToken, files(id, name, modifiedTime)"
            ).execute()
            
            folders = results.get('files', [])
            
            # Ordenar carpetas alfabéticamente
            folders_sorted = sorted(folders, key=lambda x: x['name'].lower())
            
            return [{"name": folder['name'], "id": folder['id']} for folder in folders_sorted]
            
        except Exception as e:
            st.error(f"❌ Error al obtener carpetas: {str(e)}")
            return []
    
    def find_pptx_files(self, folder_id):
        """Buscar archivos PPTX en subcarpetas con formato específico y obtener información completa"""
        try:
            if not self.service:
                return []
            
            all_pptx_files = []
            
            # Buscar todas las subcarpetas dentro de la carpeta seleccionada
            subfolders = self._get_subfolders_recursive(folder_id)
            
            # Filtrar subcarpetas que sigan el patrón XXXXX-SESIONXX
            pattern = re.compile(r'^\d{5}-SESION\d{2}$')
            valid_subfolders = [folder for folder in subfolders if pattern.match(folder['name'])]
            
            # Buscar archivos PPTX en las subcarpetas válidas
            for subfolder in valid_subfolders:
                pptx_files = self._get_pptx_in_folder(subfolder['id'])
                for file in pptx_files:
                    file['subfolder'] = subfolder['name']
                    file['size_mb'] = round(int(file.get('size', 0)) / (1024 * 1024), 1) if file.get('size') else 0
                    all_pptx_files.append(file)
            
            return all_pptx_files
            
        except Exception as e:
            st.error(f"❌ Error al buscar archivos PPTX: {str(e)}")
            return []
    
    def _get_subfolders_recursive(self, parent_folder_id, max_depth=3, current_depth=0):
        """Obtener todas las subcarpetas recursivamente"""
        subfolders = []
        
        if current_depth >= max_depth:
            return subfolders
        
        try:
            query = f"mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            for folder in folders:
                subfolders.append(folder)
                # Buscar recursivamente en subcarpetas
                subfolders.extend(self._get_subfolders_recursive(folder['id'], max_depth, current_depth + 1))
            
            return subfolders
            
        except Exception as e:
            st.warning(f"⚠️ Error al buscar en subcarpetas: {str(e)}")
            return subfolders
    
    def _get_pptx_in_folder(self, folder_id):
        """Obtener archivos PPTX en una carpeta específica con información completa"""
        try:
            query = f"'{folder_id}' in parents and trashed=false and (name contains '.pptx' or name contains '.ppt')"
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, size, modifiedTime, parents)"
            ).execute()
            
            files = results.get('files', [])
            return files
            
        except Exception as e:
            st.warning(f"⚠️ Error al buscar archivos PPTX en carpeta: {str(e)}")
            return []
    
    def download_file(self, file_id):
        """Descargar un archivo de Google Drive"""
        try:
            if not self.service:
                return None
            
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            file_io.seek(0)
            return file_io.getvalue()
            
        except Exception as e:
            st.error(f"❌ Error al descargar archivo: {str(e)}")
            return None

    def add_folder_to_root(self, folder_id):
        """Añadir una carpeta compartida a la raíz del Service Account"""
        try:
            if not self.service:
                st.error("❌ No hay servicio de Google Drive inicializado.")
                return False
            self.service.files().update(
                fileId=folder_id,
                addParents='root'
            ).execute()
            st.success(f"✅ Carpeta añadida a la raíz del Service Account (ID: {folder_id})")
            return True
        except Exception as e:
            st.error(f"❌ Error al añadir carpeta a la raíz: {str(e)}")
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
        "Conexión Drive", "URL", "Plantillas", "Bibliografía", "Imágenes", 
        "Archivos", "Redacción", "Secuencia", "Videos", "Datos"
    ]
    
    tabs = st.tabs(tab_names)
    
    # Pestaña 0: Conexión y gestión de Google Drive
    with tabs[0]:
        st.header("🔌 Conexión y Gestión de Google Drive")
        has_google_credentials = (
            (hasattr(st, 'secrets') and 'GOOGLE_CREDENTIALS' in st.secrets) or 
            os.path.exists(SERVICE_ACCOUNT_FILE)
        )
        if has_google_credentials:
            st.success("📁 **Google Drive configurado correctamente**")
        if 'drive_manager' not in st.session_state:
            st.session_state.drive_manager = GoogleDriveManager()
        if 'selected_files' not in st.session_state:
            st.session_state.selected_files = []
        if st.session_state.get('connected', False):
            st.success("📁 Conectado a Google Drive")
        col1, col2 = st.columns([1, 3])
        with col1:
            connect_button = st.button("🔌 Conectar con Google Drive", type="primary")
        with col2:
            if st.session_state.get('connected', False):
                if st.button("🔄 Reconectar", type="secondary"):
                    if os.path.exists(SERVICE_ACCOUNT_FILE):
                        os.remove(SERVICE_ACCOUNT_FILE)
                    st.session_state.connected = False
                    st.rerun()
        if connect_button:
            with st.spinner("🔐 Autenticando con Google Drive..."):
                st.session_state.connected = st.session_state.drive_manager.authenticate()
        # NUEVO: Añadir carpeta a la raíz
        if st.session_state.get('connected', False):
            st.markdown("---")
            st.subheader("➕ Añadir carpeta compartida a la raíz del Service Account")
            folder_id_input = st.text_input("Pega aquí el ID de la carpeta de Google Drive compartida")
            if st.button("Añadir carpeta a la raíz"):
                if folder_id_input:
                    st.session_state.drive_manager.add_folder_to_root(folder_id_input)
                else:
                    st.warning("Debes ingresar un ID de carpeta")
            st.markdown("---")
            st.subheader("📥 Añadir varias carpetas desde archivo CSV")
            csv_file = st.file_uploader("Sube un archivo CSV con una columna 'folder_id'", type=["csv"])
            if csv_file is not None:
                try:
                    df = pd.read_csv(csv_file)
                    if 'folder_id' in df.columns:
                        if st.button("Añadir todas las carpetas del CSV a la raíz"):
                            resultados = []
                            for folder_id in df['folder_id'].dropna().astype(str):
                                resultado = st.session_state.drive_manager.add_folder_to_root(folder_id)
                                resultados.append((folder_id, resultado))
                            exitos = sum(1 for _, ok in resultados if ok)
                            st.success(f"Se añadieron {exitos} carpetas a la raíz correctamente.")
                    else:
                        st.error("El CSV debe tener una columna llamada 'folder_id'")
                except Exception as e:
                    st.error(f"Error al procesar el archivo CSV: {e}")
            st.markdown("---")
            if st.button("🔄 Actualizar lista de carpetas"):
                st.session_state.folders_cache = st.session_state.drive_manager.get_folders()
                st.success("Lista de carpetas actualizada")
    # Pestaña 1: Selección de carpeta y análisis de URLs
    with tabs[1]:
        st.header("🔗 Análisis de URLs en Presentaciones")
        if st.session_state.get('connected', False):
            with st.spinner("📁 Cargando todas las carpetas de la raíz..."):
                folders = st.session_state.drive_manager.get_folders()
            if folders:
                folder_names = [folder['name'] for folder in folders]
                st.info(f"📊 Se encontraron {len(folders)} carpetas en la raíz de Google Drive")
                selected_folder = st.selectbox(
                    "Selecciona una carpeta de la raíz:",
                    options=folder_names,
                    index=None,
                    placeholder="Elige una carpeta...",
                    help="Lista completa de todas las carpetas disponibles en la raíz"
                )
                if selected_folder:
                    folder_id = next(folder['id'] for folder in folders if folder['name'] == selected_folder)
                    st.info(f"🔍 Buscando archivos PPTX en: **{selected_folder}**")
                    with st.spinner("🔍 Buscando archivos PPTX..."):
                        pptx_files = st.session_state.drive_manager.find_pptx_files(folder_id)
                    if pptx_files:
                        st.subheader("📋 Archivos PPTX Encontrados")
                        st.markdown("*Solo se muestran archivos en subcarpetas con formato XXXXX-SESIONXX*")
                        st.info(f"📊 Encontrados **{len(pptx_files)}** archivos PPTX")
                        with st.form("file_selection_form"):
                            st.write("**Selecciona los archivos a analizar:**")
                            col_header1, col_header2, col_header3, col_header4 = st.columns([1, 4, 2, 1.5])
                            with col_header1:
                                st.write("**Seleccionar**")
                            with col_header2:
                                st.write("**Archivo PPT**")
                            with col_header3:
                                st.write("**Carpeta**")
                            with col_header4:
                                st.write("**Tamaño**")
                            st.markdown("---")
                            selected_indices = []
                            for i, file in enumerate(pptx_files):
                                col_check, col_name, col_folder, col_size = st.columns([1, 4, 2, 1.5])
                                with col_check:
                                    checkbox_value = st.checkbox("", key=f"form_file_{i}", label_visibility="collapsed")
                                    if checkbox_value:
                                        selected_indices.append(i)
                                with col_name:
                                    st.write(f"📄 {file['name']}")
                                with col_folder:
                                    st.write(f"📁 {file.get('subfolder', 'N/A')}")
                                with col_size:
                                    st.write(f"💾 {file.get('size_mb', 0)} MB")
                            submitted = st.form_submit_button("✅ Confirmar Selección", type="primary")
                            if submitted and selected_indices:
                                st.session_state.selected_files = [pptx_files[i] for i in selected_indices]
                                st.success(f"✅ {len(selected_indices)} archivo(s) seleccionado(s) para análisis")
                        if hasattr(st.session_state, 'selected_files') and st.session_state.selected_files:
                            st.write("**Archivos seleccionados para análisis:**")
                            for file in st.session_state.selected_files:
                                st.write(f"• {file['name']} ({file.get('subfolder', 'N/A')})")
                            extract_button = st.button("🔍 Extraer URLs", type="primary", help=f"Extraer URLs de {len(st.session_state.selected_files)} archivo(s) seleccionado(s)")
                            if extract_button:
                                st.subheader("🌐 URLs Encontradas")
                                st.info("🚧 **Funcionalidad de extracción de URLs en desarrollo**")
                                st.write("Una vez conectado exitosamente, se habilitará la extracción completa de URLs de archivos PPTX.")
                    else:
                        st.info("👆 No se encontraron archivos PPTX en las subcarpetas con formato XXXXX-SESIONXX")
            else:
                st.warning("No se encontraron carpetas en la raíz de Google Drive.")
        else:
            st.info("👆 Conéctate primero en la pestaña 'Conexión Drive'")
    # Pestañas vacías (2-9)
    for i in range(2, 10):
        with tabs[i]:
            st.header(f"🚧 {tab_names[i]}")
            st.info("Esta sección estará disponible próximamente.")

if __name__ == "__main__":
    main() 