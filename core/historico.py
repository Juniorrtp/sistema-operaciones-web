from core.database import get_db
from collections import defaultdict
from datetime import datetime

# Constantes
TIPOS_ACERO = ["SHANK", "COUPLING", "BARRA", "RIMADORAS", "BROCAS"]
FAMILIA_MAP = {
    "SHANK": "SHANK",
    "COUPLING": "ACOPLES",
    "BARRA": "BARRAS",
    "RIMADORAS": "RIMADORAS",
    "BROCAS": "BROCAS"
}


def obtener_companias():
    """Obtiene lista de compañías para filtros"""
    db = get_db()
    query = """
        SELECT DISTINCT compania FROM equipo 
        WHERE compania IS NOT NULL AND compania != ''
        ORDER BY compania
    """
    try:
        resultados = db.execute_query(query)
        return [row['compania'] for row in resultados]
    except Exception as e:
        print(f"Error en obtener_companias: {e}")
        return []


def obtener_equipos_por_compania(compania=None):
    """Obtiene equipos con su tipo perforación"""
    db = get_db()
    
    if compania:
        query = """
            SELECT equipo, tipo_perforacion FROM equipo 
            WHERE compania = ? 
            ORDER BY tipo_perforacion, equipo
        """
        try:
            resultados = db.execute_query(query, (compania,))
            return [dict(row) for row in resultados]
        except:
            return []
    else:
        query = """
            SELECT equipo, tipo_perforacion FROM equipo 
            ORDER BY tipo_perforacion, equipo
        """
        try:
            resultados = db.execute_query(query)
            return [dict(row) for row in resultados]
        except:
            return []


def obtener_objetivos():
    """Obtiene objetivos de la tabla objetivos"""
    db = get_db()
    try:
        resultados = db.execute_query('SELECT "Tipo Perforacion", "Acero", objetivo FROM objetivos')
        objetivos_dict = {}
        for row in resultados:
            tp = row[0].strip().upper() if row[0] else None
            ac = row[1].strip().upper() if row[1] else None
            if tp and ac:
                objetivos_dict[(tp, ac)] = row[2] or 0
        return objetivos_dict
    except Exception as e:
        print(f"Error en obtener_objetivos: {e}")
        return {}


def obtener_ultimo_mes_ano():
    """Obtiene el último año y mes registrado en metros_general"""
    db = get_db()
    try:
        resultado = db.execute_query("""
            SELECT ano, mes FROM metros_general 
            WHERE ano IS NOT NULL AND mes IS NOT NULL
            ORDER BY ano DESC, 
                CASE UPPER(mes)
                    WHEN 'ENERO' THEN 1 WHEN 'FEBRERO' THEN 2 WHEN 'MARZO' THEN 3
                    WHEN 'ABRIL' THEN 4 WHEN 'MAYO' THEN 5 WHEN 'JUNIO' THEN 6
                    WHEN 'JULIO' THEN 7 WHEN 'AGOSTO' THEN 8 WHEN 'SEPTIEMBRE' THEN 9
                    WHEN 'OCTUBRE' THEN 10 WHEN 'NOVIEMBRE' THEN 11 WHEN 'DICIEMBRE' THEN 12
                    ELSE 13
                END DESC
            LIMIT 1
        """)
        
        if resultado:
            return resultado[0]['ano'], resultado[0]['mes']
        return None, None
    except Exception as e:
        print(f"Error en obtener_ultimo_mes_ano: {e}")
        return None, None


