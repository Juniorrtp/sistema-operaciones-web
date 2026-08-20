import sqlite3
import hashlib

db_path = '/media/datadisk/sistema-operaciones-web/data/sistema.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar admin actual
cursor.execute("SELECT id, username, password FROM usuarios WHERE username = 'admin'")
admin = cursor.fetchone()

if admin:
    print(f"🔍 Admin encontrado:")
    print(f"   ID: {admin[0]}")
    print(f"   Username: {admin[1]}")
    print(f"   Password actual: {admin[2]}")
    
    # Hash correcto de "admin123"
    hash_correcto = hashlib.sha256("admin123".encode()).hexdigest()
    print(f"   Hash correcto: {hash_correcto}")
    
    # Actualizar
    cursor.execute("UPDATE usuarios SET password = ? WHERE username = 'admin'", (hash_correcto,))
    conn.commit()
    print("✅ Contraseña de admin ACTUALIZADA al hash correcto")
    
    # Verificar
    cursor.execute("SELECT id, username, password FROM usuarios WHERE username = 'admin'")
    admin_verif = cursor.fetchone()
    print(f"\n📋 Verificación:")
    print(f"   Password: {admin_verif[2]}")
    print(f"   Longitud: {len(admin_verif[2])} caracteres")
    
    # Probar la autenticación
    hash_ingresado = hashlib.sha256("admin123".encode()).hexdigest()
    if hash_ingresado == admin_verif[2]:
        print("\n✅ CORRECTO: admin123 funciona")
    else:
        print("\n❌ ERROR: No coincide")
else:
    print("⚠️ Admin no existe, creando...")
    hash_correcto = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("""
        INSERT INTO usuarios (username, password, nombre, rol) 
        VALUES (?, ?, ?, ?)
    """, ('admin', hash_correcto, 'Administrador', 'admin'))
    conn.commit()
    print("✅ Admin creado")

conn.close()