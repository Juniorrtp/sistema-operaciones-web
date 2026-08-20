import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.metros import (
    obtener_metro_por_id, guardar_metro,
    obtener_operadores, obtener_equipos_completos, obtener_actividades
)

# Factor de conversión: 1 pie = 0.3048 metros
FACTOR_PIES_A_METROS = 0.3048


def generar_id():
    return str(uuid.uuid4())[:6]


def mostrar_formulario():
    """Muestra el formulario de Metros"""
    
    es_edicion = st.session_state.get('metro_editar_id') is not None
    titulo = "✏️ Editar Metros" if es_edicion else "📏 Nuevo Registro de Metros"
    
    if es_edicion and 'metro_datos_cargados' not in st.session_state:
        datos = obtener_metro_por_id(st.session_state.metro_editar_id)
        if datos:
            st.session_state.metro_datos = datos
            st.session_state.metro_datos_cargados = True
    
    st.markdown("---")
    st.markdown(f"## {titulo}")
    
    with st.container():
        
        # ========== CABECERA ==========
        st.markdown("### 📋 Información General")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if es_edicion and st.session_state.get('metro_datos'):
                fecha_val = datetime.strptime(st.session_state.metro_datos['generales']['fecha'], "%Y-%m-%d")
            else:
                fecha_val = datetime.now()
            fecha = st.date_input("Fecha", value=fecha_val, key="metro_fecha")
            
            if es_edicion and st.session_state.get('metro_datos'):
                ano_val = st.session_state.metro_datos['generales']['ano']
            else:
                ano_val = datetime.now().year
            ano = st.number_input("Año", min_value=2000, max_value=2100, value=ano_val, key="metro_ano")
            
            meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            if es_edicion and st.session_state.get('metro_datos'):
                mes_idx = meses.index(st.session_state.metro_datos['generales']['mes'])
            else:
                mes_idx = datetime.now().month - 1
            mes = st.selectbox("Mes", meses, index=mes_idx, key="metro_mes")
        
        with col2:
            turnos = ["", "DIA", "NOCHE"]
            if es_edicion and st.session_state.get('metro_datos'):
                turno_val = st.session_state.metro_datos['generales']['turno']
                turno_idx = turnos.index(turno_val) if turno_val in turnos else 0
            else:
                turno_idx = 0
            turno = st.selectbox("Turno", turnos, index=turno_idx, key="metro_turno")
            
            operadores = obtener_operadores()
            opciones_operador = [""] + [op['nombre'] for op in operadores]
            
            if es_edicion and st.session_state.get('metro_datos'):
                operador_val = st.session_state.metro_datos['generales']['operador']
                operador_idx = opciones_operador.index(operador_val) if operador_val in opciones_operador else 0
            else:
                operador_idx = 0
            
            operador = st.selectbox("Operador", options=opciones_operador, index=operador_idx, key="metro_operador")
            
            if operador:
                guardia = next((op['guardia'] for op in operadores if op['nombre'] == operador), '')
                st.text_input("Guardia", value=guardia, disabled=True, key="metro_guardia")
            
            equipos = obtener_equipos_completos()
            opciones_equipo = [""] + [eq['equipo'] for eq in equipos]
            
            if es_edicion and st.session_state.get('metro_datos'):
                equipo_val = st.session_state.metro_datos['generales']['equipo']
                equipo_idx = opciones_equipo.index(equipo_val) if equipo_val in opciones_equipo else 0
            else:
                equipo_idx = 0
            
            equipo = st.selectbox("Equipo", options=opciones_equipo, index=equipo_idx, key="metro_equipo")
            
            if equipo:
                eq_data = next((eq for eq in equipos if eq['equipo'] == equipo), None)
                if eq_data:
                    st.text_input("Compañía", value=eq_data['compania'], disabled=True, key="metro_compania")
                    st.text_input("Tipo Perforación", value=eq_data['tipo'], disabled=True, key="metro_tipo_perf")
        
        # ========== DETALLES ==========
        st.markdown("---")
        st.markdown("### 📋 Detalles de Perforación")
        st.caption("💡 Completa los datos. Los MP se calculan automáticamente.")
        
        # Obtener actividades
        actividades_dict = obtener_actividades()
        actividades_dict = {str(k): v for k, v in actividades_dict.items()}
        
        # Crear opciones combinadas: "Código - Descripción"
        opciones_combinadas = [""]
        for codigo, descripcion in sorted(actividades_dict.items()):
            opciones_combinadas.append(f"{codigo} - {descripcion}")
        
        # Inicializar detalles
        if 'metro_detalles' not in st.session_state:
            if es_edicion and st.session_state.get('metro_datos'):
                st.session_state.metro_detalles = []
                for d in st.session_state.metro_datos['detalles']:
                    st.session_state.metro_detalles.append({
                        'id': generar_id(),
                        'brazo': d.get('brazo', ''),
                        'cod_ac': str(d.get('cod_ac', '')),
                        'actividad': d.get('actividad', ''),
                        'nivel_perf': d.get('nivel_perf', ''),
                        'labor_perf': d.get('labor_perf', ''),
                        'tipo_roca': d.get('tipo_roca', ''),
                        'num_tal': d.get('num_tal', 0),
                        'rimados': d.get('rimados', 0),
                        'lon_perf': d.get('lon_perf', 0),
                        'mp_produccion': d.get('mp_produccion', 0),
                        'mp_rimado': d.get('mp_rimado', 0),
                        'total_mp': d.get('total_mp', 0)
                    })
            else:
                st.session_state.metro_detalles = [{
                    'id': generar_id(),
                    'brazo': '', 'cod_ac': '', 'actividad': '',
                    'nivel_perf': '', 'labor_perf': '',
                    'tipo_roca': '', 'num_tal': 0, 'rimados': 0, 'lon_perf': 0,
                    'mp_produccion': 0, 'mp_rimado': 0, 'total_mp': 0
                }]
        
        # ========== MOSTRAR DETALLES ==========
        for idx, detalle in enumerate(st.session_state.metro_detalles):
            detalle_id = detalle['id']
            
            with st.container():
                st.markdown(f"**Detalle {idx + 1}**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    brazo = st.selectbox(
                        "Brazo",
                        options=["", "BRAZO 1", "BRAZO 2"],
                        index=0 if not detalle.get('brazo') else 
                              (["", "BRAZO 1", "BRAZO 2"].index(detalle['brazo']) if detalle['brazo'] in ["", "BRAZO 1", "BRAZO 2"] else 0),
                        key=f"metro_brazo_{detalle_id}"
                    )
                    
                    # Selector combinado: código + descripción
                    cod_actual = str(detalle.get('cod_ac', ''))
                    
                    # Buscar el valor actual en las opciones combinadas
                    valor_actual = ""
                    if cod_actual and cod_actual in actividades_dict:
                        valor_actual = f"{cod_actual} - {actividades_dict[cod_actual]}"
                    
                    if valor_actual not in opciones_combinadas:
                        valor_actual = ""
                    
                    idx_seleccion = opciones_combinadas.index(valor_actual) if valor_actual in opciones_combinadas else 0
                    
                    seleccion = st.selectbox(
                        "Código Actividad",
                        options=opciones_combinadas,
                        index=idx_seleccion,
                        key=f"metro_cod_{detalle_id}"
                    )
                    
                    # Extraer código y descripción de la selección
                    if seleccion and " - " in seleccion:
                        cod_ac = seleccion.split(" - ")[0]
                        actividad_texto = seleccion.split(" - ")[1]
                    else:
                        cod_ac = ""
                        actividad_texto = ""
                    
                    # Mostrar actividad (editable)
                    actividad_manual = st.text_input(
                        "Actividad",
                        value=actividad_texto,
                        key=f"metro_actividad_{detalle_id}"
                    )
                
                with col2:
                    nivel = st.text_input("Nivel", value=detalle.get('nivel_perf', ''), key=f"metro_nivel_{detalle_id}")
                    labor_perf = st.text_input("Labor Perf.", value=detalle.get('labor_perf', ''), key=f"metro_labor_{detalle_id}")
                    
                    tipo_roca = st.selectbox(
                        "Tipo Roca",
                        options=["", "MINERAL", "DESMONTE"],
                        index=0 if not detalle.get('tipo_roca') else 
                              (["", "MINERAL", "DESMONTE"].index(detalle['tipo_roca']) if detalle['tipo_roca'] in ["", "MINERAL", "DESMONTE"] else 0),
                        key=f"metro_roca_{detalle_id}"
                    )
                
                with col3:
                    # ORDEN: Taladros → Rimados → Longitud
                    num_tal = st.number_input(
                        "N° Taladros", 
                        min_value=0, 
                        value=int(detalle.get('num_tal', 0)),
                        key=f"metro_tal_{detalle_id}"
                    )
                    
                    rimados = st.number_input(
                        "Rimados", 
                        min_value=0, 
                        value=int(detalle.get('rimados', 0)),
                        key=f"metro_rim_{detalle_id}"
                    )
                    
                    lon_perf = st.number_input(
                        "Long. Perf. (pies)", 
                        min_value=0.0, 
                        value=float(detalle.get('lon_perf', 0)),
                        step=0.5,
                        key=f"metro_lon_{detalle_id}"
                    )
                
                # ========== CÁLCULOS ==========
                mp_prod = num_tal * lon_perf * FACTOR_PIES_A_METROS
                mp_rim = rimados * lon_perf * FACTOR_PIES_A_METROS
                total_mp = mp_prod + mp_rim
                
                # Mostrar resumen
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("MP Prod.", f"{mp_prod:.2f}")
                with col2:
                    st.metric("MP Rim.", f"{mp_rim:.2f}")
                with col3:
                    st.metric("Total MP", f"{total_mp:.2f}")
                with col4:
                    if st.button("📋 Copiar", key=f"metro_copy_{detalle_id}"):
                        copia = {
                            'id': generar_id(),
                            'brazo': brazo,
                            'cod_ac': cod_ac,
                            'actividad': actividad_manual,
                            'nivel_perf': nivel,
                            'labor_perf': labor_perf,
                            'tipo_roca': tipo_roca,
                            'num_tal': num_tal,
                            'rimados': rimados,
                            'lon_perf': lon_perf,
                            'mp_produccion': mp_prod,
                            'mp_rimado': mp_rim,
                            'total_mp': total_mp
                        }
                        st.session_state.metro_detalles.insert(idx + 1, copia)
                        st.rerun()
                with col5:
                    if st.button("🗑️", key=f"metro_del_{detalle_id}"):
                        if len(st.session_state.metro_detalles) > 1:
                            st.session_state.metro_detalles = [d for d in st.session_state.metro_detalles if d['id'] != detalle_id]
                            st.rerun()
                        else:
                            st.warning("⚠️ Debe haber al menos un detalle")
                
                # Actualizar valores en session_state
                for d in st.session_state.metro_detalles:
                    if d['id'] == detalle_id:
                        d['brazo'] = brazo
                        d['cod_ac'] = cod_ac
                        d['actividad'] = actividad_manual
                        d['nivel_perf'] = nivel
                        d['labor_perf'] = labor_perf
                        d['tipo_roca'] = tipo_roca
                        d['num_tal'] = num_tal
                        d['rimados'] = rimados
                        d['lon_perf'] = lon_perf
                        d['mp_produccion'] = mp_prod
                        d['mp_rimado'] = mp_rim
                        d['total_mp'] = total_mp
                        break
                
                st.divider()
        
        # ========== BOTONES ==========
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("➕ Agregar Fila", use_container_width=True):
                st.session_state.metro_detalles.append({
                    'id': generar_id(),
                    'brazo': '', 'cod_ac': '', 'actividad': '',
                    'nivel_perf': '', 'labor_perf': '',
                    'tipo_roca': '', 'num_tal': 0, 'rimados': 0, 'lon_perf': 0,
                    'mp_produccion': 0, 'mp_rimado': 0, 'total_mp': 0
                })
                st.rerun()
        
        with col2:
            if st.button("💾 Guardar", type="primary", use_container_width=True):
                guardar_metro_formulario()
        with col3:
            if st.button("❌ Cancelar", use_container_width=True):
                cerrar_metro_formulario()


