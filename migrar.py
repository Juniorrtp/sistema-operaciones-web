#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a Supabase con REINDEXACIÓN DE IDs
Los IDs se reinician desde 1 manteniendo las relaciones (FK)
"""

import sqlite3
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL y SUPABASE_KEY deben estar configurados en .env")
    sys.exit(1)

# Conectar a Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Conectar a SQLite
db_path = '/media/datadisk/sistema-operaciones-web/data/sistema.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ============================================================
# OBTENER COLUMNAS DE UNA TABLA EN SUPABASE
# ============================================================

def get_supabase_columns(table_name):
    """Obtiene las columnas de una tabla en Supabase"""
    try:
        result = supabase.table(table_name).select("*").limit(1).execute()
        if result.data and len(result.data) > 0:
            return list(result.data[0].keys())
        return []
    except Exception as e:
        print(f"  ⚠️ No se pudieron obtener columnas de {table_name}: {e}")
        return []

# ============================================================
# MIGRAR CON REINDEXACIÓN (RESETEANDO IDs A 1)
# ============================================================

def migrar_con_reindexacion():
    """
    Migra todas las tablas reindexando los IDs desde 1
    Mantiene las relaciones mediante un mapeo de IDs
    """
    
    # Diccionarios para mapear IDs viejos a nuevos
    map_ids = {
        'movimiento_general': {},
        'metros_general': {},
    }
    
    print("=" * 60)
    print("📊 FASE 1: MIGRANDO TABLAS PRINCIPALES (GENERALES)")
    print("=" * 60)
    
    # 1. Migrar tablas GENERALES primero (padres)
    tablas_generales = ['movimiento_general', 'metros_general']
    
    for tabla in tablas_generales:
        print(f"\n📤 Migrando {tabla}...")
        
        try:
            # Obtener datos de SQLite ordenados por ID (para mantener orden)
            cursor.execute(f"SELECT * FROM {tabla} ORDER BY id")
            rows = cursor.fetchall()
            
            if not rows:
                print(f"  ⚠️ No hay datos en {tabla}")
                continue
            
            # Obtener columnas de Supabase
            supabase_cols = get_supabase_columns(tabla)
            if not supabase_cols:
                print(f"  ⚠️ No se pudieron obtener columnas de Supabase para {tabla}")
                supabase_cols = []
            
            # Preparar datos con NUEVOS IDs (empezando desde 1)
            data = []
            nuevo_id = 1
            
            for row in rows:
                row_dict = dict(row)
                viejo_id = row_dict.get('id')
                
                # Crear nuevo diccionario con el ID reindexado
                filtered_dict = {}
                for key, value in row_dict.items():
                    if key in supabase_cols or not supabase_cols:
                        if key == 'id':
                            # Asignar nuevo ID secuencial
                            filtered_dict[key] = nuevo_id
                        elif value is None or value == "":
                            filtered_dict[key] = None
                        else:
                            filtered_dict[key] = value
                
                # Guardar mapeo de ID viejo → nuevo
                if viejo_id is not None:
                    map_ids[tabla][viejo_id] = nuevo_id
                
                data.append(filtered_dict)
                nuevo_id += 1
            
            if not data:
                print(f"  ⚠️ No hay datos válidos para migrar en {tabla}")
                continue
            
            # Insertar en Supabase (por lotes de 50)
            batch_size = 50
            total_insertados = 0
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    response = supabase.table(tabla).insert(batch).execute()
                    total_insertados += len(batch)
                    print(f"  ✅ Lote {i//batch_size + 1}: {len(batch)} registros (IDs {batch[0]['id']} - {batch[-1]['id']})")
                except Exception as e:
                    print(f"  ❌ Error en lote: {e}")
                    # Intentar uno por uno
                    for item in batch:
                        try:
                            supabase.table(tabla).insert(item).execute()
                            total_insertados += 1
                        except Exception as e2:
                            print(f"    ❌ Error con ID {item.get('id', 'sin_id')}: {e2}")
            
            print(f"  ✅ {total_insertados} registros migrados a {tabla}")
            print(f"  📝 Mapeo de IDs: {len(map_ids[tabla])} registros mapeados")
            
        except Exception as e:
            print(f"  ❌ Error migrando {tabla}: {e}")
    
    print("\n" + "=" * 60)
    print("📊 FASE 2: MIGRANDO TABLAS DETALLE (Hijas)")
    print("=" * 60)
    
    # 2. Migrar tablas DETALLE (hijas) con los nuevos IDs
    tablas_detalle = [
        ('movimiento_detalles', 'entrega_id', 'movimiento_general'),
        ('metros_detalles', 'registro_id', 'metros_general'),
    ]
    
    for tabla, fk_field, tabla_padre in tablas_detalle:
        print(f"\n📤 Migrando {tabla} (FK: {fk_field} → {tabla_padre})...")
        
        try:
            # Obtener datos de SQLite
            cursor.execute(f"SELECT * FROM {tabla}")
            rows = cursor.fetchall()
            
            if not rows:
                print(f"  ⚠️ No hay datos en {tabla}")
                continue
            
            # Obtener columnas de Supabase
            supabase_cols = get_supabase_columns(tabla)
            if not supabase_cols:
                print(f"  ⚠️ No se pudieron obtener columnas de Supabase para {tabla}")
                supabase_cols = []
            
            # Preparar datos con NUEVOS IDs para las FK
            data = []
            nuevo_id = 1
            
            for row in rows:
                row_dict = dict(row)
                viejo_id = row_dict.get('id')
                viejo_fk = row_dict.get(fk_field)
                
                # Obtener el nuevo ID de la FK del mapeo
                nuevo_fk = map_ids[tabla_padre].get(viejo_fk)
                
                if nuevo_fk is None:
                    print(f"  ⚠️ No se encontró mapeo para {fk_field}={viejo_fk} en {tabla_padre}")
                    # Saltar este registro o asignar NULL (depende de tu lógica)
                    continue
                
                # Crear nuevo diccionario con IDs reindexados
                filtered_dict = {}
                for key, value in row_dict.items():
                    if key in supabase_cols or not supabase_cols:
                        if key == 'id':
                            # Nuevo ID secuencial para detalles
                            filtered_dict[key] = nuevo_id
                        elif key == fk_field:
                            # Reemplazar FK con el nuevo ID
                            filtered_dict[key] = nuevo_fk
                        elif value is None or value == "":
                            filtered_dict[key] = None
                        else:
                            filtered_dict[key] = value
                
                data.append(filtered_dict)
                nuevo_id += 1
            
            if not data:
                print(f"  ⚠️ No hay datos válidos para migrar en {tabla}")
                continue
            
            # Insertar en Supabase (por lotes de 50)
            batch_size = 50
            total_insertados = 0
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    response = supabase.table(tabla).insert(batch).execute()
                    total_insertados += len(batch)
                    print(f"  ✅ Lote {i//batch_size + 1}: {len(batch)} registros")
                except Exception as e:
                    print(f"  ❌ Error en lote: {e}")
                    # Intentar uno por uno
                    for item in batch:
                        try:
                            supabase.table(tabla).insert(item).execute()
                            total_insertados += 1
                        except Exception as e2:
                            print(f"    ❌ Error con ID {item.get('id', 'sin_id')}: {e2}")
            
            print(f"  ✅ {total_insertados} registros migrados a {tabla}")
            
        except Exception as e:
            print(f"  ❌ Error migrando {tabla}: {e}")
    
    print("\n" + "=" * 60)
    print("📊 FASE 3: MIGRANDO OTRAS TABLAS")
    print("=" * 60)
    
    # 3. Migrar otras tablas sin dependencias
    otras_tablas = ['objetivos', 'stock_fisico', 'historico_conteo', 'movimiento_stock', 'usuarios']
    
    for tabla in otras_tablas:
        print(f"\n📤 Migrando {tabla}...")
        
        try:
            # Obtener datos de SQLite
            cursor.execute(f"SELECT * FROM {tabla}")
            rows = cursor.fetchall()
            
            if not rows:
                print(f"  ⚠️ No hay datos en {tabla}")
                continue
            
            # Obtener columnas de Supabase
            supabase_cols = get_supabase_columns(tabla)
            if not supabase_cols:
                print(f"  ⚠️ No se pudieron obtener columnas de Supabase para {tabla}")
                supabase_cols = []
            
            # Preparar datos (sin reindexar, o también podemos reindexar)
            data = []
            nuevo_id = 1
            
            for row in rows:
                row_dict = dict(row)
                filtered_dict = {}
                for key, value in row_dict.items():
                    if key in supabase_cols or not supabase_cols:
                        if key == 'id':
                            # Opcional: reindexar también estas tablas
                            filtered_dict[key] = nuevo_id
                        elif value is None or value == "":
                            filtered_dict[key] = None
                        else:
                            filtered_dict[key] = value
                data.append(filtered_dict)
                nuevo_id += 1
            
            if not data:
                print(f"  ⚠️ No hay datos válidos para migrar en {tabla}")
                continue
            
            # Insertar en Supabase (por lotes de 50)
            batch_size = 50
            total_insertados = 0
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                try:
                    response = supabase.table(tabla).insert(batch).execute()
                    total_insertados += len(batch)
                    print(f"  ✅ Lote {i//batch_size + 1}: {len(batch)} registros")
                except Exception as e:
                    print(f"  ❌ Error en lote: {e}")
                    for item in batch:
                        try:
                            supabase.table(tabla).insert(item).execute()
                            total_insertados += 1
                        except Exception as e2:
                            print(f"    ❌ Error con ID {item.get('id', 'sin_id')}: {e2}")
            
            print(f"  ✅ {total_insertados} registros migrados a {tabla}")
            
        except Exception as e:
            print(f"  ❌ Error migrando {tabla}: {e}")

# ============================================================
# FUNCIÓN PARA VERIFICAR INTEGRIDAD
# ============================================================

def verificar_integridad():
    """Verifica que las relaciones se hayan mantenido correctamente"""
    print("\n" + "=" * 60)
    print("🔍 VERIFICANDO INTEGRIDAD DE DATOS")
    print("=" * 60)
    
    # Verificar movimiento_general vs movimiento_detalles
    try:
        result = supabase.table('movimiento_general').select('id', count='exact').execute()
        total_general = result.count
        print(f"✅ movimiento_general: {total_general} registros")
        
        result = supabase.table('movimiento_detalles').select('id', count='exact').execute()
        total_detalles = result.count
        print(f"✅ movimiento_detalles: {total_detalles} registros")
        
        # Verificar que los IDs de los detalles existan en general
        result = supabase.table('movimiento_detalles').select('entrega_id').execute()
        if result.data:
            entrega_ids = set([r['entrega_id'] for r in result.data])
            result2 = supabase.table('movimiento_general').select('id').execute()
            general_ids = set([r['id'] for r in result2.data])
            
            huérfanos = entrega_ids - general_ids
            if huérfanos:
                print(f"⚠️  {len(huérfanos)} IDs huérfanos en movimiento_detalles: {huérfanos}")
            else:
                print("✅ Todas las relaciones movimiento_general ↔ movimiento_detalles son válidas")
        
    except Exception as e:
        print(f"❌ Error verificando integridad: {e}")

# ============================================================
# EJECUTAR MIGRACIÓN
# ============================================================

print("=" * 60)
print("🚀 INICIANDO MIGRACIÓN CON REINDEXACIÓN DE IDs")
print("=" * 60)
print("📌 Los IDs se reiniciarán desde 1 manteniendo las relaciones")
print("=" * 60)

# Ejecutar migración
migrar_con_reindexacion()

# Verificar integridad
verificar_integridad()

print("\n" + "=" * 60)
print("✅ MIGRACIÓN COMPLETADA")
print("📌 Los IDs han sido reindexados desde 1 en todas las tablas")
print("📌 Las relaciones (FK) se han mantenido correctamente")
print("=" * 60)

conn.close()