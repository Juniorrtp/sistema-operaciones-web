"""
Funciones de cálculo de rendimiento
Equivalente a los métodos de TabGeneralRendimiento y TabOperadoresRendimiento en PyQt6
"""

from typing import Dict, List, Tuple, Optional
from collections import defaultdict


# ============================================================
# UTILIDADES (igual que en PyQt6)
# ============================================================

def normalizar_tipo_perforacion(tipo: str) -> Optional[str]:
    """Normaliza y unifica tipos de perforación (igual que en PyQt6)"""
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
    
    if "PERFORACION" in tipo_upper:
        base = tipo_upper.replace("PERFORACION", "PERFORACIÓN")
    else:
        base = tipo_upper
    
    sufijos = [' 6FT', ' 8FT', ' 10FT', ' 15M', ' 20M', ' 16TT', ' 12FT', ' 14FT']
    for sufijo in sufijos:
        base = base.split(sufijo)[0]
    
    return base.strip()


# ============================================================
# RENDIMIENTO GENERAL (TabGeneralRendimiento)
# ============================================================

def calcular_rendimiento_general(
    movimientos: List[Dict],
    metros: List[Dict],
    metros_detalles: List[Dict],
    objetivos: List[Dict],
    detalles_movimientos: List[Dict],
    equipos_dict: Dict[str, str],
    ano: int,
    mes: str,
    compania: Optional[str] = None
) -> Dict[str, List[Tuple]]:
    """
    Calcula el rendimiento general de aceros
    Equivalente a _obtener_rendimiento_aceros en PyQt6
    """

    # ============================================================
    # 1. FILTRAR MOVIMIENTOS (igual que en PyQt6)
    # ============================================================
    movimientos_filtrados = [
        m for m in movimientos 
        if m.get('ano') == ano and (m.get('mes') or '').upper() == mes.upper()
    ]
    
    if compania:
        compania_upper = compania.upper()
        movimientos_filtrados = [
            m for m in movimientos_filtrados 
            if (m.get('compania') or '').upper() == compania_upper
        ]
    
    # ============================================================
    # 2. FILTRAR METROS (igual que en PyQt6)
    # ============================================================
    metros_filtrados = [
        m for m in metros 
        if m.get('ano') == ano and (m.get('mes') or '').upper() == mes.upper()
    ]
    
    if compania:
        compania_upper = compania.upper()
        metros_filtrados = [
            m for m in metros_filtrados 
            if (m.get('compania') or '').upper() == compania_upper
        ]
    
    # ============================================================
    # 3. CREAR DICCIONARIO DE OBJETIVOS (igual que en PyQt6)
    # ============================================================
    objetivos_dict = {}
    for obj in objetivos:
        tp = (obj.get('Tipo Perforacion') or '').strip().upper() if obj.get('Tipo Perforacion') else None
        ac = (obj.get('Acero') or '').strip().upper() if obj.get('Acero') else None
        if tp and ac:
            objetivos_dict[(tp, ac)] = obj.get('Objetivo', 0)
    
    # ============================================================
    # 4. AGRUPAR ENTREGAS (igual que en PyQt6)
    #    JOIN movimiento_general + movimiento_detalles + equipo
    # ============================================================
    
    # Crear diccionario de detalles por entrega_id
    detalles_por_entrega = defaultdict(list)
    for detalle in detalles_movimientos:
        entrega_id = detalle.get('entrega_id')
        if entrega_id:
            detalles_por_entrega[entrega_id].append(detalle)
    
    # Agrupar entregas: (tipo_perforacion, familia) -> total_entregado
    entregas_dict = defaultdict(float)
    
    for movimiento in movimientos_filtrados:
        # Solo SALIDAS (como en PyQt6: cantidad * -1)
        if (movimiento.get('movimiento') or '').upper() != 'SALIDA':
            continue
        
        movimiento_id = movimiento.get('id')
        if not movimiento_id:
            continue
        
        # Obtener tipo_perforacion desde equipo (como en PyQt6: JOIN equipo)
        equipo_nombre = (movimiento.get('equipo') or '').strip().upper()
        tipo_perf = equipos_dict.get(equipo_nombre, '').strip().upper()
        if not tipo_perf:
            continue
        
        # Obtener detalles
        detalles = detalles_por_entrega.get(movimiento_id, [])
        
        for detalle in detalles:
            familia = (detalle.get('familia') or '').strip().upper() if detalle.get('familia') else None
            if not familia:
                continue
            
            cantidad = detalle.get('cantidad') or 0
            if cantidad < 0:  # SALIDA
                key = (tipo_perf, familia)
                entregas_dict[key] += abs(cantidad)  # cantidad * -1 como en PyQt6
    
    # ============================================================
    # 5. AGRUPAR METROS (igual que en PyQt6)
    #    JOIN metros_general + metros_detalles + equipo
    # ============================================================
    
    # Crear diccionario de detalles de metros por registro_id
    detalles_metros_por_registro = defaultdict(list)
    for detalle in metros_detalles:
        registro_id = detalle.get('registro_id')
        if registro_id:
            detalles_metros_por_registro[registro_id].append(detalle)
    
    # ============================================================
    # AGRUPAR METROS (SOLO DESDE metros_detalles)
    # ============================================================
    metros_dict = defaultdict(lambda: {'total_mp': 0, 'mp_produccion': 0, 'mp_rimado': 0})

    # Agrupar detalles de metros por tipo_perforacion
    for detalle in metros_detalles:
        registro_id = detalle.get('registro_id')
        if not registro_id:
            continue
        
        # Buscar el metro general para obtener metadatos (ano, mes, compania, equipo)
        # Como metros_detalles no tiene equipo directamente, lo buscamos en metros_general
        metro = next((m for m in metros if m.get('id') == registro_id), None)
        if not metro:
            continue
        
        # Filtrar por año y mes
        if metro.get('ano') != ano or (metro.get('mes') or '').upper() != mes.upper():
            continue
        
        # Filtrar por compañía
        if compania and (metro.get('compania') or '').upper() != compania.upper():
            continue
        
        # Obtener tipo_perforacion desde el equipo (como en PyQt6)
        equipo_nombre = (metro.get('equipo') or '').strip().upper()
        tipo_perf = equipos_dict.get(equipo_nombre, '').strip().upper()
        if not tipo_perf:
            continue
        
        # Sumar valores (usando or 0 para evitar None)
        mp_prod = detalle.get('mp_produccion') or 0
        mp_rim = detalle.get('mp_rimado') or 0
        total_mp = detalle.get('total_mp') or 0
        
        metros_dict[tipo_perf]['mp_produccion'] += mp_prod
        metros_dict[tipo_perf]['mp_rimado'] += mp_rim
        metros_dict[tipo_perf]['total_mp'] += total_mp

    print(f"📏 Metros agrupados desde detalles: {len(metros_dict)} tipos")
    
    # ============================================================
    # 6. CALCULAR RESULTADOS (igual que en PyQt6)
    # ============================================================
    resultados = {}
    
    for (tipo_perf, familia), total_entregado in entregas_dict.items():
        if not tipo_perf or not familia:
            continue
        
        total_mp, mp_prod, mp_rim = (
            metros_dict.get(tipo_perf, {}).get('total_mp', 0),
            metros_dict.get(tipo_perf, {}).get('mp_produccion', 0),
            metros_dict.get(tipo_perf, {}).get('mp_rimado', 0)
        )
        
        # Determinar metros perforados según familia (como en PyQt6)
        if familia == "BROCAS":
            metros_perforados = mp_prod
        elif familia == "RIMADORAS":
            metros_perforados = mp_rim
        else:
            metros_perforados = total_mp
        
        if total_entregado > 0 or metros_perforados > 0:
            rendimiento = round(metros_perforados / total_entregado, 2) if total_entregado > 0 else metros_perforados
            
            objetivo = objetivos_dict.get((tipo_perf, familia), 0)
            
            if objetivo and objetivo > 0:
                eficiencia = round(rendimiento / objetivo * 100, 2)
                eficiencia_str = f"{eficiencia:.1f}%"
            else:
                eficiencia_str = "-"
            
            if tipo_perf not in resultados:
                resultados[tipo_perf] = []
            
            resultados[tipo_perf].append((
                familia,
                int(total_entregado),
                int(metros_perforados),
                rendimiento,
                objetivo or "-",
                eficiencia_str
            ))
    
    # Ordenar por eficiencia (como en PyQt6)
    for tipo in resultados:
        resultados[tipo] = sorted(
            resultados[tipo],
            key=lambda x: float(x[5].replace('%', '')) if x[5] != '-' else 0,
            reverse=True
        )


    
    return resultados


