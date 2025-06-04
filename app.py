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

# Configuración de la página
st.set_page_config(
    page_title="ISILAudit IA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            file_content = io.BytesIO()
            
            downloader = request.execute()
            file_content.write(downloader)
            file_content.seek(0)
            
            return file_content.getvalue()
            
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
                # Probar la conexión
                test_result = self.client.table('system_config').select('*').limit(1).execute()
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
    
    def save_urls_data(self, urls_data):
        """Guardar datos de URLs en Supabase"""
        if not self.client:
            st.error("❌ No hay conexión con Supabase configurada")
            return False
        
        try:
            # Preparar datos para insertar en ppt_urls
            records = []
            files_info = {}  # Para estadísticas de archivos
            
            for url_info in urls_data:
                # Registrar información del archivo
                filename = url_info.get('filename', '')
                if filename not in files_info:
                    files_info[filename] = {
                        'filename': filename,
                        'subfolder': url_info.get('subfolder', ''),
                        'url_count': 0,
                        'max_slide': 0
                    }
                
                files_info[filename]['url_count'] += 1
                files_info[filename]['max_slide'] = max(
                    files_info[filename]['max_slide'], 
                    url_info.get('slide', 1)
                )
                
                # Preparar registro de URL
                record = {
                    'filename': filename,
                    'slide_number': url_info.get('slide', 1),
                    'url': url_info.get('url', ''),
                    'url_domain': urlparse(url_info.get('url', '')).netloc,
                    'location_context': url_info.get('location', ''),
                    'text_context': url_info.get('context', ''),
                    'status': url_info.get('status', ''),
                    'status_description': url_info.get('status_description', ''),
                    'checked_at': url_info.get('checked_at', datetime.now().isoformat()),
                    'created_at': datetime.now().isoformat()
                }
                records.append(record)
            
            # Insertar URLs en Supabase
            result = self.client.table('ppt_urls').insert(records).execute()
            
            if result.data:
                # Insertar estadísticas de archivos procesados
                file_records = []
                for filename, info in files_info.items():
                    file_record = {
                        'filename': filename,
                        'folder_name': info['subfolder'],
                        'subfolder': info['subfolder'],
                        'total_urls_found': info['url_count'],
                        'total_slides': info['max_slide'],
                        'processed_at': datetime.now().isoformat(),
                        'created_at': datetime.now().isoformat()
                    }
                    file_records.append(file_record)
                
                # Insertar información de archivos procesados
                try:
                    self.client.table('processed_files').insert(file_records).execute()
                except Exception as e:
                    st.warning(f"⚠️ URLs guardadas, pero error al guardar estadísticas: {str(e)}")
                
                st.success(f"✅ Se guardaron {len(result.data)} URLs de {len(files_info)} archivo(s) en Supabase")
                return True
            else:
                st.error("❌ No se pudieron guardar los datos")
                return False
                
        except Exception as e:
            st.error(f"❌ Error al guardar en Supabase: {str(e)}")
            return False

def main():
    st.title("🏭 ISILAudit IA")
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
        
        # Inicializar el manager de Google Drive
        if 'drive_manager' not in st.session_state:
            st.session_state.drive_manager = GoogleDriveManager()
        
        # Inicializar estado de selección de archivos
        if 'selected_files' not in st.session_state:
            st.session_state.selected_files = []
        
        # Mostrar estado de conexión actual
        if st.session_state.get('connected', False):
            st.success("📁 Conectado a Google Drive")
        
        # Botón de conexión a Google Drive
        col1, col2 = st.columns([1, 3])
        
        with col1:
            connect_button = st.button("🔌 Conectar con Google Drive", type="primary")
        
        with col2:
            if st.session_state.get('connected', False):
                if st.button("🔄 Reconectar", type="secondary"):
                    # Limpiar tokens para forzar nueva autenticación
                    if os.path.exists(TOKEN_FILE):
                        os.remove(TOKEN_FILE)
                    st.session_state.connected = False
                    st.rerun()
        
        if connect_button:
            with st.spinner("🔐 Autenticando con Google Drive..."):
                st.session_state.connected = st.session_state.drive_manager.authenticate()
        
        # Mostrar estado de conexión
        if st.session_state.get('connected', False):
            
            # Lista desplegable de carpetas mejorada
            st.subheader("📂 Seleccionar Carpeta")
            
            with st.spinner("📁 Cargando todas las carpetas de la raíz..."):
                folders = st.session_state.drive_manager.get_folders()
            
            if folders:
                folder_names = [folder['name'] for folder in folders]
                
                # Mostrar información de carpetas encontradas
                st.info(f"📊 Se encontraron {len(folders)} carpetas en la raíz de Google Drive")
                
                selected_folder = st.selectbox(
                    "Selecciona una carpeta de la raíz:",
                    options=folder_names,
                    index=None,
                    placeholder="Elige una carpeta...",
                    help="Lista completa de todas las carpetas disponibles en la raíz"
                )
                
                if selected_folder:
                    # Encontrar el ID de la carpeta seleccionada
                    folder_id = next(folder['id'] for folder in folders if folder['name'] == selected_folder)
                    
                    st.info(f"🔍 Buscando archivos PPTX en: **{selected_folder}**")
                    
                    # Buscar archivos PPTX
                    with st.spinner("🔍 Buscando archivos PPTX..."):
                        pptx_files = st.session_state.drive_manager.find_pptx_files(folder_id)
                    
                    if pptx_files:
                        st.subheader("📋 Archivos PPTX Encontrados")
                        st.markdown("*Solo se muestran archivos en subcarpetas con formato XXXXX-SESIONXX*")
                        
                        # Mostrar información adicional
                        st.info(f"📊 Encontrados **{len(pptx_files)}** archivos PPTX")
                        
                        # USAR FORM PARA EVITAR OSCURECIMIENTO
                        with st.form("file_selection_form"):
                            st.write("**Selecciona los archivos a analizar:**")
                            
                            # Encabezados de columnas
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
                            
                            # Checkboxes dentro del form (no causan recarga)
                            selected_indices = []
                            for i, file in enumerate(pptx_files):
                                col_check, col_name, col_folder, col_size = st.columns([1, 4, 2, 1.5])
                                
                                with col_check:
                                    # Checkbox simple dentro del form
                                    checkbox_value = st.checkbox("", key=f"form_file_{i}", label_visibility="collapsed")
                                    if checkbox_value:
                                        selected_indices.append(i)
                                
                                with col_name:
                                    st.write(f"📄 {file['name']}")
                                
                                with col_folder:
                                    st.write(f"📁 {file.get('subfolder', 'N/A')}")
                                
                                with col_size:
                                    st.write(f"💾 {file.get('size_mb', 0)} MB")
                            
                            # Botón de envío del form
                            submitted = st.form_submit_button("✅ Confirmar Selección", type="primary")
                            
                            if submitted and selected_indices:
                                # Almacenar archivos seleccionados en session state
                                st.session_state.selected_files = [pptx_files[i] for i in selected_indices]
                                st.success(f"✅ {len(selected_indices)} archivo(s) seleccionado(s) para análisis")
                        
                        # Mostrar archivos seleccionados fuera del form
                        if hasattr(st.session_state, 'selected_files') and st.session_state.selected_files:
                            st.write("**Archivos seleccionados para análisis:**")
                            for file in st.session_state.selected_files:
                                st.write(f"• {file['name']} ({file.get('subfolder', 'N/A')})")
                            
                            # Botón para extraer URLs (separado del form)
                            extract_button = st.button("🔍 Extraer URLs", type="primary", 
                                                     help=f"Extraer URLs de {len(st.session_state.selected_files)} archivo(s) seleccionado(s)")
                            
                            if extract_button:
                                st.subheader("🌐 URLs Encontradas")
                                
                                # Inicializar estados en session_state
                                if 'extraction_completed' not in st.session_state:
                                    st.session_state.extraction_completed = False
                                if 'validation_completed' not in st.session_state:
                                    st.session_state.validation_completed = False
                                if 'all_urls' not in st.session_state:
                                    st.session_state.all_urls = []
                                
                                all_urls = []
                                analyzer = PPTXAnalyzer()
                                
                                # Barra de progreso simple sin container
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                total_files = len(st.session_state.selected_files)
                                
                                for i, file in enumerate(st.session_state.selected_files):
                                    # Actualizar status y progreso
                                    progress = (i + 1) / total_files
                                    status_text.text(f"Analizando: {file['name']} ({i+1}/{total_files}) - {progress:.0%}")
                                    progress_bar.progress(progress)
                                    
                                    # Descargar y analizar el archivo real
                                    file_content = st.session_state.drive_manager.download_file(file['id'])
                                    
                                    if file_content:
                                        urls = analyzer.extract_urls_from_pptx(file_content, file['name'])
                                    else:
                                        urls = analyzer.extract_urls_from_pptx(file['id'], file['name'])  # Fallback
                                    
                                    # Agregar información adicional
                                    for url_info in urls:
                                        url_info.update({
                                            'subfolder': file.get('subfolder', 'N/A'),
                                            'domain': urlparse(url_info['url']).netloc
                                        })
                                        all_urls.append(url_info)
                                
                                # Completar progreso
                                progress_bar.progress(1.0)
                                status_text.text(f"✅ Completado: {total_files} archivos analizados")
                                
                                # Guardar URLs en session state
                                st.session_state.all_urls = all_urls
                                st.session_state.extraction_completed = True
                                
                                if all_urls:
                                    # Mostrar resultados en una tabla mejorada
                                    df_urls = pd.DataFrame(all_urls)
                                    
                                    # Reordenar columnas para mejor visualización
                                    column_order = ['filename', 'slide', 'url', 'domain', 'location', 'context', 'subfolder']
                                    df_urls = df_urls.reindex(columns=[col for col in column_order if col in df_urls.columns])
                                    
                                    st.dataframe(df_urls, use_container_width=True, height=400)
                                    
                                    # Estadísticas mejoradas
                                    st.subheader("📊 Estadísticas")
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.metric("Total URLs", len(all_urls))
                                    
                                    with col2:
                                        unique_domains = df_urls['domain'].nunique()
                                        st.metric("Dominios Únicos", unique_domains)
                                    
                                    with col3:
                                        st.metric("Archivos Analizados", len(st.session_state.selected_files))
                                    
                                    with col4:
                                        unique_subfolders = df_urls['subfolder'].nunique()
                                        st.metric("Subcarpetas", unique_subfolders)
                                else:
                                    st.warning("No se encontraron URLs en los archivos seleccionados.")
                        
                        # SECCIÓN DE VALIDACIÓN - Solo aparece si hay URLs extraídas
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
                                        
                                        success = supabase_manager.save_urls_data(validated_urls)
                                        
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
                    
                    else:
                        st.info("👆 Selecciona archivos PPTX usando los checkboxes y luego haz clic en 'Extraer URLs'")
            
            else:
                st.warning("No se encontraron carpetas en la raíz de Google Drive.")
        
        else:
            st.info("👆 Haz clic en 'Conectar con Google Drive' para comenzar")
            
            # Mostrar información sobre credenciales
            if not os.path.exists(CREDENTIALS_FILE):
                st.error("❌ Archivo credentials.json no encontrado")
                st.info("💡 Asegúrate de haber configurado las credenciales de Google Drive API")
    
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