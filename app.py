import os
import sqlite3
from datetime import datetime, date, time as dtime
import streamlit as st

# 1. IMPORTAR FUNCIONES DESDE EL MÓDULO DE BASE DE DATOS
from base_de_datos import (
    conn,
    init_db,
    create_draw,
    get_draw,
    close_draw,
    get_participants,
    register_successful_payment,
    draw_winner
)

# Configuración de página de Streamlit
st.set_page_config(
    page_title="🐷 La Chancha - Sorteos",
    page_icon="🐷",
    layout="wide"
)

# Clave de administración (Podés cambiarla por la clave que prefieras)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "sorteando")

# ==========================================
# ESTILOS CSS PERSONALIZADOS (MODERNO & NEÓN)
# ==========================================
st.markdown("""
<style>
    /* Fondo con degradado nocturno */
    .stApp {
        background: linear-gradient(135deg, #1d0933 0%, #390d59 40%, #11052c 100%);
        color: #ffffff;
    }

    /* Título Principal */
    .hero-title {
        font-size: 3rem !important;
        font-weight: 900 !important;
        text-align: center;
        background: linear-gradient(90deg, #ff007f, #ffaa00, #00f0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        text-shadow: 0px 10px 20px rgba(255, 0, 127, 0.3);
    }
    
    .hero-subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #e0c3fc;
        margin-bottom: 25px;
        font-weight: 500;
    }

    /* Mensaje aclaratorio de pago obligatorio */
    .notice-box {
        background: rgba(255, 170, 0, 0.15);
        border: 2px solid #ffaa00;
        border-radius: 15px;
        padding: 15px 20px;
        margin-bottom: 25px;
        text-align: center;
    }

    /* Tarjetas estilo Pop / Neón */
    .fun-card {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(10px);
        border: 2px solid #ff007f;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(255, 0, 127, 0.2);
        margin-bottom: 20px;
    }

    .info-card {
        background: linear-gradient(145deg, #ff007f, #7928ca);
        border-radius: 20px;
        padding: 25px;
        color: white;
        box-shadow: 0 10px 30px rgba(121, 40, 202, 0.4);
    }

    /* Tarjeta Destacada de Fecha y Cuenta Regresiva */
    .date-card {
        background: rgba(0, 240, 255, 0.1);
        border: 2px dashed #00f0ff;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 10px;
    }

    /* Botones principales */
    .stButton>button {
        border-radius: 50px !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        background: linear-gradient(90deg, #ff007f 0%, #7928ca 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(255, 0, 127, 0.4) !important;
    }

    /* Badges de Tickets */
    .ticket-badge {
        display: inline-block;
        background: #00f0ff;
        color: #000;
        font-weight: 900;
        padding: 6px 14px;
        border-radius: 12px;
        margin: 4px;
        font-family: monospace;
        font-size: 1.1rem;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
    }
</style>
""", unsafe_allow_html=True)

# 2. Inicialización de Base de Datos
init_db()

# Función auxiliar para actualizar la fecha del sorteo en la BD
def update_draw_dates(draw_id, start_dt, end_dt):
    with conn() as c:
        cur = c.cursor()
        cur.execute(
            "UPDATE draws SET start=?, end=? WHERE id=?",
            (start_dt.isoformat(), end_dt.isoformat(), draw_id)
        )
        c.commit()

# 3. Cargar datos del sorteo activo
draw = get_draw()
if not draw:
    create_draw(
        name="🐷 Gran Sorteo La Chancha 🚀",
        price=1000.0,
        start=datetime.now(),
        end=datetime.now(),
        prize_percent=50.0
    )
    draw = get_draw()

participants = get_participants(draw["id"])

# Procesar la fecha de finalización desde la BD
try:
    end_date_obj = datetime.fromisoformat(draw["end"])
except Exception:
    end_date_obj = datetime.now()

# Header Principal
st.markdown('<h1 class="hero-title">🎉 🐷 LA CHANCHA SORTEOS 🐷 🎉</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">¡Elegí tus números, participá y llevate el pozo en efectivo! 💸✨</p>', unsafe_allow_html=True)

# Aclaración explícita sobre la obligación del pago previo
st.markdown("""
<div class="notice-box">
    <b>📢 REQUISITO PARA PARTICIPAR:</b> Es indispensable realizar la transferencia/pago del ticket antes de registrar tu comprobante. 
    Los registros sin pago verificado no participan ni tendrán validez en el sorteo.
</div>
""", unsafe_allow_html=True)

