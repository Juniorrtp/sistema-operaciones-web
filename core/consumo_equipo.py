from core.database import get_db
from collections import defaultdict
from datetime import datetime

FAMILIAS = ["SHANK", "ACOPLES", "BARRAS", "BROCAS", "RIMADORAS"]


def obtener_filtros_consumo():
    """Obtiene opciones para filtros de consumo por equipo"""
    db = get_db()
    
    try:
        # Tipos de perforación
        result = db.client.table("equipo").select("tipo_perforacion").execute()
        tipos = [row['tipo_perforacion'] for row in result.data if row.get('tipo_perforacion') and row['tipo_perforacion'] != '']
        opciones_tipos = ["TODOS"] + sorted(set(tipos))
        
        # Compañías
        result = db.client.table("equipo").select("compania").execute()
        companias = [row['compania'] for row in result.data if row.get('compania') and row['compania'] != '']
        opciones_companias = ["TODAS"] + sorted(set(companias))
        
        return opciones_tipos, opciones_companias
    except Exception as e:
        print(f"Error en obtener_filtros_consumo: {e}")
        return ["TODOS"], ["TODAS"]


def obtener_consumo_equipo(desde, hasta, tipo=None, compania=None):
    """Obtiene consumo por equipo para cada familia"""
    db = get_db()
    
    try:
        query = """
            SELECT 
                UPPER(TRIM(md.familia)) as familia,
                mg.equipo,
                SUM(md.cantidad * -1) as total_consumo
            FROM movimiento_general mg
            JOIN movimiento_detalles md ON mg.id = md.entrega_id
            WHERE mg.movimiento = 'SALIDA'
                AND md.cantidad < 0
                AND mg.fecha BETWEEN ? AND ?
        """
        params = [desde, hasta]
        
        if tipo:
            query += " AND mg.tipo_perforacion = ?"
            params.append(tipo)
        if compania:
            query += " AND mg.compania = ?"
            params.append(compania)
        
        query += " GROUP BY md.familia, mg.equipo ORDER BY mg.equipo"
        
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados] if resultados else []
        
    except Exception as e:
        print(f"Error en obtener_consumo_equipo: {e}")
        return []


def obtener_entregas_descripcion(desde, hasta, tipo=None, compania=None):
    """Obtiene entregas por descripción con compañías y equipos"""
    db = get_db()
    
    try:
        query = """
            SELECT 
                UPPER(TRIM(md.descripcion)) as descripcion,
                mg.compania,
                mg.equipo,
                SUM(md.cantidad * -1) as total_entregado
            FROM movimiento_general mg
            JOIN movimiento_detalles md ON mg.id = md.entrega_id
            WHERE mg.movimiento = 'SALIDA'
                AND md.cantidad < 0
                AND mg.fecha BETWEEN ? AND ?
        """
        params = [desde, hasta]
        
        if tipo:
            query += " AND mg.tipo_perforacion = ?"
            params.append(tipo)
        if compania:
            query += " AND mg.compania = ?"
            params.append(compania)
        
        query += " GROUP BY md.descripcion, mg.compania, mg.equipo ORDER BY total_entregado DESC"
        
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados] if resultados else []
        
    except Exception as e:
        print(f"Error en obtener_entregas_descripcion: {e}")
        return []


def obtener_metros_equipo(desde, hasta, tipo=None, compania=None):
    """Obtiene metros por equipo - tabla y gráfico"""
    db = get_db()
    
    # Datos para tabla (por fecha)
    try:
        query_tabla = """
            SELECT 
                mg.equipo,
                mg.fecha,
                SUM(md.total_mp) as total_mp
            FROM metros_general mg
            JOIN metros_detalles md ON mg.id = md.registro_id
            WHERE mg.fecha BETWEEN ? AND ?
        """
        params_tabla = [desde, hasta]
        
        if tipo:
            query_tabla += " AND mg.tipo_perforacion = ?"
            params_tabla.append(tipo)
        if compania:
            query_tabla += " AND mg.compania = ?"
            params_tabla.append(compania)
        
        query_tabla += " GROUP BY mg.equipo, mg.fecha ORDER BY mg.equipo, mg.fecha"
        tabla = db.execute_query(query_tabla, params_tabla)
        tabla = [dict(row) for row in tabla] if tabla else []
    except Exception as e:
        print(f"Error en tabla metros: {e}")
        tabla = []
    
    # Datos para gráfico (resumen por equipo)
    try:
        query_grafico = """
            SELECT 
                mg.equipo,
                SUM(md.mp_produccion) as mp_produccion,
                SUM(md.mp_rimado) as mp_rimado,
                SUM(md.total_mp) as total_mp
            FROM metros_general mg
            JOIN metros_detalles md ON mg.id = md.registro_id
            WHERE mg.fecha BETWEEN ? AND ?
        """
        params_grafico = [desde, hasta]
        
        if tipo:
            query_grafico += " AND mg.tipo_perforacion = ?"
            params_grafico.append(tipo)
        if compania:
            query_grafico += " AND mg.compania = ?"
            params_grafico.append(compania)
        
        query_grafico += " GROUP BY mg.equipo ORDER BY total_mp DESC"
        grafico = db.execute_query(query_grafico, params_grafico)
        grafico = [dict(row) for row in grafico] if grafico else []
    except Exception as e:
        print(f"Error en grafico metros: {e}")
        grafico = []
    
    return tabla, grafico


def obtener_resumen_compania(desde, hasta, tipo=None):
    """Obtiene resumen de metros por compañía"""
    db = get_db()
    
    try:
        query = """
            SELECT 
                mg.compania,
                SUM(md.total_mp) as total_metros
            FROM metros_general mg
            JOIN metros_detalles md ON mg.id = md.registro_id
            WHERE mg.fecha BETWEEN ? AND ?
        """
        params = [desde, hasta]
        
        if tipo:
            query += " AND mg.tipo_perforacion = ?"
            params.append(tipo)
        
        query += " AND mg.compania IS NOT NULL AND mg.compania != ''"
        query += " GROUP BY mg.compania ORDER BY total_metros DESC"
        
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados] if resultados else []
        
    except Exception as e:
        print(f"Error en obtener_resumen_compania: {e}")
        return []