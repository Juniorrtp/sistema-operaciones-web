import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Ruta de la base de datos SQLite
DB_PATH = Path(__file__).parent.parent / "data" / "sistema.db"

# 🔥 Variable para elegir el modo
MODO = os.getenv('DB_MODO', 'sqlite')  # 'sqlite' o 'supabase'


# ============================================================
# CLASE SQLITE (MANTENIDA)
# ============================================================

class DatabaseSQLite:
    """Conexión a SQLite"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or str(DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid


# ============================================================
# 🔥 SELECCIONAR EL MOTOR
# ============================================================

if MODO == 'supabase':
    from core.database_supabase import DatabaseSupabase
    
    class DatabaseWrapper(DatabaseSupabase):
        """Wrapper para mantener compatibilidad con SQLite"""
        
        def __init__(self):
            super().__init__()
        
        # Mantener compatibilidad con código existente
        def execute_query(self, query, params=None):
            """Redirige a los métodos específicos de Supabase"""
            print(f"⚠️ execute_query no soportado en Supabase. Query: {query[:100]}...")
            return []
        
        def execute_update(self, query, params=None):
            print(f"⚠️ execute_update no soportado en Supabase. Query: {query[:100]}...")
            return 0
        
        def execute_insert(self, query, params=None):
            print(f"⚠️ execute_insert no soportado en Supabase. Query: {query[:100]}...")
            return None

else:
    # Usar SQLite directamente
    DatabaseWrapper = DatabaseSQLite


# ============================================================
# SINGLETON GLOBAL
# ============================================================

_db_instance = None

def get_db():
    """Obtiene instancia única de la base de datos"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseWrapper()
    return _db_instance