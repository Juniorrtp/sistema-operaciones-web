import os
import re
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


class Database:
    """Conexión a Supabase con compatibilidad para consultas SQL"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en .env")
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # ============================================================
    # MÉTODO PRINCIPAL PARA CONSULTAS SQL
    # ============================================================
    
    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta SQL en Supabase.
        Usa el cliente de Supabase para consultas específicas.
        """
        try:
            query_clean = query.strip()
            query_upper = query_clean.upper()
            
            # ============================================================
            # CONSULTAS SELECT CON DISTINCT
            # ============================================================
            if query_upper.startswith('SELECT DISTINCT'):
                return self._handle_distinct_query(query_clean, params)
            
            # ============================================================
            # CONSULTAS SELECT SIMPLES (sin JOIN complejos)
            # ============================================================
            elif query_upper.startswith('SELECT') and 'JOIN' not in query_upper:
                return self._handle_simple_select(query_clean, params)
            
            # ============================================================
            # CONSULTAS CON JOIN
            # ============================================================
            elif query_upper.startswith('SELECT') and 'JOIN' in query_upper:
                return self._handle_join_query(query_clean, params)
            
            # ============================================================
            # CONSULTAS INSERT
            # ============================================================
            elif query_upper.startswith('INSERT'):
                return self._handle_insert(query_clean, params)
            
            # ============================================================
            # CONSULTAS UPDATE
            # ============================================================
            elif query_upper.startswith('UPDATE'):
                return self._handle_update(query_clean, params)
            
            # ============================================================
            # CONSULTAS DELETE
            # ============================================================
            elif query_upper.startswith('DELETE'):
                return self._handle_delete(query_clean, params)
            
            # ============================================================
            # CONSULTAS COUNT
            # ============================================================
            elif 'COUNT(' in query_upper:
                return self._handle_count_query(query_clean, params)
            
            else:
                print(f"⚠️ Consulta no soportada: {query_clean[:100]}...")
                return []
                
        except Exception as e:
            print(f"❌ Error en execute_query: {e}")
            return []
    
    # ============================================================
    # MANEJADORES DE CONSULTAS ESPECÍFICAS
    # ============================================================
    
    def _handle_distinct_query(self, query, params=None):
        """Maneja consultas SELECT DISTINCT"""
        try:
            # Extraer tabla y columna
            # SELECT DISTINCT columna FROM tabla WHERE condiciones
            match = re.search(r'SELECT DISTINCT\s+(\w+)\s+FROM\s+(\w+)', query, re.IGNORECASE)
            if not match:
                return []
            
            column = match.group(1)
            table = match.group(2)
            
            print(f"🔍 Consultando DISTINCT {column} de {table}")
            
            # Obtener todos los registros y extraer valores únicos
            result = self.client.table(table).select(column).execute()
            
            if not result.data:
                return []
            
            # Extraer valores únicos
            valores = list(set([row.get(column) for row in result.data if row.get(column)]))
            
            # Devolver en formato compatible (lista de tuplas)
            return [[v] for v in valores if v]
            
        except Exception as e:
            print(f"❌ Error en _handle_distinct_query: {e}")
            return []
    
    def _handle_simple_select(self, query, params=None):
        """Maneja consultas SELECT simples"""
        try:
            # Extraer tabla
            match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            if not match:
                return []
            
            table = match.group(1)
            
            # Extraer condición WHERE
            where_match = re.search(r'WHERE\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            
            # Extraer ORDER BY
            order_match = re.search(r'ORDER BY\s+(\w+)\s*(DESC|ASC)?', query, re.IGNORECASE)
            order_by = order_match.group(1) if order_match else None
            order_dir = order_match.group(2) if order_match and order_match.group(2) else 'ASC'
            
            # Extraer LIMIT
            limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
            limit = int(limit_match.group(1)) if limit_match else None
            
            # Si hay condición WHERE con parámetros
            if where_match and params:
                column = where_match.group(1)
                value = params[0]
                print(f"🔍 Consultando {table} con {column}={value}")
                result = self.client.table(table).select("*").eq(column, value).execute()
                return result.data
            
            # Si hay múltiples condiciones WHERE
            where_conditions = re.findall(r'(\w+)\s*=\s*\?', query)
            if where_conditions and params:
                query_builder = self.client.table(table).select("*")
                for i, col in enumerate(where_conditions):
                    if i < len(params):
                        query_builder = query_builder.eq(col, params[i])
                result = query_builder.execute()
                return result.data
            
            # Si hay condiciones con != ''
            if "!=''" in query or "!= ''" in query:
                # Obtener todos y filtrar manualmente
                result = self.client.table(table).select("*").execute()
                if result.data:
                    # Buscar columna con condición != ''
                    col_match = re.search(r'(\w+)\s*!=\s*[\'\"]+[\'\"]+', query)
                    if col_match:
                        col = col_match.group(1)
                        return [row for row in result.data if row.get(col) and row.get(col) != '']
                return result.data if result.data else []
            
            # Consulta simple sin condiciones
            print(f"📊 Consultando toda la tabla: {table}")
            query_builder = self.client.table(table).select("*")
            
            if order_by:
                query_builder = query_builder.order(order_by, desc=(order_dir.upper() == 'DESC'))
            
            if limit:
                query_builder = query_builder.limit(limit)
            
            result = query_builder.execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"❌ Error en _handle_simple_select: {e}")
            return []
    
    def _handle_join_query(self, query, params=None):
        """Maneja consultas con JOIN (simplificado)"""
        try:
            # Esta es una simplificación. Para consultas complejas, 
            # recomendamos ejecutar directamente en Supabase.
            print(f"⚠️ JOIN query simplificada: {query[:100]}...")
            
            # Extraer tabla principal
            match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            if not match:
                return []
            
            table = match.group(1)
            
            # Obtener datos de la tabla principal
            result = self.client.table(table).select("*").execute()
            
            # Si hay condición WHERE
            where_match = re.search(r'WHERE\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            if where_match and params:
                column = where_match.group(1)
                value = params[0]
                result = self.client.table(table).select("*").eq(column, value).execute()
            
            # Si hay múltiples condiciones
            where_conditions = re.findall(r'(\w+)\s*=\s*\?', query)
            if where_conditions and params:
                query_builder = self.client.table(table).select("*")
                for i, col in enumerate(where_conditions):
                    if i < len(params):
                        query_builder = query_builder.eq(col, params[i])
                result = query_builder.execute()
            
            # Si hay BETWEEN
            between_match = re.search(r'(\w+)\s+BETWEEN\s+\?\s+AND\s+\?', query, re.IGNORECASE)
            if between_match and params and len(params) >= 2:
                column = between_match.group(1)
                from_val = params[0]
                to_val = params[1]
                result = self.client.table(table).select("*").gte(column, from_val).lte(column, to_val).execute()
            
            # Si hay LIKE
            like_match = re.search(r'(\w+)\s+LIKE\s+\?', query, re.IGNORECASE)
            if like_match and params:
                column = like_match.group(1)
                value = params[0].replace('%', '')
                result = self.client.table(table).select("*").ilike(column, f"%{value}%").execute()
            
            return result.data if result else []
            
        except Exception as e:
            print(f"❌ Error en _handle_join_query: {e}")
            return []
    
    def _handle_insert(self, query, params=None):
        """Maneja consultas INSERT"""
        try:
            match = re.search(r'INSERT INTO\s+(\w+)\s*\(([^)]+)\)', query, re.IGNORECASE)
            if not match or not params:
                return None
            
            table = match.group(1)
            columns = [col.strip() for col in match.group(2).split(',')]
            
            data = {}
            for i, col in enumerate(columns):
                if i < len(params):
                    data[col] = params[i]
            
            result = self.client.table(table).insert(data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"❌ Error en _handle_insert: {e}")
            return None
    
    def _handle_update(self, query, params=None):
        """Maneja consultas UPDATE"""
        try:
            match = re.search(r'UPDATE\s+(\w+)\s+SET\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            if not match or not params:
                return 0
            
            table = match.group(1)
            column = match.group(2)
            value = params[0]
            
            where_match = re.search(r'WHERE\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            if where_match and len(params) > 1:
                id_col = where_match.group(1)
                id_val = params[1]
                result = self.client.table(table).update({column: value}).eq(id_col, id_val).execute()
                return len(result.data) if result.data else 0
            
            return 0
            
        except Exception as e:
            print(f"❌ Error en _handle_update: {e}")
            return 0
    
    def _handle_delete(self, query, params=None):
        """Maneja consultas DELETE"""
        try:
            match = re.search(r'DELETE FROM\s+(\w+)', query, re.IGNORECASE)
            if not match:
                return 0
            
            table = match.group(1)
            
            where_match = re.search(r'WHERE\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            if where_match and params:
                id_col = where_match.group(1)
                id_val = params[0]
                result = self.client.table(table).delete().eq(id_col, id_val).execute()
                return len(result.data) if result.data else 0
            
            return 0
            
        except Exception as e:
            print(f"❌ Error en _handle_delete: {e}")
            return 0
    
    def _handle_count_query(self, query, params=None):
        """Maneja consultas COUNT"""
        try:
            match = re.search(r'FROM\s+(\w+)', query, re.IGNORECASE)
            if not match:
                return [(0,)]
            
            table = match.group(1)
            
            where_match = re.search(r'WHERE\s+(\w+)\s*=\s*\?', query, re.IGNORECASE)
            if where_match and params:
                column = where_match.group(1)
                value = params[0]
                result = self.client.table(table).select("*", count="exact").eq(column, value).execute()
                return [(result.count,)]
            
            result = self.client.table(table).select("*", count="exact").execute()
            return [(result.count,)]
            
        except Exception as e:
            print(f"❌ Error en _handle_count_query: {e}")
            return [(0,)]
    
    # ============================================================
    # MÉTODOS DE COMPATIBILIDAD
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