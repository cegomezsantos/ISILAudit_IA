-- =================================
-- ISILAudit - Estructura de Base de Datos
-- Supabase SQL Script
-- =================================

-- Tabla principal para almacenar URLs encontradas en presentaciones PPT
CREATE TABLE IF NOT EXISTS ppt_urls (
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla para almacenar información de archivos procesados
CREATE TABLE IF NOT EXISTS processed_files (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    file_id VARCHAR(255),
    folder_name VARCHAR(255),
    subfolder VARCHAR(255),
    file_size_mb DECIMAL(10,2),
    total_urls_found INTEGER DEFAULT 0,
    total_slides INTEGER DEFAULT 0,
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_id)
);

-- Tabla para almacenar estadísticas de dominios
CREATE TABLE IF NOT EXISTS domain_statistics (
    id BIGSERIAL PRIMARY KEY,
    domain VARCHAR(255) NOT NULL,
    total_occurrences INTEGER DEFAULT 1,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    domain_category VARCHAR(100), -- 'social', 'educational', 'commercial', etc.
    UNIQUE(domain)
);

-- Tabla para log de validaciones de URLs
CREATE TABLE IF NOT EXISTS url_validations (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    status_code INTEGER,
    status VARCHAR(100),
    response_time_ms INTEGER,
    validation_date TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT
);

