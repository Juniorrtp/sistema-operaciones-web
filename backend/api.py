from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import MovimientoCreate, MovimientoUpdate, MetroCreate, DetalleMovimiento
from database import get_db

# ============================================================
# CREAR APP
# ============================================================
app = FastAPI(title="API Sistema de Operaciones")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SERVIR ARCHIVOS ESTÁTICOS (Frontend)
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Crear directorio frontend si no existe (para Render)
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Montar archivos estáticos
if os.path.exists(os.path.join(FRONTEND_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
if os.path.exists(os.path.join(FRONTEND_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
if os.path.exists(os.path.join(FRONTEND_DIR, "movimientos")):
    app.mount("/movimientos", StaticFiles(directory=os.path.join(FRONTEND_DIR, "movimientos")), name="movimientos")
if os.path.exists(os.path.join(FRONTEND_DIR, "metros")):
    app.mount("/metros", StaticFiles(directory=os.path.join(FRONTEND_DIR, "metros")), name="metros")
if os.path.exists(os.path.join(FRONTEND_DIR, "stock")):
    app.mount("/stock", StaticFiles(directory=os.path.join(FRONTEND_DIR, "stock")), name="stock")

# ============================================================
# ENDPOINTS DE PÁGINAS HTML
# ============================================================

@app.get("/")
async def servir_index():
    """Sirve la página principal"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html no encontrado"}

@app.get("/{pagina}.html")
async def servir_pagina(pagina: str):
    """Sirve cualquier página HTML"""
    archivo = os.path.join(FRONTEND_DIR, f"{pagina}.html")
    if os.path.exists(archivo):
        return FileResponse(archivo)
    return {"error": "Página no encontrada"}


# ============================================================
# VARIABLE GLOBAL DE STOCK
# ============================================================
stock_cache = {}

def actualizar_cache_stock():
    """Actualiza el cache de stock en memoria"""
    global stock_cache
    try:
        print("🔄 ACTUALIZANDO CACHE DE STOCK...")
        db = get_db()
        
        page = 0
        page_size = 1000
        all_data = []
        
        while True:
            result = db.client.table("movimiento_detalles") \
                .select("codigo, cantidad") \
                .range(page * page_size, (page + 1) * page_size - 1) \
                .execute()
            
            if not result.data:
                break
            
            all_data.extend(result.data)
            print(f"📄 Página {page + 1}: {len(result.data)} registros")
            
            if len(result.data) < page_size:
                break
            
            page += 1
        
        print(f"📊 Total registros traídos: {len(all_data)}")
        
        stock_temp = {}
        for row in all_data:
            cod = row.get('codigo')
            cantidad = row.get('cantidad', 0)
            if cod and cantidad != 0:
                cod_clean = cod.upper().strip()
                stock_temp[cod_clean] = stock_temp.get(cod_clean, 0) + cantidad
        
        stock_cache = stock_temp
        
        positivos = len([k for k, v in stock_cache.items() if v > 0])
        print(f"✅ Cache: {len(stock_cache)} productos, {positivos} con stock positivo")
        
    except Exception as e:
        print(f"❌ Error: {e}")

@app.on_event("startup")
async def startup_event():
    """Carga el stock al iniciar la API"""
    print("🚀 INICIANDO API...")
    actualizar_cache_stock()


# ============================================================
# STOCK - ENDPOINTS
# ============================================================

@app.get("/api/stock")
async def get_all_stock():
    """Obtiene todo el stock desde el cache"""
    stock_positivo = {k: v for k, v in stock_cache.items() if v > 0}
    return [{"codigo": k, "stock": v} for k, v in stock_positivo.items()]

@app.get("/api/stock/{codigo}")
async def get_stock(codigo: str):
    """Obtiene stock de un producto desde el cache"""
    if not codigo:
        return {"codigo": codigo, "stock": 0}
    stock = stock_cache.get(codigo.upper().strip(), 0)
    return {"codigo": codigo, "stock": stock}

@app.get("/api/stock/debug")
async def debug_stock_cache():
    """Muestra el cache de stock para depuración"""
    return {
        "total_productos": len(stock_cache),
        "productos_con_stock": len([k for k, v in stock_cache.items() if v > 0]),
        "ejemplos": dict(list(stock_cache.items())[:10])
    }


# ============================================================
# DETALLES DE MOVIMIENTOS (descripciones)
# ============================================================

@app.get("/api/detalles-movimientos")
async def get_movimientos_detalles():
    """Obtiene todos los detalles de movimientos con código y descripción"""
    try:
        db = get_db()
        
        page = 0
        page_size = 1000
        all_data = []
        
        while True:
            result = db.client.table("movimiento_detalles") \
                .select("codigo, descripcion") \
                .range(page * page_size, (page + 1) * page_size - 1) \
                .execute()
            
            if not result.data:
                break
            
            all_data.extend(result.data)
            
            if len(result.data) < page_size:
                break
            
            page += 1
        
        descripciones = {}
        for row in all_data:
            codigo = row.get('codigo')
            descripcion = row.get('descripcion')
            if codigo:
                if descripcion and descripcion.strip():
                    if codigo not in descripciones or len(descripcion) > len(descripciones.get(codigo, '')):
                        descripciones[codigo] = descripcion.strip()
                else:
                    if codigo not in descripciones:
                        descripciones[codigo] = codigo
        
        data = [{'codigo': k, 'descripcion': v} for k, v in descripciones.items()]
        print(f"📦 {len(data)} detalles con descripción")
        return data
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


# ============================================================
# MOVIMIENTOS - ENDPOINTS
# ============================================================

@app.get("/api/movimientos")
async def listar_movimientos(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    movimiento: Optional[str] = None,
    limit: int = 100
):
    try:
        db = get_db()
        query = db.client.table("movimiento_general").select("*")
        
        if fecha_desde:
            query = query.gte("fecha", fecha_desde)
        if fecha_hasta:
            query = query.lte("fecha", fecha_hasta)
        if movimiento:
            query = query.eq("movimiento", movimiento)
        
        query = query.order("fecha", desc=True).limit(limit)
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/movimientos/{id}")
async def obtener_movimiento(id: int):
    try:
        db = get_db()
        general = db.get_by_id("movimiento_general", id)
        if not general:
            raise HTTPException(status_code=404, detail="No encontrado")
        
        detalles = db.client.table("movimiento_detalles").select("*").eq("entrega_id", id).execute()
        general["detalles"] = detalles.data if detalles.data else []
        return general
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/movimientos")
async def crear_movimiento(data: MovimientoCreate):
    try:
        db = get_db()
        
        cabecera = data.model_dump(exclude={'detalles'})
        
        for key in ['operador', 'equipo', 'guardia', 'compania', 'estado', 'turno']:
            if key in cabecera and cabecera[key] == '':
                cabecera[key] = None
        
        result = db.client.table("movimiento_general").insert(cabecera).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Error al guardar cabecera")
        
        movimiento_id = result.data[0]['id']
        es_salida = data.movimiento == "SALIDA"
        
        for detalle in data.detalles:
            nuevo_detalle = detalle.model_dump()
            nuevo_detalle['entrega_id'] = movimiento_id
            
            if es_salida:
                nuevo_detalle['cantidad'] = -abs(detalle.cantidad)
            else:
                nuevo_detalle['cantidad'] = abs(detalle.cantidad)
            
            db.client.table("movimiento_detalles").insert(nuevo_detalle).execute()
        
        actualizar_cache_stock()
        return {"success": True, "id": movimiento_id}
    except Exception as e:
        print(f"❌ Error al guardar movimiento: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/movimientos/{id}")
async def actualizar_movimiento(id: int, data: MovimientoUpdate):
    try:
        db = get_db()
        data_dict = {k: v for k, v in data.dict().items() if v is not None}
        if data_dict:
            db.client.table("movimiento_general").update(data_dict).eq("id", id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/movimientos/{id}")
async def eliminar_movimiento(id: int):
    try:
        db = get_db()
        db.client.table("movimiento_detalles").delete().eq("entrega_id", id).execute()
        db.client.table("movimiento_general").delete().eq("id", id).execute()
        actualizar_cache_stock()
        return {"success": True}
    except Exception as e:
        print(f"Error en eliminar_movimiento: {e}")
        return {"success": False, "error": str(e)}

#
# ============================================================
# STOCK (VERSIÓN ÚNICA)
# ============================================================

stock_cache = {}


def actualizar_cache_stock():
    global stock_cache
    try:
        print("🔄 ACTUALIZANDO CACHE DE STOCK...")
        db = get_db()
        
        # 🔥 USAR PAGINACIÓN para traer todos los registros
        page = 0
        page_size = 1000
        all_data = []
        
        while True:
            result = db.client.table("movimiento_detalles") \
                .select("codigo, cantidad") \
                .range(page * page_size, (page + 1) * page_size - 1) \
                .execute()
            
            if not result.data:
                break
            
            all_data.extend(result.data)
            print(f"📄 Página {page + 1}: {len(result.data)} registros")
            
            if len(result.data) < page_size:
                break
            
            page += 1
        
        print(f"📊 Total registros traídos: {len(all_data)}")
        
        stock_temp = {}
        for row in all_data:
            cod = row.get('codigo')
            cantidad = row.get('cantidad', 0)
            if cod and cantidad != 0:
                cod_clean = cod.upper().strip()
                stock_temp[cod_clean] = stock_temp.get(cod_clean, 0) + cantidad
        
        stock_cache = stock_temp
        
        positivos = len([k for k, v in stock_cache.items() if v > 0])
        print(f"✅ Cache: {len(stock_cache)} productos, {positivos} con stock positivo")
        
        top_positivos = sorted([(k, v) for k, v in stock_cache.items() if v > 0], 
                              key=lambda x: x[1], reverse=True)[:10]
        if top_positivos:
            print("📊 Top 10 con stock positivo:")
            for k, v in top_positivos:
                print(f"  {k}: {v}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
@app.on_event("startup")
async def startup_event():
    """Carga el stock al iniciar la API"""
    print("🚀 INICIANDO API...")
    actualizar_cache_stock()


@app.get("/api/stock")
async def get_all_stock():
    """Obtiene todo el stock desde el cache (rápido)"""
    # 🔥 Mostrar solo productos con stock > 0
    stock_positivo = {k: v for k, v in stock_cache.items() if v > 0}
    return [{"codigo": k, "stock": v} for k, v in stock_positivo.items()]


@app.get("/api/stock/{codigo}")
async def get_stock(codigo: str):
    """Obtiene stock de un producto desde el cache (rápido)"""
    if not codigo:
        return {"codigo": codigo, "stock": 0}
    stock = stock_cache.get(codigo.upper().strip(), 0)
    return {"codigo": codigo, "stock": stock}



@app.get("/api/stock/debug")
async def debug_stock_cache():
    """Muestra todo el cache de stock para depuración"""
    return {
        "total_productos": len(stock_cache),
        "productos_con_stock": len([k for k, v in stock_cache.items() if v > 0]),
        "ejemplos": dict(list(stock_cache.items())[:10])
    }

@app.get("/api/aceros")
async def buscar_aceros(q: str = "", movimiento: str = "INGRESO"):
    """Busca aceros por código o descripción usando el cache de stock"""
    try:
        print(f"🔍 Buscando aceros: q='{q}', movimiento='{movimiento}'")
        
        db = get_db()
        query = db.client.table("aceros").select("*")
        
        if q and len(q) >= 2:
            query = query.or_(f"codigo.ilike.%{q}%,descripcion.ilike.%{q}%")
        
        result = query.limit(50).execute()
        aceros = result.data if result.data else []
        
        print(f"📦 Encontrados {len(aceros)} aceros en la BD")
        
        if movimiento == "SALIDA":
            aceros_con_stock = []
            for acero in aceros:
                cod = acero.get('codigo', '')
                if cod:
                    cod_clean = cod.upper().strip()
                    # 🔥 Buscar en el cache (rápido)
                    stock = stock_cache.get(cod_clean, 0)
                    if stock > 0:
                        acero['stock'] = stock
                        aceros_con_stock.append(acero)
            
            print(f"✅ {len(aceros_con_stock)} aceros con stock > 0")
            return aceros_con_stock
        
        # INGRESO: mostrar todos con su stock (rápido)
        for acero in aceros:
            cod = acero.get('codigo', '')
            if cod:
                cod_clean = cod.upper().strip()
                acero['stock'] = stock_cache.get(cod_clean, 0)
        
        return aceros
        
    except Exception as e:
        print(f"❌ Error en buscar_aceros: {e}")
        import traceback
        traceback.print_exc()
        return []


@app.get("/api/stock/debug")
async def debug_stock():
    """Muestra el cache actual y el stock real desde Supabase"""
    try:
        db = get_db()
        
        # Stock real desde Supabase
        result = db.client.table("movimiento_detalles").select("codigo, cantidad").execute()
        
        stock_real = {}
        for row in result.data:
            cod = row.get('codigo')
            cantidad = row.get('cantidad', 0)
            if cod and cantidad != 0:
                cod_clean = cod.upper().strip()
                stock_real[cod_clean] = stock_real.get(cod_clean, 0) + cantidad
        
        # Stock en cache
        stock_cache_positivo = {k: v for k, v in stock_cache.items() if v > 0}
        
        return {
            "cache": {
                "total": len(stock_cache),
                "con_stock_positivo": len(stock_cache_positivo),
                "ejemplos": dict(list(stock_cache_positivo.items())[:10])
            },
            "real": {
                "total": len(stock_real),
                "con_stock_positivo": len([k for k, v in stock_real.items() if v > 0]),
                "ejemplos": dict(list({k: v for k, v in stock_real.items() if v > 0}.items())[:10])
            }
        }
    except Exception as e:
        return {"error": str(e)}

# ============================================================
# MOVIMIENTOS - DETALLES (para obtener descripciones)
# ============================================================
# ============================================================
# MOVIMIENTOS - DETALLES (para obtener descripciones)
# ============================================================

@app.get("/api/detalles-movimientos")
async def get_movimientos_detalles():
    """Obtiene TODOS los detalles de movimientos con código y descripción (con paginación)"""
    try:
        db = get_db()
        
        # 🔥 USAR PAGINACIÓN para traer todos los registros
        page = 0
        page_size = 1000
        all_data = []
        
        print("📡 Obteniendo todos los detalles de movimientos...")
        
        while True:
            result = db.client.table("movimiento_detalles") \
                .select("codigo, descripcion") \
                .range(page * page_size, (page + 1) * page_size - 1) \
                .execute()
            
            if not result.data:
                break
            
            all_data.extend(result.data)
            print(f"📄 Página {page + 1}: {len(result.data)} registros")
            
            if len(result.data) < page_size:
                break
            
            page += 1
        
        print(f"📊 Total registros traídos: {len(all_data)}")
        
        # 🔥 Crear diccionario con la mejor descripción por código
        descripciones = {}
        for row in all_data:
            codigo = row.get('codigo')
            descripcion = row.get('descripcion')
            
            if not codigo:
                continue
            
            # Si la descripción existe y no está vacía
            if descripcion and descripcion.strip():
                # Si no tenemos descripción o esta es más larga, usarla
                if codigo not in descripciones or len(descripcion) > len(descripciones.get(codigo, '')):
                    descripciones[codigo] = descripcion.strip()
            else:
                # Si no tiene descripción, usar el código
                if codigo not in descripciones:
                    descripciones[codigo] = codigo
        
        # 🔥 Convertir a lista de resultados
        data = [{'codigo': k, 'descripcion': v} for k, v in descripciones.items()]
        
        print(f"📦 {len(data)} códigos únicos con descripción")
        return data
    except Exception as e:
        print(f"❌ Error en get_movimientos_detalles: {e}")
        import traceback
        traceback.print_exc()
        return []
# ============================================================
# METROS
# ============================================================

@app.get("/api/metros")
async def listar_metros(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    limit: int = 100
):
    try:
        db = get_db()
        query = db.client.table("metros_general").select("*")
        if fecha_desde:
            query = query.gte("fecha", fecha_desde)
        if fecha_hasta:
            query = query.lte("fecha", fecha_hasta)
        query = query.order("fecha", desc=True).limit(limit)
        result = query.execute()
        return result.data if result.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metros/{id}")
async def obtener_metro(id: int):
    try:
        db = get_db()
        result = db.client.table("metros_general").select("*").eq("id", id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="No encontrado")
        
        # Obtener detalles
        detalles = db.client.table("metros_detalles").select("*").eq("registro_id", id).execute()
        metro = result.data[0]
        metro["detalles"] = detalles.data if detalles.data else []
        return metro
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/api/metros")
async def crear_metro(data: dict):
    try:
        db = get_db()
        
        # Separar cabecera y detalles
        detalles = data.pop('detalles', [])
        
        result = db.client.table("metros_general").insert(data).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Error al guardar cabecera")
        
        metro_id = result.data[0]['id']
        
        for detalle in detalles:
            detalle['registro_id'] = metro_id
            db.client.table("metros_detalles").insert(detalle).execute()
        
        return {"success": True, "id": metro_id}
    except Exception as e:
        print(f"❌ Error al guardar metro: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/metros/{id}")
async def actualizar_metro(id: int, data: dict):
    try:
        db = get_db()
        
        detalles = data.pop('detalles', [])
        
        # Actualizar cabecera
        db.client.table("metros_general").update(data).eq("id", id).execute()
        
        # Eliminar detalles viejos
        db.client.table("metros_detalles").delete().eq("registro_id", id).execute()
        
        # Insertar detalles nuevos
        for detalle in detalles:
            detalle['registro_id'] = id
            db.client.table("metros_detalles").insert(detalle).execute()
        
        return {"success": True}
    except Exception as e:
        print(f"❌ Error al actualizar metro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/metros/{id}")
async def eliminar_metro(id: int):
    try:
        db = get_db()
        db.client.table("metros_detalles").delete().eq("registro_id", id).execute()
        db.client.table("metros_general").delete().eq("id", id).execute()
        return {"success": True}
    except Exception as e:
        print(f"❌ Error al eliminar metro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# OPERADORES
# ============================================================

@app.get("/api/operadores")
async def listar_operadores():
    """Lista todos los operadores"""
    try:
        db = get_db()
        result = db.client.table("operador").select("*").order("nombre").execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error en listar_operadores: {e}")
        return []


@app.get("/api/operadores/{id}")
async def obtener_operador(id: int):
    """Obtiene un operador por ID"""
    try:
        db = get_db()
        result = db.client.table("operador").select("*").eq("id", id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error en obtener_operador: {e}")
        return None


@app.post("/api/operadores")
async def crear_operador(data: dict):
    """Crea un nuevo operador"""
    try:
        db = get_db()
        result = db.client.table("operador").insert(data).execute()
        return {"success": True, "id": result.data[0]['id'] if result.data else None}
    except Exception as e:
        print(f"Error en crear_operador: {e}")
        return {"success": False, "error": str(e)}


@app.put("/api/operadores/{id}")
async def actualizar_operador(id: int, data: dict):
    """Actualiza un operador"""
    try:
        db = get_db()
        db.client.table("operador").update(data).eq("id", id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error en actualizar_operador: {e}")
        return {"success": False, "error": str(e)}


@app.delete("/api/operadores/{id}")
async def eliminar_operador(id: int):
    """Elimina un operador"""
    try:
        db = get_db()
        db.client.table("operador").delete().eq("id", id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error en eliminar_operador: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# EQUIPOS
# ============================================================
@app.get("/api/equipos")
async def listar_equipos():
    """Lista todos los equipos"""
    try:
        db = get_db()
        result = db.client.table("equipo").select("equipo, compania, tipo_perforacion, ceco_tipo").order("equipo").execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error en listar_equipos: {e}")
        return []



@app.get("/api/equipos/{id}")
async def obtener_equipo(id: int):
    """Obtiene un equipo por ID"""
    try:
        db = get_db()
        result = db.client.table("equipo").select("*").eq("id", id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error en obtener_equipo: {e}")
        return None


@app.post("/api/equipos")
async def crear_equipo(data: dict):
    """Crea un nuevo equipo"""
    try:
        db = get_db()
        result = db.client.table("equipo").insert(data).execute()
        return {"success": True, "id": result.data[0]['id'] if result.data else None}
    except Exception as e:
        print(f"Error en crear_equipo: {e}")
        return {"success": False, "error": str(e)}


@app.put("/api/equipos/{id}")
async def actualizar_equipo(id: int, data: dict):
    """Actualiza un equipo"""
    try:
        db = get_db()
        db.client.table("equipo").update(data).eq("id", id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error en actualizar_equipo: {e}")
        return {"success": False, "error": str(e)}


@app.delete("/api/equipos/{id}")
async def eliminar_equipo(id: int):
    """Elimina un equipo"""
    try:
        db = get_db()
        db.client.table("equipo").delete().eq("id", id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error en eliminar_equipo: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# ACTIVIDADES
# ============================================================
@app.get("/api/actividades")
async def listar_actividades():
    """Lista todas las actividades"""
    try:
        db = get_db()
        result = db.client.table("actividad").select("*").order("codigo").execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error en listar_actividades: {e}")
        return []




@app.post("/api/stock/conteo")
async def guardar_conteo(data: dict):
    """Guarda un conteo físico de stock"""
    try:
        db = get_db()
        fecha = data.get('fecha')
        datos = data.get('datos', [])
        usuario = data.get('usuario', 'admin')
        
        if not fecha:
            return {"success": False, "message": "Fecha requerida"}
        
        print(f"📝 Guardando conteo: {fecha}, {len(datos)} productos")
        
        # Guardar en la tabla conteo_fisico
        for item in datos:
            db.client.table("conteo_fisico").insert({
                'codigo': item['codigo'],
                'ubicacion': 'TALLER',  # Por defecto
                'cantidad': item['cantidad'],
                'fecha': fecha,
                'usuario': usuario
            }).execute()
        
        return {"success": True, "message": "Conteo guardado correctamente"}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "message": str(e)}

@app.get("/api/stock/conteo/fecha")
async def get_conteo_fecha(fecha: str, ubicacion: str = "TODAS"):
    """Obtiene el conteo físico guardado para una fecha y ubicación"""
    try:
        db = get_db()
        query = db.client.table("conteo_fisico").select("*").eq("fecha", fecha)
        
        if ubicacion and ubicacion != "TODAS":
            query = query.eq("ubicacion", ubicacion)
        
        result = query.execute()
        
        return {
            "success": True,
            "datos": result.data if result.data else []
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "datos": [], "message": str(e)}


# ============================================================
# OBJETIVOS - ENDPOINTS
# ============================================================

@app.get("/api/objetivos")
async def get_objetivos():
    """Obtiene todos los objetivos de perforación"""
    try:
        db = get_db()
        result = db.client.table("objetivos").select("*").execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"❌ Error al obtener objetivos: {e}")
        return []

@app.get("/api/objetivos/tipo/{tipo_perforacion}")
async def get_objetivos_por_tipo(tipo_perforacion: str):
    """Obtiene objetivos filtrados por tipo de perforación"""
    try:
        db = get_db()
        result = db.client.table("objetivos") \
            .select("*") \
            .eq("Tipo Perforacion", tipo_perforacion) \
            .execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"❌ Error al obtener objetivos por tipo: {e}")
        return []


# ============================================================
# METROS DETALLES - ENDPOINTS
# ============================================================

@app.get("/api/metros-detalles")
async def get_metros_detalles():
    """Obtiene todos los detalles de metros"""
    try:
        db = get_db()
        result = db.client.table("metros_detalles").select("*").execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"❌ Error al obtener metros detalles: {e}")
        return []

@app.get("/api/exportar/excel")
async def exportar_excel(
    desde: str,
    hasta: str,
    tipo: str = "movimientos"  # movimientos, metros, o todos
):
    """Exporta datos a Excel - Una sola hoja con datos repetidos"""
    try:
        import io
        import pandas as pd
        from datetime import datetime
        
        db = get_db()
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            if tipo == "movimientos" or tipo == "todos":
                # ============================================================
                # MOVIMIENTOS - UNA SOLA HOJA
                # ============================================================
                
                # Obtener movimientos
                mov_result = db.client.table("movimiento_general") \
                    .select("*") \
                    .gte("fecha", desde) \
                    .lte("fecha", hasta) \
                    .order("fecha", desc=True) \
                    .execute()
                
                if mov_result.data:
                    # Obtener IDs para detalles
                    ids = [row['id'] for row in mov_result.data]
                    detalles_result = db.client.table("movimiento_detalles") \
                        .select("*") \
                        .in_("entrega_id", ids) \
                        .execute() if ids else []
                    
                    # Crear diccionario de detalles por entrega_id
                    detalles_por_id = {}
                    for det in detalles_result.data or []:
                        entrega_id = det.get('entrega_id')
                        if entrega_id not in detalles_por_id:
                            detalles_por_id[entrega_id] = []
                        detalles_por_id[entrega_id].append(det)
                    
                    # Construir filas (general + detalles)
                    rows = []
                    for mov in mov_result.data:
                        detalles = detalles_por_id.get(mov['id'], [])
                        
                        if detalles:
                            for det in detalles:
                                row = {
                                    # Generales
                                    'ID': mov.get('id'),
                                    'Fecha': mov.get('fecha'),
                                    'Mes': mov.get('mes'),
                                    'Año': mov.get('ano'),
                                    'Turno': mov.get('turno'),
                                    'Guía': mov.get('guia'),
                                    'Movimiento': mov.get('movimiento'),
                                    'Operador': mov.get('operador'),
                                    'Equipo': mov.get('equipo'),
                                    'Compañía': mov.get('compania'),
                                    'Estado': mov.get('estado'),
                                    # Detalles
                                    'Brazo': det.get('brazo'),
                                    'Código': det.get('codigo'),
                                    'Descripción': det.get('descripcion'),
                                    'Cantidad': det.get('cantidad'),
                                    'Familia': det.get('familia'),
                                    'Motivo': det.get('razon'),
                                }
                                rows.append(row)
                        else:
                            # Si no hay detalles, una fila con datos generales
                            row = {
                                'ID': mov.get('id'),
                                'Fecha': mov.get('fecha'),
                                'Mes': mov.get('mes'),
                                'Año': mov.get('ano'),
                                'Turno': mov.get('turno'),
                                'Guía': mov.get('guia'),
                                'Movimiento': mov.get('movimiento'),
                                'Operador': mov.get('operador'),
                                'Equipo': mov.get('equipo'),
                                'Compañía': mov.get('compania'),
                                'Estado': mov.get('estado'),
                                'Brazo': '',
                                'Código': '',
                                'Descripción': '',
                                'Cantidad': '',
                                'Familia': '',
                                'Motivo': '',
                            }
                            rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    df.to_excel(writer, sheet_name='Movimientos', index=False)
            
            if tipo == "metros" or tipo == "todos":
                # ============================================================
                # METROS - UNA SOLA HOJA
                # ============================================================
                
                # Obtener metros
                met_result = db.client.table("metros_general") \
                    .select("*") \
                    .gte("fecha", desde) \
                    .lte("fecha", hasta) \
                    .order("fecha", desc=True) \
                    .execute()
                
                if met_result.data:
                    # Obtener IDs para detalles
                    ids = [row['id'] for row in met_result.data]
                    detalles_result = db.client.table("metros_detalles") \
                        .select("*") \
                        .in_("registro_id", ids) \
                        .execute() if ids else []
                    
                    # Crear diccionario de detalles por registro_id
                    detalles_por_id = {}
                    for det in detalles_result.data or []:
                        registro_id = det.get('registro_id')
                        if registro_id not in detalles_por_id:
                            detalles_por_id[registro_id] = []
                        detalles_por_id[registro_id].append(det)
                    
                    # Construir filas (general + detalles)
                    rows = []
                    for met in met_result.data:
                        detalles = detalles_por_id.get(met['id'], [])
                        
                        if detalles:
                            for det in detalles:
                                row = {
                                    # Generales
                                    'ID': met.get('id'),
                                    'Fecha': met.get('fecha'),
                                    'Mes': met.get('mes'),
                                    'Año': met.get('ano'),
                                    'Turno': met.get('turno'),
                                    'Operador': met.get('operador'),
                                    'Equipo': met.get('equipo'),
                                    'Compañía': met.get('compania'),
                                    'Tipo Perforación': met.get('tipo_perforacion'),
                                    'Total MP': met.get('total_mp'),
                                    # Detalles
                                    'Brazo': det.get('brazo'),
                                    'Código Actividad': det.get('cod_ac'),
                                    'Actividad': det.get('actividad'),
                                    'Nivel': det.get('nivel_perf'),
                                    'Labor Perf.': det.get('labor_perf'),
                                    'Tipo Roca': det.get('tipo_roca'),
                                    'N° Taladros': det.get('num_tal'),
                                    'Long. Perf.': det.get('lon_perf'),
                                    'Rimados': det.get('rimados'),
                                    'MP Producción': det.get('mp_produccion'),
                                    'MP Rimado': det.get('mp_rimado'),
                                }
                                rows.append(row)
                        else:
                            row = {
                                'ID': met.get('id'),
                                'Fecha': met.get('fecha'),
                                'Mes': met.get('mes'),
                                'Año': met.get('ano'),
                                'Turno': met.get('turno'),
                                'Operador': met.get('operador'),
                                'Equipo': met.get('equipo'),
                                'Compañía': met.get('compania'),
                                'Tipo Perforación': met.get('tipo_perforacion'),
                                'Total MP': met.get('total_mp'),
                                'Brazo': '',
                                'Código Actividad': '',
                                'Actividad': '',
                                'Nivel': '',
                                'Labor Perf.': '',
                                'Tipo Roca': '',
                                'N° Taladros': '',
                                'Long. Perf.': '',
                                'Rimados': '',
                                'MP Producción': '',
                                'MP Rimado': '',
                            }
                            rows.append(row)
                    
                    df = pd.DataFrame(rows)
                    df.to_excel(writer, sheet_name='Metros', index=False)
            
            # Metadatos
            metadata = pd.DataFrame({
                'Campo': ['Fecha Desde', 'Fecha Hasta', 'Tipo', 'Exportación', 'Usuario'],
                'Valor': [
                    desde, 
                    hasta, 
                    tipo,
                    datetime.now().strftime("%d/%m/%Y %H:%M"),
                    'admin'
                ]
            })
            metadata.to_excel(writer, sheet_name='Metadatos', index=False)
        
        output.seek(0)
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=Reporte_{tipo}_{desde}_{hasta}.xlsx"
            }
        )
        
    except Exception as e:
        print(f"❌ Error exportando Excel: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


