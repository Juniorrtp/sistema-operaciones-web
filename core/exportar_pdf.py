from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from collections import defaultdict
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
    KeepTogether,
)

from reportlab.pdfbase.pdfmetrics import stringWidth

from datetime import datetime
import tempfile
import os
import math


# ============================================================
# IDENTIDAD CORPORATIVA
# ============================================================

EMPRESA = "ROCK TOOLS PERU SAC"
UNIDAD = "JRC - SAN CRISTOBAL"
SISTEMA = "Sistema de Gestión de Operaciones"

# Paleta corporativa
AZUL_OSCURO = HexColor("#17324D")
AZUL = HexColor("#1F5A7A")
AZUL_CLARO = HexColor("#DCEAF2")

GRIS_GRAFITO = HexColor("#263238")
GRIS = HexColor("#607D8B")
GRIS_MEDIO = HexColor("#90A4AE")
GRIS_CLARO = HexColor("#ECEFF1")
GRIS_FONDO = HexColor("#F7F9FA")

BLANCO = colors.white

VERDE = HexColor("#2E7D5B")
VERDE_CLARO = HexColor("#E6F2EC")

AMBAR = HexColor("#C58A17")
AMBAR_CLARO = HexColor("#FFF4D6")

ROJO = HexColor("#B64040")
ROJO_CLARO = HexColor("#F9E5E5")

NEGRO = HexColor("#17202A")


# ============================================================
# UTILIDADES
# ============================================================

def _numero(valor, decimales=0):
    """Formatea números de manera segura."""
    try:
        if valor is None:
            valor = 0

        valor = float(valor)

        if decimales == 0:
            return f"{valor:,.0f}"

        return f"{valor:,.{decimales}f}"

    except (ValueError, TypeError):
        return "0"


def _texto(valor, defecto="SIN DATO"):
    """Convierte cualquier valor a texto seguro."""
    if valor is None:
        return defecto

    texto = str(valor).strip()

    return texto if texto else defecto


def _escapar(texto):
    """Escapa caracteres básicos para Paragraph."""
    texto = _texto(texto)
    return (
        texto
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _porcentaje(valor, total):
    try:
        if float(total) == 0:
            return 0
        return float(valor) / float(total) * 100
    except (ValueError, TypeError):
        return 0


def _safe_float(valor):
    try:
        return float(valor or 0)
    except (ValueError, TypeError):
        return 0.0


# ============================================================
# ESTILOS
# ============================================================

class EstilosPDF:

    @staticmethod
    def get_estilos():

        styles = getSampleStyleSheet()

        styles.add(
            ParagraphStyle(
                name="PortadaEmpresa",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=21,
                alignment=TA_CENTER,
                textColor=AZUL_OSCURO,
                spaceAfter=4,
            )
        )

        styles.add(
            ParagraphStyle(
                name="PortadaUnidad",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=15,
                alignment=TA_CENTER,
                textColor=GRIS,
                spaceAfter=20,
            )
        )

        styles.add(
            ParagraphStyle(
                name="PortadaTitulo",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=29,
                leading=32,
                alignment=TA_CENTER,
                textColor=AZUL_OSCURO,
                spaceAfter=8,
            )
        )

        styles.add(
            ParagraphStyle(
                name="PortadaSubtitulo",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=13,
                leading=17,
                alignment=TA_CENTER,
                textColor=GRIS,
            )
        )

        styles.add(
            ParagraphStyle(
                name="Seccion",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=15,
                leading=18,
                alignment=TA_LEFT,
                textColor=AZUL_OSCURO,
                spaceBefore=9,
                spaceAfter=6,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SubSeccion",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=10.2,
                leading=12.5,
                alignment=TA_LEFT,
                textColor=AZUL,
                spaceBefore=6,
                spaceAfter=4,
            )
        )

        styles.add(
            ParagraphStyle(
                name="NormalOperativo",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                alignment=TA_LEFT,
                textColor=GRIS_GRAFITO,
                spaceAfter=5,
            )
        )

        styles.add(
            ParagraphStyle(
                name="NormalCentro",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                alignment=TA_CENTER,
                textColor=GRIS_GRAFITO,
            )
        )

        styles.add(
            ParagraphStyle(
                name="KPIValor",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=19,
                leading=21,
                alignment=TA_CENTER,
                textColor=AZUL_OSCURO,
            )
        )

        styles.add(
            ParagraphStyle(
                name="KPILabel",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
                alignment=TA_CENTER,
                textColor=GRIS,
            )
        )

        styles.add(
            ParagraphStyle(
                name="TablaHeader",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7.7,
                leading=9.5,
                alignment=TA_CENTER,
                textColor=BLANCO,
            )
        )

        styles.add(
            ParagraphStyle(
                name="TablaCelda",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.7,
                leading=9.5,
                alignment=TA_CENTER,
                textColor=GRIS_GRAFITO,
            )
        )

        styles.add(
            ParagraphStyle(
                name="TablaCeldaIzquierda",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.7,
                leading=9.5,
                alignment=TA_LEFT,
                textColor=GRIS_GRAFITO,
            )
        )

        styles.add(
            ParagraphStyle(
                name="TablaTotal",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                alignment=TA_CENTER,
                textColor=AZUL_OSCURO,
            )
        )

        styles.add(
            ParagraphStyle(
                name="Alerta",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=13,
                textColor=ROJO,
            )
        )

        styles.add(
            ParagraphStyle(
                name="Exito",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=13,
                textColor=VERDE,
            )
        )

        styles.add(
            ParagraphStyle(
                name="Footer",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7,
                leading=9,
                alignment=TA_CENTER,
                textColor=GRIS_MEDIO,
            )
        )

        return styles


# ============================================================
# ENCABEZADO / PIE DE PÁGINA
# ============================================================

def _dibujar_pagina(canvas, doc, desde, hasta):

    canvas.saveState()

    ancho, alto = A4

    # --------------------------------------------------------
    # Barra superior
    # --------------------------------------------------------

    canvas.setFillColor(AZUL_OSCURO)
    canvas.rect(
        0,
        alto - 0.45 * cm,
        ancho,
        0.45 * cm,
        stroke=0,
        fill=1,
    )

    # --------------------------------------------------------
    # Encabezado
    # --------------------------------------------------------

    if doc.page > 1:

        canvas.setFillColor(AZUL_OSCURO)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(
            1.7 * cm,
            alto - 1.15 * cm,
            EMPRESA,
        )

        canvas.setFillColor(GRIS)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawRightString(
            ancho - 1.7 * cm,
            alto - 1.15 * cm,
            f"UNIDAD: {UNIDAD}",
        )

        canvas.setStrokeColor(GRIS_CLARO)
        canvas.setLineWidth(0.5)
        canvas.line(
            1.7 * cm,
            alto - 1.4 * cm,
            ancho - 1.7 * cm,
            alto - 1.4 * cm,
        )

    # --------------------------------------------------------
    # Pie
    # --------------------------------------------------------

    canvas.setStrokeColor(GRIS_CLARO)
    canvas.setLineWidth(0.5)
    canvas.line(
        1.7 * cm,
        1.35 * cm,
        ancho - 1.7 * cm,
        1.35 * cm,
    )

    canvas.setFillColor(GRIS)
    canvas.setFont("Helvetica", 6.8)

    canvas.drawString(
        1.7 * cm,
        0.9 * cm,
        f"{EMPRESA} | {UNIDAD}",
    )

    canvas.drawCentredString(
        ancho / 2,
        0.9 * cm,
        f"Periodo: {desde} al {hasta}",
    )

    canvas.drawRightString(
        ancho - 1.7 * cm,
        0.9 * cm,
        f"Página {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# COMPONENTES VISUALES
# ============================================================

def _titulo_seccion(numero, titulo, styles):

    contenido = [
        Paragraph(
            f'<font color="{AZUL_OSCURO.hexval()}"><b>{numero}</b></font>'
            f'&nbsp;&nbsp;{_escapar(titulo)}',
            styles["Seccion"],
        ),
        HRFlowable(
            width="100%",
            thickness=1,
            color=AZUL_CLARO,
            spaceBefore=0,
            spaceAfter=7,
        ),
    ]

    return contenido


def _kpi_card(valor, etiqueta, styles):

    return Table(
        [
            [
                Paragraph(
                    _escapar(valor),
                    styles["KPIValor"],
                )
            ],
            [
                Paragraph(
                    _escapar(etiqueta.upper()),
                    styles["KPILabel"],
                )
            ],
        ],
        colWidths=[3.0 * cm],
        rowHeights=[0.85 * cm, 0.55 * cm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GRIS_FONDO),
                ("BOX", (0, 0), (-1, -1), 0.7, GRIS_CLARO),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        ),
    )


def _tabla_profesional(
    data,
    col_widths,
    styles,
    header_bg=AZUL_OSCURO,
    total_row=None,
    left_columns=None,
):

    tabla_data = []

    for fila_idx, fila in enumerate(data):

        nueva_fila = []

        for col_idx, valor in enumerate(fila):

            if fila_idx == 0:

                estilo = styles["TablaHeader"]

            elif total_row is not None and fila_idx == total_row:

                estilo = styles["TablaTotal"]

            elif left_columns and col_idx in left_columns:

                estilo = styles["TablaCeldaIzquierda"]

            else:

                estilo = styles["TablaCelda"]

            nueva_fila.append(
                Paragraph(
                    str(valor),
                    estilo,
                )
            )

        tabla_data.append(nueva_fila)

    tabla = Table(
        tabla_data,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="CENTER",
    )

    comandos = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            header_bg,
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            BLANCO,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            GRIS_CLARO,
        ),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [BLANCO, GRIS_FONDO],
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    if total_row is not None:

        comandos.extend(
            [
                (
                    "BACKGROUND",
                    (0, total_row),
                    (-1, total_row),
                    AZUL_CLARO,
                ),
                (
                    "LINEABOVE",
                    (0, total_row),
                    (-1, total_row),
                    1,
                    AZUL,
                ),
            ]
        )

    tabla.setStyle(TableStyle(comandos))

    return tabla


