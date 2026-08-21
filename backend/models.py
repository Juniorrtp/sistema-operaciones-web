from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class DetalleMovimiento(BaseModel):
    brazo: Optional[str] = ""
    codigo: str
    descripcion: str
    cantidad: float
    razon: Optional[str] = ""

class MovimientoCreate(BaseModel):
    fecha: str
    mes: str
    ano: int
    turno: str
    guia: str
    movimiento: str  # INGRESO o SALIDA
    estado: Optional[str] = ""
    operador: Optional[str] = ""
    equipo: Optional[str] = ""
    detalles: List[DetalleMovimiento]

class MovimientoUpdate(BaseModel):
    fecha: Optional[str] = None
    mes: Optional[str] = None
    ano: Optional[int] = None
    turno: Optional[str] = None
    guia: Optional[str] = None
    movimiento: Optional[str] = None
    estado: Optional[str] = None
    operador: Optional[str] = None
    equipo: Optional[str] = None

class MetroCreate(BaseModel):
    fecha: str
    mes: str
    ano: int
    turno: str
    operador: str
    equipo: str
    tipo_perforacion: str
    total_mp: float