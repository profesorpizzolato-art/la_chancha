import sys
import os
import time
import random
from datetime import datetime, timedelta

import streamlit as st
import mercadopago

# Asegurar path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_db,
    get_draw,
    create_draw,
    get_participants,
    register_successful_payment,
    draw_winner
)

# Configuración de página
st.set_page_config(page_title="LA CHANCHA 🐷", page_icon="🐷", layout="wide")
init_db()

# Inicializar cliente de Mercado Pago (usar st.secrets en producción)
MP_ACCESS_TOKEN = st.secrets.get("MP_ACCESS_TOKEN", "TU_ACCESS_TOKEN_PROD_O_TEST")
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

# Estilos CSS
st.markdown("""
<style>
.main-title { font-size: 3.5rem; font-weight: 900; color: #E63946; line-height: 1; }
.subtitle { font-size: 1.1rem; color: #6c757d; margin-bottom: 1rem; }
.pozo-box {
    background: linear-gradient(135deg, #11998e, #38ef7d);
    color: white; padding: 1.5rem; border-radius: 18px; text-align: center;
}
.premio-box {
    background: linear-gradient(135deg, #FF416C, #FF4B2B);
    color: white; padding: 1.5rem; border-radius: 18px; text-align: center;
}
.timer-box {
    background: linear-gradient(135deg, #8A2387, #E94057, #F27121);
    color: white; padding: 1.5rem; border-radius: 18px; text-align: center;
}
.value-num { font-size: 2.8rem; font-weight: 900; }
.card { padding: 1.2rem; border-radius: 15px; background: #f8f9fa; border: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# Encabezado
st.markdown('<div class="main-title">🐷 LA CHANCHA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Sorteos transparentes en tiempo real.</div>', unsafe_allow_html=True)
st.divider()

draw = get_draw()

if not draw:
    st.info("No hay ningún sorteo activo.")
    st.stop()

# Datos del sorteo
participants = get_participants(draw["id"])
recaudado = len(participants) * draw["price"]
premio = recaudado * draw["prize_percent"] / 100

# Conteo de tiempo
end_time = datetime.fromisoformat(draw["end"])
restante = max(0, int((end_time - datetime.now()).total_seconds()))
horas, rem = divmod(restante, 3600)
minutos, segundos = divmod(rem, 60)

# Métricas
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="pozo-box"><div style="font-size:1.1rem;">💰 Pozo Acumulado</div><div class="value-num">$ {recaudado:,.0f}</div></div>'.replace(",", "."), unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="premio-box"><div style="font-size:1.1rem;">🏆 Premio ({draw["prize_percent"]:.0f}%)</div><div class="value-num">$ {premio:,.0f}</div></div>'.replace(",", "."), unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="timer-box"><div style="font-size:1.1rem;">⏱️ Tiempo Restante</div><div class="value-num">{horas:02d}:{minutos:02d}:{segundos:02d}</div></div>', unsafe_allow_html=True)

st.write("")

# Comprobación de retorno de pago por URL (retorno desde Mercado Pago)
query_params = st.query_params
if "payment_status" in query_params:
    if query_params["payment_status"] == "approved":
        st.success("🎉 ¡Pago aprobado con éxito! Tus tickets han sido asignados.")
    elif query_params["payment_status"] == "pending":
        st.warning("⌛ Tu pago está pendiente de aprobación.")

tab_comprar, tab_lista, tab_admin = st.tabs(["💳 Comprar Participaciones", "👥 Participantes", "⚙️ Administración"])

# --- TAB 1: COMPRA DE PARTICIPACIONES REALES ---
with tab_comprar:
    st.subheader("Adquirir Participaciones")
    
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        with st.form("checkout_form"):
            nombre = st.text_input("Nombre y Apellido*", placeholder="Ej: Juan Pérez")
            email = st.text_input("Correo Electrónico*", placeholder="ejemplo@email.com")
            cantidad = st.number_input("Cantidad de participaciones", min_value=1, max_value=50, value=1)
            
            total_pagar = cantidad * draw["price"]
            st.markdown(f"**Total a pagar: $ {total_pagar:,.0f} ARS**".replace(",", "."))
            
            submit = st.form_submit_button("💳 Pagar con Mercado Pago", type="primary")
            
            if submit:
                if not nombre or not email:
                    st.error("Por favor completa tu nombre y correo electrónico.")
                else:
                    # Crear preferencia de pago en Mercado Pago
                    preference_data = {
                        "items": [
                            {
                                "title": f"Participación Sorteo: {draw['name']}",
                                "quantity": int(cantidad),
                                "unit_price": float(draw["price"]),
                                "currency_id": "ARS"
                            }
                        ],
                        "payer": {
                            "name": nombre,
                            "email": email
                        },
                        "back_urls": {
                            "success": "https://tu-app.streamlit.app/?payment_status=approved",
                            "failure": "https://tu-app.streamlit.app/?payment_status=failed",
                            "pending": "https://tu-app.streamlit.app/?payment_status=pending"
                        },
                        "auto_return": "approved",
                        "external_reference": f"DRAW_{draw['id']}_{int(time.time())}"
                    }

                    preference_response = sdk.preference().create(preference_data)
                    preference = preference_response["response"]
                    
                    # Redirección al checkout seguro
                    init_point = preference["init_point"]
                    st.markdown(f'👉 [**Haz clic aquí para completar el pago de forma segura**]({init_point})')
                    st.link_button("Ir a Pagar", init_point, type="primary")

    with col_f2:
        st.markdown(f"""
        <div class="card">
            <b>Información General:</b><br>
            • Sorteo: <b>{draw['name']}</b><br>
            • Precio por unidad: <b>$ {draw['price']:,.0f}</b><br>
            • Participaciones emitidas: <b>{len(participants)}</b>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 2: LISTA DE PARTICIPACIONES ---
with tab_lista:
    st.subheader(f"🎟️ Tickets Confirmados ({len(participants)})")
    if participants:
        st.dataframe(
            [{"Ticket N°": p["ticket"], "Participante": p["name"], "Fecha": p["created_at"]} for p in participants],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aún no hay tickets confirmados mediante pago.")

# --- TAB 3: PANEL DE ADMINISTRACIÓN ---
with tab_admin:
    st.subheader("⚙️ Control del Sorteo")
    
    # Contraseña simple para el panel de administración
    admin_pass = st.text_input("Clave de Administrador", type="password")
    
    if admin_pass == st.secrets.get("ADMIN_PASSWORD", "admin123"):
        if st.button("🎲 CERRAR Y SORTEAR GANADOR", type="primary"):
            result = draw_winner(draw["id"])
            if result:
                st.balloons()
                st.success(f"🎉 Ganador confirmado: Ticket {result['ticket']} — {result['name']}")
            else:
                st.error("No hay tickets en el sorteo.")
