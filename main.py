from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import date, datetime

# 1. Configuración de Base de Datos SQLite
DATABASE_URL = "sqlite:///./gym.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modelos de la Base de Datos
class Alumno(Base):
    __tablename__ = "alumnos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    telefono = Column(String)

class Pago(Base):
    __tablename__ = "pagos"
    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer, ForeignKey("alumnos.id"))
    monto = Column(Float, nullable=False)
    fecha_pago = Column(Date, default=date.today)
    fecha_vencimiento = Column(Date, nullable=False)

# Crear las tablas en el archivo gym.db
Base.metadata.create_all(bind=engine)

# 3. Inicializar FastAPI
app = FastAPI(title="Gym Payment API")

# Permitir conexiones desde el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia para conectar a la BD en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. Rutas / Endpoints de la API

@app.post("/alumnos/")
def registrar_alumno(nombre: str, apellido: str, telefono: str = None, db: Session = Depends(get_db)):
    nuevo_alumno = Alumno(nombre=nombre, apellido=apellido, telefono=telefono)
    db.add(nuevo_alumno)
    db.commit()
    db.refresh(nuevo_alumno)
    return {"message": "Alumno registrado con éxito", "alumno": nuevo_alumno}

@app.post("/pagos/")
def registrar_pago(alumno_id: int, monto: float, meses_a_pagar: int = 1, db: Session = Depends(get_db)):
    # Verificar si el alumno existe
    alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    
    # Calcular fecha de vencimiento (por simplicidad, sumamos meses de 30 días)
    # En producción puedes usar librerías como python-dateutil
    from datetime import timedelta
    vencimiento = date.today() + timedelta(days=30 * meses_a_pagar)
    
    nuevo_pago = Pago(alumno_id=alumno_id, monto=monto, fecha_vencimiento=vencimiento)
    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)
    return {"message": "Pago registrado", "pago": nuevo_pago}

@app.get("/alumnos/estado/")
def listar_alumnos_y_estados(db: Session = Depends(get_db)):
    alumnos = db.query(Alumno).all()
    resultado = []
    
    hoy = date.today()
    
    for alumno in alumnos:
        # Buscar el último pago registrado de este alumno
        ultimo_pago = db.query(Pago).filter(Pago.alumno_id == alumno.id).order_by(Pago.fecha_vencimiento.desc()).first()
        
        if ultimo_pago and ultimo_pago.fecha_vencimiento >= hoy:
            estado = "🟢 AL DÍA"
            vencimiento = ultimo_pago.fecha_vencimiento
        else:
            estado = "🔴 DEUDOR / VENCIDO"
            vencimiento = ultimo_pago.fecha_vencimiento if ultimo_pago else "Sin pagos registrados"
            
        resultado.append({
            "id": alumno.id,
            "nombre_completo": f"{alumno.nombre} {alumno.apellido}",
            "telefono": alumno.telefono,
            "estado_pago": estado,
            "fecha_vencimiento": vencimiento
        })
        
    return resultado
