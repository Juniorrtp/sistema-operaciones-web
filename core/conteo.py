from core.database import get_db
import pandas as pd
from datetime import datetime


def obtener_ubicaciones():
    """Obtiene todas las ubicaciones activas"""
    db = get_db()
    try:
        result = db.client.table("ubicaciones").select("nombre").eq("activo", 1).order("nombre").execute()
        return [row['nombre'] for row in result.data]
    except Exception as e:
        print(f"Error en obtener_ubicaciones: {e}")
        return ["TALLER", "CAMIONETA", "T.AFILADO", "NV_120", "JIMENA", "RP-617", "NV_1370", "RP-616"]


def obtener_productos_con_stock():
    """Obtiene todos los productos que tienen stock en el sistema"""
    db = get_db()
    try:
        result = db.client.table("movimiento_detalles").select("codigo, descripcion").execute()
        productos = {}
        for row in result.data:
            codigo = row.get('codigo')
            if codigo:
                productos[codigo] = row.get('descripcion', '')
        
        return pd.DataFrame([{'codigo': k, 'descripcion': v} for k, v in productos.items()])
    except Exception as e:
        print(f"Error en obtener_productos_con_stock: {e}")
        return pd.DataFrame(columns=['codigo', 'descripcion'])


def obtener_ultimo_conteo_fisico(fecha=None, ubicacion_filtro=None):
    """Obtiene el último conteo físico guardado"""
    db = get_db()
    
    try:
        query = db.client.table("stock_fisico").select("*")
        
        if fecha:
            query = query.eq("fecha", fecha.strftime("%Y-%m-%d"))
        
        if ubicacion_filtro and ubicacion_filtro != "TODAS":
            query = query.eq("ubicacion", ubicacion_filtro)
        
        result = query.execute()
        return pd.DataFrame(result.data) if result.data else pd.DataFrame(columns=['codigo', 'descripcion', 'ubicacion', 'cantidad'])
    except Exception as e:
        print(f"Error en obtener_ultimo_conteo_fisico: {e}")
        return pd.DataFrame(columns=['codigo', 'descripcion', 'ubicacion', 'cantidad'])


def guardar_conteo_fisico(df, fecha, usuario=None, observacion=None):
    """Guarda el conteo físico"""
    db = get_db()
    
    try:
        # Eliminar registros anteriores de la misma fecha y ubicación
        ubicaciones = df['ubicacion'].unique() if 'ubicacion' in df else []
        
        for ubicacion in ubicaciones:
            df_ubicacion = df[df['ubicacion'] == ubicacion]
            codigos = df_ubicacion['codigo'].tolist()
            
            if codigos:
                for codigo in codigos:
                    db.client.table("stock_fisico").delete().eq("fecha", fecha.strftime("%Y-%m-%d")).eq("ubicacion", ubicacion).eq("codigo", codigo).execute()
        
        # Insertar nuevos registros
        registros_guardados = 0
        for _, row in df.iterrows():
            codigo = row['codigo']
            descripcion = row.get('descripcion', '')
            ubicacion = row['ubicacion']
            cantidad = row.get('cantidad', 0)
            
            if cantidad > 0:
                data = {
                    'codigo': str(codigo),
                    'descripcion': str(descripcion),
                    'ubicacion': str(ubicacion),
                    'cantidad': float(cantidad),
                    'fecha': fecha.strftime("%Y-%m-%d"),
                    'usuario': usuario or 'admin',
                    'observacion': observacion or ''
                }
                db.client.table("stock_fisico").insert(data).execute()
                registros_guardados += 1
        
        return registros_guardados
    except Exception as e:
        print(f"Error en guardar_conteo_fisico: {e}")
        return 0


def obtener_fechas_conteo(ubicacion=None):
    """Obtiene las fechas donde hay conteos guardados"""
    db = get_db()
    try:
        query = db.client.table("stock_fisico").select("fecha").execute()
        fechas = [row['fecha'] for row in result.data]
        return sorted(set(fechas), reverse=True)
    except Exception as e:
        print(f"Error en obtener_fechas_conteo: {e}")
        return []


def obtener_conteo_por_fecha(fecha, ubicacion=None):
    """Obtiene todos los registros de un conteo específico"""
    db = get_db()
    try:
        query = db.client.table("stock_fisico").select("*").eq("fecha", fecha)
        if ubicacion and ubicacion != "TODAS":
            query = query.eq("ubicacion", ubicacion)
        result = query.execute()
        return [dict(row) for row in result.data] if result.data else []
    except Exception as e:
        print(f"Error en obtener_conteo_por_fecha: {e}")
        return []