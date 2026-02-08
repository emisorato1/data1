"""
Checkpoint Manager - Estado persistente del pipeline.
Gestiona el archivo checkpoint.json para control de ejecución incremental.
"""
import os
import json
from datetime import datetime
from src.common.logger import setup_logger

logger = setup_logger("CheckpointManager")

DEFAULT_CHECKPOINT_FILE = os.path.join("data", "checkpoint.json")

class CheckpointManager:
    def __init__(self, checkpoint_path: str = DEFAULT_CHECKPOINT_FILE):
        self.checkpoint_path = checkpoint_path
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Asegura que el directorio data/ exista."""
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
    
    def get_last_checkpoint(self, default_date: str) -> dict:
        """
        Obtiene el último checkpoint guardado.
        Retorna dict con last_checkpoint_date y metadata del último run.
        """
        if not os.path.exists(self.checkpoint_path):
            logger.info(f"[CHECKPOINT] No existe archivo de estado. Usando fecha default: {default_date}")
            return {
                "last_checkpoint_date": default_date,
                "last_successful_run": None,
                "documents_processed": 0
            }
        
        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
                logger.info(f"[CHECKPOINT] Estado cargado | Último run: {checkpoint.get('last_successful_run')}")
                return checkpoint
        except Exception as e:
            logger.error(f"[CHECKPOINT] Error al leer estado: {e}. Usando fecha default.")
            return {
                "last_checkpoint_date": default_date,
                "last_successful_run": None,
                "documents_processed": 0
            }
    
    def save_checkpoint(self, run_id: str, checkpoint_date: str, documents_processed: int) -> bool:
        """
        Guarda el checkpoint después de una ejecución exitosa.
        """
        checkpoint_data = {
            "last_successful_run": run_id,
            "last_checkpoint_date": checkpoint_date,
            "documents_processed": documents_processed,
            "timestamp_saved": datetime.now().isoformat()
        }
        
        try:
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=4, ensure_ascii=False)
            logger.info(f"[CHECKPOINT] Estado guardado | RunID: {run_id} | Docs: {documents_processed}")
            return True
        except Exception as e:
            logger.error(f"[CHECKPOINT] Error al guardar estado: {e}")
            return False
    
    def reset_checkpoint(self) -> bool:
        """Elimina el checkpoint para forzar reprocesamiento completo."""
        try:
            if os.path.exists(self.checkpoint_path):
                os.remove(self.checkpoint_path)
                logger.info("[CHECKPOINT] Estado reseteado. Próxima ejecución procesará desde fecha default.")
            return True
        except Exception as e:
            logger.error(f"[CHECKPOINT] Error al resetear estado: {e}")
            return False
