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
    
    # Cargar datos si es edición
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
    
    # Estado
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
    st.caption("💡 Cada detalle se muestra individualmente. Usa 'Buscar Acero' para encontrar productos.")
    
    # Inicializar detalles
    if 'dialog_detalles' not in st.session_state:
        if es_edicion and st.session_state.get('dialog_datos'):
            detalles = st.session_state.dialog_datos['detalles']
            st.session_state.dialog_detalles = [dict(d) for d in detalles]
        else:
            st.session_state.dialog_detalles = [{
                'id': generar_id(),
                'brazo': '', 'codigo': '', 'descripcion': '', 'cantidad': 0, 'motivo': ''
            }]
    
    # ========== MOSTRAR DETALLES UNO DEBAJO DE OTRO ==========
    detalles_actualizados = []
    
    for idx, detalle in enumerate(st.session_state.dialog_detalles):
        detalle_id = detalle.get('id', f"det_{idx}")
        
        with st.container():
            st.markdown(f"**Detalle {idx + 1}**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # BRAZO como combobox
                brazo_opciones = ["", "BRAZO 1", "BRAZO 2"]
                brazo_idx = brazo_opciones.index(detalle.get('brazo', '')) if detalle.get('brazo', '') in brazo_opciones else 0
                brazo = st.selectbox(
                    "Brazo",
                    options=brazo_opciones,
                    index=brazo_idx,
                    key=f"dialog_brazo_{detalle_id}"
                )
                
                # 🔥 Código
                codigo_actual = detalle.get('codigo', '')
                codigo = st.text_input(
                    "Código",
                    value=codigo_actual,
                    key=f"dialog_codigo_{detalle_id}"
                )
                if codigo != st.session_state.dialog_detalles[idx].get('codigo', ''):
                    st.session_state.dialog_detalles[idx]['codigo'] = codigo
            
            with col2:
                # 🔥 Descripción
                descripcion_actual = detalle.get('descripcion', '')
                descripcion = st.text_input(
                    "Descripción",
                    value=descripcion_actual,
                    key=f"dialog_desc_{detalle_id}"
                )
                if descripcion != st.session_state.dialog_detalles[idx].get('descripcion', ''):
                    st.session_state.dialog_detalles[idx]['descripcion'] = descripcion
                
                # 🔥 Cantidad - mostrar valor absoluto
                cantidad_valor = detalle.get('cantidad', 0)
                if isinstance(cantidad_valor, (int, float)) and cantidad_valor < 0:
                    cantidad_valor = abs(cantidad_valor)
                
                cantidad = st.number_input(
                    "Cantidad",
                    min_value=0.0,
                    step=0.5,
                    value=float(cantidad_valor),
                    key=f"dialog_cant_{detalle_id}"
                )
            
            with col3:
                motivo = st.text_input(
                    "Motivo/Observación",
                    value=detalle.get('motivo', ''),
                    key=f"dialog_motivo_{detalle_id}"
                )
                
                # 🔥 Botones de acción para esta fila
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button("📋 Copiar", key=f"copy_det_{detalle_id}", use_container_width=True):
                        copia = {
                            'id': generar_id(),
                            'brazo': brazo,
                            'codigo': codigo,
                            'descripcion': descripcion,
                            'cantidad': cantidad,
                            'motivo': motivo
                        }
                        st.session_state.dialog_detalles.insert(idx + 1, copia)
                        st.rerun()
                
                with col_btn2:
                    if st.button("🗑️ Eliminar", key=f"del_det_{detalle_id}", use_container_width=True):
                        if len(st.session_state.dialog_detalles) > 1:
                            st.session_state.dialog_detalles.pop(idx)
                            st.rerun()
                        else:
                            st.warning("⚠️ Debe haber al menos un detalle")
                
                with col_btn3:
                    # Botón para buscar acero
                    if st.button("🔍 Buscar Acero", key=f"buscar_det_{detalle_id}", use_container_width=True):
                        st.session_state[f"mostrar_buscador_{detalle_id}"] = True
            
            # ========== BUSCADOR DE ACEROS ==========
            if st.session_state.get(f"mostrar_buscador_{detalle_id}", False):
                with st.expander("🔍 Buscar Acero", expanded=True):
                    
                    if movimiento == "SALIDA":
                        st.info("🔴 Modo SALIDA: Solo se muestran aceros con STOCK DISPONIBLE")
                    else:
                        st.info("🟢 Modo INGRESO: Se muestran todos los aceros")
                    
                    busqueda = st.text_input("Buscar por código o descripción", key=f"buscar_input_{detalle_id}")
                    
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
                                    key=f"select_acero_{detalle_id}"
                                )
                                
                                col_agregar, col_cancelar = st.columns(2)
                                with col_agregar:
                                    if st.button("✅ Agregar", key=f"add_acero_{detalle_id}", use_container_width=True, type="primary"):
                                        if codigo_seleccionado:
                                            acero = next(a for a in aceros if a['codigo'] == codigo_seleccionado)
                                            # Actualizar el detalle actual
                                            st.session_state.dialog_detalles[idx]['codigo'] = acero['codigo']
                                            st.session_state.dialog_detalles[idx]['descripcion'] = acero['descripcion']
                                            st.session_state[f"mostrar_buscador_{detalle_id}"] = False
                                            st.rerun()
                                with col_cancelar:
                                    if st.button("❌ Cancelar", key=f"cancel_buscar_{detalle_id}", use_container_width=True):
                                        st.session_state[f"mostrar_buscador_{detalle_id}"] = False
                                        st.rerun()
                        else:
                            if movimiento == "SALIDA":
                                st.warning("No se encontraron aceros con stock disponible")
                            else:
                                st.warning("No se encontraron aceros")
            
            # Guardar datos de esta fila
            detalles_actualizados.append({
                'id': detalle_id,
                'brazo': brazo,
                'codigo': codigo,
                'descripcion': descripcion,
                'cantidad': cantidad,
                'motivo': motivo
            })
            
            st.divider()
    
    # Actualizar session_state
    st.session_state.dialog_detalles = detalles_actualizados
    
    # ========== BOTONES ==========
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("➕ Agregar Fila", use_container_width=True):
            st.session_state.dialog_detalles.append({
                'id': generar_id(),
                'brazo': '', 'codigo': '', 'descripcion': '', 'cantidad': 0, 'motivo': ''
            })
            st.rerun()
    
    with col2:
        if st.button("💾 Guardar", type="primary", use_container_width=True):
            guardar_dialogo()
    
    with col3:
        if st.button("❌ Cancelar", use_container_width=True):
            cerrar_dialogo()


def buscar_aceros_con_stock(busqueda, movimiento):
    """Busca aceros filtrando por stock si es SALIDA"""
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
    """Guarda el formulario"""
    try:
        guia = st.session_state.get('dialog_guia', '')
        if not guia:
            st.error("❌ La Guía es obligatoria")
            return
        
        # Obtener detalles actuales desde session_state
        detalles = st.session_state.dialog_detalles
        detalles_validos = []
        
        for d in detalles:
            if d.get('codigo') and d.get('cantidad', 0) > 0:
                detalles_validos.append({
                    'brazo': d.get('brazo', ''),
                    'codigo': d.get('codigo', ''),
                    'descripcion': d.get('descripcion', ''),
                    'cantidad': d.get('cantidad', 0),
                    'motivo': d.get('motivo', '')
                })
        
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
    """Cierra el formulario"""
    st.session_state.mostrar_formulario = False
    st.session_state.editar_id = None
    st.session_state.dialog_detalles = []
    st.session_state.dialog_datos_cargados = False
    
    # Limpiar keys del diálogo
    for key in list(st.session_state.keys()):
        if key.startswith("dialog_"):
            del st.session_state[key]
        if key.startswith("mostrar_buscador_"):
            del st.session_state[key]
    
    st.rerun()