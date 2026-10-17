import streamlit as st
import psycopg2
from datetime import date, timedelta

# Configuración de la página
st.set_page_config(page_title="Control de Pagos - Gym", page_icon="🏋️‍♂️", layout="wide")

# Conexión fija y directa a la base de datos
def get_db_connection():
    return psycopg2.connect(
        host="://supabase.com",
        port=6543,
        database="postgres",
        user="postgres.pmufgjummnqpcivnngdk",
        password="CSb!#a7_UY*_E4C"
    )

# Crear las tablas automáticamente si no existen
try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alumnos (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            apellido VARCHAR(100) NOT NULL,
            telefono VARCHAR(20)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id SERIAL PRIMARY KEY,
            alumno_id INT,
            monto FLOAT NOT NULL,
            fecha_pago DATE DEFAULT CURRENT_DATE,
            fecha_vencimiento DATE NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
except Exception as e:
    pass

# SISTEMA DE AUTENTICACIÓN (LOGIN)
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.markdown("<h2 style='text-align: center;'>🔐 Acceso Restringido - Gestión Gym</h2>", unsafe_allow_html=True)
    
    # Corregido: Agregamos el número 3 para que no de TypeError
    col1, col2, col3 = st.columns(3)
    with col2:
        with st.form("login_form"):
            usuario = st.text_input("Usuario Administrador")
            contrasena = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema")
            if submit:
                if usuario == "admin" and contrasena == "GymViejo2026":
                    st.session_state["password_correct"] = True
                    st.toast("¡Bienvenido!")
                    st.rerun()
                else:
                    st.error("⚠️ Usuario o contraseña incorrectos")
                    return False
    return False

# PANTALLA PRINCIPAL
if check_password():
    col_titulo, col_logout = st.columns([4, 1])
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

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, nombre, apellido, telefono FROM alumnos;")
            alumnos = cur.fetchall()
            hoy = date.today()
            
            if not alumnos:
                st.info("No hay alumnos registrados todavía.")
            else:
                if buscar:
                    alumnos = [a for a in alumnos if buscar.lower() in f"{a[1]} {a[2]}".lower()]
                
                for alumno in alumnos:
                    al_id, nombre, apellido, telefono = alumno
                    
                    cur.execute("SELECT fecha_vencimiento FROM pagos WHERE alumno_id = %s ORDER BY fecha_vencimiento DESC LIMIT 1;", (al_id,))
                    pago_res = cur.fetchone()
                    
                    if pago_res and pago_res[0] >= hoy:
                        estado = "🟢 AL DÍA"
                        vencimiento_str = str(pago_res[0])
                        es_deudor = False
                    else:
                        estado = "🔴 DEUDOR / VENCIDO"
                        vencimiento_str = str(pago_res[0]) if pago_res else "Sin pagos"
                        es_deudor = True

                    col_a, col_b, col_c, col_d = st.columns(4)
                    with col_a: st.markdown(f"**ID: {al_id}**")
                    with col_b: st.markdown(f"👤 **{nombre} {apellido}**")
                    with col_c:
                        if not es_deudor: st.success(estado)
                        else: st.error(estado)
                    with col_d: st.caption(f"📅 Vence: {vencimiento_str}")
                    st.markdown("---")
            cur.close()
            conn.close()
        except Exception as e:
            st.error(f"Error al leer datos: {e}")

    with tab_registro:
        col_al, col_pa = st.columns(2)
        with col_al:
            st.subheader("📝 Registrar Nuevo Alumno")
            with st.form("form_alumno", clear_on_submit=True):
                nom = st.text_input("Nombre")
                ape = st.text_input("Apellido")
                tel = st.text_input("Teléfono (Opcional)")
                if st.form_submit_button("Guardar Alumno") and nom and ape:
                    try:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO alumnos (nombre, apellido, telefono) VALUES (%s, %s, %s);", (nom, ape, tel))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(f"¡{nom} {ape} registrado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

        with col_pa:
            st.subheader("💵 Registrar Pago de Cuota")
            with st.form("form_pago", clear_on_submit=True):
                al_id = st.number_input("ID del Alumno", min_value=1, step=1)
                mon = st.number_input("Monto Pagado ($)", min_value=0.0, step=100.0)
                meses = st.number_input("Meses a abonar", min_value=1, max_value=12, step=1)
                if st.form_submit_button("Cargar Pago"):
                    try:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT id FROM alumnos WHERE id = %s;", (al_id,))
                        if cur.fetchone():
                            venc = date.today() + timedelta(days=30 * meses)
                            cur.execute("INSERT INTO pagos (alumno_id, monto, fecha_vencimiento) VALUES (%s, %s, %s);", (al_id, mon, venc))
                            conn.commit()
                            st.success("¡Pago cargado correctamente!")
                            st.rerun()
                        else:
                            st.error("El ID de alumno no existe.")
                        cur.close()
                        conn.close()
                    except Exception as e:
                        st.error(f"Error al procesar pago: {e}")
