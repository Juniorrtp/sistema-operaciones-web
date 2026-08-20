from core.database import get_db


def obtener_operadores(busqueda=None):
    """Obtiene lista de operadores"""
    db = get_db()
    query = "SELECT id, nombre, guardia FROM operador ORDER BY nombre"
    params = []
    
    if busqueda:
        query = "SELECT id, nombre, guardia FROM operador WHERE nombre LIKE ? OR guardia LIKE ? ORDER BY nombre"
        params = [f"%{busqueda}%", f"%{busqueda}%"]
    
    resultados = db.execute_query(query, params)
    return [dict(row) for row in resultados]


def guardar_operador(datos, operador_id=None):
    """Guarda operador (nuevo o edición)"""
    db = get_db()
    
    if operador_id:
        db.execute_update(
            "UPDATE operador SET nombre = ?, guardia = ? WHERE id = ?",
            (datos['nombre'], datos['guardia'], operador_id)
        )
        return operador_id
    else:
        return db.execute_insert(
            "INSERT INTO operador (nombre, guardia) VALUES (?, ?)",
            (datos['nombre'], datos['guardia'])
        )


def eliminar_operador(operador_id):
    """Elimina operador"""
    db = get_db()
    db.execute_update("DELETE FROM operador WHERE id = ?", (operador_id,))


def obtener_equipos(busqueda=None):
    """Obtiene lista de equipos"""
    db = get_db()
    query = "SELECT id, equipo, compania, tipo_perforacion, ceco_tipo FROM equipo ORDER BY equipo"
    params = []
    
    if busqueda:
        query = """SELECT id, equipo, compania, tipo_perforacion, ceco_tipo 
                   FROM equipo 
                   WHERE equipo LIKE ? OR compania LIKE ? OR tipo_perforacion LIKE ?
                   ORDER BY equipo"""
        params = [f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"]
    
    resultados = db.execute_query(query, params)
    return [dict(row) for row in resultados]


def guardar_equipo(datos, equipo_id=None):
    """Guarda equipo (nuevo o edición)"""
    db = get_db()
    
    if equipo_id:
        db.execute_update(
            """UPDATE equipo SET equipo = ?, compania = ?, tipo_perforacion = ?, ceco_tipo = ?
               WHERE id = ?""",
            (datos['equipo'], datos['compania'], datos['tipo_perforacion'], datos['ceco_tipo'], equipo_id)
        )
        return equipo_id
    else:
        return db.execute_insert(
            """INSERT INTO equipo (equipo, compania, tipo_perforacion, ceco_tipo)
               VALUES (?, ?, ?, ?)""",
            (datos['equipo'], datos['compania'], datos['tipo_perforacion'], datos['ceco_tipo'])
        )


def eliminar_equipo(equipo_id):
    """Elimina equipo"""
    db = get_db()
    db.execute_update("DELETE FROM equipo WHERE id = ?", (equipo_id,))


def obtener_aceros(busqueda=None):
    """Obtiene lista de aceros"""
    db = get_db()
    query = """SELECT id, codigo, numparte, descripcion, proveedor, marca, familia, subfamilia
               FROM aceros ORDER BY descripcion"""
    params = []
    
    if busqueda:
        query = """SELECT id, codigo, numparte, descripcion, proveedor, marca, familia, subfamilia
                   FROM aceros 
                   WHERE codigo LIKE ? OR descripcion LIKE ? OR familia LIKE ?
                   ORDER BY descripcion"""
        params = [f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"]
    
    resultados = db.execute_query(query, params)
    return [dict(row) for row in resultados]


def guardar_acero(datos, acero_id=None):
    """Guarda acero (nuevo o edición)"""
    db = get_db()
    
    if acero_id:
        db.execute_update(
            """UPDATE aceros SET codigo = ?, numparte = ?, descripcion = ?, proveedor = ?,
               marca = ?, familia = ?, subfamilia = ? WHERE id = ?""",
            (datos['codigo'], datos['numparte'], datos['descripcion'], datos['proveedor'],
             datos['marca'], datos['familia'], datos['subfamilia'], acero_id)
        )
        return acero_id
    else:
        return db.execute_insert(
            """INSERT INTO aceros (codigo, numparte, descripcion, proveedor, marca, familia, subfamilia)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (datos['codigo'], datos['numparte'], datos['descripcion'], datos['proveedor'],
             datos['marca'], datos['familia'], datos['subfamilia'])
        )


def eliminar_acero(acero_id):
    """Elimina acero"""
    db = get_db()
    db.execute_update("DELETE FROM aceros WHERE id = ?", (acero_id,))


# Opciones para combobox
def obtener_tipos_perforacion_opciones():
    """Obtiene lista de tipos de perforación para combobox"""
    return ["", "FRONTONERO", "SOSTENIMIENTO", "TALADROS LARGOS", "TALADROS LARGOS 6FT"]


def obtener_familias_opciones():
    """Obtiene lista de familias para combobox"""
    return ["", "SHANK", "BARRAS", "ACOPLES", "BROCAS", "RIMADORAS"]


def obtener_guardias_opciones():
    """Obtiene lista de guardias"""
    return ["", "A", "B", "C"]