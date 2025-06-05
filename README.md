# 🏭 ISILAudit IA

Una aplicación avanzada para auditar y analizar contenido de presentaciones PowerPoint desde Google Drive, con capacidades de análisis de URLs, validación de enlaces y almacenamiento en Supabase.

## ✨ Características Principales

### 🔗 Análisis Avanzado de URLs
- **Extracción exhaustiva**: Busca URLs en texto, hipervínculos, shapes, tablas y elementos XML
- **Detección por slides**: Identifica exactamente en qué diapositiva se encuentra cada URL
- **Búsqueda en shapes**: Analiza formas agrupadas, tablas, gráficos y elementos anidados
- **Análisis XML profundo**: Examina el contenido XML interno para URLs ocultas

### 📂 Gestión de Archivos
- **Lista completa de carpetas**: Muestra todas las carpetas de la raíz de Google Drive ordenadas alfabéticamente
- **Filtrado inteligente**: Solo procesa subcarpetas con formato `XXXXX-SESIONXX`
- **Selección múltiple**: Checkboxes para seleccionar archivos específicos sin acción inmediata
- **Información detallada**: Muestra nombre, carpeta y tamaño de cada archivo PPT

### 📊 Interfaz Mejorada
- **Presentación organizada**: Información de archivos en columnas claras (Selección | Archivo | Carpeta | Tamaño)
- **Barra de progreso**: Muestra porcentaje de avance durante la extracción
- **Botón de extracción**: Solo se activa cuando hay archivos seleccionados
- **Estadísticas detalladas**: Métricas de URLs, dominios, archivos y subcarpetas

### 🔍 Validación de URLs
- **Verificación de estado**: Comprueba si las URLs están activas o rotas
- **Códigos HTTP detallados**: Explica el significado de cada estado
- **Progreso visual**: Barra de progreso durante la validación
- **Categorización**: Clasifica URLs como activas, rotas, redirigidas, etc.

### 📤 Almacenamiento en Supabase
- **Integración completa**: Envía datos a base de datos Supabase
- **Estructura optimizada**: Tabla con índices para consultas eficientes
- **Datos completos**: Incluye filename, slide, URL, estado y contexto
- **Timestamps automáticos**: Registra cuándo se crearon y actualizaron los datos

## 🚀 Instalación y Configuración

### Prerrequisitos
```bash
pip install -r requirements.txt
```

### Dependencias Principales
- `streamlit`: Interfaz web
- `google-api-python-client`: API de Google Drive
- `python-pptx`: Procesamiento de PowerPoint
- `requests`: Validación de URLs
- `supabase`: Almacenamiento en base de datos
- `pandas`: Manipulación de datos

### Configuración de Google Drive API

1. **Crear proyecto en Google Cloud Console**
2. **Habilitar Google Drive API**
3. **Crear credenciales OAuth 2.0**
4. **Descargar `credentials.json`** y colocarlo en la raíz del proyecto

### Configuración de Supabase

