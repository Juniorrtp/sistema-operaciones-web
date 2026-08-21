from core.database import get_db
from core.stock import StockCache


def obtener_movimientos(filtros):
    """Obtiene movimientos con filtros usando Supabase"""
    db = get_db()
    
    try:
        query = db.client.table("movimiento_general").select("*")
        
        # Fechas
        if filtros.get('fecha_desde'):
            query = query.gte("fecha", filtros['fecha_desde'])
        if filtros.get('fecha_hasta'):
            query = query.lte("fecha", filtros['fecha_hasta'])
        
        # Filtros múltiples
        for campo in ['ano', 'mes', 'movimiento', 'estado', 'operador', 'equipo']:
            if filtros.get(campo) and len(filtros[campo]) > 0:
                query = query.in_(campo, filtros[campo])
        
        # Guía
        if filtros.get('guia'):
            query = query.ilike("guia", f"%{filtros['guia']}%")
        
        query = query.order("fecha", desc=True).order("id", desc=True)
        
        # Limitar resultados
        query = query.limit(1000)
        
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Error en obtener_movimientos: {e}")
        return []


def obtener_movimiento_por_id(movimiento_id):
    """Obtiene movimiento completo con sus detalles"""
    db = get_db()
    
    try:
        # Cabecera
        result = db.client.table("movimiento_general").select("*").eq("id", movimiento_id).execute()
        
        if not result.data:
            return None
        
        general = result.data[0]
        
        # Detalles
        detalles_result = db.client.table("movimiento_detalles").select("*").eq("entrega_id", movimiento_id).execute()
        
        return {
            'id': movimiento_id,
            'generales': general,
            'detalles': detalles_result.data if detalles_result.data else []
        }
        
    except Exception as e:
        print(f"Error en obtener_movimiento_por_id: {e}")
        return None


def guardar_movimiento(datos_cabecera, datos_detalles, movimiento_id=None):
    """Guarda movimiento (nuevo o edición) usando Supabase"""
    db = get_db()
    
    try:
        # Determinar signo según movimiento
        movimiento = datos_cabecera['movimiento']
        for detalle in datos_detalles:
            cantidad = detalle['cantidad']
            if movimiento == "SALIDA":
                cantidad = -abs(cantidad)
            else:
                cantidad = abs(cantidad)
            detalle['cantidad_final'] = cantidad
        
        if movimiento_id:
            # ACTUALIZAR
            db.client.table("movimiento_general").update(datos_cabecera).eq("id", movimiento_id).execute()
            
            # Eliminar detalles viejos
            db.client.table("movimiento_detalles").delete().eq("entrega_id", movimiento_id).execute()
            
            # Insertar detalles nuevos
            for detalle in datos_detalles:
                nuevo_detalle = {
                    'entrega_id': movimiento_id,
                    'brazo': detalle.get('brazo', ''),
                    'codigo': detalle['codigo'],
                    'descripcion': detalle['descripcion'],
                    'cantidad': detalle['cantidad_final'],
                    'razon': detalle.get('motivo', '')
                }
                db.client.table("movimiento_detalles").insert(nuevo_detalle).execute()
            
        else:
            # NUEVO
            result = db.client.table("movimiento_general").insert(datos_cabecera).execute()
            
            if not result.data:
                return None
            
            movimiento_id = result.data[0]['id']
            
            for detalle in datos_detalles:
                nuevo_detalle = {
                    'entrega_id': movimiento_id,
                    'brazo': detalle.get('brazo', ''),
                    'codigo': detalle['codigo'],
                    'descripcion': detalle['descripcion'],
                    'cantidad': detalle['cantidad_final'],
                    'razon': detalle.get('motivo', '')
                }
                db.client.table("movimiento_detalles").insert(nuevo_detalle).execute()
        
        # Actualizar cache de stock
        StockCache.get_instance().actualizar_cache()
        
        return movimiento_id
        
    except Exception as e:
        print(f"Error en guardar_movimiento: {e}")
        return None


def eliminar_movimiento(movimiento_id):
    """Elimina movimiento y sus detalles"""
    db = get_db()
    try:
        db.client.table("movimiento_detalles").delete().eq("entrega_id", movimiento_id).execute()
        db.client.table("movimiento_general").delete().eq("id", movimiento_id).execute()
        StockCache.get_instance().actualizar_cache()
        return True
    except Exception as e:
        print(f"Error en eliminar_movimiento: {e}")
        return False