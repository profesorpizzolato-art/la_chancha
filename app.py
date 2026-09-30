import os
import time
import random
import sqlite3
from datetime import datetime
import streamlit as st
import mercadopago

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
    page_title="La Chancha - Sorteos",
    page_icon="🐷",
    layout="wide"
)

# 2. Inicializar la Base de Datos SQLite
init_db()

# 3. Inicializar el SDK de Mercado Pago desde los Secrets de Streamlit
mp_access_token = st.secrets.get("MP_ACCESS_TOKEN", "")
sdk = mercadopago.SDK(mp_access_token) if mp_access_token else None

# 4. Obtener o crear datos del sorteo activo
draw = get_draw()
if not draw:
    create_draw(
        name="Sorteo Inicial La Chancha",
        price=1000.0,
        start=datetime.now(),
        end=datetime.now(),
        prize_percent=50.0
    )
    draw = get_draw()

participants = get_participants(draw["id"])

# Título Principal
st.title("🐷 La Chancha - Sistema de Sorteos")

# 5. Definición de Pestañas
tab_comprar, tab_ganadores, tab_admin = st.tabs([
    "🛒 Adquirir Participaciones",
    "🏆 Ganadores",
    "⚙️ Panel de Administración"
])

# ==========================================
# PESTAÑA 1: ADQUIRIR PARTICIPACIONES
# ==========================================
with tab_comprar:
    st.subheader("Adquirir Participaciones")
    
    col_f1, col_f2 = st.columns([2, 1])
    
    with col_f1:
        if draw.get("status") == "CLOSED":
            st.error("🔒 Este sorteo ya se encuentra cerrado. ¡Te esperamos en el próximo!")
        else:
            st.markdown("### Opción A: Generar Pago Instantáneo (API Mercado Pago)")
            
            with st.form("checkout_form"):
                nombre = st.text_input("Nombre y Apellido*", placeholder="Ej: Juan Pérez")
                email = st.text_input("Correo Electrónico*", placeholder="ejemplo@email.com")
                cantidad = st.number_input("Cantidad de participaciones", min_value=1, max_value=50, value=1)
                
                total_pagar = cantidad * draw["price"]
                total_str = f"**Total a pagar: ${total_pagar:,.0f} ARS**".replace(",", ".")
                st.markdown(total_str)
                
                enviar = st.form_submit_button("💳 Pagar con Mercado Pago", type="primary")
                
                if enviar:
                    if not nombre.strip() or not email.strip():
                        st.error("⚠️ Por favor completa tu nombre y correo electrónico.")
                    elif not sdk:
                        st.error("🔑 Falta configurar `MP_ACCESS_TOKEN` en los Secrets de Streamlit.")
                    else:
                        base_url = st.secrets.get("APP_URL", "https://tu-app.streamlit.app")
                        clean_name = nombre.strip().replace("&", "y")
                        clean_email = email.strip()

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
                                "name": clean_name,
                                "email": clean_email
                            },
                            "back_urls": {
                                "success": f"{base_url}/?payment_status=approved&p_name={clean_name}&p_email={clean_email}&p_qty={cantidad}",
                                "failure": f"{base_url}/?payment_status=failed",
                                "pending": f"{base_url}/?payment_status=pending"
                            },
                            "auto_return": "approved",
                            "external_reference": f"DRAW_{draw['id']}_{int(time.time())}"
                        }

                        with st.spinner("Conectando con Mercado Pago..."):
                            try:
                                preference_response = sdk.preference().create(preference_data)
                                status_code = preference_response.get("status")
                                response_body = preference_response.get("response", {})
                                
                                if status_code in [200, 201]:
                                    init_point = response_body.get("init_point")
                                    st.success("✅ Orden generada correctamente.")
                                    st.link_button("👉 Abrir Pasarela de Mercado Pago", init_point, type="primary", use_container_width=True)
                                else:
                                    st.error(f"❌ Error de API ({status_code}): {response_body.get('message', 'Respuesta no válida')}")
                                    st.json(response_body)
                                    
                            except Exception as e:
                                st.error(f"🚨 Excepción al conectar con Mercado Pago: {e}")

            st.markdown("---")
            st.markdown("### Opción B: Link Directo y Registro de Comprobante")
            st.caption("Si prefieres pagar mediante un Link de Pago fijo o transferencia, realiza el pago y valida tu comprobante aquí:")
            
            # Puedes sustituir por tu Link de Pago estático de Mercado Pago en Secrets o directo
            static_mp_link = st.secrets.get("MP_STATIC_LINK", "https://mpago.la/19yACmp")
            st.link_button("🔗 Abrir Link de Pago Directo", static_mp_link)

            with st.form("manual_validation_form"):
                m_nombre = st.text_input("Nombre y Apellido*", key="m_name")
                m_email = st.text_input("Correo Electrónico*", key="m_email")
                m_cantidad = st.number_input("Cantidad abonada", min_value=1, max_value=50, value=1, key="m_qty")
                m_comprobante = st.text_input("Nº de Operación / Comprobante Mercado Pago*", placeholder="Ej: 987654321")
                
                m_enviar = st.form_submit_button("✅ Validar Comprobante y Obtener Tickets")
                
                if m_enviar:
                    if not m_nombre.strip() or not m_email.strip() or not m_comprobante.strip():
                        st.error("⚠️ Por favor completa todos los campos requeridos.")
                    else:
                        payment_key = f"MP-MANUAL-{m_comprobante.strip()}"
                        tickets = register_successful_payment(
                            draw_id=draw["id"],
                            payment_id=payment_key,
                            name=m_nombre.strip(),
                            email=m_email.strip(),
                            quantity=int(m_cantidad)
                        )
                        if tickets:
                            st.balloons()
                            st.success("🎉 ¡Pago registrado con éxito! Tus tickets son:")
                            for t in tickets:
                                st.code(t, language="text")
                            st.rerun()

    with col_f2:
        price_fmt = f"${draw['price']:,.0f}".replace(",", ".")
        st.markdown(f"""
        <div style="background-color: #1e222d; padding: 18px; border-radius: 8px; border: 1px solid #333;">
            <h4 style="margin-top:0;">Información General:</h4>
            • Sorteo: <b>{draw['name']}</b><br>
            • Estado: <b>{draw['status']}</b><br>
            • Precio por ticket: <b>{price_fmt} ARS</b><br>
            • Participaciones emitidas: <b>{len(participants)}</b>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PESTAÑA 2: GANADORES
# ==========================================
with tab_ganadores:
    st.subheader("🏆 Ganadores de Sorteos")
    if draw.get("status") == "CLOSED" and draw.get("winning_ticket"):
        st.success(f"🎟 Ticket Ganador del Sorteo: **{draw['winning_ticket']}**")
    else:
        st.info("El sorteo actual está activo. El ganador se publicará automáticamente al cerrar el sorteo.")

# ==========================================
# PESTAÑA 3: ADMINISTRACIÓN
# ==========================================
with tab_admin:
    st.subheader("⚙️ Panel de Administración")
    
    col_adm1, col_adm2 = st.columns([2, 1])
    
    with col_adm1:
        st.write("### Lista de Participantes")
        if participants:
            st.dataframe(participants, use_container_width=True)
        else:
            st.info("Aún no hay participantes registrados en este sorteo.")

    with col_adm2:
        st.write("### Control del Sorteo")
        if draw.get("status") == "ACTIVE":
            if st.button("🎲 Sortear y Elegir Ganador", type="primary", use_container_width=True):
                winner = draw_winner(draw["id"])
                if winner:
                    st.balloons()
                    st.success(f"¡Ganador Seleccionado! Ticket: **{winner['ticket']}** - Nombre: **{winner['name']}**")
                    st.rerun()
                else:
                    st.warning("No hay participantes suficientes para ejecutar el sorteo.")
        else:
            st.write("El sorteo se encuentra cerrado.")
