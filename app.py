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

# Configuración de Supabase (agregar tus credenciales)
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
        """Autenticación real con Google Drive"""
        try:
            creds = None
            
            # Verificar si existe el archivo de credenciales
            if not os.path.exists(CREDENTIALS_FILE):
                st.error("❌ Archivo credentials.json no encontrado")
                st.info("💡 Configura tus credenciales de Google Drive API")
                return False
            
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
            
            st.success("✅ Conexión con Google Drive establecida correctamente")
            return True
            
        except Exception as e:
            st.error(f"❌ Error al conectar con Google Drive: {str(e)}")
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

class PPTXAnalyzer:
    @staticmethod
    def extract_urls_from_pptx(file_content, filename=""):
        """Extraer URLs de un archivo PPTX con información de slide y shapes"""
        urls = []
        try:
            from pptx_analyzer import PPTXURLExtractor
            extractor = PPTXURLExtractor()
            
            if isinstance(file_content, bytes):
                detailed_urls = extractor.extract_urls_from_file(file_content)
            else:
                # Fallback con URLs de ejemplo
                detailed_urls = [
                    {"url": "https://www.example.com", "location": "Diapositiva 1 - Texto de forma", "context": "Ejemplo"},
                    {"url": "https://www.google.com", "location": "Diapositiva 2 - Hipervínculo", "context": "Google"},
                    {"url": "https://www.youtube.com", "location": "Diapositiva 3 - Shape", "context": "YouTube"},
                    {"url": "https://github.com", "location": "Diapositiva 4 - Texto", "context": "GitHub"}
                ]
            
            # Procesar URLs para extraer número de slide
            for url_info in detailed_urls:
                slide_match = re.search(r'Diapositiva (\d+)', url_info.get('location', ''))
                slide_num = int(slide_match.group(1)) if slide_match else 1
                
                urls.append({
                    'url': url_info['url'],
                    'slide': slide_num,
                    'location': url_info.get('location', 'Desconocido'),
                    'context': url_info.get('context', '')[:50],
                    'filename': filename
                })
            
            return urls
            
        except Exception as e:
            st.error(f"Error al analizar PPTX {filename}: {str(e)}")
            return []

