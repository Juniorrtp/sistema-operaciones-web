from core.database import get_db

class StockCache:
    """Cache de stock - Adaptado de tu código"""
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
        # 🔥 Adaptado a tu tabla movimiento_detalles
        query = """
            SELECT UPPER(TRIM(codigo)), SUM(cantidad)
            FROM movimiento_detalles 
            GROUP BY UPPER(TRIM(codigo))
        """
        try:
            resultados = db.execute_query(query)
            self._cache = {}
            for row in resultados:
                codigo = row[0]
                stock = row[1] if row[1] else 0
                if codigo:
                    self._cache[codigo.upper().strip()] = stock
        except Exception as e:
            print(f"Error actualizando cache: {e}")
            self._cache = {}
    
    def obtener_stock(self, codigo):
        if not codigo:
            return 0
        return self._cache.get(codigo.upper().strip(), 0)
    
    def actualizar_cache(self):
        self._actualizar_cache()