def _mensaje_vacio(texto, styles):

    tabla = Table(
        [
            [
                Paragraph(
                    _escapar(texto),
                    styles["NormalCentro"],
                )
            ]
        ],
        colWidths=[16.5 * cm],
    )

    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GRIS_FONDO),
                ("BOX", (0, 0), (-1, -1), 0.5, GRIS_CLARO),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    return tabla


# ============================================================
# PORTADA
# ============================================================

def _portada(desde, hasta, styles):

    story = []

    story.append(Spacer(1, 2.2 * cm))

    # Identificación
    story.append(
        Paragraph(
            EMPRESA,
            styles["PortadaEmpresa"],
        )
    )

    story.append(
        Paragraph(
            f"UNIDAD DE PRODUCCIÓN<br/><b>{UNIDAD}</b>",
            styles["PortadaUnidad"],
        )
    )

    # Bloque principal
    bloque = Table(
        [
            [
                Paragraph(
                    "REPORTE<br/>GERENCIAL",
                    styles["PortadaTitulo"],
                )
            ]
        ],
        colWidths=[14.5 * cm],
        rowHeights=[3.0 * cm],
    )

    bloque.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GRIS_FONDO),
                ("BOX", (0, 0), (-1, -1), 1.2, AZUL),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )

    story.append(bloque)

    story.append(Spacer(1, 1.0 * cm))

    story.append(
        Paragraph(
            "INDICADORES DE PRODUCCIÓN, CONSUMO,<br/>"
            "RENDIMIENTO, EQUIPOS, OPERADORES E INVENTARIO",
            styles["PortadaSubtitulo"],
        )
    )

    story.append(Spacer(1, 1.4 * cm))

    # Periodo
    periodo = Table(
        [
            [
                Paragraph(
                    "<b>PERIODO DEL INFORME</b>",
                    styles["NormalCentro"],
                )
            ],
            [
                Paragraph(
                    f"<b>{_escapar(desde)}</b>"
                    f"&nbsp;&nbsp;&nbsp;—&nbsp;&nbsp;&nbsp;"
                    f"<b>{_escapar(hasta)}</b>",
                    styles["PortadaSubtitulo"],
                )
            ],
        ],
        colWidths=[10 * cm],
    )

    periodo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
                ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
                ("BACKGROUND", (0, 1), (-1, 1), AZUL_CLARO),
                ("BOX", (0, 0), (-1, -1), 0.8, AZUL),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(periodo)

    story.append(Spacer(1, 3.0 * cm))

    fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")

    story.append(
        Paragraph(
            f"{SISTEMA}<br/>"
            f"Documento generado automáticamente<br/>"
            f"Fecha de emisión: {fecha_generacion}",
            styles["Footer"],
        )
    )

    story.append(PageBreak())

    return story


# ============================================================
# RESUMEN EJECUTIVO
# ============================================================

def _resumen_ejecutivo(resumen, styles):

    story = []

    story.extend(
        _titulo_seccion(
            "01",
            "RESUMEN EJECUTIVO",
            styles,
        )
    )

    metros = _safe_float(
        resumen.get("metros", {}).get("total_metros", 0)
    )

    consumo = _safe_float(
        resumen.get("consumos", {}).get("total_consumo", 0)
    )

    equipos = _safe_float(
        resumen.get("equipos", {}).get("total_equipos", 0)
    )

    operadores = _safe_float(
        resumen.get("operadores", {}).get("total_operadores", 0)
    )

    dias = resumen.get("dias", 0)

    eficiencia = metros / consumo if consumo > 0 else 0

    kpis = [
        _kpi_card(
            _numero(metros),
            "Metros perforados",
            styles,
        ),
        _kpi_card(
            _numero(consumo),
            "Consumos",
            styles,
        ),
        _kpi_card(
            _numero(eficiencia, 2),
            "m / unidad",
            styles,
        ),
        _kpi_card(
            _numero(equipos),
            "Equipos activos",
            styles,
        ),
        _kpi_card(
            _numero(operadores),
            "Operadores",
            styles,
        ),
    ]

    tabla_kpis = Table(
        [kpis],
        colWidths=[
            3.15 * cm,
            3.15 * cm,
            3.15 * cm,
            3.15 * cm,
            3.15 * cm,
        ],
    )

    tabla_kpis.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story.append(tabla_kpis)
    story.append(Spacer(1, 0.45 * cm))

    # Segunda fila: días + interpretación
    resumen_operativo = Table(
        [
            [
                Paragraph(
                    f"<b>{_numero(dias)}</b><br/>"
                    f"<font size='7'>DÍAS DEL PERIODO</font>",
                    styles["NormalCentro"],
                ),
                Paragraph(
                    "El presente informe consolida los principales "
                    "indicadores operativos registrados para la Unidad "
                    "de Producción durante el periodo seleccionado.",
                    styles["NormalOperativo"],
                ),
            ]
        ],
        colWidths=[3.2 * cm, 13.3 * cm],
    )

    resumen_operativo.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), AZUL_CLARO),
                ("BACKGROUND", (1, 0), (1, 0), GRIS_FONDO),
                ("BOX", (0, 0), (-1, -1), 0.5, GRIS_CLARO),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(resumen_operativo)

    return story


