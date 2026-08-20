import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.movimientos import guardar_movimiento, obtener_movimiento_por_id
from core.stock import StockCache
from core.aceros import buscar_aceros, obtener_operadores_con_guardia, obtener_equipos_completos


def generar_id():
    return str(uuid.uuid4())[:6]


def mostrar_formulario():
    """Muestra el formulario de movimientos"""
    
    es_edicion = st.session_state.get('editar_id') is not None
    titulo = "✏️ Editar Movimiento" if es_edicion else "📝 Nuevo Movimiento"
    
    if es_edicion and 'dialog_datos_cargados' not in st.session_state:
        datos = obtener_movimiento_por_id(st.session_state.editar_id)
        if datos:
            st.session_state.dialog_datos = datos
            st.session_state.dialog_datos_cargados = True
    
    st.markdown("---")
    st.markdown(f"## {titulo}")
    
    # ========== CABECERA ==========
    st.markdown("### 📋 Información General")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if es_edicion and st.session_state.get('dialog_datos'):
            fecha_val = datetime.strptime(st.session_state.dialog_datos['generales']['fecha'], "%Y-%m-%d")
        else:
            fecha_val = datetime.now()
        fecha = st.date_input("Fecha", value=fecha_val, key="dialog_fecha")
        
        if es_edicion and st.session_state.get('dialog_datos'):
            ano_val = st.session_state.dialog_datos['generales']['ano']
        else:
            ano_val = datetime.now().year
        ano = st.text_input("Año", value=str(ano_val), key="dialog_ano")
    
    with col2:
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        if es_edicion and st.session_state.get('dialog_datos'):
            mes_idx = meses.index(st.session_state.dialog_datos['generales']['mes'])
        else:
            mes_idx = datetime.now().month - 1
        mes = st.selectbox("Mes", meses, index=mes_idx, key="dialog_mes")
        
        turnos = ["", "DIA", "NOCHE"]
        if es_edicion and st.session_state.get('dialog_datos'):
            turno_val = st.session_state.dialog_datos['generales']['turno']
            turno_idx = turnos.index(turno_val) if turno_val in turnos else 0
        else:
            turno_idx = 0
        turno = st.selectbox("Turno", turnos, index=turno_idx, key="dialog_turno")
    
    with col3:
        if es_edicion and st.session_state.get('dialog_datos'):
            semana_val = st.session_state.dialog_datos['generales'].get('semana', '')
        else:
            semana_val = ''
        semana = st.text_input("Semana", value=semana_val, key="dialog_semana")
        
        if es_edicion and st.session_state.get('dialog_datos'):
            guia_val = st.session_state.dialog_datos['generales']['guia']
        else:
            guia_val = ''
        guia = st.text_input("Guía (*)", value=guia_val, key="dialog_guia")
        
        movimientos = ["INGRESO", "SALIDA"]
        if es_edicion and st.session_state.get('dialog_datos'):
            mov_idx = 0 if st.session_state.dialog_datos['generales']['movimiento'] == "INGRESO" else 1
        else:
            mov_idx = 0
        movimiento = st.selectbox("Movimiento", movimientos, index=mov_idx, key="dialog_movimiento")
    
    estados = ["", "CPM", "VENTA", "AFILADORAS", "TRASLADO"]
    if es_edicion and st.session_state.get('dialog_datos'):
        estado_val = st.session_state.dialog_datos['generales'].get('estado', '')
        estado_idx = estados.index(estado_val) if estado_val in estados else 0
    else:
        estado_idx = 0
    estado = st.selectbox("Estado", estados, index=estado_idx, key="dialog_estado")
    
    # ========== CAMPOS CONDICIONALES (SALIDA) ==========
    if movimiento == "SALIDA":
        st.markdown("### 👷 Datos de Salida")
        col1, col2 = st.columns(2)
        
        with col1:
            operadores = obtener_operadores_con_guardia()
            opciones_operador = [""] + [op['nombre'] for op in operadores]
            
            if es_edicion and st.session_state.get('dialog_datos'):
                operador_val = st.session_state.dialog_datos['generales'].get('operador', '')
                operador_idx = opciones_operador.index(operador_val) if operador_val in opciones_operador else 0
            else:
                operador_idx = 0
            
            operador = st.selectbox("Operador", options=opciones_operador, index=operador_idx, key="dialog_operador")
            
            if operador:
                guardia = next((op['guardia'] for op in operadores if op['nombre'] == operador), '')
                st.text_input("Guardia", value=guardia, disabled=True, key="dialog_guardia")
        
        with col2:
            equipos = obtener_equipos_completos()
            opciones_equipo = [""] + [eq['equipo'] for eq in equipos]
            
            if es_edicion and st.session_state.get('dialog_datos'):
                equipo_val = st.session_state.dialog_datos['generales'].get('equipo', '')
                equipo_idx = opciones_equipo.index(equipo_val) if equipo_val in opciones_equipo else 0
            else:
                equipo_idx = 0
            
            equipo = st.selectbox("Equipo", options=opciones_equipo, index=equipo_idx, key="dialog_equipo")
            
            if equipo:
                eq_data = next((eq for eq in equipos if eq['equipo'] == equipo), None)
                if eq_data:
                    st.text_input("Compañía", value=eq_data['compania'], disabled=True, key="dialog_compania")
    
    # ========== DETALLES ==========
    st.markdown("---")
    st.markdown("### 📋 Detalles del Movimiento")
    st.caption("💡 Cada fila tiene su propio ID. Usa '🗑️' para eliminar esa fila específica.")
    
    # Inicializar detalles con ID
    if 'dialog_detalles' not in st.session_state:
        if es_edicion and st.session_state.get('dialog_datos'):
            detalles = st.session_state.dialog_datos['detalles']
            st.session_state.dialog_detalles = []
            for d in detalles:
                st.session_state.dialog_detalles.append({
                    'id': generar_id(),
                    'brazo': d.get('brazo', ''),
                    'codigo': d.get('codigo', ''),
                    'descripcion': d.get('descripcion', ''),
                    'cantidad': d.get('cantidad', 0),
                    'motivo': d.get('motivo', '')
                })
        else:
            st.session_state.dialog_detalles = [{
                'id': generar_id(),
                'brazo': '', 'codigo': '', 'descripcion': '', 'cantidad': 0, 'motivo': ''
            }]
    
    # ========== MOSTRAR FILAS ==========
    # Usar un índice de posición para mostrar, pero el ID para las keys
    for idx, detalle in enumerate(st.session_state.dialog_detalles):
        detalle_id = detalle['id']
        
        with st.container():
            st.markdown(f"**Detalle {idx + 1}**")
            
            col1, col2, col3, col4 = st.columns([2, 2, 1.8, 0.8])
            
            with col1:
                brazo_opciones = ["", "BRAZO 1", "BRAZO 2"]
                brazo_idx_selected = brazo_opciones.index(detalle.get('brazo', '')) if detalle.get('brazo', '') in brazo_opciones else 0
                brazo = st.selectbox(
                    "Brazo",
                    options=brazo_opciones,
                    index=brazo_idx_selected,
                    key=f"dialog_brazo_{detalle_id}"
                )
                
                codigo = st.text_input(
                    "Código",
                    value=detalle.get('codigo', ''),
                    key=f"dialog_codigo_{detalle_id}"
                )
            
            with col2:
                descripcion = st.text_input(
                    "Descripción",
                    value=detalle.get('descripcion', ''),
                    key=f"dialog_desc_{detalle_id}"
                )
                
                cantidad = st.number_input(
                    "Cantidad",
                    min_value=0.0,
                    step=0.5,
                    value=float(detalle.get('cantidad', 0)),
                    key=f"dialog_cant_{detalle_id}"
                )
            
            with col3:
                motivo = st.text_input(
                    "Motivo/Observación",
                    value=detalle.get('motivo', ''),
                    key=f"dialog_motivo_{detalle_id}"
                )
            
            with col4:
                # 🔥 Botón eliminar usando el ID
                if st.button("🗑️", key=f"del_{detalle_id}", help="Eliminar este detalle"):
                    if len(st.session_state.dialog_detalles) > 1:
                        # Eliminar por ID
                        st.session_state.dialog_detalles = [d for d in st.session_state.dialog_detalles if d['id'] != detalle_id]
                        st.rerun()
                    else:
                        st.warning("⚠️ Debe haber al menos un detalle")
            
            # Actualizar valores en session_state
            for d in st.session_state.dialog_detalles:
                if d['id'] == detalle_id:
                    d['brazo'] = brazo
                    d['codigo'] = codigo
                    d['descripcion'] = descripcion
                    d['cantidad'] = cantidad
                    d['motivo'] = motivo
                    break
            
            st.divider()
    
    # ========== BOTÓN AGREGAR ==========
    if st.button("➕ Agregar Fila", use_container_width=True):
        st.session_state.dialog_detalles.append({
            'id': generar_id(),
            'brazo': '', 'codigo': '', 'descripcion': '', 'cantidad': 0, 'motivo': ''
        })
        st.rerun()
    
    # ========== BUSCADOR ==========
    st.markdown("---")
    st.markdown("### 🔍 Buscador de Aceros")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        busqueda = st.text_input("Buscar por código o descripción", key="dialog_busqueda_global")
    with col2:
        if st.button("🔍 Buscar", type="primary", use_container_width=True):
            st.rerun()
    
    if busqueda:
        aceros = buscar_aceros_con_stock(busqueda, movimiento)
        
        if aceros:
            df_aceros = pd.DataFrame(aceros)
            
            if movimiento == "SALIDA":
                st.dataframe(df_aceros[['codigo', 'descripcion', 'stock']])
            else:
                st.dataframe(df_aceros[['codigo', 'descripcion']])
            
            if aceros:
                opciones_aceros = [a['codigo'] for a in aceros]
                def format_acero(codigo):
                    acero = next(a for a in aceros if a['codigo'] == codigo)
                    return f"{codigo} - {acero['descripcion']}"
                
                codigo_seleccionado = st.selectbox(
                    "Seleccionar acero",
                    options=opciones_aceros,
                    format_func=format_acero,
                    key="dialog_select_acero"
                )
                
                if st.button("✅ Agregar a detalles", type="primary"):
                    if codigo_seleccionado:
                        acero = next(a for a in aceros if a['codigo'] == codigo_seleccionado)
                        st.session_state.dialog_detalles.append({
                            'id': generar_id(),
                            'brazo': '',
                            'codigo': acero['codigo'],
                            'descripcion': acero['descripcion'],
                            'cantidad': 0,
                            'motivo': ''
                        })
                        st.rerun()
        else:
            if movimiento == "SALIDA":
                st.warning("No se encontraron aceros con stock disponible")
            else:
                st.warning("No se encontraron aceros")
    
    # ========== BOTONES ==========
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("💾 Guardar", type="primary", use_container_width=True):
            guardar_dialogo()
    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            cerrar_dialogo()


