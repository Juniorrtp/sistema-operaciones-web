from core.database import get_db
from collections import defaultdict
from datetime import datetime


MESES = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
]

MES_NUMERO = {mes: i+1 for i, mes in enumerate(MESES)}


def obtener_anos_disponibles():
    """Obtiene años disponibles en movimiento_general y metros_general"""
    db = get_db()
    
    try:
        anos_movimiento = db.execute_query("""
            SELECT DISTINCT ano FROM movimiento_general 
            WHERE ano IS NOT NULL ORDER BY ano DESC
        """)
        anos_metros = db.execute_query("""
            SELECT DISTINCT ano FROM metros_general 
            WHERE ano IS NOT NULL ORDER BY ano DESC
        """)
        
        todos_anos = set()
        for row in anos_movimiento:
            if row['ano']:
                todos_anos.add(str(row['ano']))
        for row in anos_metros:
            if row['ano']:
                todos_anos.add(str(row['ano']))
        
        if not todos_anos:
            todos_anos = {str(datetime.now().year)}
        
        return sorted(todos_anos, reverse=True)
    except:
        return [str(datetime.now().year)]


def obtener_datos_avance_semanal(mes, ano):
    """Obtiene todos los datos para el avance semanal"""
    db = get_db()
    
    # ===== 1. CONSUMO DEL MES =====
    
    # Consumo CPM
    consumo_cpm = db.execute_query("""
        SELECT ea.tipo_perforacion, dea.codigo, dea.descripcion, 
            dea.familia, ea.compania, SUM(ABS(dea.cantidad)) as total
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON ea.id = dea.entrega_id
        WHERE ea.movimiento = 'SALIDA' 
        AND ea.mes = ? 
        AND ea.ano = ?
        AND ea.estado = 'CPM'
        GROUP BY ea.tipo_perforacion, dea.codigo, dea.descripcion, 
                dea.familia, ea.compania
        HAVING SUM(ABS(dea.cantidad)) > 0
    """, (mes, ano))
    
    # Consumo VENTA
    consumo_venta = db.execute_query("""
        SELECT ea.tipo_perforacion, dea.codigo, dea.descripcion, 
            dea.familia, ea.compania, SUM(ABS(dea.cantidad)) as total
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON ea.id = dea.entrega_id
        WHERE ea.movimiento = 'SALIDA' 
        AND ea.mes = ? 
        AND ea.ano = ?
        AND ea.estado = 'VENTA'
        GROUP BY ea.tipo_perforacion, dea.codigo, dea.descripcion, 
                dea.familia, ea.compania
        HAVING SUM(ABS(dea.cantidad)) > 0
    """, (mes, ano))
    
    # Consumo AFILADORAS
    consumo_copas = db.execute_query("""
        SELECT ea.tipo_perforacion, dea.codigo, dea.descripcion, 
            dea.familia, ea.compania, SUM(ABS(dea.cantidad)) as total
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON ea.id = dea.entrega_id
        WHERE ea.movimiento = 'SALIDA' 
        AND ea.mes = ? 
        AND ea.ano = ?
        AND ea.estado = 'AFILADORAS'
        GROUP BY ea.tipo_perforacion, dea.codigo, dea.descripcion, 
                dea.familia, ea.compania
        HAVING SUM(ABS(dea.cantidad)) > 0
    """, (mes, ano))
    
    # ===== 2. STOCK ACUMULADO =====
    mes_actual_num = MES_NUMERO.get(mes, 1)
    
    todos_movimientos = db.execute_query("""
        SELECT dea.codigo, dea.descripcion, dea.familia, dea.tipo_perforacion,
               ea.movimiento, ea.estado, dea.cantidad, ea.mes, ea.ano
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON ea.id = dea.entrega_id
        WHERE dea.descripcion IS NOT NULL 
        AND TRIM(dea.descripcion) != ''
        AND (ea.estado = 'CPM' OR ea.estado = 'AFILADORAS' OR ea.estado = 'VENTA')
    """)
    
    stock_cpm = defaultdict(float)
    stock_cpm_info = {}
    stock_copas = defaultdict(float)
    stock_copas_info = {}
    
    for row in todos_movimientos:
        cod = row['codigo']
        desc = row['descripcion']
        familia = row['familia']
        tipo_perf = row['tipo_perforacion']
        movimiento = row['movimiento']
        estado = row['estado']
        cantidad = row['cantidad'] or 0
        mes_reg = row['mes']
        ano_reg = str(row['ano']) if row['ano'] else ""
        
        # Solo considerar meses anteriores o iguales al seleccionado
        if int(ano_reg) > int(ano):
            continue
        if int(ano_reg) == int(ano) and MES_NUMERO.get(mes_reg, 0) > mes_actual_num:
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
    
    # ===== 3. METROS PERFORADOS =====
    metros = db.execute_query("""
        SELECT g.tipo_perforacion, g.compania,
            SUM(d.mp_produccion) as mp_produccion, 
            SUM(d.mp_rimado) as mp_rimado
        FROM metros_detalles d
        JOIN metros_general g ON g.id = d.registro_id
        WHERE g.mes = ? AND g.ano = ?
        GROUP BY g.tipo_perforacion, g.compania
    """, (mes, ano))
    
    # ===== 4. COMPAÑÍAS =====
    companias_set = set()
    
    for row in consumo_cpm:
        if row['compania']:
            companias_set.add(row['compania'])
    for row in consumo_venta:
        if row['compania']:
            companias_set.add(row['compania'])
    for row in consumo_copas:
        if row['compania']:
            companias_set.add(row['compania'])
    
    companias = sorted(companias_set)
    
    # ===== 5. FAMILIAS DE ACEROS =====
    familias_aceros = {}
    try:
        aceros = db.execute_query("""
            SELECT codigo, familia FROM aceros 
            WHERE familia IS NOT NULL AND TRIM(familia) != ''
        """)
        for row in aceros:
            if row['codigo']:
                familias_aceros[row['codigo']] = row['familia']
    except:
        pass
    
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
        tipo = row['tipo_perforacion'] or "SIN TIPO"
        cod = row['codigo']
        desc = row['descripcion']
        familia = row['familia']
        compania = row['compania']
        cantidad = row['total'] or 0
        
        if cantidad > 0:
            key = (tipo, cod, desc, familia)
            consumo[key][compania] += float(cantidad)
            if cod and cod not in consumo_info:
                consumo_info[cod] = {
                    "tipo": tipo,
                    "desc": desc,
                    "familia": familia
                }
    
    return consumo, consumo_info