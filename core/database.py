import os
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


class Database:
    """Conexión a Supabase con compatibilidad para consultas"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en .env")
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # ============================================================
    # MÉTODOS PARA EJECUTAR CONSULTAS (compatibilidad)
    # ============================================================
    
    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta SQL en Supabase.
        Intenta parsear la consulta para usar los métodos de Supabase.
        """
        try:
            # Detectar el tipo de consulta
            query_upper = query.strip().upper()
            
            # SELECT
            if query_upper.startswith('SELECT'):
                return self._parse_select(query, params)
            
            # INSERT
            elif query_upper.startswith('INSERT'):
                return self._parse_insert(query, params)
            
            # UPDATE
            elif query_upper.startswith('UPDATE'):
                return self._parse_update(query, params)
            
            # DELETE
            elif query_upper.startswith('DELETE'):
                return self._parse_delete(query, params)
            
            else:
                print(f"⚠️ Consulta no soportada: {query[:100]}...")
                return []
                
        except Exception as e:
            print(f"❌ Error en execute_query: {e}")
            return []
    
    # ============================================================
    # PARSER DE CONSULTAS
    # ============================================================
    
    def _parse_select(self, query, params=None):
        """Parsea una consulta SELECT"""
        try:
            # Extraer tabla
            import re
            match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            if not match:
                print(f"⚠️ No se pudo extraer tabla de: {query[:100]}...")
                return []
            
            table = match.group(1)
            
            # Extraer condición WHERE
            where_match = re.search(r'WHERE\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            
            if where_match and params:
                column = where_match.group(1)
                value = params[0]
                print(f"🔍 Consultando {table} con {column}={value}")
                result = self.client.table(table).select("*").eq(column, value).execute()
                return result.data
            
            # Si no hay WHERE, traer todos
            print(f"📊 Consultando toda la tabla: {table}")
            result = self.client.table(table).select("*").execute()
            return result.data
            
        except Exception as e:
            print(f"❌ Error en _parse_select: {e}")
            return []
    
    def _parse_insert(self, query, params=None):
        """Parsea una consulta INSERT"""
        try:
            import re
            match = re.search(r'INSERT INTO\s+(\w+)\s*\(([^)]+)\)', query, re.IGNORECASE)
            if not match:
                return None
            
            table = match.group(1)
            columns = [col.strip() for col in match.group(2).split(',')]
            
            if not params:
                return None
            
            # Construir diccionario de datos
            data = {}
            for i, col in enumerate(columns):
                if i < len(params):
                    data[col] = params[i]
            
            print(f"📝 Insertando en {table}: {data}")
            result = self.client.table(table).insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"❌ Error en _parse_insert: {e}")
            return None
    
    def _parse_update(self, query, params=None):
        """Parsea una consulta UPDATE"""
        try:
            import re
            match = re.search(r'UPDATE\s+(\w+)\s+SET\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            if not match or not params:
                return 0
            
            table = match.group(1)
            column = match.group(2)
            value = params[0]
            
            # Buscar condición WHERE
            where_match = re.search(r'WHERE\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            if where_match and len(params) > 1:
                id_col = where_match.group(1)
                id_val = params[1]
                print(f"📝 Actualizando {table}: {column}={value} WHERE {id_col}={id_val}")
                result = self.client.table(table).update({column: value}).eq(id_col, id_val).execute()
                return len(result.data) if result.data else 0
            
            return 0
            
        except Exception as e:
            print(f"❌ Error en _parse_update: {e}")
            return 0
    
    def _parse_delete(self, query, params=None):
        """Parsea una consulta DELETE"""
        try:
            import re
            match = re.search(r'DELETE FROM\s+(\w+)', query, re.IGNORECASE)
            if not match:
                return 0
            
            table = match.group(1)
            
            where_match = re.search(r'WHERE\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            if where_match and params:
                id_col = where_match.group(1)
                id_val = params[0]
                print(f"🗑️ Eliminando de {table} WHERE {id_col}={id_val}")
                result = self.client.table(table).delete().eq(id_col, id_val).execute()
                return len(result.data) if result.data else 0
            
            return 0
            
        except Exception as e:
            print(f"❌ Error en _parse_delete: {e}")
            return 0
    
    # ============================================================
    # MÉTODOS DIRECTOS
    # ============================================================
    
    def execute_update(self, query, params=None):
        """Ejecuta UPDATE/DELETE"""
        return self.execute_query(query, params)
    
    def execute_insert(self, query, params=None):
        """Ejecuta INSERT"""
        return self.execute_query(query, params)
    
    def get_all(self, table, filters=None, order_by=None, limit=None):
        """Obtiene todos los registros de una tabla"""
        try:
            query = self.client.table(table).select("*")
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(key, value)
                    else:
                        query = query.eq(key, value)
            
            if order_by:
                query = query.order(order_by)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error en get_all: {e}")
            return []
    
    def get_by_id(self, table, id):
        """Obtiene un registro por ID"""
        try:
            response = self.client.table(table).select("*").eq("id", id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error en get_by_id: {e}")
            return None
    
    def insert(self, table, data):
        """Inserta un registro"""
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error en insert: {e}")
            return None
    
    def insert_many(self, table, data):
        """Inserta múltiples registros"""
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data
        except Exception as e:
            print(f"Error en insert_many: {e}")
            return []
    
    def update(self, table, id, data):
        """Actualiza un registro"""
        try:
            response = self.client.table(table).update(data).eq("id", id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error en update: {e}")
            return None
    
    def delete(self, table, id):
        """Elimina un registro"""
        try:
            self.client.table(table).delete().eq("id", id).execute()
            return True
        except Exception as e:
            print(f"Error en delete: {e}")
            return False
    
    def get_by_condition(self, table, condition, value):
        """Obtiene registros por condición simple"""
        try:
            response = self.client.table(table).select("*").eq(condition, value).execute()
            return response.data
        except Exception as e:
            print(f"Error en get_by_condition: {e}")
            return []
    
    def get_with_filter(self, table, filters=None, order_by=None, limit=None):
        """Obtiene registros con filtros avanzados"""
        try:
            query = self.client.table(table).select("*")
            
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(key, value)
                    else:
                        query = query.eq(key, value)
            
            if order_by:
                query = query.order(order_by)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error en get_with_filter: {e}")
            return []
    
    def get_movimientos(self, desde=None, hasta=None, filtros=None, limit=1000):
        """Obtiene movimientos con filtros"""
        try:
            query = self.client.table("movimiento_general").select("*")
            
            if desde:
                query = query.gte("fecha", desde)
            if hasta:
                query = query.lte("fecha", hasta)
            
            if filtros:
                for key, value in filtros.items():
                    if value:
                        if isinstance(value, list):
                            query = query.in_(key, value)
                        else:
                            query = query.eq(key, value)
            
            query = query.order("fecha", desc=True).limit(limit)
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error en get_movimientos: {e}")
            return []
    
    def get_metros(self, desde=None, hasta=None, filtros=None, limit=1000):
        """Obtiene metros con filtros"""
        try:
            query = self.client.table("metros_general").select("*")
            
            if desde:
                query = query.gte("fecha", desde)
            if hasta:
                query = query.lte("fecha", hasta)
            
            if filtros:
                for key, value in filtros.items():
                    if value:
                        if isinstance(value, list):
                            query = query.in_(key, value)
                        else:
                            query = query.eq(key, value)
            
            query = query.order("fecha", desc=True).limit(limit)
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error en get_metros: {e}")
            return []


# ============================================================
# SINGLETON GLOBAL
# ============================================================

_db_instance = None

def get_db():
    """Obtiene instancia única de la base de datos"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance