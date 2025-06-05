# 🔍 ISILAudit IA - Auditoría Inteligente de URLs

## 📋 Descripción

ISILAudit IA es una aplicación web que audita y valida URLs en archivos PowerPoint (.pptx). Extrae automáticamente URLs, valida su estado y genera reportes detallados.

## ✨ Características

- 🔐 Sistema de autenticación seguro
- 📁 Integración con Google Drive  
- 🔍 Extracción automática de URLs
- ✅ Validación en tiempo real
- 📊 Reportes detallados
- 💾 Base de datos Supabase
- 📥 Exportación a CSV

## 🚀 Instalación Rápida

### 1. Clonar repositorio
```bash
git clone https://github.com/tu-usuario/ISILAudit_IA.git
cd ISILAudit_IA
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Supabase
1. Crear proyecto en [Supabase](https://supabase.com)
2. Ejecutar `simplified_database.sql` en SQL Editor
3. Configurar secrets en `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "tu-url-supabase"
SUPABASE_KEY = "tu-clave-anonima"
```

### 4. Ejecutar aplicación
```bash
streamlit run app.py
```

## 👥 Usuarios de Prueba

- **admin** / 09678916
- **jsato** / SanManz12025  
- **rrepetto** / SanManz22025

## 🗄️ Base de Datos

Tabla principal: `validated_urls`
- Almacena URLs extraídas y validadas
- Incluye metadatos y estado de validación
- Políticas de seguridad RLS habilitadas

## 📁 Estructura Optimizada

```
ISILAudit_IA/
├── app.py                    # Aplicación principal
├── pptx_analyzer.py          # Analizador de PPTX
├── simplified_database.sql   # Script SQL único
├── requirements.txt          # Dependencias
├── .streamlit/
│   └── secrets.toml         # Configuración local
└── README.md               # Documentación
```

## 🔒 Seguridad

- Credenciales protegidas en `.gitignore`
- Variables de entorno para configuración
- Row Level Security en Supabase
- Tokens de ejemplo en archivos públicos

## 🚀 Despliegue

### Streamlit Cloud
1. Conectar repositorio GitHub
2. Configurar secrets en Settings
3. Despliegue automático

### Variables requeridas:
```toml
SUPABASE_URL = "tu-url"
SUPABASE_KEY = "tu-clave"
```

## 🔧 Uso

1. **Login** con credenciales
2. **Conectar** Google Drive
3. **Seleccionar** archivos PPTX
4. **Analizar** URLs automáticamente
5. **Exportar** resultados

## 📊 Funcionalidades

- Extracción de URLs de diapositivas
- Validación HTTP en tiempo real
- Estadísticas por dominio
- Reportes por archivo
- Exportación CSV
- Modo demo con datos de ejemplo

## 🐛 Solución de Problemas

### Conexión Supabase
- Verificar credenciales
- Confirmar tabla `validated_urls` existe
- Revisar políticas RLS

### Google Drive
- Verificar `credentials.json`
- Confirmar API habilitada
- Revisar permisos

## 📞 Soporte

Para problemas o mejoras:
1. Crear issue en GitHub
2. Incluir logs de error
3. Describir pasos para reproducir

---

**✅ Proyecto optimizado y listo para producción** 