# ============================================================
# METROS POR TIPO
# ============================================================

def _metros_por_tipo(metros_tipo, resumen, styles):
    """Gráfico de barras verticales para metros por tipo de perforación"""

    story = []

    story.extend(
        _titulo_seccion(
            "02",
            "PRODUCCIÓN — METROS POR TIPO DE PERFORACIÓN",
            styles,
        )
    )

    if not metros_tipo:
        story.append(
            _mensaje_vacio(
                "No se registraron datos de metros para el periodo seleccionado.",
                styles,
            )
        )
        return story

    total_metros = sum(
        _safe_float(row.get("total_mp", 0))
        for row in metros_tipo
    )

    # Ordenar de mayor a menor
    filas = sorted(
        metros_tipo,
        key=lambda x: _safe_float(x.get("total_mp", 0)),
        reverse=True,
    )

    max_valor = max(
        [_safe_float(row.get("total_mp", 0)) for row in filas],
        default=1
    )

    # ============================================================
    # GRÁFICO DE BARRAS VERTICALES (estilo Streamlit)
    # ============================================================

    # Dimensiones - usando más ancho
    ancho_barra = 1.6 * cm
    espacio_entre_barras = 1.2 * cm
    alto_maximo_grafico = 5.0 * cm

    # Colores para las barras
    colores_barra = [
        HexColor("#1F5A7A"),  # AZUL
        HexColor("#2E7D5B"),  # VERDE
        HexColor("#C58A17"),  # AMBAR
        HexColor("#8E44AD"),  # MORADO
        HexColor("#B64040"),  # ROJO
        HexColor("#1A5276"),  # AZUL OSCURO
    ]

    # Calcular ancho total del gráfico
    total_barras = len(filas)
    ancho_total = (total_barras * ancho_barra) + ((total_barras - 1) * espacio_entre_barras)

    # ============================================================
    # CONSTRUIR EL GRÁFICO USANDO UNA SOLA TABLA
    # ============================================================

    # Fila 1: Valores encima de las barras
    fila_valores = []
    for i, row in enumerate(filas):
        valor = _safe_float(row.get("total_mp", 0))
        fila_valores.append(
            Paragraph(
                f"<font size=7 color='#1F5A7A'><b>{_numero(valor)}</b></font>",
                styles["NormalCentro"],
            )
        )
        if i < len(filas) - 1:
            fila_valores.append(Spacer(espacio_entre_barras, 0))

    # Fila 2: Barras
    fila_barras = []
    for i, row in enumerate(filas):
        valor = _safe_float(row.get("total_mp", 0))
        proporcion = valor / max_valor if max_valor > 0 else 0
        alto_barra = alto_maximo_grafico * proporcion

        color = colores_barra[i % len(colores_barra)]

        barra = Table(
            [
                [
                    Paragraph(
                        f"<font size=6 color='white'><b>{_numero(valor)}</b></font>",
                        styles["NormalCentro"],
                    )
                ]
            ],
            colWidths=[ancho_barra],
            rowHeights=[max(alto_barra, 0.3 * cm)],
        )

        barra.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), color),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("ROUNDEDCORNERS", (0, 0), (-1, -1), 3),
                ]
            )
        )

        fila_barras.append(barra)
        if i < len(filas) - 1:
            fila_barras.append(Spacer(espacio_entre_barras, 0))

    # Fila 3: Etiquetas (tipos) debajo de cada barra
    fila_etiquetas = []
    for i, row in enumerate(filas):
        tipo = _texto(row.get("tipo"), "")
        if len(tipo) > 15:
            tipo = tipo[:13] + "..."

        fila_etiquetas.append(
            Paragraph(
                f"<font size=7>{_escapar(tipo)}</font>",
                styles["NormalCentro"],
            )
        )
        if i < len(filas) - 1:
            fila_etiquetas.append(Spacer(espacio_entre_barras, 0))

    # Combinar todo en una sola tabla
    datos_grafico = [
        fila_valores,
        fila_barras,
        fila_etiquetas,
    ]

    # Calcular anchos de columna
    col_widths = []
    for i in range(total_barras):
        col_widths.append(ancho_barra)
        if i < total_barras - 1:
            col_widths.append(espacio_entre_barras)

    tabla_grafico = Table(datos_grafico, colWidths=col_widths)

    tabla_grafico.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
                ("VALIGN", (0, 1), (-1, 1), "BOTTOM"),
                ("VALIGN", (0, 2), (-1, 2), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    # Centrar el gráfico
    contenedor = Table(
        [[tabla_grafico]],
        colWidths=[16.5 * cm],
    )

    contenedor.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )

    story.append(contenedor)

    story.append(Spacer(1, 0.4 * cm))

    # ============================================================
    # PRODUCCIÓN PROMEDIO DIARIA
    # ============================================================

    dias_periodo = _safe_float(
        resumen.get("dias", 30) if hasattr(resumen, "get") else 30
    )

    promedio_diario = total_metros / dias_periodo if dias_periodo > 0 else 0

    resumen_tabla = Table(
        [
            [
                Paragraph(
                    f"<b>Total metros:</b> {_numero(total_metros)} m",
                    styles["NormalOperativo"],
                ),
                Paragraph(
                    f"<b>Promedio diario:</b> {_numero(promedio_diario, 1)} m/día",
                    styles["NormalOperativo"],
                ),
                Paragraph(
                    f"<b>Días:</b> {_numero(dias_periodo)}",
                    styles["NormalOperativo"],
                ),
            ]
        ],
        colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm],
    )

    resumen_tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GRIS_FONDO),
                ("BOX", (0, 0), (-1, -1), 0.5, GRIS_CLARO),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ROUNDEDCORNERS", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(resumen_tabla)

    return story

