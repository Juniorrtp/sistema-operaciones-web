from core.database import get_db
import hashlib
from datetime import datetime


def init_db():
    """Crea la tabla de usuarios si no existe"""
    db = get_db()
    
    try:
        # Verificar si la tabla existe
        try:
            db.execute_query("SELECT 1 FROM usuarios LIMIT 1")
            print("✅ Tabla 'usuarios' ya existe")
        except:
            print("⚠️ Tabla 'usuarios' no existe. Creándola...")
            # Crear tabla
            db.execute_update("""
                CREATE TABLE usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    email TEXT,
                    rol TEXT NOT NULL DEFAULT 'invitado',
                    activo INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Tabla creada")
            
            # Insertar admin
            hash_admin = hashlib.sha256("admin123".encode()).hexdigest()
            db.execute_insert("""
                INSERT INTO usuarios (username, password, nombre, rol) 
                VALUES (?, ?, ?, ?)
            """, ('admin', hash_admin, 'Administrador', 'admin'))
            print("✅ Usuario admin creado (contraseña: admin123)")
        
        # Verificar si admin existe (si la tabla ya existía pero no tenía admin)
        admin = db.execute_query("SELECT id FROM usuarios WHERE username = 'admin'")
        if not admin:
            hash_admin = hashlib.sha256("admin123".encode()).hexdigest()
            db.execute_insert("""
                INSERT INTO usuarios (username, password, nombre, rol) 
                VALUES (?, ?, ?, ?)
            """, ('admin', hash_admin, 'Administrador', 'admin'))
            print("✅ Usuario admin creado (contraseña: admin123)")
        
    except Exception as e:
        print(f"Error inicializando base de datos: {e}")


# Inicializar al importar
init_db()


def hash_password(password):
    """Hashea una contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verificar_password(password, hash_almacenado):
    """Verifica si la contraseña coincide con el hash"""
    return hash_password(password) == hash_almacenado


def autenticar_usuario(username, password):
    """Autentica un usuario con username y password"""
    db = get_db()
    
    query = """
        SELECT id, username, nombre, rol, activo, password
        FROM usuarios
        WHERE username = ? AND activo = 1
    """
    
    try:
        resultados = db.execute_query(query, (username,))
        if not resultados:
            print(f"❌ Usuario no encontrado: {username}")
            return None
        
        usuario = dict(resultados[0])
        print(f"🔍 Usuario encontrado: {username}")
        print(f"   Hash almacenado: {usuario['password'][:20]}...")
        
        # Verificar contraseña
        hash_ingresado = hash_password(password)
        print(f"   Hash ingresado: {hash_ingresado[:20]}...")
        
        if hash_ingresado == usuario['password']:
            del usuario['password']
            print(f"✅ Autenticación exitosa para: {username}")
            return usuario
        else:
            print(f"❌ Contraseña incorrecta para: {username}")
            return None
            
    except Exception as e:
        print(f"❌ Error en autenticar_usuario: {e}")
        import traceback
        traceback.print_exc()
        return None


def crear_usuario(username, password, nombre, rol='invitado', email=None):
    """Crea un nuevo usuario con contraseña hasheada"""
    db = get_db()
    
    # Verificar si el usuario ya existe
    existente = db.execute_query(
        "SELECT id FROM usuarios WHERE username = ?",
        (username,)
    )
    
    if existente:
        return None
    
    # 🔥 SIEMPRE hashear la contraseña
    password_hash = hash_password(password)
    
    usuario_id = db.execute_insert("""
        INSERT INTO usuarios (username, password, nombre, email, rol)
        VALUES (?, ?, ?, ?, ?)
    """, (username, password_hash, nombre, email, rol))
    
    return usuario_id


def actualizar_usuario(usuario_id, datos):
    """Actualiza datos de un usuario"""
    db = get_db()
    
    campos = []
    valores = []
    
    if 'nombre' in datos:
        campos.append("nombre = ?")
        valores.append(datos['nombre'])
    
    if 'email' in datos:
        campos.append("email = ?")
        valores.append(datos['email'])
    
    if 'rol' in datos:
        campos.append("rol = ?")
        valores.append(datos['rol'])
    
    if 'activo' in datos:
        campos.append("activo = ?")
        valores.append(datos['activo'])
    
    # 🔥 SIEMPRE hashear la contraseña si se cambia
    if 'password' in datos and datos['password']:
        campos.append("password = ?")
        valores.append(hash_password(datos['password']))
    
    if campos:
        query = f"UPDATE usuarios SET {', '.join(campos)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        valores.append(usuario_id)
        db.execute_update(query, valores)
        return True
    
    return False


def obtener_usuarios():
    """Obtiene lista de todos los usuarios"""
    db = get_db()
    
    query = """
        SELECT id, username, nombre, email, rol, activo, created_at
        FROM usuarios
        ORDER BY username
    """
    
    try:
        resultados = db.execute_query(query)
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_usuarios: {e}")
        return []


def eliminar_usuario(usuario_id):
    """Elimina un usuario (desactiva)"""
    db = get_db()
    db.execute_update("UPDATE usuarios SET activo = 0 WHERE id = ?", (usuario_id,))


def tiene_permiso(usuario, accion):
    """Verifica si un usuario tiene permiso para una acción"""
    if not usuario:
        return False
    
    rol = usuario.get('rol', 'invitado')
    
    permisos = {
        'admin': {
            'ver_movimientos': True,
            'editar_movimientos': True,
            'eliminar_movimientos': True,
            'ver_metros': True,
            'editar_metros': True,
            'eliminar_metros': True,
            'ver_stock': True,
            'editar_stock': True,
            'ver_reportes': True,
            'exportar_reportes': True,
            'ver_configuracion': True,
            'editar_configuracion': True,
            'ver_usuarios': True,
            'editar_usuarios': True,
        },
        'supervisor': {
            'ver_movimientos': True,
            'editar_movimientos': True,
            'eliminar_movimientos': False,
            'ver_metros': True,
            'editar_metros': True,
            'eliminar_metros': False,
            'ver_stock': True,
            'editar_stock': True,
            'ver_reportes': True,
            'exportar_reportes': True,
            'ver_configuracion': True,
            'editar_configuracion': False,
            'ver_usuarios': False,
            'editar_usuarios': False,
        },
        'operador': {
            'ver_movimientos': True,
            'editar_movimientos': True,
            'eliminar_movimientos': False,
            'ver_metros': True,
            'editar_metros': True,
            'eliminar_metros': False,
            'ver_stock': True,
            'editar_stock': False,
            'ver_reportes': True,
            'exportar_reportes': False,
            'ver_configuracion': False,
            'editar_configuracion': False,
            'ver_usuarios': False,
            'editar_usuarios': False,
        },
        'invitado': {
            'ver_movimientos': True,
            'editar_movimientos': False,
            'eliminar_movimientos': False,
            'ver_metros': True,
            'editar_metros': False,
            'eliminar_metros': False,
            'ver_stock': True,
            'editar_stock': False,
            'ver_reportes': True,
            'exportar_reportes': False,
            'ver_configuracion': False,
            'editar_configuracion': False,
            'ver_usuarios': False,
            'editar_usuarios': False,
        }
    }
    
    return permisos.get(rol, {}).get(accion, False)