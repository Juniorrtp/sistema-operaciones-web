import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


class DatabaseSupabase:
    """Conexión a Supabase - Versión PostgreSQL"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar en .env")
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # ============================================================
    # MÉTODOS BÁSICOS (compatibles con SQLite)
    # ============================================================
    
    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta SQL en Supabase.
        NOTA: No soporta SQL raw directamente.
        Para consultas específicas, usa los métodos dedicados.
        """
        print("⚠️ execute_query no soportado en Supabase. Usa los métodos dedicados.")
        return []
    
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
    
    # ============================================================
    # MÉTODOS ESPECÍFICOS PARA SUPABASE
    # ============================================================
    
    def get_movimientos(self, desde=None, hasta=None, filtros=None):
        """Obtiene movimientos con filtros de fecha"""
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
            
            response = query.order("fecha", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Error en get_movimientos: {e}")
            return []
    
    def get_metros(self, desde=None, hasta=None, filtros=None):
        """Obtiene metros con filtros de fecha"""
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
            
            response = query.order("fecha", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Error en get_metros: {e}")
            return []