def _rendimiento_equipos(rendimiento_equipos, styles):
    """Rendimiento por equipo - Clasificado por tipo, 2 equipos por fila, ancho adaptado"""

    story = []

    story.extend(
        _titulo_seccion(
            "05",
            "RENDIMIENTO OPERATIVO POR EQUIPO",
            styles,
        )
    )

    story.append(
        Paragraph(
            "Metros por unidad consumida. Equipos ordenados de mayor a menor rendimiento por tipo de perforación.",
            styles["NormalOperativo"],
        )
    )

    if not rendimiento_equipos:
        story.append(
            _mensaje_vacio(
                "No se encontraron datos de rendimiento por equipo.",
                styles,
            )
        )
        return story

    # ============================================================
    # 1. AGRUPAR POR TIPO DE PERFORACIÓN
    # ============================================================

    equipos_por_tipo = defaultdict(list)

    for equipo, familias in rendimiento_equipos.items():
        if not isinstance(familias, dict):
            continue

        # 🔥 OBTENER TIPO DESDE EL NOMBRE DEL EQUIPO O FAMILIAS
        tipo = "GENERAL"
        
        # Intentar obtener tipo desde el equipo (si tiene guión o patrón)
        if "-" in equipo:
            partes = equipo.split("-")
            if len(partes) > 0:
                tipo_candidato = partes[0].strip().upper()
                if tipo_candidato in ["JUMBO", "SIMBA", "SCOOP", "FRONTONERO", "TALADROS", "PERFORADORA"]:
                    tipo = tipo_candidato
        elif " " in equipo:
            partes = equipo.split(" ")
            if len(partes) > 0:
                tipo_candidato = partes[0].strip().upper()
                if tipo_candidato in ["JUMBO", "SIMBA", "SCOOP", "FRONTONERO", "TALADROS", "PERFORADORA"]:
                    tipo = tipo_candidato

        total = familias.get("TOTAL", {})
        if isinstance(total, dict):
            rendimiento = total.get("rendimiento", 0)
            metros = total.get("metros", 0)

            detalles = []
            for familia, datos_familia in familias.items():
                if familia == "TOTAL":
                    continue
                if not isinstance(datos_familia, dict):
                    continue
                consumo = datos_familia.get("consumo", 0)
                rend = datos_familia.get("rendimiento", 0)
                if consumo > 0 or rend > 0:
                    detalles.append({
                        "familia": familia,
                        "consumo": consumo,
                        "rendimiento": rend
                    })

            equipos_por_tipo[tipo].append({
                "equipo": equipo,
                "rendimiento": rendimiento,
                "metros": metros,
                "detalles": detalles
            })

    # ============================================================
    # 2. GENERAR SECCIONES POR TIPO
    # ============================================================

    for tipo, equipos in sorted(equipos_por_tipo.items()):

        equipos_ordenados = sorted(
            equipos,
            key=lambda x: x["rendimiento"],
            reverse=True
        )

        if not equipos_ordenados:
            continue

        story.append(
            Paragraph(
                f"▌ {_escapar(tipo)}",
                styles["SubSeccion"],
            )
        )

        # ============================================================
        # 3. CREAR FILAS CON 2 EQUIPOS
        # ============================================================

        # Ancho adaptado al contenido (máximo 7 cm por tabla)
        ancho_tabla = 6.5 * cm
        espacio_entre_tablas = 1.0 * cm

        for i in range(0, len(equipos_ordenados), 2):
            grupo = equipos_ordenados[i:i+2]

            # Determinar si hay 1 o 2 equipos en esta fila
            num_equipos = len(grupo)

            # Calcular anchos de columna dinámicamente
            if num_equipos == 2:
                ancho_col1 = ancho_tabla
                ancho_col2 = ancho_tabla
                ancho_total = ancho_col1 + ancho_col2 + espacio_entre_tablas
            else:
                ancho_col1 = ancho_tabla
                ancho_col2 = 0.1 * cm
                ancho_total = ancho_col1 + ancho_col2

            # Calcular espacio en blanco para centrar
            ancho_hoja = 16.5 * cm
            espacio_blanco = (ancho_hoja - ancho_total) / 2

            fila_equipos = []

            for idx, eq in enumerate(grupo):
                nombre_equipo = eq["equipo"]
                rendimiento_total = eq["rendimiento"]
                metros_total = eq["metros"]
                detalles = eq["detalles"]

                if rendimiento_total >= 5:
                    color_rend = VERDE
                elif rendimiento_total >= 3:
                    color_rend = AMBAR
                else:
                    color_rend = ROJO

                # ============================================================
                # TABLA DEL EQUIPO (COMPACTA)
                # ============================================================

                # Cabecera: Nombre del equipo
                header_data = [[
                    Paragraph(
                        f"<b>{_escapar(nombre_equipo)}</b>",
                        styles["NormalOperativo"],
                    ),
                ]]

                header_table = Table(
                    header_data,
                    colWidths=[ancho_tabla],
                )

                header_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), AZUL_CLARO),
                            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                            ("LEFTPADDING", (0, 0), (-1, 0), 4),
                            ("RIGHTPADDING", (0, 0), (-1, 0), 4),
                            ("TOPPADDING", (0, 0), (-1, 0), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
                        ]
                    )
                )

                # Métricas: Metros y Rendimiento
                metricas_data = [[
                    Paragraph(
                        f"<font size=7 color='#5D6D7E'>Metros:</font> "
                        f"<font size=7><b>{_numero(metros_total)}</b></font>",
                        styles["NormalCentro"],
                    ),
                    Paragraph(
                        f"<font size=7 color='#5D6D7E'>Rend:</font> "
                        f"<font size=7 color='{color_rend.hexval()}'><b>{_numero(rendimiento_total, 2)}</b></font>",
                        styles["NormalCentro"],
                    ),
                ]]

                metricas_table = Table(
                    metricas_data,
                    colWidths=[ancho_tabla * 0.45, ancho_tabla * 0.45],
                )

                metricas_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), GRIS_FONDO),
                            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                            ("LEFTPADDING", (0, 0), (-1, 0), 2),
                            ("RIGHTPADDING", (0, 0), (-1, 0), 2),
                            ("TOPPADDING", (0, 0), (-1, 0), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                        ]
                    )
                )

                # ============================================================
                # DETALLE DE FAMILIAS
                # ============================================================

                if detalles:
                    detalle_data = [
                        ["FAMILIA", "CONS", "REND"]
                    ]

                    for det in detalles[:4]:
                        detalle_data.append([
                            _escapar(det["familia"][:10]),
                            _numero(det["consumo"]),
                            _numero(det["rendimiento"], 1)
                        ])

                    detalle_table = Table(
                        detalle_data,
                        colWidths=[ancho_tabla * 0.45, ancho_tabla * 0.25, ancho_tabla * 0.30],
                    )

                    detalle_table.setStyle(
                        TableStyle(
                            [
                                # Encabezado
                                ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
                                ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, 0), 6.5),
                                # Celdas: fondo blanco sin alternar
                                ("BACKGROUND", (0, 1), (-1, -1), BLANCO),
                                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                                ("FONTSIZE", (0, 1), (-1, -1), 6.5),
                                ("ALIGN", (1, 1), (2, -1), "CENTER"),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("GRID", (0, 0), (-1, -1), 0.3, GRIS_CLARO),
                                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                            ]
                        )
                    )
                else:
                    detalle_table = Paragraph(
                        "<font size=6 color='#90A4AE'><i>Sin detalles</i></font>",
                        styles["NormalCentro"],
                    )

                # ============================================================
                # UNIR TODO EN UNA TABLA
                # ============================================================

                equipo_table = Table(
                    [
                        [header_table],
                        [metricas_table],
                        [detalle_table],
                    ],
                    colWidths=[ancho_tabla],
                )

                equipo_table.setStyle(
                    TableStyle(
                        [
                            ("BOX", (0, 0), (-1, -1), 0.5, GRIS_CLARO),
                            ("ROUNDEDCORNERS", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ]
                    )
                )

                fila_equipos.append(equipo_table)

            # ============================================================
            # CREAR FILA CENTRADA CON LOS EQUIPOS
            # ============================================================

            if num_equipos == 2:
                # Dos tablas: una al lado de la otra con espacio
                fila_table = Table(
                    [fila_equipos],
                    colWidths=[ancho_col1, ancho_col2],
                )

                fila_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, 0), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "CENTER"),
                            ("ALIGN", (1, 0), (1, 0), "CENTER"),
                            ("LEFTPADDING", (0, 0), (-1, 0), 0),
                            ("RIGHTPADDING", (0, 0), (-1, 0), 0),
                        ]
                    )
                )

                # Centrar la fila en la página
                contenedor = Table(
                    [[fila_table]],
                    colWidths=[16.5 * cm],
                )

                contenedor.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )

                story.append(contenedor)

            else:
                # Una sola tabla: centrada
                contenedor = Table(
                    [[fila_equipos[0]]],
                    colWidths=[16.5 * cm],
                )

                contenedor.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )

                story.append(contenedor)

            story.append(Spacer(1, 0.15 * cm))

        story.append(Spacer(1, 0.2 * cm))

    return story