# ============================================================
# RENDIMIENTO POR OPERADOR (TabOperadoresRendimiento)
# ============================================================

def calcular_rendimiento_operadores(
    movimientos: List[Dict],
    metros: List[Dict],
    metros_detalles: List[Dict],
    objetivos: List[Dict],
    detalles_movimientos: List[Dict],
    equipos_dict: Dict[str, str],
    ano: int,
    mes: str,
    compania: str
) -> Dict[str, Dict[str, List[Dict]]]:
    """
    Calcula el rendimiento por operador
    Equivalente a _obtener_datos_operadores en PyQt6
    """
    
    if not compania:
        return {}
    
    # ============================================================
    # 1. CARGAR OBJETIVOS DE BROCAS (igual que en PyQt6)
    # ============================================================
    objetivos_brocas = {}
    for obj in objetivos:
        acero = (obj.get('Acero') or '').strip().upper() if obj.get('Acero') else ''
        if 'BROCAS' in acero:
            tipo = (obj.get('Tipo Perforacion') or '').strip().upper() if obj.get('Tipo Perforacion') else None
            if tipo:
                tipo_norm = normalizar_tipo_perforacion(tipo)
                if tipo_norm:
                    if tipo_norm not in objetivos_brocas or objetivos_brocas[tipo_norm] < obj.get('Objetivo', 0):
                        objetivos_brocas[tipo_norm] = obj.get('Objetivo', 0)
    
    # ============================================================
    # 2. FILTRAR MOVIMIENTOS (igual que en PyQt6)
    # ============================================================
    compania_upper = compania.upper()
    movimientos_filtrados = [
        m for m in movimientos 
        if m.get('ano') == ano 
        and (m.get('mes') or '').upper() == mes.upper()
        and (m.get('compania') or '').upper() == compania_upper
    ]
    
    # ============================================================
    # 3. FILTRAR METROS GENERALES (para obtener equipo y metadatos)
    # ============================================================
    metros_filtrados = [
        m for m in metros 
        if m.get('ano') == ano 
        and (m.get('mes') or '').upper() == mes.upper()
        and (m.get('compania') or '').upper() == compania_upper
    ]
    
    # ============================================================
    # 4. CREAR DICCIONARIO DE METROS GENERALES POR ID
    # ============================================================
    metros_dict = {}
    for metro in metros_filtrados:
        registro_id = metro.get('id')
        if registro_id:
            metros_dict[registro_id] = metro
    
    # ============================================================
    # 5. CREAR DICCIONARIOS DE DETALLES
    # ============================================================
    detalles_por_entrega = defaultdict(list)
    for detalle in detalles_movimientos:
        entrega_id = detalle.get('entrega_id')
        if entrega_id:
            detalles_por_entrega[entrega_id].append(detalle)
    
    # ============================================================
    # 6. AGRUPAR POR GUARDIA, OPERADOR Y TIPO
    # ============================================================
    datos_operadores = defaultdict(lambda: defaultdict(list))
    
    for movimiento in movimientos_filtrados:
        # Solo SALIDAS (como en PyQt6: cantidad < 0)
        if (movimiento.get('movimiento') or '').upper() != 'SALIDA':
            continue
        
        guardia = (movimiento.get('guardia') or 'G')
        operador = (movimiento.get('operador') or '').strip().upper()
        
        if not operador:
            continue
        
        movimiento_id = movimiento.get('id')
        if not movimiento_id:
            continue
        
        detalles = detalles_por_entrega.get(movimiento_id, [])
        
        for detalle in detalles:
            familia = (detalle.get('familia') or '').strip().upper() if detalle.get('familia') else ''
            cantidad = detalle.get('cantidad') or 0
            
            # Solo BROCAS y SALIDAS (como en PyQt6)
            if 'BROCAS' in familia and cantidad < 0:
                # Obtener tipo del equipo (como en PyQt6: JOIN equipo)
                equipo_nombre = (movimiento.get('equipo') or '').strip().upper()
                tipo_original = equipos_dict.get(equipo_nombre, '')
                tipo_norm = normalizar_tipo_perforacion(tipo_original)
                
                if not tipo_norm:
                    continue
                
                # ============================================================
                # BUSCAR METROS PARA ESTE OPERADOR/EQUIPO USANDO metros_detalles
                # ============================================================
                metros_op = 0
                
                # Recorrer todos los metros_detalles
                for detalle_metro in metros_detalles:
                    registro_id = detalle_metro.get('registro_id')
                    if not registro_id:
                        continue
                    
                    # Buscar el metro general correspondiente
                    metro = metros_dict.get(registro_id)
                    if not metro:
                        continue
                    
                    # Verificar que coincida operador y equipo
                    if ((metro.get('operador') or '').strip().upper() == operador and 
                        metro.get('equipo') == movimiento.get('equipo')):
                        
                        # Sumar mp_produccion de este detalle
                        metros_op += detalle_metro.get('mp_produccion') or 0
                
                entregado = abs(cantidad)
                
                if entregado > 0:
                    rendimiento = round(metros_op / entregado, 1) if entregado > 0 and metros_op > 0 else 0
                    objetivo = objetivos_brocas.get(tipo_norm, 0)
                    eficiencia = round((rendimiento / objetivo) * 100, 1) if objetivo > 0 and rendimiento > 0 else 0
                    
                    datos_operadores[tipo_norm][guardia].append({
                        'operador': operador,
                        'entregado': entregado,
                        'metros': metros_op,
                        'rendimiento': rendimiento,
                        'objetivo': objetivo,
                        'eficiencia': eficiencia,
                        'tipo_original': tipo_original
                    })
    
    # Ordenar por eficiencia (como en PyQt6)
    for tipo in datos_operadores:
        for guardia in datos_operadores[tipo]:
            datos_operadores[tipo][guardia] = sorted(
                datos_operadores[tipo][guardia],
                key=lambda x: x['eficiencia'],
                reverse=True
            )
    
    return dict(datos_operadores)
