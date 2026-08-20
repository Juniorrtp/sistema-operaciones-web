from core.database import get_db
from collections import defaultdict


def obtener_rendimiento_operadores(ano, mes, compania):
    """Obtiene rendimiento de BROCAS por operador"""
    db = get_db()
    
    if compania is None:
        return {}
    
    query = """
        SELECT 
            COALESCE(UPPER(TRIM(ea.guardia)), 'G') as guardia,
            UPPER(TRIM(ea.operador)) as operador,
            eq.tipo_perforacion as tipo,
            SUM(CASE WHEN dea.cantidad < 0 THEN -dea.cantidad ELSE 0 END) as entregado,
            COALESCE((
                SELECT SUM(d.mp_produccion)
                FROM metros_general g
                JOIN metros_detalles d ON g.id = d.registro_id
                WHERE g.ano = ea.ano 
                    AND g.mes = ea.mes 
                    AND g.compania = ea.compania
                    AND UPPER(TRIM(g.guardia)) = COALESCE(UPPER(TRIM(ea.guardia)), 'G')
                    AND UPPER(TRIM(g.operador)) = UPPER(TRIM(ea.operador))
                    AND g.equipo = ea.equipo
            ), 0) as metros
        FROM movimiento_general ea
        JOIN movimiento_detalles dea ON ea.id = dea.entrega_id
        JOIN equipo eq ON ea.equipo = eq.equipo
        WHERE UPPER(TRIM(dea.familia)) LIKE 'BROCAS%%'
            AND ea.ano = ? 
            AND ea.mes = ? 
            AND ea.compania = ?
            AND dea.cantidad < 0
        GROUP BY COALESCE(UPPER(TRIM(ea.guardia)), 'G'),
                 UPPER(TRIM(ea.operador)),
                 eq.tipo_perforacion
        HAVING entregado > 0
    """
    
    try:
        resultados = db.execute_query(query, (ano, mes, compania))
    except Exception as e:
        print(f"Error en obtener_rendimiento_operadores: {e}")
        return {}
    
    # Obtener objetivos
    objetivos_raw = db.execute_query('SELECT "Tipo Perforacion", "Acero", objetivo FROM objetivos')
    objetivos_dict = {}
    for row in objetivos_raw:
        tp = row[0].strip().upper() if row[0] else None
        ac = row[1].strip().upper() if row[1] else None
        if tp and ac and "BROCAS" in ac:
            objetivos_dict[tp] = row[2] or 0
    
    # Procesar datos
    datos_por_tipo = defaultdict(lambda: defaultdict(list))
    
    for row in resultados:
        guardia = row['guardia'] or 'G'
        operador = row['operador']
        tipo_original = row['tipo']
        entregado = row['entregado']
        metros = row['metros']
        
        if not operador or entregado == 0:
            continue
        
        # Normalizar tipo
        tipo_normalizado = normalizar_tipo(tipo_original)
        
        if not tipo_normalizado:
            continue
        
        objetivo = objetivos_dict.get(tipo_normalizado, 0)
        rendimiento = round(metros / entregado, 1) if entregado > 0 and metros > 0 else 0
        eficiencia = round((rendimiento / objetivo) * 100, 1) if objetivo > 0 and rendimiento > 0 else 0
        
        datos_por_tipo[tipo_normalizado][guardia].append({
            'operador': operador,
            'entregado': entregado,
            'metros': metros,
            'rendimiento': rendimiento,
            'objetivo': objetivo,
            'eficiencia': eficiencia,
            'tipo_original': tipo_original
        })
    
    return dict(datos_por_tipo)


def normalizar_tipo(tipo):
    """Normaliza y unifica tipos de perforación similares"""
    if not tipo:
        return None
    
    tipo_upper = tipo.upper().strip()
    
    if "TALADROS LARGOS" in tipo_upper:
        return "TALADROS LARGOS"
    
    if "FRONTONERO" in tipo_upper:
        return "FRONTONERO"
    
    if "JUMBO" in tipo_upper:
        return "JUMBO"
    
    if "SCOOP" in tipo_upper:
        return "SCOOP"
    
    if "SIMBA" in tipo_upper:
        return "SIMBA"
    
    # Limpiar sufijos
    sufijos = [' 6FT', ' 8FT', ' 10FT', ' 15M', ' 20M', ' 16TT', ' 12FT', ' 14FT']
    base = tipo_upper
    for sufijo in sufijos:
        base = base.split(sufijo)[0]
    
    return base.strip()


def obtener_operadores_resumen(ano, mes, compania):
    """Obtiene resumen de rendimiento por operador (sin agrupar por tipo)"""
    datos = obtener_rendimiento_operadores(ano, mes, compania)
    
    if not datos:
        return []
    
    resumen = []
    for tipo, guardias in datos.items():
        for guardia, operadores in guardias.items():
            for op in operadores:
                resumen.append({
                    'tipo': tipo,
                    'guardia': guardia,
                    'operador': op['operador'],
                    'entregado': op['entregado'],
                    'metros': op['metros'],
                    'rendimiento': op['rendimiento'],
                    'objetivo': op['objetivo'],
                    'eficiencia': op['eficiencia']
                })
    
    return sorted(resumen, key=lambda x: x['eficiencia'], reverse=True)