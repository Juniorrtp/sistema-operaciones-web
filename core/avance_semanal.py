from core.database import get_db
from collections import defaultdict
from datetime import datetime


MESES = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
]

MES_NUMERO = {mes: i+1 for i, mes in enumerate(MESES)}


def obtener_anos_disponibles():
    """Obtiene años disponibles"""
    db = get_db()
    try:
        result = db.client.table("movimiento_general").select("ano").execute()
        anos = [str(row['ano']) for row in result.data if row.get('ano')]
        if not anos:
            result = db.client.table("metros_general").select("ano").execute()
            anos = [str(row['ano']) for row in result.data if row.get('ano')]
        return sorted(set(anos), reverse=True)
    except Exception as e:
        print(f"Error en obtener_anos_disponibles: {e}")
        return [str(datetime.now().year)]


def obtener_datos_avance_semanal(mes, ano):
    """Obtiene todos los datos para el avance semanal"""
    db = get_db()
    
    # ============================================================
    # CONSUMO CPM
    # ============================================================
    try:
        query = """
            SELECT 
                ea.tipo_perforacion,
                dea.codigo,
                dea.descripcion,
                dea.familia,
                ea.compania,
                SUM(ABS(dea.cantidad)) as total
            FROM movimiento_detalles dea
            JOIN movimiento_general ea ON dea.entrega_id = ea.id
            WHERE ea.movimiento = 'SALIDA' 
                AND ea.mes = ? 
                AND ea.ano = ?
                AND ea.estado = 'CPM'
                AND dea.cantidad < 0
            GROUP BY ea.tipo_perforacion, dea.codigo, dea.descripcion, 
                    dea.familia, ea.compania
            HAVING SUM(ABS(dea.cantidad)) > 0
        """
        consumo_cpm = db.execute_query(query, (mes, ano))
    except Exception as e:
        print(f"Error en consumo_cpm: {e}")
        consumo_cpm = []
    
    # ============================================================
    # CONSUMO VENTA
    # ============================================================
    try:
        query = """
            SELECT 
                ea.tipo_perforacion,
                dea.codigo,
                dea.descripcion,
                dea.familia,
                ea.compania,
                SUM(ABS(dea.cantidad)) as total
            FROM movimiento_detalles dea
            JOIN movimiento_general ea ON dea.entrega_id = ea.id
            WHERE ea.movimiento = 'SALIDA' 
                AND ea.mes = ? 
                AND ea.ano = ?
                AND ea.estado = 'VENTA'
                AND dea.cantidad < 0
            GROUP BY ea.tipo_perforacion, dea.codigo, dea.descripcion, 
                    dea.familia, ea.compania
            HAVING SUM(ABS(dea.cantidad)) > 0
        """
        consumo_venta = db.execute_query(query, (mes, ano))
    except Exception as e:
        print(f"Error en consumo_venta: {e}")
        consumo_venta = []
    
    # ============================================================
    # CONSUMO AFILADORAS
    # ============================================================
    try:
        query = """
            SELECT 
                ea.tipo_perforacion,
                dea.codigo,
                dea.descripcion,
                dea.familia,
                ea.compania,
                SUM(ABS(dea.cantidad)) as total
            FROM movimiento_detalles dea
            JOIN movimiento_general ea ON dea.entrega_id = ea.id
            WHERE ea.movimiento = 'SALIDA' 
                AND ea.mes = ? 
                AND ea.ano = ?
                AND ea.estado = 'AFILADORAS'
                AND dea.cantidad < 0
            GROUP BY ea.tipo_perforacion, dea.codigo, dea.descripcion, 
                    dea.familia, ea.compania
            HAVING SUM(ABS(dea.cantidad)) > 0
        """
        consumo_copas = db.execute_query(query, (mes, ano))
    except Exception as e:
        print(f"Error en consumo_copas: {e}")
        consumo_copas = []
    
    # ============================================================
    # STOCK ACUMULADO
    # ============================================================
    mes_actual_num = MES_NUMERO.get(mes, 1)
    
    try:
        query = """
            SELECT dea.codigo, dea.descripcion, dea.familia, dea.tipo_perforacion,
                   ea.movimiento, ea.estado, dea.cantidad, ea.mes, ea.ano
            FROM movimiento_detalles dea
            JOIN movimiento_general ea ON dea.entrega_id = ea.id
            WHERE dea.descripcion IS NOT NULL 
                AND TRIM(dea.descripcion) != ''
                AND (ea.estado = 'CPM' OR ea.estado = 'AFILADORAS' OR ea.estado = 'VENTA')
        """
        todos_movimientos = db.execute_query(query)
    except Exception as e:
        print(f"Error en todos_movimientos: {e}")
        todos_movimientos = []
    
    stock_cpm = defaultdict(float)
    stock_cpm_info = {}
    stock_copas = defaultdict(float)
    stock_copas_info = {}
    
    for row in todos_movimientos:
        cod = row.get('codigo')
        desc = row.get('descripcion')
        familia = row.get('familia')
        tipo_perf = row.get('tipo_perforacion')
        movimiento = row.get('movimiento')
        estado = row.get('estado')
        cantidad = row.get('cantidad') or 0
        mes_reg = row.get('mes')
        ano_reg = str(row.get('ano')) if row.get('ano') else ""
        
        if not cod:
            continue
        
        # Solo considerar meses anteriores o iguales al seleccionado
        try:
            if int(ano_reg) > int(ano):
                continue
            if int(ano_reg) == int(ano) and MES_NUMERO.get(mes_reg, 0) > mes_actual_num:
                continue
        except:
            continue
        
        if estado in ['CPM', 'VENTA']:
            if movimiento == 'INGRESO':
                stock_cpm[cod] += float(cantidad)
            elif movimiento == 'SALIDA':
                stock_cpm[cod] -= float(abs(cantidad))
            
            if cod and cod not in stock_cpm_info:
                stock_cpm_info[cod] = {
                    "tipo": tipo_perf or "SIN TIPO",
                    "desc": desc or "",
                    "familia": familia or ""
                }
        
        elif estado == 'AFILADORAS':
            if movimiento == 'INGRESO':
                stock_copas[cod] += float(cantidad)
            elif movimiento == 'SALIDA':
                stock_copas[cod] -= float(abs(cantidad))
            
            if cod and cod not in stock_copas_info:
                stock_copas_info[cod] = {
                    "tipo": tipo_perf or "SIN TIPO",
                    "desc": desc or "",
                    "familia": familia or ""
                }
    
    # Filtrar stock positivo
    stock_cpm = {k: v for k, v in stock_cpm.items() if v > 0}
    stock_copas = {k: v for k, v in stock_copas.items() if v > 0}
    
    # ============================================================
    # METROS PERFORADOS
    # ============================================================
    try:
        query = """
            SELECT g.tipo_perforacion, g.compania,
                SUM(d.mp_produccion) as mp_produccion, 
                SUM(d.mp_rimado) as mp_rimado
            FROM metros_detalles d
            JOIN metros_general g ON g.id = d.registro_id
            WHERE g.mes = ? AND g.ano = ?
            GROUP BY g.tipo_perforacion, g.compania
        """
        metros = db.execute_query(query, (mes, ano))
    except Exception as e:
        print(f"Error en metros: {e}")
        metros = []
    
    # ============================================================
    # COMPAÑÍAS
    # ============================================================
    companias_set = set()
    
    for row in consumo_cpm:
        if row.get('compania'):
            companias_set.add(row['compania'])
    for row in consumo_venta:
        if row.get('compania'):
            companias_set.add(row['compania'])
    for row in consumo_copas:
        if row.get('compania'):
            companias_set.add(row['compania'])
    
    companias = sorted(companias_set)
    
    # ============================================================
    # FAMILIAS DE ACEROS
    # ============================================================
    try:
        result = db.client.table("aceros").select("codigo, familia").execute()
        familias_aceros = {}
        for row in result.data:
            if row.get('codigo'):
                familias_aceros[row['codigo']] = row.get('familia', '')
    except Exception as e:
        print(f"Error en familias_aceros: {e}")
        familias_aceros = {}
    
    return {
        'consumo_cpm': consumo_cpm,
        'consumo_venta': consumo_venta,
        'consumo_copas': consumo_copas,
        'stock_cpm': stock_cpm,
        'stock_copas': stock_copas,
        'stock_cpm_info': stock_cpm_info,
        'stock_copas_info': stock_copas_info,
        'metros': metros,
        'companias': companias,
        'familias_aceros': familias_aceros
    }


def procesar_consumo(consumo_rows, stock_dict, stock_info, familias_aceros):
    """Procesa consumo para generar estructura de tabla"""
    consumo = defaultdict(lambda: defaultdict(float))
    consumo_info = {}
    
    for row in consumo_rows:
        tipo = row.get('tipo_perforacion') or "SIN TIPO"
        cod = row.get('codigo')
        desc = row.get('descripcion')
        familia = row.get('familia')
        compania = row.get('compania')
        cantidad = row.get('total') or 0
        
        if cantidad > 0 and cod:
            key = (tipo, cod, desc, familia)
            consumo[key][compania] += float(cantidad)
            if cod and cod not in consumo_info:
                consumo_info[cod] = {
                    "tipo": tipo,
                    "desc": desc,
                    "familia": familia
                }
    
    return consumo, consumo_info