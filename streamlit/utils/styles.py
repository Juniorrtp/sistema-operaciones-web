# utils/styles.py
import streamlit as st

def apply_custom_styles():
    """Aplica los estilos personalizados a cualquier página"""
    
    st.markdown("""
        <style>
            /* Ocultar elementos no deseados */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display: none;}
            
            /* ============================================
               PERSONALIZAR EL SIDEBAR NATIVO
               ============================================ */
            
            /* Fondo del sidebar */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0f1a24 0%, #1a2c3e 100%) !important;
                padding-top: 20px !important;
            }
            
            section[data-testid="stSidebar"] > div {
                background: transparent !important;
            }
            
            /* Ocultar sidebar por defecto */
            .st-emotion-cache-1v0mbdj {
                display: none !important;
            }
            
            /* Título del sidebar */
            .sidebar-title {
                color: #ffffff !important;
                font-size: 22px !important;
                font-weight: 700 !important;
                text-align: center !important;
                padding: 10px 0 5px 0 !important;
                letter-spacing: 0.5px !important;
            }
            
            .sidebar-title small {
                font-size: 14px !important;
                font-weight: 300 !important;
                color: #89b4d4 !important;
                display: block !important;
                margin-top: 2px !important;
            }
            
            .sidebar-divider {
                border: none !important;
                height: 2px !important;
                background: linear-gradient(90deg, #4472C4, #6a9fd8, #4472C4) !important;
                margin: 15px 20px !important;
                border-radius: 2px !important;
            }
            
            /* Items del menú - estilo radio */
            .st-emotion-cache-1oe5cao {
                background-color: transparent !important;
                border-radius: 8px !important;
                margin: 2px 8px !important;
                padding: 6px 12px !important;
                transition: all 0.2s ease !important;
            }
            
            .st-emotion-cache-1oe5cao:hover {
                background-color: rgba(68, 114, 196, 0.2) !important;
            }
            
            .st-emotion-cache-1oe5cao[data-selected="true"] {
                background: linear-gradient(135deg, #4472C4 0%, #2a5a9a 100%) !important;
                border-radius: 8px !important;
                box-shadow: 0 2px 8px rgba(68, 114, 196, 0.4) !important;
            }
            
            .st-emotion-cache-1oe5cao[data-selected="true"] p {
                color: #ffffff !important;
                font-weight: 600 !important;
            }
            
            .st-emotion-cache-1oe5cao p {
                color: #c8d6e5 !important;
                font-size: 14px !important;
                font-weight: 400 !important;
            }
            
            .connection-status {
                margin: 10px 20px !important;
                padding: 8px 12px !important;
                border-radius: 6px !important;
                font-size: 12px !important;
                text-align: center !important;
            }
            
            .connection-status.online {
                background-color: rgba(40, 167, 69, 0.15) !important;
                color: #5cb85c !important;
                border: 1px solid rgba(40, 167, 69, 0.3) !important;
            }
            
            .connection-status.offline {
                background-color: rgba(220, 53, 69, 0.15) !important;
                color: #dc3545 !important;
                border: 1px solid rgba(220, 53, 69, 0.3) !important;
            }
            
            .sidebar-version {
                color: #6c8aa0 !important;
                font-size: 11px !important;
                text-align: center !important;
                padding: 15px 0 10px 0 !important;
                border-top: 1px solid rgba(255,255,255,0.05) !important;
                margin: 10px 20px 0 20px !important;
            }
        </style>
    """, unsafe_allow_html=True)