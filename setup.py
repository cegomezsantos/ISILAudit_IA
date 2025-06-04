#!/usr/bin/env python3
"""
Script de configuración para el Analizador de Presentaciones
"""

import subprocess
import sys
import os

def install_requirements():
    """Instalar las dependencias del requirements.txt"""
    try:
        print("📦 Instalando dependencias...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al instalar dependencias: {e}")
        return False

def check_python_version():
    """Verificar que la versión de Python sea compatible"""
    if sys.version_info < (3, 8):
        print("❌ Se requiere Python 3.8 o superior")
        print(f"Tu versión: {sys.version}")
        return False
    else:
        print(f"✅ Versión de Python compatible: {sys.version}")
        return True

def create_credentials_template():
    """Crear un template para las credenciales de Google Drive"""
    template_path = "credentials_template.json"
    
    if not os.path.exists(template_path):
        template_content = '''{
    "installed": {
        "client_id": "TU_CLIENT_ID.apps.googleusercontent.com",
        "project_id": "tu-proyecto-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "TU_CLIENT_SECRET",
        "redirect_uris": ["http://localhost:8080/callback"]
    }
}'''
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            print(f"📝 Template de credenciales creado: {template_path}")
            print("   Configura tus credenciales de Google Drive API y renómbralo a 'credentials.json'")
        except Exception as e:
            print(f"⚠️  No se pudo crear el template de credenciales: {e}")

def run_application():
    """Ejecutar la aplicación Streamlit"""
    try:
        print("🚀 Iniciando aplicación...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error al ejecutar la aplicación: {e}")

def main():
    """Función principal de configuración"""
    print("🔧 Configurando Analizador de Presentaciones")
    print("=" * 50)
    
    # Verificar versión de Python
    if not check_python_version():
        sys.exit(1)
    
    # Instalar dependencias
    if not install_requirements():
        print("⚠️  Algunas dependencias no se pudieron instalar")
        print("   Puedes intentar instalarlas manualmente con: pip install -r requirements.txt")
    
    # Crear template de credenciales
    create_credentials_template()
    
    print("\n" + "=" * 50)
    print("✅ Configuración completada")
    print("\n📋 Próximos pasos:")
    print("1. Configura tus credenciales de Google Drive API (opcional)")
    print("2. Ejecuta: streamlit run app.py")
    print("3. Abre tu navegador en: http://localhost:8501")
    
    # Preguntar si desea ejecutar la aplicación
    response = input("\n¿Deseas ejecutar la aplicación ahora? (y/n): ").lower().strip()
    if response in ['y', 'yes', 'sí', 'si']:
        run_application()

if __name__ == "__main__":
    main() 