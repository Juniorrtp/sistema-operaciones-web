import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

class Database:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar configurados en .env")
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conectado a Supabase")
    
    def get_all(self, table, filters=None, order_by=None, limit=None):
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
        result = query.execute()
        return result.data if result.data else []
    
    def get_by_id(self, table, id):
        result = self.client.table(table).select("*").eq("id", id).execute()
        return result.data[0] if result.data else None
    
    def insert(self, table, data):
        result = self.client.table(table).insert(data).execute()
        return result.data[0] if result.data else None
    
    def update(self, table, id, data):
        result = self.client.table(table).update(data).eq("id", id).execute()
        return result.data[0] if result.data else None
    
    def delete(self, table, id):
        self.client.table(table).delete().eq("id", id).execute()
        return True

_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance