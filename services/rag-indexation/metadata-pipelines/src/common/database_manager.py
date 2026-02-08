import pyodbc
from sqlalchemy import create_engine, text
import os
from src.common.logger import setup_logger

logger = setup_logger("DatabaseManager")

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.engine = self._create_engine()

    def _create_engine(self):
            # Limpieza absoluta de la cadena
            d = self.config['driver']
            s = self.config['server']
            db = self.config['database']
            u = self.config['user']
            p = self.config['password']

            # La Biblia de la cadena de conexión: Sin espacios innecesarios
            conn_str = f"DRIVER={{{d}}};SERVER={s};DATABASE={db};UID={u};PWD={p};TrustServerCertificate=yes"

            def creator():
                # El timeout de 30 es vital para la VPN
                return pyodbc.connect(conn_str, timeout=30)

            # Usamos la URL base mssql+pyodbc:// y delegamos todo al creator
            return create_engine("mssql+pyodbc://", creator=creator)

    def load_query(self, query_path):
            """Carga una query desde un archivo .sql externo."""
            # Obtenemos la raíz del proyecto (metadata-pipelines/) de forma segura
            # Subimos dos niveles desde src/common/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            
            full_path = os.path.join(project_root, 'src', 'pipeline', 'queries', query_path)
            
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"❌ No se encontró la query en: {full_path}")
                
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()

    def execute_query(self, query_text, params=None):
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query_text), params or {})
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error crítico en ejecución SQL: {e}")
            raise