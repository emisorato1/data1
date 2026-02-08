-- Query de Conteo Pre-flight (Alineada con filtros Silver)
-- Cuenta documentos únicos que serán procesados por el pipeline
-- Filtrado a carpeta específica: PRUEBA-DATA-OILERS
-- Excluye documentos eliminados y archivos huérfanos/temporales
SELECT COUNT(DISTINCT d.DataID) as total
FROM DTreeCore d
INNER JOIN DVersData v ON d.DataID = v.DocID AND d.VersionNum = v.Version
WHERE d.SubType = 144 
AND v.MimeType IN (
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
)
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