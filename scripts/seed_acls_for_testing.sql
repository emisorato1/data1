-- ============================================================================
-- Script para crear ACLs de prueba para todos los documentos indexados
-- ============================================================================
-- 
-- CONTEXTO:
-- El sistema RAG requiere que cada documento tenga ACLs en la tabla dtreeacl
-- para determinar qué usuarios pueden acceder a él. Sin ACLs, el sistema
-- no puede recuperar contexto y siempre responde con el mensaje de fallback.
--
-- Este script:
-- 1. Crea un registro en kuaf para el usuario admin (si no existe)
-- 2. Crea ACLs para dar acceso "See Contents" (permissions = 2) a todos
--    los documentos existentes para el usuario admin
--
-- PERMISOS en OpenText:
-- permissions es un bitmap:
--   1 = See
--   2 = See Contents  <- Necesario para RAG
--   4 = Modify
--   8 = Delete
--  16 = Delete versions
--  32 = Modify permissions
-- ============================================================================

BEGIN;

-- Paso 1: Verificar que exista el usuario admin en la tabla users
DO $$
DECLARE
    v_admin_id BIGINT;
BEGIN
    SELECT id INTO v_admin_id FROM users WHERE email = 'admin@banco.com';
    
    IF v_admin_id IS NULL THEN
        RAISE EXCEPTION 'Usuario admin@banco.com no existe en la tabla users. Ejecuta la migración 005_seed_admin_user.py primero.';
    END IF;
    
    RAISE NOTICE 'Usuario admin encontrado con ID: %', v_admin_id;
END $$;

-- Paso 2: Crear entrada en kuaf para el usuario admin (espejo OpenText)
-- type = 0 para usuario individual
INSERT INTO kuaf (id, name, type, deleted)
SELECT 
    u.id,
    u.email,
    0 AS type,
    0 AS deleted
FROM users u
WHERE u.email = 'admin@banco.com'
ON CONFLICT (id) DO NOTHING;

-- Paso 3: Crear ACLs para todos los documentos existentes
-- Dar permiso "See Contents" (2) al usuario admin sobre todos los documentos
INSERT INTO dtreeacl (data_id, right_id, acl_type, permissions)
SELECT 
    d.id AS data_id,
    u.id AS right_id,
    0 AS acl_type,  -- ACL directo (no heredado)
    2 AS permissions  -- See Contents
FROM documents d
CROSS JOIN users u
WHERE u.email = 'admin@banco.com'
  AND NOT EXISTS (
      SELECT 1 FROM dtreeacl acl 
      WHERE acl.data_id = d.id 
        AND acl.right_id = u.id
  );

-- Paso 4: Refrescar vista materializada de membresías
REFRESH MATERIALIZED VIEW kuaf_membership_flat;

-- Paso 5: Verificación
DO $$
DECLARE
    v_doc_count INTEGER;
    v_acl_count INTEGER;
    v_admin_id BIGINT;
BEGIN
    SELECT id INTO v_admin_id FROM users WHERE email = 'admin@banco.com';
    SELECT COUNT(*) INTO v_doc_count FROM documents WHERE is_active = true;
    SELECT COUNT(*) INTO v_acl_count FROM dtreeacl WHERE right_id = v_admin_id;
    
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Resumen de ACLs creadas:';
    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Documentos activos: %', v_doc_count;
    RAISE NOTICE 'ACLs creadas para admin: %', v_acl_count;
    RAISE NOTICE '';
    RAISE NOTICE 'El usuario admin@banco.com ahora tiene acceso a % documentos', v_acl_count;
    RAISE NOTICE '============================================================';
END $$;

COMMIT;
