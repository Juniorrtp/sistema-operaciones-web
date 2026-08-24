import requests
import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE AUTENTICACIÓN
# ============================================

# La API Key debe coincidir con la del backend
STREAMLIT_API_KEY = "streamlit-secret-key-2024"

class APIClient:
    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            # Usar el valor de secrets o el default
            self.base_url = st.secrets.get("API_URL", "https://sistema-operaciones-web.onrender.com")
        else:
            self.base_url = base_url
        self.timeout = 60
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna los headers con la API Key para autenticación"""
        return {
            "X-API-Key": STREAMLIT_API_KEY,
            "Content-Type": "application/json"
        }
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self._get_headers()
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                st.error("❌ Error de autenticación: Verifica que la API Key sea correcta")
            else:
                st.error(f"❌ Error HTTP {e.response.status_code} en {endpoint}: {e}")
            return []
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Error de conexión: No se puede conectar con {self.base_url}")
            return []
        except Exception as e:
            st.error(f"❌ Error al conectar con {endpoint}: {e}")
            return []
    
    # ============================================================
    # ENDPOINTS
    # ============================================================
    
    def get_movimientos(self, limit: int = 10000) -> List[Dict]:
        """Obtiene movimientos generales"""
        return self._get(f"/api/movimientos?limit={limit}")
    
    def get_movimientos_filtrados(self, fecha_desde: Optional[str] = None, 
                                   fecha_hasta: Optional[str] = None, 
                                   limit: int = 10000) -> List[Dict]:
        """Obtiene movimientos con filtros de fecha"""
        params = {"limit": limit}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta
        return self._get("/api/movimientos", params)
    
    def get_metros(self, limit: int = 10000) -> List[Dict]:
        """Obtiene metros generales"""
        return self._get(f"/api/metros?limit={limit}")
    
    def get_metros_filtrados(self, fecha_desde: Optional[str] = None,
                              fecha_hasta: Optional[str] = None,
                              limit: int = 10000) -> List[Dict]:
        """Obtiene metros con filtros de fecha"""
        params = {"limit": limit}
        if fecha_desde:
            params["fecha_desde"] = fecha_desde
        if fecha_hasta:
            params["fecha_hasta"] = fecha_hasta
        return self._get("/api/metros", params)
    
    def get_metros_detalles(self) -> List[Dict]:
        """Obtiene todos los detalles de metros"""
        return self._get("/api/metros-detalles")
    
    def get_objetivos(self) -> List[Dict]:
        """Obtiene objetivos"""
        return self._get("/api/objetivos")
    
    def get_detalles_movimientos(self) -> List[Dict]:
        """Obtiene todos los detalles de movimientos"""
        return self._get("/api/detalles-movimientos")
    
    def get_equipos(self) -> List[Dict]:
        """Obtiene catálogo de equipos"""
        return self._get("/api/equipos")
    
    def get_operadores(self) -> List[Dict]:
        """Obtiene catálogo de operadores"""
        return self._get("/api/operadores")
    
    def get_stock(self) -> List[Dict]:
        """Obtiene stock actual"""
        return self._get("/api/stock")
    
    def get_aceros(self) -> List[Dict]:
        """Obtiene catálogo de aceros"""
        return self._get("/api/aceros")
    
    def get_companias_disponibles(self) -> List[str]:
        """Obtiene lista de compañías disponibles"""
        equipos = self.get_equipos()
        if not equipos:
            return []
        companias = set()
        for e in equipos:
            if e.get('compania'):
                companias.add(e.get('compania'))
        return sorted(list(companias))
    
    def get_anos_disponibles(self) -> List[int]:
        """Obtiene lista de años disponibles"""
        movimientos = self.get_movimientos(limit=10000)
        if not movimientos:
            return [datetime.now().year, datetime.now().year - 1]
        anos = set()
        for m in movimientos:
            if m.get('ano'):
                anos.add(m.get('ano'))
        if not anos:
            return [datetime.now().year, datetime.now().year - 1]
        return sorted(list(anos), reverse=True)

# ============================================================
# INSTANCIA GLOBAL (para usar en toda la app)
# ============================================================

@st.cache_resource
def get_api_client():
    """Retorna una instancia única del APIClient"""
    return APIClient()

# ============================================================
# FUNCIONES DE CONVENIENCIA (para compatibilidad con código existente)
# ============================================================

def fetch_from_api(endpoint: str, params: Optional[Dict] = None) -> Any:
    """Función genérica para consumir la API (compatibilidad)"""
    client = get_api_client()
    # Construir la URL con parámetros
    if params:
        # Convertir params a string para la URL
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return client._get(f"/api/{endpoint}?{param_str}")
    return client._get(f"/api/{endpoint}")

def load_movimientos_general(fecha_desde=None, fecha_hasta=None, limit=5000):
    """Carga movimientos generales (compatibilidad)"""
    client = get_api_client()
    params = {"limit": limit}
    if fecha_desde:
        params["fecha_desde"] = fecha_desde
    if fecha_hasta:
        params["fecha_hasta"] = fecha_hasta
    
    data = client._get("/api/movimientos", params)
    
    # Limpiar datos
    if data:
        for row in data:
            if 'compania' in row and row['compania']:
                row['compania'] = row['compania'].strip()
            if 'tipo_perforacion' in row and row['tipo_perforacion']:
                row['tipo_perforacion'] = row['tipo_perforacion'].strip()
            if 'mes' in row and row['mes']:
                row['mes'] = row['mes'].strip().upper()
            if 'movimiento' in row and row['movimiento']:
                row['movimiento'] = row['movimiento'].strip().upper()
            if 'estado' in row and row['estado']:
                row['estado'] = row['estado'].strip().upper()
    
    return data

def load_movimientos_detalles():
    """Carga detalles de movimientos (compatibilidad)"""
    client = get_api_client()
    return client._get("/api/detalles-movimientos")

def load_metros_general(fecha_desde=None, fecha_hasta=None, limit=5000):
    """Carga metros generales (compatibilidad)"""
    client = get_api_client()
    params = {"limit": limit}
    if fecha_desde:
        params["fecha_desde"] = fecha_desde
    if fecha_hasta:
        params["fecha_hasta"] = fecha_hasta
    
    data = client._get("/api/metros", params)
    
    if data:
        for row in data:
            if 'compania' in row and row['compania']:
                row['compania'] = row['compania'].strip()
            if 'tipo_perforacion' in row and row['tipo_perforacion']:
                row['tipo_perforacion'] = row['tipo_perforacion'].strip()
            if 'mes' in row and row['mes']:
                row['mes'] = row['mes'].strip().upper()
    
    return data

def load_metros_detalles():
    """Carga detalles de metros (compatibilidad)"""
    client = get_api_client()
    return client._get("/api/metros-detalles")

def load_stock_from_api():
    """Carga stock (compatibilidad)"""
    client = get_api_client()
    return client._get("/api/stock")

def load_objetivos():
    """Carga objetivos (compatibilidad)"""
    client = get_api_client()
    return client._get("/api/objetivos")

def load_aceros():
    """Carga aceros (compatibilidad)"""
    client = get_api_client()
    return client._get("/api/aceros")

def load_equipos():
    """Carga equipos (compatibilidad)"""
    client = get_api_client()
    return client._get("/api/equipos")

def load_operadores():
    """Carga operadores (compatibilidad)"""
    client = get_api_client()
    return client._get("/api/operadores")