-- Tabla para configuraciones del sistema
CREATE TABLE IF NOT EXISTS system_config (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =================================

-- Índices para tabla ppt_urls
CREATE INDEX IF NOT EXISTS idx_ppt_urls_filename ON ppt_urls(filename);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_domain ON ppt_urls(url_domain);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_slide ON ppt_urls(slide_number);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_status ON ppt_urls(status);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_created_at ON ppt_urls(created_at);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_url_hash ON ppt_urls USING hash(url);

-- Índices para tabla processed_files
CREATE INDEX IF NOT EXISTS idx_processed_files_filename ON processed_files(filename);
CREATE INDEX IF NOT EXISTS idx_processed_files_folder ON processed_files(folder_name);
CREATE INDEX IF NOT EXISTS idx_processed_files_processed_at ON processed_files(processed_at);

-- Índices para tabla domain_statistics
CREATE INDEX IF NOT EXISTS idx_domain_stats_domain ON domain_statistics(domain);
CREATE INDEX IF NOT EXISTS idx_domain_stats_occurrences ON domain_statistics(total_occurrences);
CREATE INDEX IF NOT EXISTS idx_domain_stats_category ON domain_statistics(domain_category);

-- Índices para tabla url_validations
CREATE INDEX IF NOT EXISTS idx_url_validations_url_hash ON url_validations USING hash(url);
CREATE INDEX IF NOT EXISTS idx_url_validations_date ON url_validations(validation_date);
CREATE INDEX IF NOT EXISTS idx_url_validations_status ON url_validations(status_code);

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

-- Trigger para ppt_urls
CREATE TRIGGER update_ppt_urls_updated_at 
    BEFORE UPDATE ON ppt_urls 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para system_config
CREATE TRIGGER update_system_config_updated_at 
    BEFORE UPDATE ON system_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Función para actualizar estadísticas de dominio automáticamente
CREATE OR REPLACE FUNCTION update_domain_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- Insertar o actualizar estadísticas del dominio
    INSERT INTO domain_statistics (domain, total_occurrences, first_seen_at, last_seen_at)
    VALUES (NEW.url_domain, 1, NOW(), NOW())
    ON CONFLICT (domain) 
    DO UPDATE SET 
        total_occurrences = domain_statistics.total_occurrences + 1,
        last_seen_at = NOW();
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar domain_statistics cuando se inserta una nueva URL
CREATE TRIGGER update_domain_stats_on_url_insert
    AFTER INSERT ON ppt_urls
    FOR EACH ROW EXECUTE FUNCTION update_domain_statistics();

-- =================================
-- VISTAS ÚTILES
-- =================================

-- Vista para obtener estadísticas generales
CREATE OR REPLACE VIEW url_summary_stats AS
SELECT 
    COUNT(*) as total_urls,
    COUNT(DISTINCT url_domain) as unique_domains,
    COUNT(DISTINCT filename) as total_files,
    COUNT(CASE WHEN status LIKE '%Activo%' THEN 1 END) as active_urls,
    COUNT(CASE WHEN status LIKE '%❌%' THEN 1 END) as broken_urls,
    DATE_TRUNC('day', created_at) as date
FROM ppt_urls
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- Vista para dominios más frecuentes
CREATE OR REPLACE VIEW top_domains AS
SELECT 
    domain,
    total_occurrences,
    domain_category,
    first_seen_at,
    last_seen_at
FROM domain_statistics
WHERE is_active = true
ORDER BY total_occurrences DESC
LIMIT 50;

-- Vista para archivos con más URLs
CREATE OR REPLACE VIEW files_with_most_urls AS
SELECT 
    filename,
    folder_name,
    COUNT(*) as url_count,
    COUNT(DISTINCT url_domain) as unique_domains,
    MAX(created_at) as last_processed
FROM ppt_urls p
LEFT JOIN processed_files pf ON p.filename = pf.filename
GROUP BY filename, folder_name
ORDER BY url_count DESC;

-- =================================
-- DATOS INICIALES
-- =================================

-- Configuraciones iniciales del sistema
INSERT INTO system_config (config_key, config_value, description) VALUES 
('app_version', '1.0.0', 'Versión actual de ISILAudit'),
('last_cleanup_date', NOW()::text, 'Última fecha de limpieza de datos'),
('max_urls_per_file', '1000', 'Máximo número de URLs por archivo'),
('url_validation_timeout', '10', 'Timeout en segundos para validación de URLs'),
('enable_auto_validation', 'true', 'Habilitar validación automática de URLs')
ON CONFLICT (config_key) DO NOTHING;

-- Categorías de dominios comunes
INSERT INTO domain_statistics (domain, total_occurrences, domain_category, first_seen_at, last_seen_at) VALUES
('youtube.com', 0, 'multimedia', NOW(), NOW()),
('google.com', 0, 'search', NOW(), NOW()),
('github.com', 0, 'development', NOW(), NOW()),
('microsoft.com', 0, 'technology', NOW(), NOW()),
('linkedin.com', 0, 'social', NOW(), NOW()),
('facebook.com', 0, 'social', NOW(), NOW()),
('twitter.com', 0, 'social', NOW(), NOW()),
('instagram.com', 0, 'social', NOW(), NOW()),
('zoom.us', 0, 'communication', NOW(), NOW()),
('teams.microsoft.com', 0, 'communication', NOW(), NOW()),
('vimeo.com', 0, 'multimedia', NOW(), NOW()),
('reddit.com', 0, 'social', NOW(), NOW()),
('stackoverflow.com', 0, 'development', NOW(), NOW()),
('wikipedia.org', 0, 'educational', NOW(), NOW()),
('edu', 0, 'educational', NOW(), NOW())
ON CONFLICT (domain) DO NOTHING;

-- =================================
-- POLÍTICAS DE SEGURIDAD (RLS)
-- =================================

-- Habilitar Row Level Security
ALTER TABLE ppt_urls ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE domain_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE url_validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;

-- Políticas básicas (ajustar según necesidades de autenticación)
-- Por ahora, permitir acceso completo para usuarios autenticados

CREATE POLICY "Allow all for authenticated users" ON ppt_urls
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all for authenticated users" ON processed_files
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all for authenticated users" ON domain_statistics
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all for authenticated users" ON url_validations
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow read for authenticated users" ON system_config
    FOR SELECT USING (auth.role() = 'authenticated');

-- =================================
-- COMENTARIOS FINALES
-- =================================

-- Script completado
-- Ejecutar este script en el SQL Editor de Supabase
-- Verificar que todas las tablas se crearon correctamente con:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'; 