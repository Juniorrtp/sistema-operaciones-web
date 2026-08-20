#!/usr/bin/env python3
"""
Script para generar el reporte PDF directamente desde terminal
Uso: python3 generar_reporte.py
"""

import sys
import os
import webbrowser
from datetime import datetime, timedelta

# Agregar el proyecto al path
sys.path.append('/media/datadisk/sistema-operaciones-web')

from core.reporte_gerencial import (
    obtener_resumen_general,
    obtener_metros_por_tipo,
    obtener_consumo_por_familia,
    obtener_top_equipos_por_tipo,
    obtener_rendimiento_por_equipo,
    obtener_rendimiento_operadores_brocas,
    obtener_stock_critico
)
from core.exportar_pdf import generar_reporte_pdf


def main():
    """Genera el reporte PDF con los últimos 90 días y lo abre en el navegador"""
    
    print("=" * 60)
    print("📊 GENERANDO REPORTE GERENCIAL")
    print("=" * 60)
    
    # Configurar fechas (últimos 90 días)
    hasta = datetime.now()
    desde = hasta - timedelta(days=90)
    
    desde_str = desde.strftime("%Y-%m-%d")
    hasta_str = hasta.strftime("%Y-%m-%d")
    
    print(f"📅 Período: {desde_str} - {hasta_str}")
    print("🔄 Cargando datos...")
    
    # Cargar datos
    resumen = obtener_resumen_general(desde_str, hasta_str)
    metros_tipo = obtener_metros_por_tipo(desde_str, hasta_str)
    consumo_familia = obtener_consumo_por_familia(desde_str, hasta_str)
    top_equipos = obtener_top_equipos_por_tipo(desde_str, hasta_str, 3)
    rendimiento_equipos = obtener_rendimiento_por_equipo(desde_str, hasta_str)
    operadores = obtener_rendimiento_operadores_brocas(desde_str, hasta_str)
    stock_critico = obtener_stock_critico(5)
    
    print("📄 Generando PDF...")
    
    # Generar PDF
    pdf_path = generar_reporte_pdf(
        desde_str, hasta_str, resumen, metros_tipo, consumo_familia,
        top_equipos, rendimiento_equipos, operadores, stock_critico
    )
    
    # Convertir a ruta absoluta
    pdf_abs_path = os.path.abspath(pdf_path)
    
    print(f"✅ PDF generado: {pdf_abs_path}")
    print("=" * 60)
    
    # 🔥 Abrir el PDF en el navegador
    print("🌐 Abriendo PDF en el navegador...")
    webbrowser.open(f"file://{pdf_abs_path}")
    
    print("✅ PDF abierto en el navegador")


if __name__ == "__main__":
    main()