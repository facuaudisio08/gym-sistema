import streamlit as st
import requests
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Control de Pagos - Gym", page_icon="🏋️‍♂️", layout="wide")

# URL de nuestra API de FastAPI (asegúrate de usar el puerto 8080 que funcionó antes)
API_URL = "http://127.0.0.1:8080"

st.title("🏋️‍♂️ Sistema de Gestión y Pagos del Gimnasio")
st.markdown("---")

# Creamos dos pestañas en la pantalla: una para ver el estado y otra para registrar datos
tab_estado, tab_registro = st.tabs(["📋 Estado de Alumnos", "➕ Registrar Alumno / Pago"])

# ==========================================
# PESTAÑA 1: ESTADO DE ALUMNOS Y BUSCADOR
# ==========================================
with tab_estado:
    st.subheader("Socios Registrados")
    
    # Buscador de alumnos
    buscar = st.text_input("🔍 Buscar alumno por nombre...", "")
    
    # Botón para actualizar la lista
    if st.button("🔄 Actualizar Lista"):
        st.rerun()

    # Traer datos desde FastAPI
    try:
        response = requests.get(f"{API_URL}/alumnos/estado/")
        if response.status_code == 200:
            alumnos = response.json()
            
            if not alumnos:
                st.info("No hay alumnos registrados todavía.")
            else:
                # Filtrar si hay una búsqueda activa
                if buscar:
                    alumnos = [a for a in alumnos if buscar.lower() in a["nombre_completo"].lower()]

                # Mostrar las tarjetas o filas de alumnos
                for alumno in alumnos:
                    col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
                    
                    with col1:
                        st.markdown(f"**ID: {alumno['id']}**")
                    with col2:
                        st.markdown(f"👤 **{alumno['nombre_completo']}**")
                    with col3:
                        # Darle color al estado según corresponda
                        if "🟢" in alumno["estado_pago"]:
                            st.success(alumno["estado_pago"])
                        else:
                            st.error(alumno["estado_pago"])
                    with col4:
                        st.caption(f"📅 Vence: {alumno['fecha_vencimiento']}")
                    st.markdown("---")
        else:
            st.error("Error al conectar con el servidor.")
    except Exception as e:
        st.error(f"Asegúrate de que FastAPI esté encendido en el puerto 8080. Error: {e}")

# ==========================================
# PESTAÑA 2: REGISTROS (ALUMNOS Y PAGOS)
# ==========================================
with tab_registro:
    col_al, col_pa = st.columns(2)
    
    # Formulario para Nuevo Alumno
    with col_al:
        st.subheader("📝 Registrar Nuevo Alumno")
        with st.form("form_alumno", clear_on_submit=True):
            nombre = st.text_input("Nombre")
            apellido = st.text_input("Apellido")
            telefono = st.text_input("Teléfono (Opcional)")
            btn_alumno = st.form_submit_button("Guardar Alumno")
            
            if btn_alumno:
                if nombre and apellido:
                    res = requests.post(f"{API_URL}/alumnos/?nombre={nombre}&apellido={apellido}&telefono={telefono}")
                    if res.status_code == 200:
                        st.success(f"¡{nombre} {apellido} registrado con éxito!")
                    else:
                        st.error("Hubo un problema al registrar.")
                else:
                    st.warning("Por favor completa nombre y apellido.")

    # Formulario para Nuevo Pago
    with col_pa:
        st.subheader("💵 Registrar Pago de Cuota")
        with st.form("form_pago", clear_on_submit=True):
            alumno_id = st.number_input("ID del Alumno", min_value=1, step=1)
            monto = st.number_input("Monto Pagado ($)", min_value=0.0, step=100.0)
            meses = st.number_input("Meses a abonar", min_value=1, max_value=12, step=1)
            btn_pago = st.form_submit_button("Cargar Pago")
            
            if btn_pago:
                res = requests.post(f"{API_URL}/pagos/?alumno_id={alumno_id}&monto={monto}&meses_a_pagar={meses}")
                if res.status_code == 200:
                    st.success("¡Pago cargado correctamente! Estado actualizado.")
                elif res.status_code == 404:
                    st.error("El ID de alumno no existe.")
                else:
                    st.error("Error al procesar el pago.")
