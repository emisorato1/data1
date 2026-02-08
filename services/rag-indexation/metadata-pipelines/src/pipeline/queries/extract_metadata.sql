-- Query de Extracción Metadata Bronze (Versión Final Blindada)
-- Filtrado a carpeta específica: PRUEBA-DATA-OILERS
-- Excluye documentos eliminados y archivos huérfanos/temporales
SELECT 
    d.DataID, 
    d.VersionNum AS VersionNumber, -- Usamos el puntero oficial de la versión actual
    d.Name, 
    v.DataSize AS FileSize,
    d.ModifyDate,
    p.providerData + '.dat' AS EFSRelativePath,
    v.MimeType,
    acl.RightID,
    acl.See AS AccessLevel,
    -- Clasificación de Privacidad (Basado en RightID -1: Public)
    CASE 
        WHEN acl.RightID = -1 THEN 'Public'
        ELSE 'Private'
    END AS PrivacyStatus,
    CASE 
        WHEN k.Type = 0 THEN 'User'
        WHEN k.Type = 1 THEN 'Group'
        WHEN acl.RightID = -1 THEN 'Public'
        WHEN acl.RightID = -2 THEN 'Admin'
        ELSE 'Special/System'
    END AS SubjectType
FROM DTreeCore d
-- El INNER JOIN asegura que solo traemos nodos que TIENEN versiones
-- Y el cruce con d.VersionNum garantiza que es la versión ACTUAL
INNER JOIN DVersData v ON d.DataID = v.DocID AND d.VersionNum = v.Version
INNER JOIN ProviderData p ON v.ProviderId = p.providerID
LEFT JOIN DTreeACL acl ON d.DataID = acl.DataID AND acl.See >= 1
LEFT JOIN KUAF k ON acl.RightID = k.ID
WHERE d.SubType = 144 -- Solo documentos
AND d.VersionNum IS NOT NULL -- Filtro de seguridad: debe tener versión
AND d.ModifyDate > :start_date
-- Filtro: Solo documentos NO eliminados
AND (d.Deleted IS NULL OR d.Deleted = 0)
-- Filtro: Excluir archivos con nombres GUID (huérfanos/temporales)
AND d.Name NOT LIKE '@[%'
-- Filtro: Solo documentos dentro de la carpeta PRUEBA-DATA-OILERS
AND EXISTS (
    SELECT 1 FROM DTreeAncestors anc
    INNER JOIN DTreeCore folder ON anc.AncestorID = folder.DataID
    WHERE anc.DataID = d.DataID
    AND folder.Name = 'PRUEBA-DATA-OILERS'
)
ORDER BY d.ModifyDate ASC