# ============================================================
# TOP EQUIPOS (Compacto)
# ============================================================

def _top_equipos(top_equipos, styles):

    story = []

    story.extend(
        _titulo_seccion(
            "04",
            "PRODUCTIVIDAD — TOP 3 EQUIPOS POR TIPO",
            styles,
        )
    )

    if not top_equipos:

        story.append(
            _mensaje_vacio(
                "No se encontraron registros de equipos para el periodo.",
                styles,
            )
        )

        return story

    # ============================================================
    # ESTILOS
    # ============================================================

    estilo_tipo = ParagraphStyle(
        "TopEquiposTipo",
        parent=styles["SubSeccion"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=10,
        textColor=AZUL_OSCURO,
        spaceBefore=3,
        spaceAfter=5,
    )

    estilo_equipo = ParagraphStyle(
        "TopEquiposEquipo",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=9,
        textColor=NEGRO,
        spaceAfter=0,
        spaceBefore=0,
    )

    estilo_posicion = ParagraphStyle(
        "TopEquiposPosicion",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=9,
        alignment=1,
        textColor=AZUL_OSCURO,
    )

    estilo_metros = ParagraphStyle(
        "TopEquiposMetros",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=9,
        alignment=2,
        textColor=AZUL_OSCURO,
    )

    # ============================================================
    # PROCESAR CADA TIPO
    # ============================================================

    for tipo, equipos in top_equipos.items():

        if not equipos:
            continue

        # --------------------------------------------------------
        # Ordenar por metros
        # --------------------------------------------------------

        equipos_ordenados = sorted(
            equipos,
            key=lambda x: _safe_float(
                x.get("total_mp", 0)
            ),
            reverse=True,
        )

        # --------------------------------------------------------
        # Solo los 3 primeros
        # --------------------------------------------------------

        top_3 = equipos_ordenados[:3]

        if not top_3:
            continue

        # --------------------------------------------------------
        # El máximo sirve como referencia para las barras
        # --------------------------------------------------------

        max_metros = max(
            _safe_float(
                equipo.get("total_mp", 0)
            )
            for equipo in top_3
        )

        # ========================================================
        # TÍTULO DEL TIPO
        # ========================================================

        story.append(
            Paragraph(
                f"▌ {_escapar(tipo)}",
                estilo_tipo,
            )
        )

        # ========================================================
        # ENCABEZADO LIGERO
        # ========================================================

        encabezado = Table(
            [
                [
                    Paragraph(
                        "RANKING",
                        estilo_posicion,
                    ),
                    Paragraph(
                        "EQUIPO",
                        estilo_equipo,
                    ),
                    Paragraph(
                        "PRODUCTIVIDAD",
                        estilo_equipo,
                    ),
                    Paragraph(
                        "METROS",
                        estilo_metros,
                    ),
                ]
            ],
            colWidths=[
                1.0 * cm,
                4.2 * cm,
                8.0 * cm,
                2.3 * cm,
            ],
            hAlign="CENTER",
        )

        encabezado.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        GRIS_FONDO,
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (0, -1),
                        "CENTER",
                    ),
                    (
                        "ALIGN",
                        (3, 0),
                        (3, -1),
                        "RIGHT",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3,
                    ),
                ]
            )
        )

        story.append(encabezado)

        # ========================================================
        # RANKING TOP 3
        # ========================================================

        for posicion, equipo in enumerate(top_3, start=1):

            nombre_equipo = _texto(
                equipo.get("equipo"),
                "SIN EQUIPO",
            )

            metros = _safe_float(
                equipo.get("total_mp", 0)
            )

            # ----------------------------------------------------
            # Porcentaje relativo al primero
            # ----------------------------------------------------

            if max_metros > 0:
                proporcion = (
                    metros / max_metros
                )
            else:
                proporcion = 0

            # ----------------------------------------------------
            # Barra gráfica
            # ----------------------------------------------------

            ancho_barra_max = 7.2 * cm

            ancho_barra = (
                ancho_barra_max
                * proporcion
            )

            ancho_barra = max(
                ancho_barra,
                0.05 * cm,
            )

            barra = Table(
                [
                    [
                        ""
                    ]
                ],
                colWidths=[
                    ancho_barra
                ],
                rowHeights=[
                    0.22 * cm
                ],
            )

            barra.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, -1),
                            AZUL,
                        ),
                        (
                            "BOX",
                            (0, 0),
                            (-1, -1),
                            0,
                            AZUL,
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),
                    ]
                )
            )

            # ----------------------------------------------------
            # Espacio restante para completar la barra
            # ----------------------------------------------------

            espacio_restante = (
                ancho_barra_max
                - ancho_barra
            )

            if espacio_restante < 0:
                espacio_restante = 0

            grafico = Table(
                [
                    [
                        barra,
                        ""
                    ]
                ],
                colWidths=[
                    ancho_barra,
                    espacio_restante,
                ],
                rowHeights=[
                    0.35 * cm
                ],
            )

            grafico.setStyle(
                TableStyle(
                    [
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),
                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),
                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),
                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            0,
                        ),
                    ]
                )
            )

            # ----------------------------------------------------
            # Fila completa
            # ----------------------------------------------------

            fila = Table(
                [
                    [
                        Paragraph(
                            f"{posicion}°",
                            estilo_posicion,
                        ),
                        Paragraph(
                            _escapar(nombre_equipo),
                            estilo_equipo,
                        ),
                        grafico,
                        Paragraph(
                            _numero(metros),
                            estilo_metros,
                        ),
                    ]
                ],
                colWidths=[
                    1.0 * cm,
                    4.2 * cm,
                    8.0 * cm,
                    2.3 * cm,
                ],
                hAlign="CENTER",
            )

            fila.setStyle(
                TableStyle(
                    [
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),

                        (
                            "ALIGN",
                            (0, 0),
                            (0, -1),
                            "CENTER",
                        ),

                        (
                            "ALIGN",
                            (3, 0),
                            (3, -1),
                            "RIGHT",
                        ),

                        (
                            "LINEBELOW",
                            (0, 0),
                            (-1, -1),
                            0.25,
                            GRIS_CLARO,
                        ),

                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),

                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),

                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),

                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            4,
                        ),
                    ]
                )
            )

            story.append(fila)

        story.append(
            Spacer(1, 0.25 * cm)
        )

    return story

# ============================================================
# RENDIMIENTO POR EQUIPO (Solo detalles)
# ============================================================