def buscar_aceros_con_stock(busqueda, movimiento):
    from core.aceros import buscar_aceros
    
    aceros = buscar_aceros(busqueda)
    
    if movimiento == "SALIDA":
        stock_cache = StockCache.get_instance()
        aceros_con_stock = []
        for acero in aceros:
            stock = stock_cache.obtener_stock(acero['codigo'])
            if stock > 0:
                acero['stock'] = stock
                aceros_con_stock.append(acero)
        return aceros_con_stock
    else:
        return aceros


def guardar_dialogo():
    try:
        guia = st.session_state.get('dialog_guia', '')
        if not guia:
            st.error("❌ La Guía es obligatoria")
            return
        
        # Eliminar el campo 'id' antes de guardar
        detalles_para_guardar = []
        for d in st.session_state.dialog_detalles:
            detalles_para_guardar.append({
                'brazo': d.get('brazo', ''),
                'codigo': d.get('codigo', ''),
                'descripcion': d.get('descripcion', ''),
                'cantidad': d.get('cantidad', 0),
                'motivo': d.get('motivo', '')
            })
        
        detalles_validos = [d for d in detalles_para_guardar 
                           if d.get('codigo') and d.get('cantidad', 0) > 0]
        if not detalles_validos:
            st.error("❌ Debe agregar al menos un item con código y cantidad > 0")
            return
        
        movimiento = st.session_state.dialog_movimiento
        if movimiento == "SALIDA":
            stock_cache = StockCache.get_instance()
            items_sin_stock = []
            
            for detalle in detalles_validos:
                codigo = detalle['codigo']
                cantidad = detalle['cantidad']
                stock_actual = stock_cache.obtener_stock(codigo)
                
                if st.session_state.get('editar_id') and st.session_state.get('dialog_datos'):
                    cantidad_anterior = 0
                    for d in st.session_state.dialog_datos['detalles']:
                        if d['codigo'] == codigo:
                            cantidad_anterior = abs(d['cantidad'])
                            break
                    stock_necesario = cantidad - cantidad_anterior
                else:
                    stock_necesario = cantidad
                
                if stock_necesario > stock_actual:
                    items_sin_stock.append({
                        'codigo': codigo,
                        'descripcion': detalle['descripcion'],
                        'stock': stock_actual,
                        'solicitado': cantidad
                    })
            
            if items_sin_stock:
                mensaje = "❌ No hay suficiente stock:\n\n"
                for item in items_sin_stock:
                    mensaje += f"• {item['codigo']} - {item['descripcion']}\n"
                    mensaje += f"  Stock: {item['stock']} | Solicitado: {item['solicitado']}\n\n"
                st.error(mensaje)
                return
        
        cabecera = {
            'fecha': st.session_state.dialog_fecha.strftime("%Y-%m-%d"),
            'mes': st.session_state.dialog_mes,
            'ano': st.session_state.dialog_ano,
            'turno': st.session_state.dialog_turno,
            'semana': st.session_state.dialog_semana,
            'guia': guia,
            'movimiento': movimiento,
            'estado': st.session_state.dialog_estado,
            'operador': st.session_state.get('dialog_operador', ''),
            'equipo': st.session_state.get('dialog_equipo', ''),
            'guardia': st.session_state.get('dialog_guardia', ''),
            'compania': st.session_state.get('dialog_compania', '')
        }
        
        movimiento_id = guardar_movimiento(cabecera, detalles_validos, 
                                          st.session_state.get('editar_id'))
        
        st.success(f"✅ Movimiento guardado correctamente (ID: {movimiento_id})")
        st.balloons()
        
        cerrar_dialogo()
        
    except Exception as e:
        st.error(f"❌ Error al guardar: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def cerrar_dialogo():
    st.session_state.mostrar_formulario = False
    st.session_state.editar_id = None
    st.session_state.dialog_detalles = []
    st.session_state.dialog_datos_cargados = False
    
    for key in list(st.session_state.keys()):
        if key.startswith("dialog_"):
            del st.session_state[key]
    
    st.rerun()