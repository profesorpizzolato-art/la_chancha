import os
import time
import random
import sqlite3
from datetime import datetime
import streamlit as st
import mercadopago

# Importar funciones de base de datos desde tu archivo base_de_datos.py
try:
    from base_de_datos import get_draw, get_participants, init_db
    init_db()
except ImportError:
    pass

st.set_page_config(page_title="La Chancha - Sorteos", page_icon="🐷", layout="wide")

# 1. Inicialización segura del SDK de Mercado Pago
mp_access_token = st.secrets.get("MP_ACCESS_TOKEN", "")
sdk = mercadopago.SDK(mp_access_token) if mp_access_token else None

# Obtener datos del sorteo activo
draw = get_draw() or {
    "id": 1,
    "name": "Sorteo Demo",
    "price": 1000.0,
    "status": "ACTIVE"
}
participants = get_participants(draw["id"]) if "get_participants" in globals() else []

st.title("🐷 La Chancha - Sistema de Sorteos")

# 2. DEFINICIÓN DE PESTAÑAS (Esto resuelve el NameError)
tab_comprar, tab_ganadores, tab_admin = st.tabs(["🛒 Comprar Participaciones", "🏆 Ganadores", "⚙️ Administración"])

# --- PESTAÑA 1: COMPRA DE PARTICIPACIONES ---
with tab_comprar:
    st.subheader("Adquirir Participaciones")
    
    col_f1, col_f2 = st.columns([2, 1])
    
    with col_f1:
        if draw.get("status") == "CLOSED":
            st.error("🔒 Este sorteo ya se encuentra cerrado. Espera al próximo.")
        else:
            with st.form("checkout_form"):
                nombre = st.text_input("Nombre y Apellido*", placeholder="Ej: Juan Pérez")
                email = st.text_input("Correo Electrónico*", placeholder="ejemplo@email.com")
                cantidad = st.number_input("Cantidad de participaciones", min_value=1, max_value=50, value=1)
                
                total_pagar = cantidad * draw["price"]
                total_str = f"**Total a pagar: ${total_pagar:,.0f} ARS**".replace(",", ".")
                st.markdown(total_str)
                
                enviar = st.form_submit_button("💳 Pagar con Mercado Pago", type="primary")
                
                if enviar:
                    if not nombre or not email:
                        st.error("⚠️️ Por favor completa tu nombre y correo electrónico.")
                    elif not sdk:
                        st.error("🔑 Falta configurar `MP_ACCESS_TOKEN` en los Secrets de Streamlit.")
                    else:
                        base_url = st.secrets.get("APP_URL", "https://tu-app.streamlit.app")
                        clean_name = nombre.strip().replace("&", "y")
                        clean_email = email.strip()

                        # Preferencia de Mercado Pago
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

                        # Conexión con spinner
                        with st.spinner("Conectando con Mercado Pago..."):
                            try:
                                preference_response = sdk.preference().create(preference_data)
                                status_code = preference_response.get("status")
                                response_body = preference_response.get("response", {})
                                
                                if status_code in [200, 201]:
                                    init_point = response_body.get("init_point")
                                    st.success("✅ Pre-orden generada correctamente.")
                                    st.link_button("👉 Abrir Pasarela de Mercado Pago", init_point, type="primary", use_container_width=True)
                                else:
                                    st.error(f"❌ Error de API ({status_code}): {response_body.get('message', 'Respuesta no válida')}")
                                    st.json(response_body)
                                    
                            except Exception as e:
                                st.error(f"🚨 Excepción al conectar con Mercado Pago: {e}")

    with col_f2:
        price_fmt = f"${draw['price']:,.0f}".replace(",", ".")
        st.markdown(f"""
        <div style="background-color: #1e222d; padding: 15px; border-radius: 8px;">
            <b>Información General:</b><br>
            • Sorteo: <b>{draw['name']}</b><br>
            • Estado: <b>{draw['status']}</b><br>
            • Precio por unidad: <b>{price_fmt}</b><br>
            • Participaciones emitidas: <b>{len(participants)}</b>
        </div>
        """, unsafe_allow_html=True)

with tab_ganadores:
    st.subheader("🏆 Ganadores de Sorteos Anteriores")
    st.info("Aquí se mostrarán los ganadores de los sorteos finalizados.")

with tab_admin:
    st.subheader("⚙️ Panel de Administración")
    st.info("Espacio para gestionar los sorteos y ver las ventas.")
