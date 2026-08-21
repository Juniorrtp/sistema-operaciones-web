from core.database import get_db
import hashlib
from datetime import datetime


def hash_password(password):
    """Hashea una contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verificar_password(password, hash_almacenado):
    """Verifica si la contraseña coincide con el hash"""
    return hash_password(password) == hash_almacenado


def init_db():
    """Crea la tabla de usuarios si no existe y asegura que admin tenga hash correcto"""
    db = get_db()
    
    try:
        # Verificar si la tabla existe
        usuarios = db.get_all('usuarios', limit=1)
        print("✅ Tabla 'usuarios' verificada")
        
        # Verificar si admin existe
        admin = db.get_by_condition('usuarios', 'username', 'admin')
        
        if admin:
            print(f"✅ Usuario admin encontrado")
            # Verificar contraseña
            if admin and len(admin) > 0:
                admin_data = admin[0]
                password_actual = admin_data.get('password', '')
                if len(password_actual) != 64:
                    print(f"⚠️ Contraseña de admin no es hash, actualizando...")
                    hash_correcto = hash_password("admin123")
                    db.update('usuarios', admin_data['id'], {'password': hash_correcto})
                    print("✅ Contraseña de admin actualizada")
        else:
            # Crear admin
            hash_correcto = hash_password("admin123")
            db.insert('usuarios', {
                'username': 'admin',
                'password': hash_correcto,
                'nombre': 'Administrador',
                'rol': 'admin',
                'activo': 1
            })
            print("✅ Usuario admin creado (contraseña: admin123)")
        
    except Exception as e:
        print(f"Error inicializando base de datos: {e}")


def autenticar_usuario(username, password):
    """Autentica un usuario con username y password"""
    db = get_db()
    
    try:
        # Buscar usuario por username
        usuarios = db.get_by_condition('usuarios', 'username', username)
        
        if not usuarios:
            print(f"❌ Usuario no encontrado: {username}")
            return None
        
        usuario = usuarios[0]
        print(f"✅ Usuario encontrado: {username}")
        
        # Verificar si está activo
        if usuario.get('activo', 1) != 1:
            print(f"❌ Usuario inactivo: {username}")
            return None
        
        # Verificar contraseña
        password_hash = usuario.get('password', '')
        if verificar_password(password, password_hash):
            print(f"✅ Autenticación exitosa: {username}")
            # No devolver la contraseña
            usuario_sin_password = {k: v for k, v in usuario.items() if k != 'password'}
            return usuario_sin_password
        else:
            print(f"❌ Contraseña incorrecta para: {username}")
            return None
            
    except Exception as e:
        print(f"Error en autenticar_usuario: {e}")
        return None


def crear_usuario(username, password, nombre, rol='invitado', email=None):
    """Crea un nuevo usuario"""
    db = get_db()
    
    # Verificar si el usuario ya existe
    existente = db.get_by_condition('usuarios', 'username', username)
    
    if existente:
        return None
    
    password_hash = hash_password(password)
    
    usuario = {
        'username': username,
        'password': password_hash,
        'nombre': nombre,
        'email': email,
        'rol': rol,
        'activo': 1
    }
    
    resultado = db.insert('usuarios', usuario)
    if resultado:
        return resultado.get('id')
    return None


def actualizar_usuario(usuario_id, datos):
    """Actualiza datos de un usuario"""
    db = get_db()
    
    if 'password' in datos and datos['password']:
        datos['password'] = hash_password(datos['password'])
    
    resultado = db.update('usuarios', usuario_id, datos)
    return resultado is not None


def obtener_usuarios():
    """Obtiene lista de todos los usuarios"""
    db = get_db()
    
    try:
        usuarios = db.get_all('usuarios', order_by='username')
        # No devolver contraseñas
        for u in usuarios:
            if 'password' in u:
                del u['password']
        return usuarios
    except Exception as e:
        print(f"Error en obtener_usuarios: {e}")
        return []


def eliminar_usuario(usuario_id):
    """Elimina un usuario (desactiva)"""
    db = get_db()
    return db.update('usuarios', usuario_id, {'activo': 0})


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


# Inicializar al importar
init_db()