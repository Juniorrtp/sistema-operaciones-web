"""
Panel de filtros compartido entre todas las vistas
Equivalente a PanelFiltros en PyQt6
"""

import streamlit as st
from datetime import datetime

class PanelFiltros:
    """Panel de filtros (año, mes, compañía)"""
    
    def __init__(self, api):
        self.api = api
        self._cargar_opciones()
    
    def _cargar_opciones(self):
        """Carga años, meses y compañías disponibles"""
        # Años
        self.anos = self.api.get_anos_disponibles()
        if not self.anos:
            self.anos = [datetime.now().year, datetime.now().year - 1]
        
        # Meses (ordenados como en PyQt6)
        self.meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                      "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        
        # Compañías (como en PyQt6)
        companias = self.api.get_companias_disponibles()
        self.companias_opciones = ["Todas las compañías"] + companias
    
    def render(self):
        """Renderiza los filtros en el sidebar"""
        self.ano = st.selectbox(
            "📅 AÑO",
            options=self.anos,
            index=0 if self.anos else 0
        )
        
        mes_actual = datetime.now().month - 1
        self.mes = st.selectbox(
            "📆 MES",
            options=self.meses,
            index=mes_actual if 0 <= mes_actual < 12 else 0
        )
        
        self.compania_texto = st.selectbox(
            "🏢 COMPAÑÍA",
            options=self.companias_opciones
        )
        
        self.compania = None if self.compania_texto == "Todas las compañías" else self.compania_texto
        
        # Botón para actualizar (similar al btn_filtrar en PyQt6)
        if st.button("🔍 Aplicar Filtros", type="primary", use_container_width=True):
            # Limpiar caché y recargar
            st.cache_data.clear()
            st.rerun()
    
    def obtener_filtros(self):
        """Retorna los filtros actuales (como en PyQt6)"""
        return {
            'ano': self.ano,
            'mes': self.mes,
            'compania': self.compania,
            'compania_texto': self.compania_texto
        }
    
    def obtener_filtros_dict(self):
        """Retorna los filtros actuales como diccionario (para pasar a las vistas)"""
        return {
            'ano': self.ano,
            'mes': self.mes,
            'compania': self.compania,
            'compania_texto': self.compania_texto
        }