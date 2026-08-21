from core.database import get_db
from core.stock import StockCache


def buscar_aceros(texto_busqueda):
    """Busca aceros por código o descripción"""
    db = get_db()
    stock_cache = StockCache.get_instance()
    
    try:
        # Buscar aceros usando Supabase
        result = db.client.table("aceros").select("*").ilike("codigo", f"%{texto_busqueda}%").execute()
        
        if not result.data:
            # Intentar buscar por descripción
            result = db.client.table("aceros").select("*").ilike("descripcion", f"%{texto_busqueda}%").execute()
        
        if not result.data:
            return []
        
        aceros = []
        for row in result.data:
            codigo = row.get('codigo', '')
            stock = stock_cache.obtener_stock(codigo)
            aceros.append({
                'codigo': codigo,
                'descripcion': row.get('descripcion', ''),
                'proveedor': row.get('proveedor', ''),
                'marca': row.get('marca', ''),
                'familia': row.get('familia', ''),
                'subfamilia': row.get('subfamilia', ''),
                'stock': stock
            })
        
        return aceros
        
    except Exception as e:
        print(f"Error en buscar_aceros: {e}")
        return []


def obtener_opciones(campo):
    """Obtiene opciones para filtros usando métodos de Supabase"""
    db = get_db()
    
    try:
        if campo == 'operador':
            result = db.client.table("operador").select("nombre").execute()
            nombres = [row['nombre'] for row in result.data if row.get('nombre')]
            return sorted(set(nombres))
        
        elif campo == 'equipo':
            result = db.client.table("equipo").select("equipo").execute()
            equipos = [row['equipo'] for row in result.data if row.get('equipo')]
            return sorted(set(equipos))
        
        elif campo == 'ano':
            result = db.client.table("movimiento_general").select("ano").execute()
            anos = [row['ano'] for row in result.data if row.get('ano')]
            anos = sorted(set(anos), reverse=True)
            if not anos:
                import datetime
                year = datetime.datetime.now().year
                return [str(year), str(year-1), str(year-2)]
            return [str(a) for a in anos]
        
        elif campo == 'estado':
            result = db.client.table("movimiento_general").select("estado").execute()
            estados = [row['estado'] for row in result.data if row.get('estado') and row['estado'] != '']
            estados = sorted(set(estados))
            if "TRASLADO" not in estados:
                estados.append("TRASLADO")
            return estados
        
        elif campo == 'tipo_perforacion':
            result = db.client.table("equipo").select("tipo_perforacion").execute()
            tipos = [row['tipo_perforacion'] for row in result.data if row.get('tipo_perforacion') and row['tipo_perforacion'] != '']
            return sorted(set(tipos))
        
        elif campo == 'compania':
            result = db.client.table("equipo").select("compania").execute()
            companias = [row['compania'] for row in result.data if row.get('compania') and row['compania'] != '']
            return sorted(set(companias))
        
        else:
            # Para otros campos
            result = db.client.table("movimiento_general").select(campo).execute()
            valores = [row[campo] for row in result.data if row.get(campo) and row[campo] != '']
            return sorted(set(valores))
            
    except Exception as e:
        print(f"Error en obtener_opciones para {campo}: {e}")
        return []


def obtener_operadores_con_guardia():
    """Obtiene lista de operadores con su guardia"""
    db = get_db()
    try:
        result = db.client.table("operador").select("nombre, guardia").execute()
        return [{'nombre': row['nombre'], 'guardia': row.get('guardia', '')} for row in result.data if row.get('nombre')]
    except Exception as e:
        print(f"Error en obtener_operadores_con_guardia: {e}")
        return []


def obtener_equipos_completos():
    """Obtiene lista de equipos con su compañía y tipo"""
    db = get_db()
    try:
        result = db.client.table("equipo").select("equipo, compania, tipo_perforacion, ceco_tipo").execute()
        return [{'equipo': row['equipo'], 'compania': row.get('compania', ''), 
                 'tipo': row.get('tipo_perforacion', ''), 'ceco': row.get('ceco_tipo', '')} 
                for row in result.data if row.get('equipo')]
    except Exception as e:
        print(f"Error en obtener_equipos_completos: {e}")
        return []


def obtener_actividades():
    """Obtiene diccionario de actividades {codigo: descripcion}"""
    db = get_db()
    try:
        # Intentar con columna 'codigo'
        result = db.client.table("actividad").select("codigo, descripcion").execute()
        
        if result.data:
            return {str(row['codigo']): row['descripcion'] for row in result.data if row.get('codigo')}
        
        return {}
    except Exception as e:
        print(f"Error en obtener_actividades: {e}")
        return {}