1. **Crear proyecto en Supabase**
2. **Ejecutar el SQL** del archivo `simplified_database.sql` en el SQL Editor
3. **Copiar** `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y rellenar tus valores
4. **Configurar variables de entorno**:
   ```bash
   # En Streamlit secrets o variables de entorno
   SUPABASE_URL = "tu_supabase_url"
   SUPABASE_KEY = "tu_supabase_anon_key"
   ```

## 📋 Estructura de la Base de Datos

### Tabla `ppt_urls`

```sql
CREATE TABLE ppt_urls (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,           -- Nombre del archivo PPT
    slide_number INTEGER NOT NULL,            -- Número de diapositiva
    url TEXT NOT NULL,                        -- URL completa
    url_domain VARCHAR(255),                  -- Dominio de la URL
    location_context TEXT,                    -- Contexto de ubicación
    text_context TEXT,                        -- Contexto del texto
    status VARCHAR(100),                      -- Estado de la URL
    status_description TEXT,                  -- Descripción del estado
    checked_at TIMESTAMPTZ,                   -- Fecha de verificación
    created_at TIMESTAMPTZ DEFAULT NOW(),     -- Fecha de creación
    updated_at TIMESTAMPTZ DEFAULT NOW()      -- Fecha de actualización
);
```

### Índices Optimizados
- `idx_ppt_urls_filename`: Búsqueda por archivo
- `idx_ppt_urls_slide_number`: Búsqueda por slide
- `idx_ppt_urls_domain`: Búsqueda por dominio
- `idx_ppt_urls_status`: Filtrado por estado
- `idx_ppt_urls_created_at`: Ordenamiento temporal

## 🎯 Flujo de Trabajo

### 1. Conexión a Google Drive
- Haz clic en "🔌 Conectar con Google Drive"
- Autoriza el acceso en el navegador
- Confirma la conexión exitosa

### 2. Selección de Carpeta
- Elige una carpeta de la lista desplegable completa
- La aplicación muestra todas las carpetas de la raíz ordenadas alfabéticamente
- Ve la cantidad total de carpetas disponibles

### 3. Selección de Archivos
- Marca los checkboxes de los archivos PPTX que deseas analizar
- Los archivos se presentan en formato tabla con:
  - ☑️ **Checkbox de selección**
  - 📄 **Nombre del archivo**
  - 📁 **Carpeta de origen**
  - 💾 **Tamaño en MB**
- Los checkboxes no actúan inmediatamente, solo marcan para selección

### 4. Extracción de URLs
- Haz clic en "🔍 Extraer URLs" cuando tengas archivos seleccionados
- Observa la barra de progreso con porcentaje
- El sistema busca URLs en:
  - ✅ Texto visible
  - ✅ Hipervínculos
  - ✅ Shapes y formas agrupadas
  - ✅ Tablas y celdas
  - ✅ Elementos XML internos
  - ✅ Notas de diapositivas

### 5. Validación de URLs (Opcional)
- Haz clic en "🔍 Validar Estado de URLs"
- Observa el progreso de validación
- Revisa los estados:
  - ✅ **Activo**: URL funciona correctamente (200)
  - ❌ **No encontrado**: Error 404
  - 🔒 **Prohibido**: Error 403
  - ⚠️ **Error servidor**: Error 500
  - 🔄 **Redirección**: Códigos 3xx
  - ⌛ **Timeout**: Conexión expirada

### 6. Almacenamiento en Supabase
- Haz clic en "📤 Enviar a Supabase"
- Los datos se guardan con toda la información recopilada
- Incluye validación de URLs si se realizó previamente

## 📊 Datos Extraídos

### Por cada URL se captura:
- **Archivo original**: Nombre del PPT
- **Número de slide**: Diapositiva exacta donde está la URL
- **URL completa**: Enlace encontrado
- **Dominio**: Para análisis de dominios
- **Ubicación**: Contexto específico (shape, texto, tabla, etc.)
- **Texto circundante**: Contexto del contenido
- **Estado HTTP**: Si se validó la URL
- **Descripción del estado**: Explicación del código HTTP

### Estadísticas Generadas:
- **Total de URLs**: Cantidad total encontrada
- **Dominios únicos**: Número de dominios diferentes
- **Archivos analizados**: Cantidad de PPTs procesados
- **Subcarpetas**: Número de carpetas de origen
- **URLs activas/rotas**: Si se realizó validación

## 🛠️ Ejecución

### Desarrollo Local
```bash
streamlit run app.py
```

### Producción
```bash
# Usando el script de inicio
./start.ps1   # Windows PowerShell
./start.bat   # Windows CMD
```

## 📁 Estructura del Proyecto

```
ISILAudit/
├── app.py                  # Aplicación principal
├── pptx_analyzer.py       # Analizador mejorado de PPTX
├── requirements.txt       # Dependencias
├── simplified_database.sql    # Script SQL para Supabase
├── credentials.json      # Credenciales Google (no incluir en Git)
├── token.json           # Token de autenticación (generado automáticamente)
├── README.md            # Esta documentación
├── start.ps1           # Script de inicio PowerShell
├── start.bat           # Script de inicio Batch
└── setup.py           # Configuración del proyecto
```

## 🔧 Configuración Avanzada

### Variables de Entorno (Streamlit Secrets)
```toml
[secrets]
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu_clave_anonima_supabase"
```

### Personalización de la Búsqueda
El analizador busca en múltiples ubicaciones:
- Texto directo en shapes
- Hipervínculos en elementos
- Contenido de tablas
- Formas agrupadas anidadas
- Notas de diapositivas
- Metadatos XML internos

## 🚨 Consideraciones de Seguridad

1. **Credenciales Google**: Nunca commits `credentials.json` al repositorio
2. **Supabase Keys**: Usa variables de entorno para las claves
3. **Rate Limiting**: La validación de URLs incluye pausas para evitar saturar servidores
4. **Row Level Security**: Configura RLS en Supabase según tus necesidades

## 📈 Próximas Funcionalidades

Las siguientes pestañas están preparadas para futuras implementaciones:
- 🎨 **Plantillas**: Gestión de plantillas de presentación
- 📚 **Bibliografía**: Validación de referencias bibliográficas
- 🖼️ **Imágenes**: Análisis de imágenes en presentaciones
- 📁 **Archivos**: Gestión de archivos adjuntos
- ✍️ **Redacción**: Herramientas de corrección de texto
- 🔢 **Secuencia**: Análisis de flujo de presentación
- 🎥 **Videos**: Gestión de contenido multimedia
- 📊 **Datos**: Análisis avanzado de datos

## 🤝 Contribución

Este proyecto está en desarrollo activo. Las contribuciones son bienvenidas para:
- Mejorar la extracción de URLs
- Añadir nuevos tipos de validación
- Implementar análisis adicionales
- Optimizar el rendimiento

## 📄 Licencia

[Especificar la licencia del proyecto]

---

**Desarrollado para auditorías integrales de contenido en presentaciones PowerPoint** 🚀 