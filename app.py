import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Date, Float, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta

# Configuración de la página
st.set_page_config(page_title="Control de Pagos - Gym", page_icon="🏋️‍♂️", layout="wide")

# Ocultar menús por seguridad
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# CONEXIÓN DIRECTA A LA BASE DE DATOS
DATABASE_URL = st.secrets["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MODELOS DE BASE DE DATOS
class Alumno(Base):
    __tablename__ = "alumnos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    telefono = Column(String)

class Pago(Base):
    __tablename__ = "pagos"
    id = Column(Integer, primary_key=True, index=True)
    alumno_id = Column(Integer)
    monto = Column(Float, nullable=False)
    fecha_pago = Column(Date, default=date.today)
    fecha_vencimiento = Column(Date, nullable=False)

Base.metadata.create_all(bind=engine)

# SISTEMA DE AUTENTICACIÓN (LOGIN)
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.markdown("<h2 style='text-align: center;'>🔐 Acceso Restringido - Gestión Gym</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns()
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario Administrador")
            contrasena = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema")
            if submit:
                if usuario == "admin" and contrasena == "GymViejo2026":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("⚠️ Usuario o contraseña incorrectos")
                    return False
    return False

# PANTALLA PRINCIPAL
if check_password():
    col_titulo, col_logout = st.columns()
    with col_titulo:
        st.title("🏋️‍♂️ Sistema de Gestión y Pagos del Gimnasio")
    with col_logout:
        if st.button("🚪 Cerrar Sesión"):
            st.session_state["password_correct"] = False
            st.rerun()
            
    st.markdown("---")
    tab_estado, tab_registro = st.tabs(["📋 Estado de Alumnos", "➕ Registrar Alumno / Pago"])

    with tab_estado:
        st.subheader("Socios Registrados")
        buscar = st.text_input("🔍 Buscar alumno por nombre o apellido...", "")
        if st.button("🔄 Actualizar Lista"):
            st.rerun()

        db = SessionLocal()
        try:
            alumnos = db.query(Alumno).all()
            hoy = date.today()
            if not alumnos:
                st.info("No hay alumnos registrados todavía.")
            else:
                if buscar:
                    alumnos = [a for a in alumnos if buscar.lower() in f"{a.nombre} {a.apellido}".lower()]
                for alumno in alumnos:
                    ultimo_pago = db.query(Pago).filter(Pago.alumno_id == alumno.id).order_by(desc(Pago.fecha_vencimiento)).first()
                    if ultimo_pago and ultimo_pago.fecha_vencimiento >= hoy:
                        estado = "🟢 AL DÍA"
                        vencimiento_str = str(ultimo_pago.fecha_vencimiento)
                        es_deudor = False
                    else:
                        estado = "🔴 DEUDOR / VENCIDO"
                        vencimiento_str = str(ultimo_pago.fecha_vencimiento) if ultimo_pago else "Sin pagos"
                        es_deudor = True

                    col1, col2, col3, col4 = st.columns()
                    with col1: st.markdown(f"**ID: {alumno.id}**")
                    with col2: st.markdown(f"👤 **{alumno.nombre} {alumno.apellido}**")
                    with col3:
                        if not es_deudor: st.success(estado)
                        else: st.error(estado)
                    with col4: st.caption(f"📅 Vence: {vencimiento_str}")
                    st.markdown("---")
        finally:
            db.close()

    with tab_registro:
        col_al, col_pa = st.columns(2)
        with col_al:
            st.subheader("📝 Registrar Nuevo Alumno")
            with st.form("form_alumno", clear_on_submit=True):
                nom = st.text_input("Nombre")
                ape = st.text_input("Apellido")
                tel = st.text_input("Teléfono (Opcional)")
                if st.form_submit_button("Guardar Alumno") and nom and ape:
                    db = SessionLocal()
                    nuevo = Alumno(nombre=nom, apellido=ape, telefono=tel)
                    db.add(nuevo)
                    db.commit()
                    db.close()
                    st.success(f"¡{nom} {ape} registrado!")
                    st.rerun()

        with col_pa:
            st.subheader("💵 Registrar Pago de Cuota")
            with st.form("form_pago", clear_on_submit=True):
                al_id = st.number_input("ID del Alumno", min_value=1, step=1)
                mon = st.number_input("Monto Pagado ($)", min_value=0.0, step=100.0)
                meses = st.number_input("Meses a abonar", min_value=1, max_value=12, step=1)
                if st.form_submit_button("Cargar Pago"):
                    db = SessionLocal()
                    alumno_existe = db.query(Alumno).filter(Alumno.id == al_id).first()
                    if alumno_existe:
                        venc = date.today() + timedelta(days=30 * meses)
                        nuevo_pago = Pago(alumno_id=al_id, monto=mon, fecha_vencimiento=venc)
                        db.add(nuevo_pago)
                        db.commit()
                        db.close()
                        st.success("¡Pago cargado correctamente!")
                        st.rerun()
                    else:
                        db.close()
                        st.error("El ID de alumno no existe.")
