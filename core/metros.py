from core.database import get_db
from datetime import datetime


def obtener_metros(filtros, limit=50, offset=0):
    """Obtiene registros de metros con filtros y paginación usando Supabase"""
    db = get_db()
    
    try:
        query = db.client.table("metros_general").select("*")
        
        if filtros.get('fecha_desde'):
            query = query.gte("fecha", filtros['fecha_desde'])
        if filtros.get('fecha_hasta'):
            query = query.lte("fecha", filtros['fecha_hasta'])
        
        for campo in ['ano', 'mes', 'operador', 'equipo', 'tipo_perforacion']:
            if filtros.get(campo) and len(filtros[campo]) > 0:
                query = query.in_(campo, filtros[campo])
        
        query = query.order("fecha", desc=True).order("id", desc=True)
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error en obtener_metros: {e}")
        return []


def contar_metros(filtros):
    """Cuenta total de registros para paginación"""
    db = get_db()
    
    try:
        query = db.client.table("metros_general").select("*", count="exact")
        
        if filtros.get('fecha_desde'):
            query = query.gte("fecha", filtros['fecha_desde'])
        if filtros.get('fecha_hasta'):
            query = query.lte("fecha", filtros['fecha_hasta'])
        
        for campo in ['ano', 'mes', 'operador', 'equipo', 'tipo_perforacion']:
            if filtros.get(campo) and len(filtros[campo]) > 0:
                query = query.in_(campo, filtros[campo])
        
        result = query.execute()
        return result.count if hasattr(result, 'count') else len(result.data)
        
    except Exception as e:
        print(f"Error en contar_metros: {e}")
        return 0


def obtener_metro_por_id(metro_id):
    """Obtiene un registro de metros completo con sus detalles"""
    db = get_db()
    
    try:
        result = db.client.table("metros_general").select("*").eq("id", metro_id).execute()
        if not result.data:
            return None
        
        general = result.data[0]
        
        detalles_result = db.client.table("metros_detalles").select("*").eq("registro_id", metro_id).execute()
        
        return {
            'id': metro_id,
            'generales': general,
            'detalles': detalles_result.data if detalles_result.data else []
        }
        
    except Exception as e:
        print(f"Error en obtener_metro_por_id: {e}")
        return None


def guardar_metro(datos_cabecera, datos_detalles, metro_id=None):
    """Guarda registro de metros (nuevo o edición)"""
    db = get_db()
    
    try:
        if metro_id:
            db.client.table("metros_general").update(datos_cabecera).eq("id", metro_id).execute()
            db.client.table("metros_detalles").delete().eq("registro_id", metro_id).execute()
        else:
            result = db.client.table("metros_general").insert(datos_cabecera).execute()
            if not result.data:
                return None
            metro_id = result.data[0]['id']
        
        for detalle in datos_detalles:
            detalle['registro_id'] = metro_id
            db.client.table("metros_detalles").insert(detalle).execute()
        
        return metro_id
        
    except Exception as e:
        print(f"Error en guardar_metro: {e}")
        return None


def eliminar_metro(metro_id):
    """Elimina registro de metros y sus detalles"""
    db = get_db()
    try:
        db.client.table("metros_detalles").delete().eq("registro_id", metro_id).execute()
        db.client.table("metros_general").delete().eq("id", metro_id).execute()
        return True
    except Exception as e:
        print(f"Error en eliminar_metro: {e}")
        return False


def obtener_operadores():
    """Obtiene lista de operadores"""
    db = get_db()
    try:
        result = db.client.table("operador").select("nombre, guardia").execute()
        return [{'nombre': row['nombre'], 'guardia': row.get('guardia', '')} for row in result.data if row.get('nombre')]
    except Exception as e:
        print(f"Error en obtener_operadores: {e}")
        return []


def obtener_equipos_completos():
    """Obtiene lista de equipos con compañía y tipo"""
    db = get_db()
    try:
        result = db.client.table("equipo").select("equipo, compania, tipo_perforacion, ceco_tipo").execute()
        return [{'equipo': row['equipo'], 'compania': row.get('compania', ''), 
                 'tipo': row.get('tipo_perforacion', ''), 'ceco': row.get('ceco_tipo', '')} 
                for row in result.data if row.get('equipo')]
    except Exception as e:
        print(f"Error en obtener_equipos_completos: {e}")
        return []


def obtener_tipos_perforacion():
    """Obtiene tipos de perforación únicos"""
    db = get_db()
    try:
        result = db.client.table("metros_general").select("tipo_perforacion").execute()
        tipos = [row['tipo_perforacion'] for row in result.data if row.get('tipo_perforacion') and row['tipo_perforacion'] != '']
        return sorted(set(tipos))
    except Exception as e:
        print(f"Error en obtener_tipos_perforacion: {e}")
        return []


def obtener_actividades():
    """Obtiene diccionario de actividades {codigo: descripcion}"""
    db = get_db()
    try:
        result = db.client.table("actividad").select("codigo, descripcion").execute()
        if result.data:
            return {str(row['codigo']): row['descripcion'] for row in result.data if row.get('codigo')}
        return {}
    except Exception as e:
        print(f"Error en obtener_actividades: {e}")
        return {}