def _rendimiento_equipos(rendimiento_equipos, styles):
    """Rendimiento por equipo - Clasificado por tipo, 2 equipos por fila, ancho adaptado"""

    story = []

    story.extend(
        _titulo_seccion(
            "05",
            "RENDIMIENTO OPERATIVO POR EQUIPO",
            styles,
        )
    )

    story.append(
        Paragraph(
            "Metros por unidad consumida. Equipos ordenados de mayor a menor rendimiento por tipo de perforación.",
            styles["NormalOperativo"],
        )
    )

    if not rendimiento_equipos:
        story.append(
            _mensaje_vacio(
                "No se encontraron datos de rendimiento por equipo.",
                styles,
            )
        )
        return story

    # ============================================================
    # 1. AGRUPAR POR TIPO DE PERFORACIÓN
    # ============================================================

    equipos_por_tipo = defaultdict(list)

    for equipo, familias in rendimiento_equipos.items():
        if not isinstance(familias, dict):
            continue

        # 🔥 OBTENER TIPO DESDE EL NOMBRE DEL EQUIPO O FAMILIAS
        tipo = "GENERAL"
        
        # Intentar obtener tipo desde el equipo (si tiene guión o patrón)
        if "-" in equipo:
            partes = equipo.split("-")
            if len(partes) > 0:
                tipo_candidato = partes[0].strip().upper()
                if tipo_candidato in ["JUMBO", "SIMBA", "SCOOP", "FRONTONERO", "TALADROS", "PERFORADORA"]:
                    tipo = tipo_candidato
        elif " " in equipo:
            partes = equipo.split(" ")
            if len(partes) > 0:
                tipo_candidato = partes[0].strip().upper()
                if tipo_candidato in ["JUMBO", "SIMBA", "SCOOP", "FRONTONERO", "TALADROS", "PERFORADORA"]:
                    tipo = tipo_candidato

        total = familias.get("TOTAL", {})
        if isinstance(total, dict):
            rendimiento = total.get("rendimiento", 0)
            metros = total.get("metros", 0)

            detalles = []
            for familia, datos_familia in familias.items():
                if familia == "TOTAL":
                    continue
                if not isinstance(datos_familia, dict):
                    continue
                consumo = datos_familia.get("consumo", 0)
                rend = datos_familia.get("rendimiento", 0)
                if consumo > 0 or rend > 0:
                    detalles.append({
                        "familia": familia,
                        "consumo": consumo,
                        "rendimiento": rend
                    })

            equipos_por_tipo[tipo].append({
                "equipo": equipo,
                "rendimiento": rendimiento,
                "metros": metros,
                "detalles": detalles
            })

    # ============================================================
    # 2. GENERAR SECCIONES POR TIPO
    # ============================================================

    for tipo, equipos in sorted(equipos_por_tipo.items()):

        equipos_ordenados = sorted(
            equipos,
            key=lambda x: x["rendimiento"],
            reverse=True
        )

        if not equipos_ordenados:
            continue

        story.append(
            Paragraph(
                f"▌ {_escapar(tipo)}",
                styles["SubSeccion"],
            )
        )

        # ============================================================
        # 3. CREAR FILAS CON 2 EQUIPOS
        # ============================================================

        # Ancho adaptado al contenido (máximo 7 cm por tabla)
        ancho_tabla = 6.5 * cm
        espacio_entre_tablas = 1.0 * cm

        for i in range(0, len(equipos_ordenados), 2):
            grupo = equipos_ordenados[i:i+2]

            # Determinar si hay 1 o 2 equipos en esta fila
            num_equipos = len(grupo)

            # Calcular anchos de columna dinámicamente
            if num_equipos == 2:
                ancho_col1 = ancho_tabla
                ancho_col2 = ancho_tabla
                ancho_total = ancho_col1 + ancho_col2 + espacio_entre_tablas
            else:
                ancho_col1 = ancho_tabla
                ancho_col2 = 0.1 * cm
                ancho_total = ancho_col1 + ancho_col2

            # Calcular espacio en blanco para centrar
            ancho_hoja = 16.5 * cm
            espacio_blanco = (ancho_hoja - ancho_total) / 2

            fila_equipos = []

            for idx, eq in enumerate(grupo):
                nombre_equipo = eq["equipo"]
                rendimiento_total = eq["rendimiento"]
                metros_total = eq["metros"]
                detalles = eq["detalles"]

                if rendimiento_total >= 5:
                    color_rend = VERDE
                elif rendimiento_total >= 3:
                    color_rend = AMBAR
                else:
                    color_rend = ROJO

                # ============================================================
                # TABLA DEL EQUIPO (COMPACTA)
                # ============================================================

                # Cabecera: Nombre del equipo
                header_data = [[
                    Paragraph(
                        f"<b>{_escapar(nombre_equipo)}</b>",
                        styles["NormalOperativo"],
                    ),
                ]]

                header_table = Table(
                    header_data,
                    colWidths=[ancho_tabla],
                )

                header_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), AZUL_CLARO),
                            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                            ("LEFTPADDING", (0, 0), (-1, 0), 4),
                            ("RIGHTPADDING", (0, 0), (-1, 0), 4),
                            ("TOPPADDING", (0, 0), (-1, 0), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
                        ]
                    )
                )

                # Métricas: Metros y Rendimiento
                metricas_data = [[
                    Paragraph(
                        f"<font size=7 color='#5D6D7E'>Metros:</font> "
                        f"<font size=7><b>{_numero(metros_total)}</b></font>",
                        styles["NormalCentro"],
                    ),
                    Paragraph(
                        f"<font size=7 color='#5D6D7E'>Rend:</font> "
                        f"<font size=7 color='{color_rend.hexval()}'><b>{_numero(rendimiento_total, 2)}</b></font>",
                        styles["NormalCentro"],
                    ),
                ]]

                metricas_table = Table(
                    metricas_data,
                    colWidths=[ancho_tabla * 0.45, ancho_tabla * 0.45],
                )

                metricas_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), GRIS_FONDO),
                            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                            ("LEFTPADDING", (0, 0), (-1, 0), 2),
                            ("RIGHTPADDING", (0, 0), (-1, 0), 2),
                            ("TOPPADDING", (0, 0), (-1, 0), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                        ]
                    )
                )

                # ============================================================
                # DETALLE DE FAMILIAS
                # ============================================================

                if detalles:
                    detalle_data = [
                        ["FAMILIA", "CONS", "REND"]
                    ]

                    for det in detalles[:4]:
                        detalle_data.append([
                            _escapar(det["familia"][:10]),
                            _numero(det["consumo"]),
                            _numero(det["rendimiento"], 1)
                        ])

                    detalle_table = Table(
                        detalle_data,
                        colWidths=[ancho_tabla * 0.45, ancho_tabla * 0.25, ancho_tabla * 0.30],
                    )

                    detalle_table.setStyle(
                        TableStyle(
                            [
                                # Encabezado
                                ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
                                ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
                                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, 0), 6.5),
                                # Celdas: fondo blanco sin alternar
                                ("BACKGROUND", (0, 1), (-1, -1), BLANCO),
                                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                                ("FONTSIZE", (0, 1), (-1, -1), 6.5),
                                ("ALIGN", (1, 1), (2, -1), "CENTER"),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("GRID", (0, 0), (-1, -1), 0.3, GRIS_CLARO),
                                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                            ]
                        )
                    )
                else:
                    detalle_table = Paragraph(
                        "<font size=6 color='#90A4AE'><i>Sin detalles</i></font>",
                        styles["NormalCentro"],
                    )

                # ============================================================
                # UNIR TODO EN UNA TABLA
                # ============================================================

                equipo_table = Table(
                    [
                        [header_table],
                        [metricas_table],
                        [detalle_table],
                    ],
                    colWidths=[ancho_tabla],
                )

                equipo_table.setStyle(
                    TableStyle(
                        [
                            ("BOX", (0, 0), (-1, -1), 0.5, GRIS_CLARO),
                            ("ROUNDEDCORNERS", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ]
                    )
                )

                fila_equipos.append(equipo_table)

            # ============================================================
            # CREAR FILA CENTRADA CON LOS EQUIPOS
            # ============================================================

            if num_equipos == 2:
                # Dos tablas: una al lado de la otra con espacio
                fila_table = Table(
                    [fila_equipos],
                    colWidths=[ancho_col1, ancho_col2],
                )

                fila_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, 0), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "CENTER"),
                            ("ALIGN", (1, 0), (1, 0), "CENTER"),
                            ("LEFTPADDING", (0, 0), (-1, 0), 0),
                            ("RIGHTPADDING", (0, 0), (-1, 0), 0),
                        ]
                    )
                )

                # Centrar la fila en la página
                contenedor = Table(
                    [[fila_table]],
                    colWidths=[16.5 * cm],
                )

                contenedor.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )

                story.append(contenedor)

            else:
                # Una sola tabla: centrada
                contenedor = Table(
                    [[fila_equipos[0]]],
                    colWidths=[16.5 * cm],
                )

                contenedor.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )

                story.append(contenedor)

            story.append(Spacer(1, 0.15 * cm))

        story.append(Spacer(1, 0.2 * cm))

    return story

