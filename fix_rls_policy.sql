-- =================================
-- CORRECCIÓN URGENTE - Políticas RLS
-- ISILAudit IA - Supabase
-- =================================

-- PASO 1: Eliminar política restrictiva actual
DROP POLICY IF EXISTS "Allow all for authenticated users" ON validated_urls;

-- PASO 2: Crear política permisiva para clave anónima
CREATE POLICY "Allow anonymous access" ON validated_urls
    FOR ALL 
    USING (true)
    WITH CHECK (true);

-- =================================
-- VERIFICACIÓN
-- =================================

-- Verificar que RLS está habilitado
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'validated_urls';

-- Verificar políticas activas
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'validated_urls';

-- =================================
-- EXPLICACIÓN
-- =================================

-- Esta política permite:
-- ✅ INSERT con clave anónima
-- ✅ SELECT con clave anónima  
-- ✅ UPDATE con clave anónima
-- ✅ DELETE con clave anónima

-- IMPORTANTE: Para producción, considera crear políticas más específicas
-- basadas en el campo 'processed_by' o implementar autenticación Supabase

-- =================================
-- POLÍTICA ALTERNATIVA MÁS SEGURA (OPCIONAL)
-- =================================

-- Si quieres una política más segura, descomenta estas líneas:
/*
DROP POLICY IF EXISTS "Allow anonymous access" ON validated_urls;

CREATE POLICY "Allow insert for anon" ON validated_urls
    FOR INSERT 
    WITH CHECK (true);

CREATE POLICY "Allow select for anon" ON validated_urls
    FOR SELECT 
    USING (true);

CREATE POLICY "Allow update own records" ON validated_urls
    FOR UPDATE 
    USING (processed_by IS NOT NULL)
    WITH CHECK (processed_by IS NOT NULL);
*/ 