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

# ==========================================
# ESTILOS CSS PERSONALIZADOS
# ==========================================
st.markdown("""
<style>
    /* Fondo con degradado moderno */
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
        margin-bottom: 30px;
        font-weight: 500;
    }

    /* Tarjetas estilo Pop / Neón */
    .fun-card {
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(10px);
        border: 2px solid #ff007f;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(255, 0, 127, 0.2);
        transition: transform 0.3s ease;
    }

    .info-card {
        background: linear-gradient(145deg, #ff007f, #7928ca);
        border-radius: 20px;
        padding: 25px;
        color: white;
        box-shadow: 0 10px 30px rgba(121, 40, 202, 0.4);
    }

    /* Recuadro de Fecha del Sorteo */
    .date-card {
        background: rgba(0, 240, 255, 0.1);
        border: 2px dashed #00f0ff;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
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

    /* Tickets asignados */
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

# 2. Inicializar Base de Datos
init_db()

# 3. Función auxiliar para actualizar la fecha del sorteo en BD
def update_draw_dates(draw_id, start_dt, end_dt):
    with conn() as c:
        cur = c.cursor()
        cur.execute(
            "UPDATE draws SET start=?, end=? WHERE id=?",
            (start_dt.isoformat(), end_dt.isoformat(), draw_id)
        )
        c.commit()

# 4. Obtener o crear sorteo activo
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

# Parsear fecha de finalización
try:
    end_date_obj = datetime.fromisoformat(draw["end"])
except Exception:
    end_date_obj = datetime.now()

# Encabezado principal
st.markdown('<h1 class="hero-title">🎉 🐷 LA CHANCHA SORTEOS 🐷 🎉</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">¡Elegí tus números, participá y llevate el pozo! 💸✨</p>', unsafe_allow_html=True)

# Definición de pestañas
tab_comprar, tab_ganadores, tab_admin = st.tabs([
    "🔥 ¡Quiero Participar!",
    "🏆 Salón de la Fama",
    "⚙️ Zona Segreta (Admin)"
])

# ==========================================
# PESTAÑA 1: ADQUIRIR PARTICIPACIONES
# ==========================================
with tab_comprar:
    col_f1, col_f2 = st.columns([1.8, 1.2], gap="large")
    
    with col_f1:
        if draw.get("status") == "CLOSED":
            st.error("🔒 ¡Este sorteo ya cerró! Mantente atento para el próximo lanzamiento 🚀")
        else:
            static_mp_link = st.secrets.get("MP_STATIC_LINK", "https://mpago.la/TU_LINK")
            
            st.markdown("""
            <div class="fun-card">
                <h3 style="color: #00f0ff; margin-top: 0;">PASO 1: Paga tus números 💳</h3>
                <p>Tocá el botón para abonar seguro con Mercado Pago:</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.link_button("🚀 PAGAR CON MERCADO PAGO 🚀", static_mp_link, use_container_width=True)
            st.write("")

            st.markdown("""
            <div class="fun-card">
                <h3 style="color: #ffaa00; margin-top: 0;">PASO 2: Carga tu comprobante 🎟️</h3>
                <p>Completá el formulario para asignarte tus tickets al instante:</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("manual_validation_form"):
                nombre = st.text_input("👤 Tu Nombre y Apellido*", placeholder="Ej: Juan Pérez")
                email = st.text_input("📧 Tu Email*", placeholder="ejemplo@email.com")
                cantidad = st.number_input("🎟️ ¿Cuántos tickets compraste?", min_value=1, max_value=50, value=1)
                comprobante = st.text_input("🔢 Nº de Operación de Mercado Pago*", placeholder="Ej: 9876543210")
                
                enviar = st.form_submit_button("🎉 ¡VALIDAR Y OBTENER MIS TICKETS!", type="primary", use_container_width=True)
                
                if enviar:
                    if not nombre.strip() or not email.strip() or not comprobante.strip():
                        st.error("⚠️ Por favor completa todos los campos obligatorios.")
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
                            st.success("🥳 ¡FELICITACIONES! Ya estás participando.")
                            st.markdown("### 🎟️ Tus números de la suerte son:")
                            badge_html = "".join([f'<span class="ticket-badge">#{t}</span>' for t in tickets])
                            st.markdown(badge_html, unsafe_allow_html=True)
                            st.rerun()

    with col_f2:
        price_fmt = f"${draw['price']:,.0f}".replace(",", ".")
        formatted_end_date = end_date_obj.strftime("%d/%m/%Y a las %H:%M hs")
        
        # Cálculo del tiempo restante
        now = datetime.now()
        time_diff = end_date_obj - now
        if time_diff.total_seconds() > 0:
            days_left = time_diff.days
            hours_left = int(time_diff.seconds // 3600)
            countdown_str = f"⏳ Quedan {days_left}d {hours_left}h para el sorteo"
        else:
            countdown_str = "⌛ Sorteo listo para realizarse"

        st.markdown(f"""
        <div class="info-card">
            <h2 style="margin-top:0; text-align:center; color:#fff;">📊 ESTADO DEL SORTEO</h2>
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p style="font-size: 1.1rem;">🎯 <b>Sorteo:</b> {draw['name']}</p>
            <p style="font-size: 1.1rem;">🔥 <b>Estado:</b> <span style="background:#00f0ff; color:#000; padding:2px 8px; border-radius:8px; font-weight:bold;">{draw['status']}</span></p>
            <p style="font-size: 1.1rem;">💰 <b>Valor del Ticket:</b> {price_fmt} ARS</p>
            <p style="font-size: 1.1rem;">⚡ <b>Tickets Vendidos:</b> {len(participants)}</p>
            
            <div class="date-card">
                <span style="font-size: 0.9rem; color: #e0c3fc;">📅 FECHA DEL SORTEO</span><br>
                <b style="font-size: 1.2rem; color: #00f0ff;">{formatted_end_date}</b><br>
                <small style="color: #ffaa00;">{countdown_str}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PESTAÑA 2: GANADORES
# ==========================================
with tab_ganadores:
    st.subheader("🏆 Ganadores y Premios Entregados")
    if draw.get("status") == "CLOSED" and draw.get("winning_ticket"):
        st.balloons()
        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #ffaa00, #ff007f); padding: 30px; border-radius: 20px; text-align: center; color: white;">
            <h1>🥇 ¡TENEMOS GANADOR/A! 🥇</h1>
            <h2 style="font-size: 2.5rem;">🎟️️ Ticket Ganador: <span class="ticket-badge" style="font-size:2.5rem;">#{draw['winning_ticket']}</span></h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"🕒 El sorteo actual está activo. El ganador se anunciará el **{end_date_obj.strftime('%d/%m/%Y a las %H:%M hs')}**.")

# ==========================================
# PESTAÑA 3: ADMINISTRACIÓN
# ==========================================
with tab_admin:
    st.subheader("⚙️ Panel de Control del Sorteo")
    
    col_adm1, col_adm2 = st.columns([1.5, 1], gap="large")
    
    with col_adm1:
        st.write("### 📋 Participantes Registrados")
        if participants:
            st.dataframe(participants, use_container_width=True)
        else:
            st.info("Aún no hay tickets vendidos para este sorteo.")

    with col_adm2:
        st.write("### 📅 Configuración de Fecha de Sorteo")
        
        with st.form("form_config_fechas"):
            # Selectores de Fecha y Hora
            nueva_fecha = st.date_input(
                "Fecha de Cierre/Sorteo",
                value=end_date_obj.date()
            )
            nueva_hora = st.time_input(
                "Hora del Sorteo",
                value=end_date_obj.time()
            )
            
            btn_guardar_fecha = st.form_submit_button("💾 Guardar Nueva Fecha", type="primary", use_container_width=True)
            
            if btn_guardar_fecha:
                nueva_fechahora = datetime.combine(nueva_fecha, nueva_hora)
                update_draw_dates(draw["id"], datetime.now(), nueva_fechahora)
                st.success(f"✅ Fecha actualizada al {nueva_fechahora.strftime('%d/%m/%Y %H:%M hs')}")
                st.rerun()

        st.markdown("---")
        st.write("### 🎛️ Finalizar Sorteo")
        if draw.get("status") == "ACTIVE":
            if st.button("🎲 ¡ELEGIR GANADOR AHORA!", type="primary", use_container_width=True):
                winner = draw_winner(draw["id"])
                if winner:
                    st.balloons()
                    st.success(f"🎉 ¡Ticket Ganador: #{winner['ticket']} - Pertenece a: {winner['name']}!")
                    st.rerun()
                else:
                    st.warning("Aún no hay participantes registrados.")
        else:
            st.write("🔒 El sorteo ya finalizó.")