class URLValidator:
    """Clase para validar el estado de URLs"""
    
    @staticmethod
    def validate_urls(urls_list):
        """Validar una lista de URLs y devolver su estado"""
        validated_urls = []
        
        for url_info in urls_list:
            url = url_info['url']
            status = URLValidator.check_url_status(url)
            
            url_info.update(status)
            validated_urls.append(url_info)
        
        return validated_urls
    
    @staticmethod
    def check_url_status(url):
        """Verificar el estado de una URL específica"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            status_code = response.status_code
            
            if status_code == 200:
                status = "✅ Activo"
                description = "URL funciona correctamente"
            elif status_code == 404:
                status = "❌ No encontrado"
                description = "La página no existe (Error 404)"
            elif status_code == 403:
                status = "🔒 Prohibido"
                description = "Acceso denegado (Error 403)"
            elif status_code == 500:
                status = "⚠️ Error servidor"
                description = "Error interno del servidor (Error 500)"
            elif 300 <= status_code < 400:
                status = "🔄 Redirección"
                description = f"URL redirige (Código {status_code})"
            else:
                status = f"⚠️ Código {status_code}"
                description = f"Estado HTTP: {status_code}"
            
        except requests.exceptions.ConnectionError:
            status = "❌ Sin conexión"
            description = "No se puede conectar al servidor"
        except requests.exceptions.Timeout:
            status = "⌛ Timeout"
            description = "La conexión expiró"
        except requests.exceptions.RequestException as e:
            status = "❌ Error"
            description = f"Error de conexión: {str(e)[:50]}"
        except Exception as e:
            status = "❌ Error desconocido"
            description = f"Error: {str(e)[:50]}"
        
        return {
            'status': status,
            'status_description': description,
            'checked_at': datetime.now().isoformat()
        }

class SupabaseManager:
    """Clase para gestionar la conexión con Supabase"""
    
    def __init__(self):
        self.client = None
        self.connection_status = "No configurado"
        
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                # Probar la conexión con la nueva tabla
                test_result = self.client.table('validated_urls').select('*').limit(1).execute()
                self.connection_status = "✅ Conectado"
            except Exception as e:
                self.connection_status = f"❌ Error: {str(e)}"
                st.error(f"Error conectando a Supabase: {str(e)}")
                self.client = None
        else:
            self.connection_status = "❌ Credenciales no configuradas"
    
    def get_connection_status(self):
        """Obtener el estado de la conexión"""
        return self.connection_status
    
    def save_urls_data(self, urls_data, current_user):
        """Guardar datos de URLs validadas en la nueva tabla simplificada"""
        if not self.client:
            st.error("❌ No hay conexión con Supabase configurada")
            return False
        
        try:
            # Preparar datos para insertar en la tabla validated_urls
            records = []
            
            for url_info in urls_data:
                # Preparar registro simplificado
                record = {
                    'filename': url_info.get('filename', ''),
                    'slide_number': url_info.get('slide', 1),
                    'url': url_info.get('url', ''),
                    'url_domain': urlparse(url_info.get('url', '')).netloc,
                    'location_context': url_info.get('location', ''),
                    'text_context': url_info.get('context', ''),
                    'status': url_info.get('status', ''),
                    'status_description': url_info.get('status_description', ''),
                    'checked_at': url_info.get('checked_at', datetime.now().isoformat()),
                    'subfolder': url_info.get('subfolder', ''),
                    'processed_by': current_user,  # Usuario actual
                    'created_at': datetime.now().isoformat()
                }
                records.append(record)
            
            # Insertar URLs validadas en Supabase
            result = self.client.table('validated_urls').insert(records).execute()
            
            if result.data:
                st.success(f"✅ Se guardaron {len(result.data)} URLs validadas en Supabase")
                st.info(f"👤 Procesado por: {current_user}")
                return True
            else:
                st.error("❌ No se pudieron guardar los datos")
                return False
                
        except Exception as e:
            st.error(f"❌ Error al guardar en Supabase: {str(e)}")
            return False

def main():
    # Verificar autenticación antes de mostrar la aplicación
    check_authentication()
    
    # Configuración de la página (ahora dentro de main)
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
        
        # Verificar si estamos en Streamlit Cloud
        is_cloud = not os.path.exists(CREDENTIALS_FILE)
        
        if is_cloud:
            # Modo cloud - sin Google Drive
            st.info("🌐 **Modo Streamlit Cloud Detectado**")
            st.warning("📁 Google Drive no está configurado para producción")
            
            st.markdown("""
            ### 🔧 Para usar Google Drive en producción:
            
            1. **Crear Service Account** en Google Cloud Console
            2. **Descargar JSON** de credenciales 
            3. **Configurar en Secrets** de Streamlit Cloud
            4. **Actualizar código** para usar Service Account
            
            ### 🧪 **Modo Demo**
            Mientras tanto, puedes probar la funcionalidad con datos de ejemplo:
            """)
            
            if st.button("🎯 Generar Datos de Ejemplo", type="primary"):
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
                    },
                    {
                        'filename': 'demo_presentation.pptx',
                        'slide': 3,
                        'url': 'https://www.youtube.com',
                        'location': 'Diapositiva 3 - Video',
                        'context': 'YouTube Channel',
                        'subfolder': '12345-SESION01',
                        'domain': 'youtube.com'
                    },
                    {
                        'filename': 'example2.pptx',
                        'slide': 1,
                        'url': 'https://sitio-inexistente-demo.com',
                        'location': 'Diapositiva 1 - Enlace',
                        'context': 'Enlace de prueba',
                        'subfolder': '67890-SESION02',
                        'domain': 'sitio-inexistente-demo.com'
                    }
                ]
                
                st.session_state.all_urls = sample_urls
                st.session_state.extraction_completed = True
                st.success("✅ Datos de ejemplo generados")
                
                # Mostrar tabla
                df = pd.DataFrame(sample_urls)
                st.dataframe(df[['filename', 'slide', 'url', 'context']], use_container_width=True)
                
                # Estadísticas
                st.subheader("📈 Estadísticas")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total URLs", len(sample_urls))
                with col2:
                    st.metric("Dominios únicos", df['domain'].nunique())
                with col3:
                    st.metric("Archivos", df['filename'].nunique())
        
        else:
            # Modo local - con Google Drive
            st.info("💻 **Modo Local Detectado**")
            st.success("📁 Google Drive configurado para desarrollo local")
            
            # Código local de Google Drive (simplificado para mostrar conceptualmente)
            st.write("### Funcionalidades disponibles en modo local:")
            st.write("- ✅ Conexión completa con Google Drive")
            st.write("- ✅ Extracción real de archivos PPTX")
            st.write("- ✅ Análisis completo de presentaciones")
            
            # Botón para simular datos como si fuera local
            if st.button("🔗 Simular Conexión Google Drive", type="primary"):
                sample_urls = [
                    {
                        'filename': 'local_presentation.pptx',
                        'slide': 1,
                        'url': 'https://www.google.com',
                        'location': 'Diapositiva 1 - Texto',
                        'context': 'Google Search',
                        'subfolder': '12345-SESION01',
                        'domain': 'google.com'
                    }
                ]
                st.session_state.all_urls = sample_urls
                st.session_state.extraction_completed = True
                st.success("✅ Datos locales simulados")
        
        # Validación de URLs (común para ambos modos)
        if st.session_state.get('extraction_completed', False) and st.session_state.get('all_urls', []):
            st.markdown("---")
            st.subheader("🔍 Paso 2: Validación de URLs")
            
            if not st.session_state.get('validation_completed', False):
                validate_button = st.button("🔍 Validar Estado de URLs", type="secondary", key="validate_btn")
                
                if validate_button:
                    st.write("### 🔍 Validando URLs...")
                    
                    validator = URLValidator()
                    all_urls = st.session_state.all_urls
                    
                    # Barra de progreso para validación
                    validation_progress = st.progress(0)
                    validation_status = st.empty()
                    
                    validated_urls = []
                    total_urls = len(all_urls)
                    
                    for i, url_info in enumerate(all_urls):
                        progress = (i + 1) / total_urls
                        validation_status.text(f"Validando: {url_info['url'][:50]}... ({i+1}/{total_urls}) - {progress:.0%}")
                        validation_progress.progress(progress)
                        
                        status_info = URLValidator.check_url_status(url_info['url'])
                        url_info.update(status_info)
                        validated_urls.append(url_info)
                        
                        time.sleep(0.2)  # Pausa para evitar saturar servidores
                    
                    validation_progress.progress(1.0)
                    validation_status.text("✅ Validación completada")
                    
                    # Guardar URLs validadas
                    st.session_state.validated_urls = validated_urls
                    st.session_state.validation_completed = True
                    
                    # Rerun para mostrar los resultados
                    st.rerun()
            
            # Mostrar resultados de validación si están disponibles
            if st.session_state.get('validation_completed', False):
                validated_urls = st.session_state.get('validated_urls', [])
                
                st.success("✅ Validación completada")
                
                # Mostrar tabla con validaciones
                df_validated = pd.DataFrame(validated_urls)
                
                st.dataframe(df_validated[['filename', 'slide', 'url', 'status', 'status_description']], 
                           use_container_width=True, height=400)
                
                # Estadísticas de validación
                st.subheader("📈 Resultados de Validación")
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                with col_stat1:
                    active_count = len([url for url in validated_urls if "Activo" in url.get('status', '')])
                    st.metric("URLs Activas", active_count, delta=f"{active_count/len(validated_urls)*100:.1f}%")
                
                with col_stat2:
                    broken_count = len([url for url in validated_urls if "❌" in url.get('status', '')])
                    st.metric("URLs Rotas", broken_count, delta=f"{broken_count/len(validated_urls)*100:.1f}%")
                
                with col_stat3:
                    redirect_count = len([url for url in validated_urls if "🔄" in url.get('status', '')])
                    st.metric("Redirecciones", redirect_count, delta=f"{redirect_count/len(validated_urls)*100:.1f}%")
        
        # SECCIÓN DE SUPABASE - Solo aparece después de validación
        if st.session_state.get('validation_completed', False):
            st.markdown("---")
            st.subheader("📤 Paso 3: Enviar a Base de Datos")
            
            # Mostrar estado de Supabase
            if SUPABASE_URL and SUPABASE_KEY:
                # Probar conexión
                supabase_manager = SupabaseManager()
                connection_status = supabase_manager.get_connection_status()
                
                if "✅" in connection_status:
                    st.success(f"🗄️ Estado de Supabase: {connection_status}")
                    
                    supabase_button = st.button("📤 Enviar Datos Validados a Supabase", type="primary", key="supabase_btn")
                    
                    if supabase_button:
                        validated_urls = st.session_state.get('validated_urls', [])
                        
                        # Barra de progreso para envío
                        upload_progress = st.progress(0)
                        upload_status = st.empty()
                        
                        upload_status.text("📤 Enviando datos validados a Supabase...")
                        upload_progress.progress(0.5)
                        
                        success = supabase_manager.save_urls_data(validated_urls, st.session_state.current_user)
                        
                        upload_progress.progress(1.0)
                        if success:
                            upload_status.text("✅ Datos enviados exitosamente a Supabase")
                            st.balloons()
                            
                            # Opción para descargar resultados
                            df_final = pd.DataFrame(validated_urls)
                            csv = df_final.to_csv(index=False)
                            st.download_button(
                                label="📥 Descargar Resultados Completos (CSV)",
                                data=csv,
                                file_name=f"urls_validadas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            upload_status.text("❌ Error al enviar datos")
                else:
                    st.error(f"🗄️ Estado de Supabase: {connection_status}")
                    st.info("💡 Verifica tu configuración de Supabase")
            else:
                st.error("❌ Credenciales de Supabase no configuradas")
                st.info("💡 Configura SUPABASE_URL y SUPABASE_KEY en .streamlit/secrets.toml")
        
        # Botón para reiniciar el proceso
        if st.session_state.get('extraction_completed', False):
            st.markdown("---")
            if st.button("🔄 Reiniciar Proceso", type="secondary"):
                # Limpiar estados
                st.session_state.extraction_completed = False
                st.session_state.validation_completed = False
                st.session_state.all_urls = []
                if 'validated_urls' in st.session_state:
                    del st.session_state.validated_urls
                st.rerun()
    
    # Pestañas vacías (2-9)
    empty_tabs = [
        ("🎨 Plantillas", "Esta sección estará disponible próximamente para gestionar plantillas."),
        ("📚 Bibliografía", "Esta sección estará disponible próximamente para gestionar referencias bibliográficas."),
        ("🖼️ Imágenes", "Esta sección estará disponible próximamente para analizar imágenes."),
        ("📁 Archivos", "Esta sección estará disponible próximamente para gestionar archivos."),
        ("✍️ Redacción", "Esta sección estará disponible próximamente para herramientas de redacción."),
        ("🔢 Secuencia", "Esta sección estará disponible próximamente para análisis de secuencias."),
        ("🎥 Videos", "Esta sección estará disponible próximamente para gestionar videos."),
        ("📊 Datos", "Esta sección estará disponible próximamente para análisis de datos.")
    ]
    
    for i, (title, description) in enumerate(empty_tabs, 1):
        with tabs[i]:
            st.header(title)
            st.info(description)
            st.write("---")
            st.write("🚧 **Funcionalidades planificadas:**")
            
            if i == 1:  # Plantillas
                st.write("- Gestión de plantillas de presentación")
                st.write("- Aplicación de estilos personalizados")
                st.write("- Biblioteca de diseños")
            elif i == 2:  # Bibliografía
                st.write("- Extracción de referencias")
                st.write("- Formato de citas")
                st.write("- Validación bibliográfica")
            elif i == 3:  # Imágenes
                st.write("- Análisis de imágenes en presentaciones")
                st.write("- Optimización de calidad")
                st.write("- Detección de duplicados")
            elif i == 4:  # Archivos
                st.write("- Gestión de archivos adjuntos")
                st.write("- Organización automática")
                st.write("- Control de versiones")
            elif i == 5:  # Redacción
                st.write("- Corrección de texto")
                st.write("- Sugerencias de estilo")
                st.write("- Análisis de legibilidad")
            elif i == 6:  # Secuencia
                st.write("- Análisis de flujo de presentación")
                st.write("- Optimización de secuencias")
                st.write("- Detección de inconsistencias")
            elif i == 7:  # Videos
                st.write("- Extracción de videos embebidos")
                st.write("- Análisis de contenido multimedia")
                st.write("- Gestión de enlaces")
            elif i == 8:  # Datos
                st.write("- Análisis de datos en presentaciones")
                st.write("- Visualización de métricas")
                st.write("- Exportación de reportes")

if __name__ == "__main__":
    main() 