def guardar_metro_formulario():
    """Guarda el formulario de metros"""
    try:
        if not st.session_state.get('metro_operador', ''):
            st.error("❌ El Operador es obligatorio")
            return
        
        if not st.session_state.get('metro_equipo', ''):
            st.error("❌ El Equipo es obligatorio")
            return
        
        # Eliminar el campo 'id' antes de guardar
        detalles_para_guardar = []
        for d in st.session_state.metro_detalles:
            detalles_para_guardar.append({
                'brazo': d.get('brazo', ''),
                'cod_ac': d.get('cod_ac', ''),
                'actividad': d.get('actividad', ''),
                'nivel_perf': d.get('nivel_perf', ''),
                'labor_perf': d.get('labor_perf', ''),
                'tipo_roca': d.get('tipo_roca', ''),
                'num_tal': d.get('num_tal', 0),
                'rimados': d.get('rimados', 0),
                'lon_perf': d.get('lon_perf', 0),
                'mp_produccion': d.get('mp_produccion', 0),
                'mp_rimado': d.get('mp_rimado', 0),
                'total_mp': d.get('total_mp', 0)
            })
        
        detalles_validos = [d for d in detalles_para_guardar 
                           if d.get('cod_ac') and d.get('num_tal', 0) > 0]
        if not detalles_validos:
            st.error("❌ Debe agregar al menos un detalle con código y N° Taladros > 0")
            return
        
        cabecera = {
            'fecha': st.session_state.metro_fecha.strftime("%Y-%m-%d"),
            'mes': st.session_state.metro_mes,
            'ano': st.session_state.metro_ano,
            'turno': st.session_state.metro_turno,
            'operador': st.session_state.metro_operador,
            'guardia': st.session_state.get('metro_guardia', ''),
            'equipo': st.session_state.metro_equipo,
            'compania': st.session_state.get('metro_compania', ''),
            'tipo_perforacion': st.session_state.get('metro_tipo_perf', ''),
            'ceco_tipo_perf': ''
        }
        
        metro_id = guardar_metro(
            cabecera, 
            detalles_validos, 
            st.session_state.get('metro_editar_id')
        )
        
        st.success(f"✅ Registro guardado correctamente (ID: {metro_id})")
        st.balloons()
        
        cerrar_metro_formulario()
        
    except Exception as e:
        st.error(f"❌ Error al guardar: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def cerrar_metro_formulario():
    """Cierra el formulario"""
    st.session_state.metro_mostrar_formulario = False
    st.session_state.metro_editar_id = None
    st.session_state.metro_detalles = []
    st.session_state.metro_datos_cargados = False
    
    for key in list(st.session_state.keys()):
        if key.startswith("metro_"):
            del st.session_state[key]
    
    st.rerun()