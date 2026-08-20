from core.database import get_db
from collections import defaultdict
from datetime import datetime


def obtener_resumen_general(desde, hasta):
    """Obtiene el resumen general del período."""
    db = get_db()

    query_metros = """
        SELECT
            COALESCE(SUM(d.mp_produccion), 0) AS total_produccion,
            COALESCE(SUM(d.mp_rimado), 0) AS total_rimado,
            COALESCE(SUM(d.total_mp), 0) AS total_metros
        FROM metros_detalles d
        JOIN metros_general g ON d.registro_id = g.id
        WHERE g.fecha BETWEEN ? AND ?
    """

    query_consumos = """
        SELECT
            COALESCE(SUM(ABS(dea.cantidad)), 0) AS total_consumo
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON dea.entrega_id = ea.id
        WHERE ea.movimiento = 'SALIDA'
          AND ea.fecha BETWEEN ? AND ?
          AND dea.cantidad < 0
    """

    query_equipos = """
        SELECT COUNT(DISTINCT g.equipo) AS total_equipos
        FROM metros_general g
        JOIN metros_detalles d ON g.id = d.registro_id
        WHERE g.fecha BETWEEN ? AND ?
    """

    query_operadores = """
        SELECT COUNT(DISTINCT g.operador) AS total_operadores
        FROM metros_general g
        JOIN metros_detalles d ON g.id = d.registro_id
        WHERE g.fecha BETWEEN ? AND ?
          AND g.operador IS NOT NULL
          AND g.operador != ''
    """

    try:
        metros = db.execute_query(query_metros, (desde, hasta))
        consumos = db.execute_query(query_consumos, (desde, hasta))
        equipos = db.execute_query(query_equipos, (desde, hasta))
        operadores = db.execute_query(query_operadores, (desde, hasta))

        return {
            "metros": dict(metros[0]) if metros else {
                "total_produccion": 0,
                "total_rimado": 0,
                "total_metros": 0,
            },
            "consumos": dict(consumos[0]) if consumos else {
                "total_consumo": 0,
            },
            "equipos": dict(equipos[0]) if equipos else {
                "total_equipos": 0,
            },
            "operadores": dict(operadores[0]) if operadores else {
                "total_operadores": 0,
            },
            "dias": (
                datetime.strptime(hasta, "%Y-%m-%d")
                - datetime.strptime(desde, "%Y-%m-%d")
            ).days + 1,
        }

    except Exception as e:
        print(f"Error en obtener_resumen_general: {e}")
        return {
            "metros": {"total_metros": 0},
            "consumos": {"total_consumo": 0},
            "equipos": {"total_equipos": 0},
            "operadores": {"total_operadores": 0},
            "dias": 0,
        }


def obtener_metros_por_tipo(desde, hasta):
    """Obtiene metros perforados por tipo de perforación."""
    db = get_db()

    query = """
        SELECT
            UPPER(TRIM(eq.tipo_perforacion)) AS tipo,
            COALESCE(SUM(d.total_mp), 0) AS total_mp
        FROM metros_detalles d
        JOIN metros_general g ON d.registro_id = g.id
        JOIN equipo eq ON g.equipo = eq.equipo
        WHERE g.fecha BETWEEN ? AND ?
        GROUP BY UPPER(TRIM(eq.tipo_perforacion))
        ORDER BY total_mp DESC
    """

    try:
        resultados = db.execute_query(query, (desde, hasta))
        return [dict(row) for row in resultados if row["tipo"]]
    except Exception as e:
        print(f"Error en obtener_metros_por_tipo: {e}")
        return []


def obtener_consumo_por_familia(desde, hasta):
    """Obtiene consumo total por familia."""
    db = get_db()

    query = """
        SELECT
            UPPER(TRIM(dea.familia)) AS familia,
            COALESCE(SUM(ABS(dea.cantidad)), 0) AS total_consumo
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON dea.entrega_id = ea.id
        WHERE ea.movimiento = 'SALIDA'
          AND ea.fecha BETWEEN ? AND ?
          AND dea.cantidad < 0
          AND dea.familia IS NOT NULL
          AND TRIM(dea.familia) != ''
        GROUP BY UPPER(TRIM(dea.familia))
        ORDER BY total_consumo DESC
    """

    try:
        resultados = db.execute_query(query, (desde, hasta))
        return [dict(row) for row in resultados if row["familia"]]
    except Exception as e:
        print(f"Error en obtener_consumo_por_familia: {e}")
        return []


