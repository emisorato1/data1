import os
from datetime import datetime
from src.common.utils import calculate_checksum, save_json_artifact
from src.common.logger import setup_logger

logger = setup_logger("MetadataPipeline")

class MetadataPipeline:
    def __init__(self, db_manager):
        self.db = db_manager
        # Cargamos la query una sola vez al instanciar
        self.extract_query = self.db.load_query('extract_metadata.sql')
    
    def has_new_changes(self, start_date):
            """
            Validación Pre-flight: Ejecuta query ligera de conteo.
            Evita procesamientos innecesarios y generación de archivos vacíos.
            """
            try:
                count_query = self.db.load_query('count_changes.sql')
                result = self.db.execute_query(count_query, {"start_date": start_date})
                total_changes = result[0]['total'] if result else 0
                return total_changes > 0, total_changes
            except Exception as e:
                logger.error(f"[PREFLIGHT] Error en validación de cambios: {e}")
                return True, 0

    def run_bronze(self, start_date, run_id):
        """
        CAPA BRONZE: Extracción y Persistencia Cruda.
        """
        logger.info(f"[BRONZE] Iniciando extracción | Desde: {start_date}")

        # 1. Ejecución de la query externa
        raw_rows = self.db.execute_query(self.extract_query, {"start_date": start_date})

        # 2. Construcción del objeto de estado Bronze (Sin transformaciones)
        # La DOC pide: Timestamp, Cantidad, Checksum.
        bronze_payload = {
            "metadata_run": {
                "run_id": run_id,
                "stage": "bronze",
                "timestamp_extraction": datetime.now().isoformat(),
                "record_count": len(raw_rows),
                "source_system": "OpenText Content Server (LAB)",
                "checksum_data": calculate_checksum(raw_rows)
            },
            "raw_data": raw_rows
        }

        # 3. Persistencia en el Data Lake (Bronze)
        # Definimos la ruta: data/bronze/BRZ_{run_id}.json
        output_path = os.path.join("data", "1_bronze", f"BRZ_{run_id}.json")
        save_json_artifact(bronze_payload, output_path)

        logger.info(f"[BRONZE] Completado | Records: {len(raw_rows)} | Output: {output_path}")
        
        return bronze_payload
    
    def run_silver(self, bronze_payload):
        """
        CAPA SILVER: Estandarización y Procesamiento de Seguridad.
        Cumple con: Biblia Sección 5 - Metadata Silver.
        """
        run_id = bronze_payload["metadata_run"]["run_id"]
        logger.info(f"[SILVER] Iniciando transformación y agrupamiento")

        # Lista blanca de MimeTypes (Biblia Sección 5.8 - Filtrado)
        allowed_mimetypes = [
            'application/pdf', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        processed_docs = {}
        extraction_data = bronze_payload["raw_data"]

        for row in extraction_data:
            # 1. Validación de tipo de archivo
            if row['MimeType'] not in allowed_mimetypes:
                continue

            data_id = row['DataID']

            # 2. Inicialización de documento (Normalización)
            if data_id not in processed_docs:
                processed_docs[data_id] = {
                    "source_id": f"CS-{data_id}",
                    "source_version": row['VersionNumber'],
                    "name": row['Name'],
                    "file_size_bytes": row['FileSize'],
                    "modify_date_iso": row['ModifyDate'].isoformat() if hasattr(row['ModifyDate'], 'isoformat') else str(row['ModifyDate']),
                    "efs_relative_path": row['EFSRelativePath'],
                    "mime_type": row['MimeType'],
                    "security_tokens": [],
                    "lineage": {
                        "run_id": run_id,
                        "stage": "silver",
                        "previous_stage_id": f"BRZ_{run_id}"
                    }
                }

            # 3. Procesamiento de Seguridad (Biblia Sección 5.6)
            # Formato esperado: "T:ID:N" (Tipo:RightID:AccessLevel)
            if row['RightID'] is not None:
                subject_initial = row['SubjectType'][0] # U, G, P, A o S
                token = f"{subject_initial}:{row['RightID']}:{row['AccessLevel']}"
                
                if token not in processed_docs[data_id]["security_tokens"]:
                    processed_docs[data_id]["security_tokens"].append(token)

        # 4. Construcción del Payload Silver
        silver_payload = {
            "metadata_run": {
                "run_id": run_id,
                "stage": "silver",
                "timestamp_processed": datetime.now().isoformat(),
                "input_records": len(extraction_data),
                "output_documents": len(processed_docs),
                "checksum_silver": calculate_checksum(list(processed_docs.values()))
            },
            "data": list(processed_docs.values())
        }

        # 5. Persistencia en Silver
        output_path = os.path.join("data", "2_silver", f"SLV_{run_id}.json")
        save_json_artifact(silver_payload, output_path)

        logger.info(f"[SILVER] Completado | Input: {len(extraction_data)} rows -> Output: {len(processed_docs)} docs")
        
        return silver_payload
    
    def run_gold(self, silver_payload):
        """
        CAPA GOLD: Validación de Contrato y Formato Final.
        Cumple con: Biblia Sección 5 - Metadata Gold y Sección 7 - Contratos.
        """
        run_id = silver_payload["metadata_run"]["run_id"]
        logger.info(f"[GOLD] Iniciando validación de contrato final")

        gold_documents = []
        silver_data = silver_payload["data"]

        for doc in silver_data:
            # 1. Generación de ID Final (Biblia Sección 7 - Formato DOC-system-id-version)
            # Ejemplo: DOC-CS-6572-v9
            document_id = f"DOC-CS-{doc['source_id'].split('-')[1]}-v{doc['source_version']}"

            # 2. Construcción del Objeto Gold (Data Contract Silver -> Gold)
            gold_record = {
                "document_id": document_id,
                "title": doc["name"],
                "classification": "Unclassified", # Valor por defecto o mapeado
                "access_groups": doc["security_tokens"], # Tokens resueltos en Silver
                "version": str(doc["source_version"]),
                "effective_date": doc["modify_date_iso"],
                "source_metadata": {
                    "system": "Content Server",
                    "efs_path": doc["efs_relative_path"],
                    "file_size": doc["file_size_bytes"],
                    "mime_type": doc["mime_type"]
                },
                "integrity_hash": calculate_checksum(doc) # Hash de integridad del registro
            }
            gold_documents.append(gold_record)

        # 3. Payload Final de la Capa Gold
        gold_payload = {
            "metadata_run": {
                "run_id": run_id,
                "stage": "gold",
                "timestamp_ready": datetime.now().isoformat(),
                "final_record_count": len(gold_documents),
                "integrity_hash_total": calculate_checksum(gold_documents)
            },
            "data": gold_documents
        }

        # 4. Persistencia en Gold
        output_path = os.path.join("data", "3_gold", f"GLD_{run_id}.json")
        save_json_artifact(gold_payload, output_path)

        logger.info(f"[GOLD] Completado | Documentos finales: {len(gold_documents)} | Output: {output_path}")
        
        return gold_payload