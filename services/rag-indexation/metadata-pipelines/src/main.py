import os
import sys
import json

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import DB_CONFIG, PIPELINE_SETTINGS
from src.common.database_manager import DatabaseManager
from src.common.checkpoint_manager import CheckpointManager
from src.pipeline.metadata_pipeline import MetadataPipeline
from src.common.utils import generate_run_id
from src.common.logger import setup_logger

logger = setup_logger("MainOrchestrator")

def run_pipeline():
    run_id = generate_run_id()
    checkpoint_mgr = CheckpointManager()
    
    # Obtener último checkpoint
    checkpoint = checkpoint_mgr.get_last_checkpoint(PIPELINE_SETTINGS['default_start_date'])
    start_date = checkpoint['last_checkpoint_date']
    
    logger.info(f"[INIT] Pipeline incremental iniciado | RunID: {run_id}")
    logger.info(f"[INIT] Checkpoint de extracción: {start_date}")

    try:
        db = DatabaseManager(DB_CONFIG)
        pipeline = MetadataPipeline(db)
        
        # Pre-flight validation
        has_changes, doc_count = pipeline.has_new_changes(start_date)
        
        if not has_changes:
            logger.info(f"[SKIP] Sin cambios detectados desde {start_date}. Pipeline omitido.")
            return
        
        logger.info(f"[DETECT] {doc_count} documento(s) pendiente(s) de procesamiento")

        # Bronze Layer
        bronze_payload = pipeline.run_bronze(start_date, run_id)
        
        if bronze_payload and bronze_payload["metadata_run"]["record_count"] > 0:
            # Silver Layer
            silver_payload = pipeline.run_silver(bronze_payload)
            
            # Gold Layer
            gold_payload = pipeline.run_gold(silver_payload)
            
            # Guardar checkpoint con la fecha más reciente de los documentos procesados
            # Usamos effective_date (ModifyDate del documento) para mantener compatibilidad SQL
            max_date = max(doc["effective_date"] for doc in gold_payload["data"])
            docs_processed = gold_payload["metadata_run"]["final_record_count"]
            checkpoint_mgr.save_checkpoint(run_id, max_date, docs_processed)
            
            logger.info(f"[DONE] Pipeline completado exitosamente | RunID: {run_id}")
        else:
            logger.warning("[WARN] Conteo pre-flight positivo pero extracción vacía. Verificar consistencia en origen.")

    except Exception as e:
        logger.error(f"[ERROR] Fallo crítico en pipeline: {e}")

if __name__ == "__main__":
    run_pipeline()