def obtener_brazos_equipo(equipo):
    """Obtiene los brazos que tiene un equipo"""
    db = get_db()
    brazos = set()
    
    try:
        # Brazos desde movimiento_detalles
        mov_brazos = db.execute_query("""
            SELECT DISTINCT dea.brazo 
            FROM movimiento_detalles dea
            JOIN movimiento_general ea ON dea.entrega_id = ea.id
            WHERE ea.equipo = ? AND dea.brazo IS NOT NULL
        """, (equipo,))
        for row in mov_brazos:
            if row['brazo'] and row['brazo'].strip():
                brazos.add(row['brazo'].strip())
        
        # Brazos desde metros_detalles
        met_brazos = db.execute_query("""
            SELECT DISTINCT rd.brazo 
            FROM metros_detalles rd
            JOIN metros_general rg ON rd.registro_id = rg.id
            WHERE rg.equipo = ? AND rd.brazo IS NOT NULL
        """, (equipo,))
        for row in met_brazos:
            if row['brazo'] and row['brazo'].strip():
                brazos.add(row['brazo'].strip())
        
        # Si no tiene brazos definidos, agregar uno vacío (equipo de 1 brazo)
        if not brazos:
            brazos.add("")
        
        return list(brazos)
    except Exception as e:
        print(f"Error en obtener_brazos_equipo: {e}")
        return [""]




def calcular_estado_actual(equipo, brazo, familia, objetivo, ultimo_ano, ultimo_mes):
    """Calcula estado actual de un equipo/brazo/familia"""
    db = get_db()
    
    # Condición de brazo
    if brazo == "":
        cond_brazo = "AND (rd.brazo IS NULL OR rd.brazo = '')"
        cond_brazo_consumo = "AND (dea.brazo IS NULL OR dea.brazo = '')"
    elif brazo:
        cond_brazo = "AND rd.brazo = ?"
        cond_brazo_consumo = "AND dea.brazo = ?"
    else:
        cond_brazo = ""
        cond_brazo_consumo = ""
    
    # Obtener última entrega
    if brazo == "":
        ultima_entrega = db.execute_query(f"""
            SELECT MAX(ea.fecha) as fecha
            FROM movimiento_general ea
            JOIN movimiento_detalles dea ON ea.id = dea.entrega_id
            WHERE ea.equipo = ? AND ea.movimiento = 'SALIDA' 
            AND dea.familia = ?
            {cond_brazo_consumo}
        """, (equipo, familia))
    elif brazo:
        ultima_entrega = db.execute_query("""
            SELECT MAX(ea.fecha) as fecha
            FROM movimiento_general ea
            JOIN movimiento_detalles dea ON ea.id = dea.entrega_id
            WHERE ea.equipo = ? AND ea.movimiento = 'SALIDA' 
            AND dea.familia = ? AND dea.brazo = ?
        """, (equipo, familia, brazo))
    else:
        ultima_entrega = db.execute_query("""
            SELECT MAX(ea.fecha) as fecha
            FROM movimiento_general ea
            JOIN movimiento_detalles dea ON ea.id = dea.entrega_id
            WHERE ea.equipo = ? AND ea.movimiento = 'SALIDA' 
            AND dea.familia = ?
        """, (equipo, familia))
    
    # 🔥 Extraer la fecha correctamente
    fecha_ultima = None
    if ultima_entrega and len(ultima_entrega) > 0:
        row = ultima_entrega[0]
        if row and row['fecha']:
            fecha_ultima = row['fecha']
    
    # Si no hay entrega, devolver sin metros
    if not fecha_ultima:
        return {
            'metros': 0,
            'objetivo': objetivo,
            'porcentaje': 0,
            'estado': 'SIN DATOS',
            'ultima_entrega': None
        }
    
    # Obtener metros desde última entrega
    if brazo == "":
        metros = db.execute_query(f"""
            SELECT COALESCE(SUM(rd.total_mp), 0) as total
            FROM metros_general rg
            JOIN metros_detalles rd ON rg.id = rd.registro_id
            WHERE rg.equipo = ? AND rg.fecha >= ?
            {cond_brazo}
        """, (equipo, fecha_ultima))
    elif brazo:
        metros = db.execute_query(f"""
            SELECT COALESCE(SUM(rd.total_mp), 0) as total
            FROM metros_general rg
            JOIN metros_detalles rd ON rg.id = rd.registro_id
            WHERE rg.equipo = ? AND rg.fecha >= ?
            {cond_brazo}
        """, (equipo, fecha_ultima, brazo))
    else:
        metros = db.execute_query("""
            SELECT COALESCE(SUM(rd.total_mp), 0) as total
            FROM metros_general rg
            JOIN metros_detalles rd ON rg.id = rd.registro_id
            WHERE rg.equipo = ? AND rg.fecha >= ?
        """, (equipo, fecha_ultima))
    
    metros_valor = metros[0]['total'] if metros else 0
    porcentaje = (metros_valor / objetivo * 100) if objetivo > 0 else 0
    
    if objetivo > 0:
        if metros_valor >= objetivo:
            estado = "OBJETIVO CUMPLIDO"
        elif porcentaje >= 80:
            estado = "PRÓXIMO A CAMBIAR"
        elif porcentaje >= 50:
            estado = "EN PROGRESO"
        else:
            estado = "EN INICIO"
    else:
        estado = "SIN OBJETIVO"
    
    return {
        'metros': metros_valor,
        'objetivo': objetivo,
        'porcentaje': porcentaje,
        'estado': estado,
        'ultima_entrega': fecha_ultima
    }