# ============================================================
# MÉTRICAS (igual que en PyQt6)
# ============================================================

def calcular_metricas_totales(resultados: Dict[str, List[Tuple]]) -> Dict:
    """
    Calcula métricas resumen
    Equivalente a _actualizar_metricas en PyQt6
    """
    total_familias = 0
    total_eficiencia = 0
    sobre_objetivo = 0
    bajo_80 = 0
    contador_eficiencia = 0
    
    for tipo_perf, datos in resultados.items():
        total_familias += len(datos)
        for datos_fila in datos:
            eficiencia_str = datos_fila[5]
            if eficiencia_str != "-":
                try:
                    eficiencia = float(eficiencia_str.replace('%', ''))
                    total_eficiencia += eficiencia
                    contador_eficiencia += 1
                    if eficiencia >= 100:
                        sobre_objetivo += 1
                    elif eficiencia < 80:
                        bajo_80 += 1
                except:
                    pass
    
    eficiencia_prom = total_eficiencia / contador_eficiencia if contador_eficiencia > 0 else 0
    
    return {
        'total_familias': total_familias,
        'eficiencia_promedio': eficiencia_prom,
        'sobre_objetivo': sobre_objetivo,
        'bajo_80': bajo_80,
        'total_tipos': len(resultados)
    }


def obtener_estadisticas_guardia(datos_guardia: Dict[str, List[Dict]]) -> Dict:
    """
    Calcula estadísticas por guardia
    Equivalente a _crear_resumen_estadistico en PyQt6
    """
    estadisticas = {}
    
    for guardia, operadores in datos_guardia.items():
        total_brocas = sum(op['entregado'] for op in operadores)
        total_metros = sum(op['metros'] for op in operadores)
        rend_promedio = total_metros / total_brocas if total_brocas > 0 else 0
        mejor_eficiencia = max((op['eficiencia'] for op in operadores), default=0)
        
        estadisticas[guardia] = {
            'operadores': len(operadores),
            'brocas': total_brocas,
            'metros': total_metros,
            'rendimiento': rend_promedio,
            'mejor_efi': mejor_eficiencia
        }
    
    return estadisticas