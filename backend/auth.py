from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db
import os

# ============================================================
# CONFIGURACIÓN
# ============================================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu-secreto-super-seguro-cambia-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# ============================================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera hash de una contraseña"""
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str):
    """Autentica un usuario contra la tabla usuarios"""
    try:
        db = get_db()
        
        # Buscar usuario por username
        result = db.client.table("usuarios") \
            .select("*") \
            .eq("username", username) \
            .eq("activo", 1) \
            .execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        user = result.data[0]
        
        # Verificar contraseña
        if not verify_password(password, user["password"]):
            return None
        
        return user
        
    except Exception as e:
        print(f"❌ Error en authenticate_user: {e}")
        return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def get_current_user(token: str):
    """Obtiene el usuario actual desde el token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
        
        # Buscar usuario en la base de datos
        db = get_db()
        result = db.client.table("usuarios") \
            .select("*") \
            .eq("username", username) \
            .eq("activo", 1) \
            .execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        return result.data[0]
        
    except JWTError:
        return None

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica el token en las peticiones"""
    token = credentials.credentials
    
    user = get_current_user(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# ============================================================
# ENDPOINTS DE AUTENTICACIÓN
# ============================================================

def register_auth_endpoints(app):
    """Registra los endpoints de autenticación en la app"""
    
    @app.post("/api/auth/login")
    async def login(username: str, password: str):
        """Inicia sesión y devuelve un token"""
        user = authenticate_user(username, password)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )
        
        # Crear token
        access_token = create_access_token(
            data={"sub": user["username"], "rol": user["rol"]}
        )
        
        return {
            "success": True,
            "token": access_token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "nombre": user["nombre"],
                "email": user["email"],
                "rol": user["rol"]
            }
        }
    
    @app.post("/api/auth/logout")
    async def logout():
        """Cierra sesión (solo para consistencia)"""
        return {"success": True}
    
    @app.get("/api/auth/me")
    async def get_me(user = Depends(verify_token)):
        """Obtiene el usuario actual"""
        return {
            "id": user["id"],
            "username": user["username"],
            "nombre": user["nombre"],
            "email": user["email"],
            "rol": user["rol"]
        }
    
    @app.post("/api/auth/register")
    async def register(username: str, password: str, nombre: str, email: str = None, rol: str = "invitado"):
        """Registra un nuevo usuario"""
        try:
            db = get_db()
            
            # Verificar si el usuario ya existe
            existing = db.client.table("usuarios") \
                .select("id") \
                .eq("username", username) \
                .execute()
            
            if existing.data and len(existing.data) > 0:
                raise HTTPException(
                    status_code=400,
                    detail="El usuario ya existe"
                )
            
            # Crear usuario con contraseña hasheada
            hashed_password = get_password_hash(password)
            
            result = db.client.table("usuarios").insert({
                "username": username,
                "password": hashed_password,
                "nombre": nombre,
                "email": email,
                "rol": rol,
                "activo": 1
            }).execute()
            
            return {"success": True, "message": "Usuario creado correctamente"}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))