def obtener_historico_equipo(equipo, ano=None):
    """Obtiene histórico de consumo por equipo"""
    db = get_db()
    familias = ['SHANK', 'ACOPLES', 'BARRAS', 'RIMADORAS']
    historico = {}
    
    for familia in familias:
        if ano:
            entregas = db.execute_query("""
                SELECT ea.fecha, dea.cantidad, ea.id
                FROM movimiento_general ea
                JOIN movimiento_detalles dea ON ea.id = dea.entrega_id
                WHERE ea.movimiento = 'SALIDA' AND ea.equipo = ?
                  AND dea.familia = ? AND ea.ano = ?
                ORDER BY ea.fecha
            """, (equipo, familia, ano))
        else:
            entregas = db.execute_query("""
                SELECT ea.fecha, dea.cantidad, ea.id
                FROM movimiento_general ea
                JOIN movimiento_detalles dea ON ea.id = dea.entrega_id
                WHERE ea.movimiento = 'SALIDA' AND ea.equipo = ? AND dea.familia = ?
                ORDER BY ea.fecha
            """, (equipo, familia))
        
        if not entregas:
            continue
        
        historico[familia] = []
        for i, entrega in enumerate(entregas):
            fecha_inicio = entrega['fecha']
            
            if i < len(entregas) - 1:
                fecha_fin = entregas[i + 1]['fecha']
                estado = "CERRADO"
            else:
                ultima_fecha = db.execute_query("""
                    SELECT MAX(fecha) FROM metros_general WHERE equipo = ?
                """, (equipo,))
                fecha_fin = ultima_fecha[0][0] if ultima_fecha and ultima_fecha[0][0] else fecha_inicio
                estado = "ABIERTO"
            
            if familia == "RIMADORAS":
                metros = db.execute_query("""
                    SELECT COALESCE(SUM(rd.mp_rimado), 0)
                    FROM metros_general rg
                    JOIN metros_detalles rd ON rg.id = rd.registro_id
                    WHERE rg.equipo = ? AND rg.fecha BETWEEN ? AND ?
                """, (equipo, fecha_inicio, fecha_fin))
            else:
                metros = db.execute_query("""
                    SELECT COALESCE(SUM(rd.total_mp), 0)
                    FROM metros_general rg
                    JOIN metros_detalles rd ON rg.id = rd.registro_id
                    WHERE rg.equipo = ? AND rg.fecha BETWEEN ? AND ?
                """, (equipo, fecha_inicio, fecha_fin))
            
            metros_valor = metros[0][0] if metros else 0
            
            historico[familia].append({
                'fecha_cambio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'metros_perforados': metros_valor,
                'estado': estado,
                'ano': entrega['fecha'][:4] if entrega['fecha'] else "N/A"
            })
    
    return historico