def obtener_consumo_por_tipo_familia(desde, hasta):
    """
    Obtiene consumo de aceros clasificado por:
        TIPO DE PERFORACIÓN -> FAMILIA

    También sirve para calcular participación de cada familia
    dentro de su respectivo tipo en el PDF.
    """
    db = get_db()

    query = """
        SELECT
            UPPER(TRIM(eq.tipo_perforacion)) AS tipo,
            UPPER(TRIM(dea.familia)) AS familia,
            COALESCE(SUM(ABS(dea.cantidad)), 0) AS total_consumo
        FROM movimiento_detalles dea
        JOIN movimiento_general ea
            ON dea.entrega_id = ea.id
        JOIN equipo eq
            ON ea.equipo = eq.equipo
        WHERE ea.movimiento = 'SALIDA'
          AND ea.fecha BETWEEN ? AND ?
          AND dea.cantidad < 0
          AND dea.familia IS NOT NULL
          AND TRIM(dea.familia) != ''
          AND eq.tipo_perforacion IS NOT NULL
          AND TRIM(eq.tipo_perforacion) != ''
        GROUP BY
            UPPER(TRIM(eq.tipo_perforacion)),
            UPPER(TRIM(dea.familia))
        ORDER BY tipo, total_consumo DESC
    """

    try:
        resultados = db.execute_query(query, (desde, hasta))

        agrupado = defaultdict(list)

        for row in resultados:
            tipo = row["tipo"] or "SIN TIPO"
            familia = row["familia"] or "SIN FAMILIA"

            agrupado[tipo].append({
                "familia": familia,
                "total_consumo": row["total_consumo"] or 0,
            })

        return dict(agrupado)

    except Exception as e:
        print(f"Error en obtener_consumo_por_tipo_familia: {e}")
        return {}


def obtener_top_equipos_por_tipo(desde, hasta, top=3):
    """Obtiene los equipos con mayor producción por tipo de perforación."""
    db = get_db()

    query = """
        SELECT
            UPPER(TRIM(eq.tipo_perforacion)) AS tipo,
            g.equipo,
            COALESCE(SUM(d.total_mp), 0) AS total_mp
        FROM metros_detalles d
        JOIN metros_general g ON d.registro_id = g.id
        JOIN equipo eq ON g.equipo = eq.equipo
        WHERE g.fecha BETWEEN ? AND ?
          AND g.equipo IS NOT NULL
          AND g.equipo != ''
        GROUP BY UPPER(TRIM(eq.tipo_perforacion)), g.equipo
        HAVING COALESCE(SUM(d.total_mp), 0) > 0
        ORDER BY tipo, total_mp DESC
    """

    try:
        resultados = db.execute_query(query, (desde, hasta))

        tipo_equipos = defaultdict(list)

        for row in resultados:
            if row["tipo"]:
                tipo_equipos[row["tipo"]].append({
                    "equipo": row["equipo"],
                    "total_mp": row["total_mp"] or 0,
                })

        return {
            tipo: sorted(equipos, key=lambda x: x["total_mp"], reverse=True)[:top]
            for tipo, equipos in tipo_equipos.items()
        }

    except Exception as e:
        print(f"Error en obtener_top_equipos_por_tipo: {e}")
        return {}


