
const isLocal = window.location.hostname === 'localhost' || 
                window.location.hostname === '127.0.0.1' ||
                window.location.hostname === '';

// 🔥 URL base de la API
const API_BASE = isLocal 
    ? 'http://localhost:8000' 
    : 'https://sistema-operaciones-web.onrender.com';

const API_URL = `${API_BASE}/api`;

console.log(`🌐 API URL: ${API_URL}`);
console.log(`📍 Entorno: ${isLocal ? 'Local' : 'Producción'}`);
// Funciones para Movimientos
async function listarMovimientos(filtros = {}) {
    const params = new URLSearchParams(filtros);
    const response = await fetch(`${API_URL}/movimientos?${params}`);
    return response.json();
}

async function obtenerMovimiento(id) {
    const response = await fetch(`${API_URL}/movimientos/${id}`);
    return response.json();
}

async function crearMovimiento(data) {
    try {
        const response = await fetch(`${API_URL}/movimientos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error en crearMovimiento:', error);
        throw error;
    }
}

async function actualizarMovimiento(id, data) {
    const response = await fetch(`${API_URL}/movimientos/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return response.json();
}

async function eliminarMovimiento(id) {
    const response = await fetch(`${API_URL}/movimientos/${id}`, {
        method: 'DELETE'
    });
    return response.json();
}

// Funciones para Metros
async function listarMetros(filtros = {}) {
    const params = new URLSearchParams(filtros);
    const response = await fetch(`${API_URL}/metros?${params}`);
    return response.json();
}

async function crearMetro(data) {
    const response = await fetch(`${API_URL}/metros`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return response.json();
}

// Funciones para Stock
async function obtenerStock() {
    const response = await fetch(`${API_URL}/stock`);
    return response.json();
}

// Función para mostrar notificaciones
function mostrarNotificacion(mensaje, tipo = 'success') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${tipo} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `${mensaje} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.prepend(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// ============================================================
// OPERADORES Y EQUIPOS
// ============================================================

async function listarOperadores() {
    try {
        const response = await fetch(`${API_URL}/operadores`);
        if (!response.ok) {
            console.error('Error al cargar operadores:', response.status);
            return [];
        }
        const data = await response.json();
        console.log('Operadores cargados:', data.length);
        return data;
    } catch (error) {
        console.error('Error cargando operadores:', error);
        return [];
    }
}

async function listarEquipos() {
    try {
        const response = await fetch(`${API_URL}/equipos`);
        if (!response.ok) {
            console.error('Error al cargar equipos:', response.status);
            return [];
        }
        const data = await response.json();
        console.log('Equipos cargados:', data.length);
        return data;
    } catch (error) {
        console.error('Error cargando equipos:', error);
        return [];
    }
}

// ============================================================
// METROS
// ============================================================

// ============================================================
// METROS
// ============================================================

async function listarMetros(filtros = {}) {
    const params = new URLSearchParams(filtros);
    const response = await fetch(`${API_URL}/metros?${params}`);
    return response.json();
}

async function obtenerMetro(id) {
    const response = await fetch(`${API_URL}/metros/${id}`);
    return response.json();
}

async function crearMetro(data) {
    const response = await fetch(`${API_URL}/metros`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return response.json();
}

async function actualizarMetro(id, data) {
    const response = await fetch(`${API_URL}/metros/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return response.json();
}

async function eliminarMetro(id) {
    const response = await fetch(`${API_URL}/metros/${id}`, {
        method: 'DELETE'
    });
    return response.json();
}