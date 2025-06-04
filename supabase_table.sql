-- SQL para crear la tabla en Supabase
-- Este script debe ejecutarse en el SQL Editor de Supabase

CREATE TABLE IF NOT EXISTS ppt_urls (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    slide_number INTEGER NOT NULL,
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

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_ppt_urls_filename ON ppt_urls(filename);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_slide_number ON ppt_urls(slide_number);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_domain ON ppt_urls(url_domain);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_status ON ppt_urls(status);
CREATE INDEX IF NOT EXISTS idx_ppt_urls_created_at ON ppt_urls(created_at);

-- Función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER update_ppt_urls_updated_at 
    BEFORE UPDATE ON ppt_urls 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentar la tabla
COMMENT ON TABLE ppt_urls IS 'Tabla para almacenar URLs extraídas de archivos PowerPoint';
COMMENT ON COLUMN ppt_urls.filename IS 'Nombre del archivo PowerPoint original';
COMMENT ON COLUMN ppt_urls.slide_number IS 'Número de la diapositiva donde se encontró la URL';
COMMENT ON COLUMN ppt_urls.url IS 'URL completa encontrada';
COMMENT ON COLUMN ppt_urls.url_domain IS 'Dominio de la URL para facilitar búsquedas';
COMMENT ON COLUMN ppt_urls.location_context IS 'Contexto de ubicación (shape, texto, etc.)';
COMMENT ON COLUMN ppt_urls.text_context IS 'Contexto del texto donde apareció la URL';
COMMENT ON COLUMN ppt_urls.status IS 'Estado de la URL (activa, rota, etc.)';
COMMENT ON COLUMN ppt_urls.status_description IS 'Descripción detallada del estado HTTP';
COMMENT ON COLUMN ppt_urls.checked_at IS 'Timestamp de cuando se verificó el estado de la URL';

-- Habilitar Row Level Security (RLS) si es necesario
-- ALTER TABLE ppt_urls ENABLE ROW LEVEL SECURITY;

-- Política de ejemplo para RLS (opcional - personalizar según necesidades)
-- CREATE POLICY "Permitir lectura y escritura para usuarios autenticados" ON ppt_urls
--     FOR ALL USING (auth.role() = 'authenticated'); 