def obtener_rendimiento_por_equipo(desde, hasta):
    """
    Obtiene rendimiento por equipo (metros / consumo) para cada familia
    INCLUYENDO tipo_perforacion
    """
    db = get_db()
    
    # 🔥 CONSUMO por equipo, familia Y tipo_perforacion
    query_consumo = """
        SELECT 
            ea.equipo,
            UPPER(TRIM(eq.tipo_perforacion)) as tipo_perforacion,
            UPPER(TRIM(dea.familia)) as familia,
            COALESCE(SUM(ABS(dea.cantidad)), 0) as consumo
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON dea.entrega_id = ea.id
        JOIN equipo eq ON ea.equipo = eq.equipo
        WHERE ea.movimiento = 'SALIDA'
            AND ea.fecha BETWEEN ? AND ?
            AND dea.cantidad < 0
            AND UPPER(TRIM(dea.familia)) IN ('BARRAS', 'BROCAS', 'ACOPLES', 'SHANK', 'RIMADORAS')
        GROUP BY ea.equipo, UPPER(TRIM(eq.tipo_perforacion)), UPPER(TRIM(dea.familia))
        HAVING COALESCE(SUM(ABS(dea.cantidad)), 0) > 0
    """
    
    # 🔥 METROS por equipo Y tipo_perforacion
    query_metros = """
        SELECT 
            g.equipo,
            UPPER(TRIM(eq.tipo_perforacion)) as tipo_perforacion,
            COALESCE(SUM(d.total_mp), 0) as total_mp
        FROM metros_detalles d
        JOIN metros_general g ON d.registro_id = g.id
        JOIN equipo eq ON g.equipo = eq.equipo
        WHERE g.fecha BETWEEN ? AND ?
            AND g.equipo IS NOT NULL 
            AND g.equipo != ''
        GROUP BY g.equipo, UPPER(TRIM(eq.tipo_perforacion))
        HAVING COALESCE(SUM(d.total_mp), 0) > 0
    """
    
    try:
        consumos = db.execute_query(query_consumo, (desde, hasta))
        metros = db.execute_query(query_metros, (desde, hasta))
        
        # Crear diccionario de metros por equipo (incluyendo tipo)
        metros_por_equipo = {}
        for row in metros:
            equipo = row['equipo'] or "SIN EQUIPO"
            tipo = row['tipo_perforacion'] or "GENERAL"
            key = (equipo, tipo)
            metros_por_equipo[key] = row['total_mp'] or 0
        
        # Procesar consumos y calcular rendimiento
        rendimiento_por_equipo = {}
        
        for row in consumos:
            equipo = row['equipo'] or "SIN EQUIPO"
            tipo = row['tipo_perforacion'] or "GENERAL"
            familia = row['familia'] or "OTROS"
            consumo = row['consumo'] or 0
            
            key = (equipo, tipo)
            metros_equipo = metros_por_equipo.get(key, 0)
            rendimiento = metros_equipo / consumo if consumo > 0 else 0
            
            # Inicializar equipo si no existe
            if equipo not in rendimiento_por_equipo:
                rendimiento_por_equipo[equipo] = {
                    "__tipo__": tipo,
                    "TOTAL": {
                        "metros": 0,
                        "consumo": 0,
                        "rendimiento": 0,
                        "tipo_perforacion": tipo
                    }
                }
            
            # Agregar familia
            rendimiento_por_equipo[equipo][familia] = {
                'metros': metros_equipo,
                'consumo': consumo,
                'rendimiento': round(rendimiento, 2),
                'tipo_perforacion': tipo
            }
        
        # Calcular rendimiento total por equipo
        for equipo, familias in rendimiento_por_equipo.items():
            total_consumo = 0
            total_metros = 0
            
            for key, value in familias.items():
                if key in ["__tipo__", "TOTAL"]:
                    continue
                if isinstance(value, dict):
                    total_consumo += value.get('consumo', 0)
                    total_metros += value.get('metros', 0)
            
            rendimiento_total = total_metros / total_consumo if total_consumo > 0 else 0
            
            if "TOTAL" in familias and isinstance(familias["TOTAL"], dict):
                familias["TOTAL"]["metros"] = total_metros
                familias["TOTAL"]["consumo"] = total_consumo
                familias["TOTAL"]["rendimiento"] = round(rendimiento_total, 2)
        
        return rendimiento_por_equipo
        
    except Exception as e:
        print(f"Error en obtener_rendimiento_por_equipo: {e}")
        import traceback
        traceback.print_exc()
        return {}