# ===========================================================
# OPERADORES / BROCAS (Compacto)
# ============================================================

def _operadores_brocas(operadores, styles):

    story = []

    story.extend(
        _titulo_seccion(
            "06",
            "RENDIMIENTO DE BROCAS POR OPERADOR",
            styles,
        )
    )

    story.append(
        Paragraph(
            "Resultados organizados por tipo de perforación y guardia.",
            styles["NormalOperativo"],
        )
    )

    if not operadores:

        story.append(
            _mensaje_vacio(
                "No se encontraron registros de rendimiento de brocas por operador.",
                styles,
            )
        )

        return story

    for tipo, guardias in operadores.items():

        if not isinstance(guardias, dict):
            continue

        story.append(
            Paragraph(
                f"▌ {_escapar(tipo)}",
                styles["SubSeccion"],
            )
        )

        for guardia, ops in guardias.items():

            if not ops:
                continue            
                story.append(
                Paragraph(
                    f"Guardia: <b>{_escapar(guardia)}</b>",
                    styles["NormalOperativo"],
                )
            )

            # Tabla compacta: solo Operador y Rendimiento
            datos = [
                ["OPERADOR", "BROCAS", "METROS", "RENDIMIENTO"]
            ]

            filas = sorted(
                ops,
                key=lambda x: _safe_float(x.get("rendimiento", 0)),
                reverse=True,
            )

            for operador in filas:
                datos.append([
                    _escapar(_texto(operador.get("operador"), "SIN OPERADOR")),
                    _numero(operador.get("brocas", 0)),
                    _numero(operador.get("metros", 0)),
                    _numero(operador.get("rendimiento", 0), 2),
                ])

            tabla = _tabla_profesional(
                datos,
                [5.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm],
                styles,
                header_bg=AZUL,
                left_columns=[0],
            )

            story.append(tabla)
            story.append(Spacer(1, 0.2 * cm))

    return story


# ============================================================
# STOCK CRÍTICO
# ============================================================

def _stock_critico(stock_critico, styles):

    story = []

    story.extend(
        _titulo_seccion(
            "07",
            "CONTROL DE INVENTARIO — STOCK CRÍTICO",
            styles,
        )
    )

    story.append(
        Paragraph(
            "Productos cuyo stock se encuentra dentro del umbral crítico "
            "configurado para el reporte.",
            styles["NormalOperativo"],
        )
    )

    if not stock_critico:

        tabla = Table(
            [
                [
                    Paragraph(
                        "SIN ALERTAS DE STOCK CRÍTICO",
                        styles["Exito"],
                    )
                ]
            ],
            colWidths=[16.5 * cm],
        )

        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), VERDE_CLARO),
                    ("BOX", (0, 0), (-1, -1), 0.7, VERDE),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )

        story.append(tabla)

        return story

    filas = sorted(
        stock_critico,
        key=lambda x: _safe_float(x.get("stock", 0)),
    )

    datos = [
        [
            "CÓDIGO",
            "DESCRIPCIÓN",
            "STOCK",
            "NIVEL",
        ]
    ]

    for row in filas:

        stock = _safe_float(row.get("stock", 0))

        if stock <= 2:
            nivel = "CRÍTICO"
        elif stock <= 5:
            nivel = "ALTO"
        else:
            nivel = "ATENCIÓN"

        datos.append(
            [
                _escapar(
                    _texto(
                        row.get("codigo"),
                        "SIN CÓDIGO",
                    )
                ),
                _escapar(
                    _texto(
                        row.get("descripcion"),
                        "SIN DESCRIPCIÓN",
                    )
                ),
                _numero(stock),
                nivel,
            ]
        )

    tabla = _tabla_profesional(
        datos,
        [3.0 * cm, 8.5 * cm, 2.0 * cm, 3.0 * cm],
        styles,
        header_bg=AZUL_OSCURO,
        left_columns=[0, 1],
    )

    # Pintar niveles
    comandos = []

    for fila in range(1, len(datos)):

        nivel = datos[fila][3]

        if nivel == "CRÍTICO":

            comandos.append(
                (
                    "BACKGROUND",
                    (3, fila),
                    (3, fila),
                    ROJO_CLARO,
                )
            )

        elif nivel == "ALTO":

            comandos.append(
                (
                    "BACKGROUND",
                    (3, fila),
                    (3, fila),
                    AMBAR_CLARO,
                )
            )

    tabla.setStyle(TableStyle(comandos))

    story.append(tabla)

    story.append(Spacer(1, 0.3 * cm))

    story.append(
        Paragraph(
            f"<b>Productos identificados:</b> {len(filas)}",
            styles["Alerta"],
        )
    )

    return story


# ============================================================
# CONCLUSIONES OPERATIVAS
# ============================================================

