"""
Cliente API para conectar Streamlit con el backend en Render
"""

import requests
import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime

class APIClient:
    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            self.base_url = "https://sistema-operaciones-web.onrender.com"
        else:
            self.base_url = base_url
        self.timeout = 30
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Error al conectar con {endpoint}: {e}")
            return []
    
    # ============================================================
    # ENDPOINTS (todos los que necesitas)
    # ============================================================
    
    def get_movimientos(self, limit: int = 10000) -> List[Dict]:
        return self._get(f"/api/movimientos?limit={limit}")
    
    def get_metros(self, limit: int = 10000) -> List[Dict]:
        return self._get(f"/api/metros?limit={limit}")
    
    def get_metros_detalles(self) -> List[Dict]:
        return self._get("/api/metros-detalles")
    
    def get_objetivos(self) -> List[Dict]:
        return self._get("/api/objetivos")
    
    def get_detalles_movimientos(self) -> List[Dict]:
        return self._get("/api/detalles-movimientos")
    
    def get_equipos(self) -> List[Dict]:
        return self._get("/api/equipos")
    
    def get_operadores(self) -> List[Dict]:
        return self._get("/api/operadores")
    
    def get_companias_disponibles(self) -> List[str]:
        equipos = self.get_equipos()
        if not equipos:
            return []
        companias = set()
        for e in equipos:
            if e.get('compania'):
                companias.add(e.get('compania'))
        return sorted(list(companias))
    
    def get_anos_disponibles(self) -> List[int]:
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