def obtener_rendimiento_operadores_brocas(desde, hasta):
    """Obtiene rendimiento de brocas por operador, tipo y guardia."""
    db = get_db()

    query = """
        SELECT
            UPPER(TRIM(eq.tipo_perforacion)) AS tipo,
            ea.operador,
            COALESCE(ea.guardia, 'G') AS guardia,
            COALESCE(SUM(ABS(dea.cantidad)), 0) AS total_brocas,
            COALESCE((
                SELECT COALESCE(SUM(d.mp_produccion), 0)
                FROM metros_general g
                JOIN metros_detalles d
                    ON g.id = d.registro_id
                WHERE g.operador = ea.operador
                  AND g.guardia = ea.guardia
                  AND g.fecha BETWEEN ? AND ?
            ), 0) AS metros_perforados
        FROM movimiento_detalles dea
        JOIN movimiento_general ea
            ON dea.entrega_id = ea.id
        JOIN equipo eq
            ON ea.equipo = eq.equipo
        WHERE ea.movimiento = 'SALIDA'
          AND ea.fecha BETWEEN ? AND ?
          AND dea.cantidad < 0
          AND UPPER(TRIM(dea.familia)) = 'BROCAS'
          AND ea.operador IS NOT NULL
          AND ea.operador != ''
        GROUP BY
            UPPER(TRIM(eq.tipo_perforacion)),
            ea.operador,
            ea.guardia
        HAVING COALESCE(SUM(ABS(dea.cantidad)), 0) > 0
        ORDER BY tipo, guardia
    """

    try:
        resultados = db.execute_query(
            query,
            (desde, hasta, desde, hasta)
        )

        operadores_por_tipo = defaultdict(lambda: defaultdict(list))

        for row in resultados:
            tipo = row["tipo"] or "SIN TIPO"
            guardia = row["guardia"] or "G"
            operador = row["operador"] or "SIN OPERADOR"
            brocas = row["total_brocas"] or 0
            metros = row["metros_perforados"] or 0

            rendimiento = metros / brocas if brocas > 0 else 0

            operadores_por_tipo[tipo][guardia].append({
                "operador": operador,
                "brocas": brocas,
                "metros": metros,
                "rendimiento": round(rendimiento, 2),
            })

        return {
            tipo: dict(guardias)
            for tipo, guardias in operadores_por_tipo.items()
        }

    except Exception as e:
        print(f"Error en obtener_rendimiento_operadores_brocas: {e}")
        return {}



def obtener_stock_critico(umbral=5):
    """Obtiene productos con stock crítico."""
    db = get_db()

    query = """
        SELECT
            codigo,
            MAX(descripcion) AS descripcion,
            COALESCE(SUM(cantidad), 0) AS stock
        FROM movimiento_detalles
        WHERE cantidad > 0
        GROUP BY codigo
        HAVING COALESCE(SUM(cantidad), 0) <= ?
        ORDER BY stock ASC
    """

    try:
        resultados = db.execute_query(query, (umbral,))
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_stock_critico: {e}")
        return []


def obtener_consumo_por_familia(desde, hasta):
    """Obtiene consumo de aceros por familia Y tipo de perforación"""
    db = get_db()
    
    query = """
        SELECT 
            UPPER(TRIM(eq.tipo_perforacion)) as tipo_perforacion,
            UPPER(TRIM(dea.familia)) as familia,
            COALESCE(SUM(ABS(dea.cantidad)), 0) as total_consumo
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON dea.entrega_id = ea.id
        JOIN equipo eq ON ea.equipo = eq.equipo
        WHERE ea.movimiento = 'SALIDA'
            AND ea.fecha BETWEEN ? AND ?
            AND dea.cantidad < 0
            AND dea.familia IS NOT NULL 
            AND TRIM(dea.familia) != ''
        GROUP BY UPPER(TRIM(eq.tipo_perforacion)), UPPER(TRIM(dea.familia))
        ORDER BY tipo_perforacion, total_consumo DESC
    """
    
    try:
        resultados = db.execute_query(query, (desde, hasta))
        return [dict(row) for row in resultados if row['familia']]
    except Exception as e:
        print(f"Error en obtener_consumo_por_familia: {e}")
        return []