def _conclusiones(
    resumen,
    metros_tipo,
    consumo_familia,
    rendimiento_equipos,
    stock_critico,
    styles,
):

    story = []

    story.extend(
        _titulo_seccion(
            "08",
            "OBSERVACIONES Y PUNTOS DE ATENCIÓN",
            styles,
        )
    )

    observaciones = []

    # --------------------------------------------------------
    # Producción
    # --------------------------------------------------------

    if metros_tipo:

        mayor_tipo = max(
            metros_tipo,
            key=lambda x: _safe_float(x.get("total_mp", 0)),
        )

        tipo = _texto(
            mayor_tipo.get("tipo"),
            "SIN TIPO",
        )

        metros = _safe_float(
            mayor_tipo.get("total_mp", 0)
        )

        total = sum(
            _safe_float(x.get("total_mp", 0))
            for x in metros_tipo
        )

        participacion = _porcentaje(metros, total)

        observaciones.append(
            (
                "PRODUCCIÓN",
                f"El tipo de perforación con mayor participación "
                f"en la producción registrada es <b>{_escapar(tipo)}</b>, "
                f"con {_numero(metros)} m, equivalente al "
                f"{participacion:.1f}% del total.",
                AZUL_CLARO,
            )
        )

    # --------------------------------------------------------
    # Consumo
    # --------------------------------------------------------

    if consumo_familia:

        mayor_consumo = max(
            consumo_familia,
            key=lambda x: _safe_float(x.get("total_consumo", 0)),
        )

        familia = _texto(
            mayor_consumo.get("familia"),
            "SIN FAMILIA",
        )

        consumo = _safe_float(
            mayor_consumo.get("total_consumo", 0)
        )

        total_consumo = sum(
            _safe_float(x.get("total_consumo", 0))
            for x in consumo_familia
        )

        participacion = _porcentaje(
            consumo,
            total_consumo,
        )

        observaciones.append(
            (
                "CONSUMO",
                f"La familia <b>{_escapar(familia)}</b> concentra "
                f"el mayor consumo registrado, con {_numero(consumo)} "
                f"unidades ({participacion:.1f}% del total).",
                VERDE_CLARO,
            )
        )

    # --------------------------------------------------------
    # Equipo con mejor rendimiento
    # --------------------------------------------------------

    if rendimiento_equipos:

        ranking = []

        for equipo, familias in rendimiento_equipos.items():

            if not isinstance(familias, dict):
                continue

            total = familias.get("TOTAL", {})

            if isinstance(total, dict):

                ranking.append(
                    (
                        equipo,
                        _safe_float(
                            total.get("rendimiento", 0)
                        ),
                    )
                )

        if ranking:

            ranking.sort(
                key=lambda x: x[1],
                reverse=True,
            )

            mejor_equipo, mejor_rendimiento = ranking[0]

            observaciones.append(
                (
                    "PRODUCTIVIDAD",
                    f"El equipo con mayor rendimiento total registrado "
                    f"es <b>{_escapar(mejor_equipo)}</b>, con "
                    f"{_numero(mejor_rendimiento, 2)} m/unidad.",
                    AZUL_CLARO,
                )
            )

    # --------------------------------------------------------
    # Stock
    # --------------------------------------------------------

    if stock_critico:

        cantidad = len(stock_critico)

        observaciones.append(
            (
                "INVENTARIO",
                f"Se identificaron <b>{cantidad}</b> productos dentro "
                f"del stock crítico. Se recomienda priorizar su revisión "
                f"para evitar impactos sobre la continuidad operativa.",
                AMBAR_CLARO,
            )
        )

    else:

        observaciones.append(
            (
                "INVENTARIO",
                "No se identificaron productos dentro del stock crítico "
                "al momento de generar el reporte.",
                VERDE_CLARO,
            )
        )

    # --------------------------------------------------------
    # Si no existe información
    # --------------------------------------------------------

    if not observaciones:

        story.append(
            _mensaje_vacio(
                "No fue posible generar observaciones con los datos disponibles.",
                styles,
            )
        )

        return story

    for titulo, texto, fondo in observaciones:

        tabla = Table(
            [
                [
                    Paragraph(
                        f"<b>{_escapar(titulo)}</b>",
                        styles["NormalOperativo"],
                    ),
                    Paragraph(
                        texto,
                        styles["NormalOperativo"],
                    ),
                ]
            ],
            colWidths=[3.2 * cm, 13.3 * cm],
        )

        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), fondo),
                    ("BACKGROUND", (1, 0), (1, 0), BLANCO),
                    ("BOX", (0, 0), (-1, -1), 0.5, GRIS_CLARO),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )

        story.append(tabla)
        story.append(Spacer(1, 0.18 * cm))

    return story


# ============================================================
# GENERADOR PRINCIPAL
# ============================================================

def generar_reporte_pdf(
    desde,
    hasta,
    resumen,
    metros_tipo,
    consumo_familia,
    top_equipos,
    rendimiento_equipos,
    operadores,
    stock_critico,
):
    """
    Genera el Reporte Operativo Corporativo de
    ROCK TOOLS PERU SAC - JRC SAN CRISTOBAL.

    Mantiene la misma firma utilizada por la página Streamlit.
    """

    styles = EstilosPDF.get_estilos()

    # --------------------------------------------------------
    # Archivo temporal
    # --------------------------------------------------------

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf",
    ) as tmp:

        pdf_path = tmp.name

    # --------------------------------------------------------
    # Documento
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        topMargin=1.65 * cm,
        bottomMargin=1.55 * cm,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        title=f"Reporte Operativo - {EMPRESA}",
        author=EMPRESA,
        subject=f"Unidad de Producción {UNIDAD}",
    )

    story = []

    # --------------------------------------------------------
    # PORTADA
    # --------------------------------------------------------

    story.extend(
        _portada(
            desde,
            hasta,
            styles,
        )
    )

    # --------------------------------------------------------
    # 01 - RESUMEN
    # --------------------------------------------------------

    story.extend(
        _resumen_ejecutivo(
            resumen,
            styles,
        )
    )

    # --------------------------------------------------------
    # 02 - PRODUCCIÓN
    # --------------------------------------------------------

    story.extend(
        _metros_por_tipo(
            metros_tipo,
            resumen,
            styles,
        )
    )

    story.append(Spacer(1, 0.3 * cm))

    # --------------------------------------------------------
    # 03 - CONSUMO
    # --------------------------------------------------------

    story.extend(
        consumo_familia(
            consumo_familia,
            styles,
        )
    )

    # --------------------------------------------------------
    # 04 - TOP EQUIPOS
    # --------------------------------------------------------

    story.extend(
        _top_equipos(
            top_equipos,
            styles,
        )
    )

    # --------------------------------------------------------
    # 05 - RENDIMIENTO EQUIPOS
    # --------------------------------------------------------

    story.extend(
        _rendimiento_equipos(
            rendimiento_equipos,
            styles,
        )
    )

    # --------------------------------------------------------
    # 06 - OPERADORES
    # --------------------------------------------------------

    story.extend(
        _operadores_brocas(
            operadores,
            styles,
        )
    )

    # --------------------------------------------------------
    # 07 - STOCK
    # --------------------------------------------------------

    story.extend(
        _stock_critico(
            stock_critico,
            styles,
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    # --------------------------------------------------------
    # 08 - OBSERVACIONES
    # --------------------------------------------------------

    story.extend(
        _conclusiones(
            resumen,
            metros_tipo,
            consumo_familia,
            rendimiento_equipos,
            stock_critico,
            styles,
        )
    )

    # --------------------------------------------------------
    # Cierre
    # --------------------------------------------------------

    story.append(Spacer(1, 0.45 * cm))

    story.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=GRIS_CLARO,
        )
    )

    story.append(Spacer(1, 0.2 * cm))

    story.append(
        Paragraph(
            f"<b>{EMPRESA}</b> — Unidad de Producción "
            f"<b>{UNIDAD}</b><br/>"
            "Reporte generado automáticamente por el Sistema de Gestión "
            "de Operaciones.",
            styles["Footer"],
        )
    )

    # --------------------------------------------------------
    # Construcción PDF
    # --------------------------------------------------------

    doc.build(
        story,
        onFirstPage=lambda canvas, document: _dibujar_pagina(
            canvas,
            document,
            desde,
            hasta,
        ),
        onLaterPages=lambda canvas, document: _dibujar_pagina(
            canvas,
            document,
            desde,
            hasta,
        ),
    )

    return pdf_path