# Estructura de Pestañas
tab_comprar, tab_ganadores, tab_admin = st.tabs([
    "🔥 ¡Quiero Participar!",
    "🏆 Salón de la Fama",
    "🔒 Administración"
])

# ==========================================
# PESTAÑA 1: COMPRAR TICKETS
# ==========================================
with tab_comprar:
    col_f1, col_f2 = st.columns([1.8, 1.2], gap="large")
    
    with col_f1:
        if draw.get("status") == "CLOSED":
            st.error("🔒 ¡Este sorteo ya cerró! Mantente atento para el próximo lanzamiento 🚀")
        else:
            static_mp_link = st.secrets.get("MP_STATIC_LINK", "https://mpago.la/19yACmp")
            
            st.markdown("""
            <div class="fun-card">
                <h3 style="color: #00f0ff; margin-top: 0;">PASO 1: Paga tus números 💳</h3>
                <p>Primero realiza el pago correspondiente según la cantidad de tickets que quieras comprar. Tocá el botón para abonar con Mercado Pago:</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.link_button("🚀 PAGAR CON MERCADO PAGO 🚀", static_mp_link, use_container_width=True)
            st.write("")

            st.markdown("""
            <div class="fun-card">
                <h3 style="color: #ffaa00; margin-top: 0;">PASO 2: Valida tu comprobante 🎟️</h3>
                <p>Una vez realizado el pago, ingresá tus datos y el N° de comprobante para que el sistema te asigne automáticamente tus números:</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("manual_validation_form"):
                nombre = st.text_input("👤 Tu Nombre y Apellido*", placeholder="Ej: Cosme Fulanito")
                email = st.text_input("📧 Tu Email (para enviarte la confirmación)*", placeholder="ejemplo@email.com")
                cantidad = st.number_input("🎟 ¿Cuántos tickets compraste y pagaste?", min_value=1, max_value=50, value=1)
                comprobante = st.text_input("🔢 Nº de Operación / Comprobante MP*", placeholder="Ej: 9876543210")
                
                enviar = st.form_submit_button("🎉 ¡VALIDAR Y OBTENER MIS TICKETS!", type="primary", use_container_width=True)
                
                if enviar:
                    if not nombre.strip() or not email.strip() or not comprobante.strip():
                        st.error("⚠️ Por favor completa todos los campos requeridos para validar tu pago.")
                    else:
                        payment_key = f"MP-{comprobante.strip()}"
                        tickets = register_successful_payment(
                            draw_id=draw["id"],
                            payment_id=payment_key,
                            name=nombre.strip(),
                            email=email.strip(),
                            quantity=int(cantidad)
                        )
                        if tickets:
                            st.balloons()
                            st.success("🥳 ¡PAGO COMPROBADO Y REGISTRADO! Ya estás participando.")
                            st.markdown("### 🎟 Tus números asignados son:")
                            badge_html = "".join([f'<span class="ticket-badge">#{t}</span>' for t in tickets])
                            st.markdown(badge_html, unsafe_allow_html=True)
                            st.rerun()

    with col_f2:
        price_fmt = f"${draw['price']:,.0f}".replace(",", ".")
        pozo_estimado = len(participants) * draw['price'] * (draw.get('prize_percent', 50.0) / 100.0)
        pozo_fmt = f"${pozo_estimado:,.0f}".replace(",", ".")
        
        # Cálculo dinámico de tiempo restante
        now = datetime.now()
        time_diff = end_date_obj - now
        
        if time_diff.total_seconds() > 0:
            days = time_diff.days
            hours = int(time_diff.seconds // 3600)
            minutes = int((time_diff.seconds % 3600) // 60)
            
            if days > 0:
                countdown_str = f"⏳ Quedan {days}d {hours}h para el sorteo"
            else:
                countdown_str = f"⏳ Quedan {hours}h {minutes}m para el sorteo"
        else:
            countdown_str = "⌛ ¡Tiempo cumplido! El sorteo se realizará en breve"

        formatted_end_date = end_date_obj.strftime("%d/%m/%Y a las %H:%M hs")

        info_card_html = f"""
<div class="info-card">
    <h2 style="margin-top:0; text-align:center; color:#fff;">📊 ESTADO DEL SORTEO</h2>
    <hr style="border-color: rgba(255,255,255,0.3);">
    <p style="font-size: 1.1rem; margin-bottom: 8px;">🎯 <b>Sorteo:</b> {draw['name']}</p>
    <p style="font-size: 1.1rem; margin-bottom: 8px;">🔥 <b>Estado:</b> <span style="background:#00f0ff; color:#000; padding:2px 8px; border-radius:8px; font-weight:bold;">{draw['status']}</span></p>
    <p style="font-size: 1.1rem; margin-bottom: 8px;">💰 <b>Valor del Ticket:</b> {price_fmt} ARS</p>
    <p style="font-size: 1.1rem; margin-bottom: 8px;">🏆 <b>Pozo Acumulado Premio:</b> <span style="color:#ffaa00; font-weight:bold;">{pozo_fmt} ARS</span></p>
    <p style="font-size: 1.1rem; margin-bottom: 8px;">⚡ <b>Tickets Pagados y Vendidos:</b> {len(participants)}</p>
    <div class="date-card">
        <span style="font-size: 0.9rem; color: #e0c3fc;">📅 FECHA DEL SORTEO</span><br>
        <b style="font-size: 1.2rem; color: #00f0ff;">{formatted_end_date}</b><br>
        <small style="color: #ffaa00;">{countdown_str}</small>
    </div>
</div>
"""
        st.markdown(info_card_html, unsafe_allow_html=True)

# ==========================================
# PESTAÑA 2: GANADORES
# ==========================================
with tab_ganadores:
    st.subheader("🏆 Ganadores y Premios")
    if draw.get("status") == "CLOSED" and draw.get("winning_ticket"):
        st.balloons()
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #ffaa00, #ff007f); padding: 30px; border-radius: 20px; text-align: center; color: white;">
            <h1>🥇 ¡TENEMOS GANADOR/A! 🥇</h1>
            <h2 style="font-size: 2.5rem;">🎟️ Ticket Ganador: <span class="ticket-badge" style="font-size:2.5rem;">#{draw['winning_ticket']}</span></h2>
            <p style="font-size: 1.2rem;">¡Muchas gracias a todos por participar!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"🕒 El sorteo actual está activo. El ganador/a se anunciará el **{end_date_obj.strftime('%d/%m/%Y a las %H:%M hs')}**.")

# ==========================================
# PESTAÑA 3: ADMINISTRACIÓN (PROTEGIDA POR CLAVE)
# ==========================================
with tab_admin:
    st.subheader("🔒 Panel de Administración Exclusivo")
    
    # Sistema de autenticación para el panel
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    if not st.session_state["admin_authenticated"]:
        st.warning("Acceso restringido solo para el organizador del sorteo.")
        pass_input = st.text_input("🔑 Ingrese la contraseña de Administrador:", type="password")
        if st.button("Ingresar al Panel"):
            if pass_input == ADMIN_PASSWORD:
                st.session_state["admin_authenticated"] = True
                st.success("¡Acceso concedido!")
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        # Botón para cerrar sesión de admin
        if st.button("🚪 Cerrar Sesión de Admin"):
            st.session_state["admin_authenticated"] = False
            st.rerun()

        st.markdown("---")
        col_adm1, col_adm2 = st.columns([1.5, 1], gap="large")
        
        with col_adm1:
            st.write("### 📋 Listado de Participantes con Pago Comprobado")
            if participants:
                st.dataframe(participants, use_container_width=True)
            else:
                st.info("Aún no se han registrado tickets para este sorteo.")

        with col_adm2:
            st.write("### 📅 Programar Fecha del Sorteo")
            
            with st.form("form_config_fechas"):
                nueva_fecha = st.date_input(
                    "Fecha de Cierre",
                    value=end_date_obj.date()
                )
                nueva_hora = st.time_input(
                    "Hora de Cierre",
                    value=end_date_obj.time()
                )
                
                btn_guardar_fecha = st.form_submit_button("💾 Guardar Fecha", type="primary", use_container_width=True)
                
                if btn_guardar_fecha:
                    nueva_fechahora = datetime.combine(nueva_fecha, nueva_hora)
                    update_draw_dates(draw["id"], datetime.now(), nueva_fechahora)
                    st.success(f"✅ Fecha actualizada al {nueva_fechahora.strftime('%d/%m/%Y %H:%M hs')}")
                    st.rerun()

            st.markdown("---")
            st.write("### 🎛️ Acciones de Cierre")
            if draw.get("status") == "ACTIVE":
                if st.button("🎲 ¡ELEGIR GANADOR Y CERRAR!", type="primary", use_container_width=True):
                    winner = draw_winner(draw["id"])
                    if winner:
                        st.balloons()
                        st.success(f"🎉 Ticket Ganador: #{winner['ticket']} - Asignado a: {winner['name']}")
                        st.rerun()
                    else:
                        st.warning("No hay tickets registrados para sortear.")
            else:
                st.write("🔒 El sorteo se encuentra cerrado.")
