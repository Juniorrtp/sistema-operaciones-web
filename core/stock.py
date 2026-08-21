from core.database import get_db

class StockCache:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = StockCache()
        return cls._instance
    
    def __init__(self):
        self._cache = {}
        self._actualizar_cache()
    
    def _actualizar_cache(self):
        db = get_db()
        try:
            # Obtener todos los detalles con cantidad > 0
            result = db.client.table("movimiento_detalles").select("codigo, cantidad").execute()
            
            cache = {}
            for row in result.data:
                codigo = row.get('codigo')
                cantidad = row.get('cantidad', 0)
                if codigo:
                    codigo_clean = codigo.upper().strip()
                    cache[codigo_clean] = cache.get(codigo_clean, 0) + cantidad
            
            self._cache = cache
        except Exception as e:
            print(f"Error actualizando cache: {e}")
            self._cache = {}
    
    def obtener_stock(self, codigo):
        if not codigo:
            return 0
        return self._cache.get(codigo.upper().strip(), 0)
    
    def actualizar_cache(self):
        self._actualizar_cache()