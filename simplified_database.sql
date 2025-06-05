-- =================================
-- ISILAudit IA - Base de Datos Simplificada
-- Solo para datos de revisión de URLs
-- =================================

-- Borrar todas las tablas existentes
DROP TABLE IF EXISTS url_validations CASCADE;
DROP TABLE IF EXISTS domain_statistics CASCADE;
DROP TABLE IF EXISTS processed_files CASCADE;
DROP TABLE IF EXISTS system_config CASCADE;

-- Borrar views existentes
DROP VIEW IF EXISTS url_summary_stats CASCADE;
DROP VIEW IF EXISTS top_domains CASCADE;
DROP VIEW IF EXISTS files_with_most_urls CASCADE;

-- Borrar funciones existentes
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS update_domain_statistics() CASCADE;

-- =================================
-- TABLA PRINCIPAL SIMPLIFICADA
-- =================================

-- Tabla única para URLs validadas después de revisión
CREATE TABLE IF NOT EXISTS validated_urls (
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
    processed_by VARCHAR(100), -- Usuario que procesó
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =================================

CREATE INDEX IF NOT EXISTS idx_validated_urls_filename ON validated_urls(filename);
CREATE INDEX IF NOT EXISTS idx_validated_urls_domain ON validated_urls(url_domain);
CREATE INDEX IF NOT EXISTS idx_validated_urls_status ON validated_urls(status);
CREATE INDEX IF NOT EXISTS idx_validated_urls_user ON validated_urls(processed_by);
CREATE INDEX IF NOT EXISTS idx_validated_urls_created_at ON validated_urls(created_at);
CREATE INDEX IF NOT EXISTS idx_validated_urls_url_hash ON validated_urls USING hash(url);

-- =================================
-- FUNCIONES Y TRIGGERS
-- =================================

-- Función para actualizar automáticamente el campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para validated_urls
CREATE TRIGGER update_validated_urls_updated_at 
    BEFORE UPDATE ON validated_urls 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =================================
-- VISTAS ÚTILES
-- =================================

-- Vista resumen de URLs por usuario
CREATE OR REPLACE VIEW user_url_summary AS
SELECT 
    processed_by,
    COUNT(*) as total_urls,
    COUNT(DISTINCT url_domain) as unique_domains,
    COUNT(DISTINCT filename) as total_files,
    COUNT(CASE WHEN status LIKE '%Activo%' THEN 1 END) as active_urls,
    COUNT(CASE WHEN status LIKE '%❌%' THEN 1 END) as broken_urls,
    DATE_TRUNC('day', created_at) as processing_date
FROM validated_urls
GROUP BY processed_by, DATE_TRUNC('day', created_at)
ORDER BY processing_date DESC, processed_by;

-- Vista de dominios más frecuentes
CREATE OR REPLACE VIEW frequent_domains AS
SELECT 
    url_domain,
    COUNT(*) as occurrences,
    COUNT(DISTINCT filename) as files_count,
    COUNT(CASE WHEN status LIKE '%Activo%' THEN 1 END) as active_count,
    COUNT(CASE WHEN status LIKE '%❌%' THEN 1 END) as broken_count,
    ROUND(
        COUNT(CASE WHEN status LIKE '%Activo%' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as active_percentage
FROM validated_urls
WHERE url_domain IS NOT NULL AND url_domain != ''
GROUP BY url_domain
ORDER BY occurrences DESC
LIMIT 50;

-- Vista de archivos con más URLs problemáticas
CREATE OR REPLACE VIEW problematic_files AS
SELECT 
    filename,
    subfolder,
    processed_by,
    COUNT(*) as total_urls,
    COUNT(CASE WHEN status LIKE '%❌%' THEN 1 END) as broken_urls,
    ROUND(
        COUNT(CASE WHEN status LIKE '%❌%' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as broken_percentage,
    MAX(created_at) as last_processed
FROM validated_urls
GROUP BY filename, subfolder, processed_by
HAVING COUNT(CASE WHEN status LIKE '%❌%' THEN 1 END) > 0
ORDER BY broken_percentage DESC, broken_urls DESC;

-- =================================
-- POLÍTICAS DE SEGURIDAD (RLS)
-- =================================

-- Habilitar Row Level Security
ALTER TABLE validated_urls ENABLE ROW LEVEL SECURITY;

-- Política para permitir todo a usuarios autenticados
CREATE POLICY "Allow all for authenticated users" ON validated_urls
    FOR ALL USING (auth.role() = 'authenticated');

-- =================================
-- COMENTARIOS PARA DOCUMENTACIÓN
-- =================================

COMMENT ON TABLE validated_urls IS 'Tabla principal que almacena URLs validadas extraídas de presentaciones PPT después de revisión';
COMMENT ON COLUMN validated_urls.filename IS 'Nombre del archivo PPTX procesado';
COMMENT ON COLUMN validated_urls.slide_number IS 'Número de diapositiva donde se encontró la URL';
COMMENT ON COLUMN validated_urls.url IS 'URL completa encontrada';
COMMENT ON COLUMN validated_urls.url_domain IS 'Dominio extraído de la URL';
COMMENT ON COLUMN validated_urls.status IS 'Estado de validación de la URL (Activo, Error, etc.)';
COMMENT ON COLUMN validated_urls.processed_by IS 'Usuario que realizó el procesamiento';
COMMENT ON COLUMN validated_urls.subfolder IS 'Subcarpeta donde se encontró el archivo';

-- =================================
-- =================================
-- CONFIGURACIÓN COMPLETADA
-- =================================

-- Base de datos optimizada para ISILAudit IA
-- Tabla: validated_urls
-- Funciones: update_updated_at_column()
-- Vistas: user_url_summary, frequent_domains, problematic_files
-- Políticas: RLS habilitado para usuarios autenticados 