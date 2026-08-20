import streamlit as st
import pandas as pd
import io
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.avance_semanal import (
    obtener_anos_disponibles, obtener_datos_avance_semanal,
    procesar_consumo, MESES, MES_NUMERO
)


def mostrar():
    """Página de Avance Semanal"""
    
    st.subheader("📊 Avance Semanal - Consumo y Metros")
    
    # ========== FILTROS ==========
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        anos = obtener_anos_disponibles()
        ano_seleccionado = st.selectbox("Año", options=anos, key="avance_ano")
    
    with col2:
        mes_seleccionado = st.selectbox("Mes", options=MESES, key="avance_mes")
    
    with col3:
        if st.button("🔄 Actualizar", type="primary", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # ========== CARGAR DATOS ==========
    with st.spinner("Cargando datos..."):
        datos = obtener_datos_avance_semanal(mes_seleccionado, ano_seleccionado)
    
    if not datos or not datos['companias']:
        st.info("No hay datos para los filtros seleccionados")
        return
    
    # ========== PESTAÑAS ==========
    tab1, tab2 = st.tabs(["📦 Consumo de Aceros", "📐 Metros Perforados"])
    
    with tab1:
        mostrar_consumo_aceros(datos, mes_seleccionado, ano_seleccionado)
    
    with tab2:
        mostrar_metros_perforados(datos, mes_seleccionado, ano_seleccionado)
    
    # ========== BOTÓN EXPORTAR ==========
    st.markdown("---")
    if st.button("📊 Exportar a Excel", type="primary"):
        exportar_excel(datos, mes_seleccionado, ano_seleccionado)


def mostrar_consumo_aceros(datos, mes, ano):
    """Muestra consumo de aceros - Cada tipo en su propio cuadro"""
    
    st.markdown(f"### 📦 Consumo de Aceros - {mes} {ano}")
    st.caption("💡 Cada tipo de perforación tiene su propia tabla")
    
    # Procesar consumos
    consumo_cpm, info_cpm = procesar_consumo(
        datos['consumo_cpm'], datos['stock_cpm'], 
        datos['stock_cpm_info'], datos['familias_aceros']
    )
    consumo_venta, info_venta = procesar_consumo(
        datos['consumo_venta'], {}, {},
        datos['familias_aceros']
    )
    consumo_copas, info_copas = procesar_consumo(
        datos['consumo_copas'], datos['stock_copas'],
        datos['stock_copas_info'], datos['familias_aceros']
    )
    
    companias = datos['companias']
    
    # ========== PROCESAR POR TIPO ==========
    # Recolectar todos los items por tipo
    items_por_tipo = {}
    
    for estado, consumo, info, stock, stock_info in [
        ("CPM", consumo_cpm, info_cpm, datos['stock_cpm'], datos['stock_cpm_info']),
        ("AFILADORAS", consumo_copas, info_copas, datos['stock_copas'], datos['stock_copas_info']),
        ("VENTA", consumo_venta, info_venta, {}, {})
    ]:
        if not consumo and not stock:
            continue
        
        # Agrupar por tipo de perforación
        for (tipo, cod, desc, familia), comp_data in consumo.items():
            if tipo not in items_por_tipo:
                items_por_tipo[tipo] = []
            
            total_consumo = sum(comp_data.values()) if comp_data else 0
            items_por_tipo[tipo].append({
                'estado': estado,
                'codigo': cod or '',
                'descripcion': desc or '',
                'familia': familia or '',
                'companias': comp_data,
                'total': total_consumo,
                'tipo_item': 'CONSUMO'
            })
        
        # Agregar items de stock sin consumo
        for cod, stock_val in stock.items():
            if stock_val > 0:
                info_item = stock_info.get(cod, {})
                tipo = info_item.get('tipo', 'SIN TIPO')
                desc = info_item.get('desc', '')
                familia = info_item.get('familia', '')
                
                # Verificar si ya existe consumo para este código
                tiene_consumo = False
                for (t_consumo, cod_consumo, desc_consumo, fam_consumo) in consumo.keys():
                    if cod_consumo == cod:
                        tiene_consumo = True
                        break
                
                if not tiene_consumo:
                    if tipo not in items_por_tipo:
                        items_por_tipo[tipo] = []
                    
                    items_por_tipo[tipo].append({
                        'estado': estado,
                        'codigo': cod,
                        'descripcion': desc,
                        'familia': familia,
                        'companias': {},
                        'total': 0,
                        'stock': int(stock_val) if stock_val > 0 else 0,
                        'tipo_item': 'STOCK'
                    })
    
    # ========== MOSTRAR POR TIPO ==========
    if not items_por_tipo:
        st.info("No hay datos de consumo")
        return
    
    for tipo, items in sorted(items_por_tipo.items()):
        if not items:
            continue
        
        st.markdown(f"#### 🔹 {tipo}")
        
        # Construir filas para este tipo
        rows = []
        for item in items:
            row = {
                'Estado': item['estado'],
                'Código': item['codigo'],
                'Descripción': item['descripcion'],
                'Familia': item['familia'],
            }
            for comp in companias:
                row[comp] = item['companias'].get(comp, 0)
            row['TOTAL'] = item['total']
            row['STOCK'] = item.get('stock', 0)
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Configurar columnas
        column_config = {
            'Estado': st.column_config.TextColumn('Estado', width='small'),
            'Código': st.column_config.TextColumn('Código', width='small'),
            'Descripción': st.column_config.TextColumn('Descripción', width='large'),
            'Familia': st.column_config.TextColumn('Familia', width='small'),
            'TOTAL': st.column_config.NumberColumn('TOTAL', width='small'),
            'STOCK': st.column_config.NumberColumn('STOCK', width='small')
        }
        
        for comp in companias:
            column_config[comp] = st.column_config.NumberColumn(comp, width='small')
        
        st.dataframe(
            df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            height=300
        )
        
        st.divider()


def mostrar_metros_perforados(datos, mes, ano):
    """Muestra metros perforados - Cada compañía en su propio cuadro"""
    
    st.markdown(f"### 📐 Metros Perforados - {mes} {ano}")
    st.caption("💡 Cada compañía tiene su propia tabla")
    
    # Procesar metros por compañía y tipo
    metros_por_compania = {}
    
    for row in datos['metros']:
        tp = row['tipo_perforacion'] or "SIN TIPO"
        comp = row['compania']
        mp_prod = row['mp_produccion'] or 0
        mp_rim = row['mp_rimado'] or 0
        total_mp = mp_prod + mp_rim
        
        if comp not in metros_por_compania:
            metros_por_compania[comp] = {}
        
        if tp not in metros_por_compania[comp]:
            metros_por_compania[comp][tp] = {'produccion': 0, 'rimado': 0, 'total': 0}
        
        metros_por_compania[comp][tp]['produccion'] += mp_prod
        metros_por_compania[comp][tp]['rimado'] += mp_rim
        metros_por_compania[comp][tp]['total'] += total_mp
    
    if not metros_por_compania:
        st.info("No hay datos de metros")
        return
    
    # Mostrar cada compañía en su propio cuadro
    for comp, tipos in sorted(metros_por_compania.items()):
        st.markdown(f"#### 🏢 {comp}")
        
        rows = []
        total_general = 0
        for tp, valores in sorted(tipos.items()):
            rows.append({
                'Tipo Perforación': tp,
                'Total MP': int(valores['total']),
                'MP Producción': int(valores['produccion']),
                'MP Rimado': int(valores['rimado'])
            })
            total_general += valores['total']
        
        df = pd.DataFrame(rows)
        
        # Configurar columnas
        column_config = {
            'Tipo Perforación': st.column_config.TextColumn('Tipo', width='medium'),
            'Total MP': st.column_config.NumberColumn('Total MP', width='small'),
            'MP Producción': st.column_config.NumberColumn('MP Prod.', width='small'),
            'MP Rimado': st.column_config.NumberColumn('MP Rim.', width='small')
        }
        
        st.dataframe(
            df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True
        )
        
        # Mostrar total general
        st.caption(f"📊 **Total Metros: {total_general:,.0f} m**")
        st.divider()


def exportar_excel(datos, mes, ano):
    """Exporta datos a Excel"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de Consumo de Aceros
            exportar_consumo_excel(datos, writer, mes, ano)
            
            # Hoja de Metros
            exportar_metros_excel(datos, writer, mes, ano)
        
        st.download_button(
            label="📥 Descargar Excel",
            data=output.getvalue(),
            file_name=f"Avance_Semanal_{mes}_{ano}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("✅ Excel generado correctamente")
        
    except Exception as e:
        st.error(f"❌ Error al exportar: {str(e)}")


def exportar_consumo_excel(datos, writer, mes, ano):
    """Exporta tabla de consumo a Excel"""
    
    consumo_cpm, info_cpm = procesar_consumo(
        datos['consumo_cpm'], datos['stock_cpm'], 
        datos['stock_cpm_info'], datos['familias_aceros']
    )
    consumo_venta, info_venta = procesar_consumo(
        datos['consumo_venta'], {}, {},
        datos['familias_aceros']
    )
    consumo_copas, info_copas = procesar_consumo(
        datos['consumo_copas'], datos['stock_copas'],
        datos['stock_copas_info'], datos['familias_aceros']
    )
    
    companias = datos['companias']
    
    items_por_tipo = {}
    
    for estado, consumo, info, stock, stock_info in [
        ("CPM", consumo_cpm, info_cpm, datos['stock_cpm'], datos['stock_cpm_info']),
        ("AFILADORAS", consumo_copas, info_copas, datos['stock_copas'], datos['stock_copas_info']),
        ("VENTA", consumo_venta, info_venta, {}, {})
    ]:
        if not consumo and not stock:
            continue
        
        for (tipo, cod, desc, familia), comp_data in consumo.items():
            if tipo not in items_por_tipo:
                items_por_tipo[tipo] = []
            
            total_consumo = sum(comp_data.values()) if comp_data else 0
            items_por_tipo[tipo].append({
                'estado': estado,
                'codigo': cod or '',
                'descripcion': desc or '',
                'familia': familia or '',
                'companias': comp_data,
                'total': total_consumo,
                'tipo_item': 'CONSUMO'
            })
        
        for cod, stock_val in stock.items():
            if stock_val > 0:
                info_item = stock_info.get(cod, {})
                tipo = info_item.get('tipo', 'SIN TIPO')
                desc = info_item.get('desc', '')
                familia = info_item.get('familia', '')
                
                tiene_consumo = False
                for (t_consumo, cod_consumo, desc_consumo, fam_consumo) in consumo.keys():
                    if cod_consumo == cod:
                        tiene_consumo = True
                        break
                
                if not tiene_consumo:
                    if tipo not in items_por_tipo:
                        items_por_tipo[tipo] = []
                    
                    items_por_tipo[tipo].append({
                        'estado': estado,
                        'codigo': cod,
                        'descripcion': desc,
                        'familia': familia,
                        'companias': {},
                        'total': 0,
                        'stock': int(stock_val) if stock_val > 0 else 0,
                        'tipo_item': 'STOCK'
                    })
    
    # Escribir cada tipo en su propia hoja
    for tipo, items in items_por_tipo.items():
        if not items:
            continue
        
        rows = []
        for item in items:
            row = {
                'Estado': item['estado'],
                'Código': item['codigo'],
                'Descripción': item['descripcion'],
                'Familia': item['familia'],
            }
            for comp in companias:
                row[comp] = item['companias'].get(comp, 0)
            row['TOTAL'] = item['total']
            row['STOCK'] = item.get('stock', 0)
            rows.append(row)
        
        df = pd.DataFrame(rows)
        sheet_name = f"Consumo_{tipo[:20]}"[:31]
        df.to_excel(writer, sheet_name=sheet_name, index=False)


def exportar_metros_excel(datos, writer, mes, ano):
    """Exporta tabla de metros a Excel"""
    
    metros_por_compania = {}
    
    for row in datos['metros']:
        tp = row['tipo_perforacion'] or "SIN TIPO"
        comp = row['compania']
        mp_prod = row['mp_produccion'] or 0
        mp_rim = row['mp_rimado'] or 0
        total_mp = mp_prod + mp_rim
        
        if comp not in metros_por_compania:
            metros_por_compania[comp] = {}
        
        if tp not in metros_por_compania[comp]:
            metros_por_compania[comp][tp] = {'produccion': 0, 'rimado': 0, 'total': 0}
        
        metros_por_compania[comp][tp]['produccion'] += mp_prod
        metros_por_compania[comp][tp]['rimado'] += mp_rim
        metros_por_compania[comp][tp]['total'] += total_mp
    
    for comp, tipos in metros_por_compania.items():
        rows = []
        for tp, valores in sorted(tipos.items()):
            rows.append({
                'Tipo Perforación': tp,
                'Total MP': int(valores['total']),
                'MP Producción': int(valores['produccion']),
                'MP Rimado': int(valores['rimado'])
            })
        
        df = pd.DataFrame(rows)
        sheet_name = f"Metros_{comp[:20]}"[:31]
        df.to_excel(writer, sheet_name=sheet_name, index=False)