def calcular_rendimiento_mes(equipo, brazo, familia, tipo_acero, objetivo, ultimo_ano, ultimo_mes):
    """Calcula rendimiento del último mes por BRAZO"""
    db = get_db()
    
    if not ultimo_ano or not ultimo_mes:
        return 0, 0, 0, 0
    
    # Condición de brazo
    if brazo == "":
        cond_brazo = "AND (rd.brazo IS NULL OR rd.brazo = '')"
        cond_brazo_consumo = "AND (dea.brazo IS NULL OR dea.brazo = '')"
    elif brazo:
        cond_brazo = "AND rd.brazo = ?"
        cond_brazo_consumo = "AND dea.brazo = ?"
    else:
        cond_brazo = ""
        cond_brazo_consumo = ""
    
    # Obtener metros del mes
    if tipo_acero == "RIMADORAS":
        if brazo and brazo != "":
            metros = db.execute_query(f"""
                SELECT COALESCE(SUM(rd.mp_rimado), 0) as total
                FROM metros_general rg
                JOIN metros_detalles rd ON rg.id = rd.registro_id
                WHERE rg.equipo = ? AND rg.ano = ? AND rg.mes = ?
                {cond_brazo}
            """, (equipo, ultimo_ano, ultimo_mes, brazo))
        else:
            metros = db.execute_query(f"""
                SELECT COALESCE(SUM(rd.mp_rimado), 0) as total
                FROM metros_general rg
                JOIN metros_detalles rd ON rg.id = rd.registro_id
                WHERE rg.equipo = ? AND rg.ano = ? AND rg.mes = ?
                {cond_brazo}
            """, (equipo, ultimo_ano, ultimo_mes))
    else:
        if brazo and brazo != "":
            metros = db.execute_query(f"""
                SELECT COALESCE(SUM(rd.total_mp), 0) as total
                FROM metros_general rg
                JOIN metros_detalles rd ON rg.id = rd.registro_id
                WHERE rg.equipo = ? AND rg.ano = ? AND rg.mes = ?
                {cond_brazo}
            """, (equipo, ultimo_ano, ultimo_mes, brazo))
        else:
            metros = db.execute_query(f"""
                SELECT COALESCE(SUM(rd.total_mp), 0) as total
                FROM metros_general rg
                JOIN metros_detalles rd ON rg.id = rd.registro_id
                WHERE rg.equipo = ? AND rg.ano = ? AND rg.mes = ?
                {cond_brazo}
            """, (equipo, ultimo_ano, ultimo_mes))
    
    metros_valor = metros[0]['total'] if metros else 0
    
    # Obtener consumo del mes
    if brazo and brazo != "":
        consumo = db.execute_query(f"""
            SELECT COALESCE(SUM(ABS(dea.cantidad)), 0) as total
            FROM movimiento_general ea
            JOIN movimiento_detalles dea ON ea.id = dea.entrega_id
            WHERE ea.equipo = ? AND ea.movimiento = 'SALIDA'
            AND dea.familia = ? AND ea.ano = ? AND ea.mes = ?
            {cond_brazo_consumo}
        """, (equipo, familia, ultimo_ano, ultimo_mes, brazo))
    else:
        consumo = db.execute_query(f"""
            SELECT COALESCE(SUM(ABS(dea.cantidad)), 0) as total
            FROM movimiento_general ea
            JOIN movimiento_detalles dea ON ea.id = dea.entrega_id
            WHERE ea.equipo = ? AND ea.movimiento = 'SALIDA'
            AND dea.familia = ? AND ea.ano = ? AND ea.mes = ?
            {cond_brazo_consumo}
        """, (equipo, familia, ultimo_ano, ultimo_mes))
    
    consumo_valor = consumo[0]['total'] if consumo else 0
    
    rendimiento = metros_valor / consumo_valor if consumo_valor > 0 else 0
    eficiencia = (rendimiento / objetivo * 100) if objetivo > 0 and rendimiento > 0 else 0
    
    return metros_valor, consumo_valor, rendimiento, eficiencia