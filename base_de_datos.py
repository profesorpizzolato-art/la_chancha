import os
import random
import sqlite3
from datetime import datetime
import streamlit as st

# 1. IMPORTAR FUNCIONES DE BASE DE DATOS
# Si el archivo en tu repo se llama 'base_de_datos.py'
try:
    from base_de_datos import (
        init_db,
        create_draw,
        get_draw,
        get_participants,
        register_successful_payment,
        draw_winner,
        close_draw
    )
except ImportError:
    # Si el archivo en GitHub aún se llama 'base de datos.py' (con espacios)
    import importlib
    db = importlib.import_module("base de datos")
    init_db = db.init_db
    create_draw = db.create_draw
    get_draw = db.get_draw
    get_participants = db.get_participants
    register_successful_payment = db.register_successful_payment
    draw_winner = db.draw_winner
    close_draw = db.close_draw

# Configuración de página
st.set_page_config(
    page_title="La Chancha - Sorteos",
    page_icon="🐷",
    layout="wide"
)

# 2. Inicializar la Base de Datos
init_db()

# 3. Obtener o crear sorteo activo
draw = get_draw()
if not draw:
    create_draw(
        name="Sorteo La Chancha",
        price=1000.0,
        start=datetime.now(),
        end=datetime.now(),
        prize_percent=50.0
    )
    draw = get_draw()

participants = get_participants(draw["id"])

# Título Principal
st.title("🐷 La Chancha - Sistema de Sorteos")

# 4. Estructura de Pestañas
tab_comprar, tab_ganadores, tab_admin = st.tabs([
    "🛒 Adquirir Participaciones",
    "🏆 Ganadores",
    "⚙️ Panel de Control"
])

# ==========================================
# PESTAÑA 1: TRANSFERENCIA DIRECTA (CVU/ALIAS)
# ==========================================
with tab_comprar:
    st.subheader("Compra de Tickets por Transferencia Directa")
    
    col_form, col_info = st.columns([2, 1])
    
    with col_form:
        if draw.get("status") == "CLOSED":
            st.error("🔒 Este sorteo se encuentra cerrado actualmente. ¡Mantente atento al próximo!")
        else:
            with st.form("transfer_checkout_form"):
                nombre = st.text_input("Nombre y Apellido*", placeholder="Ej: Juan Pérez")
                email = st.text_input("Correo Electrónico*", placeholder="ejemplo@email.com")
                cantidad = st.number_input("Cantidad de participaciones", min_value=1, max_value=50, value=1)
                
                total_pagar = cantidad * draw["price"]
                st.markdown(f"### Total a transferir: **${total_pagar:,.0f} ARS**".replace(",", "."))
                
                # Datos bancarios / Mercado Pago para transferir
                st.info("""
                📌 **Datos para realizar la transferencia:**
                * **Alias:** `la.chancha.sorteos`
                * **CVU:** `0000003100012345678901`
                * **Titular:** Fabricio Pizzolato
                """)
                
                comprobante = st.text_input(
                    "Número de Comprobante / Operación*",
                    placeholder="Ej: 849201938"
                )
                
                enviar = st.form_submit_button("✅ Registrar Transferencia y Generar Tickets", type="primary")
                
                if enviar:
                    if not nombre.strip() or not email.strip() or not comprobante.strip():
                        st.error("⚠️ Todos los campos son obligatorios. Ingresa tu comprobante de pago.")
                    else:
                        payment_key = f"TRANSF-{comprobante.strip()}"
                        
                        # Se registran los tickets asociándolos al comprobante
                        tickets = register_successful_payment(
                            draw_id=draw["id"],
                            payment_id=payment_key,
                            name=nombre.strip(),
                            email=email.strip(),
                            quantity=int(cantidad)
                        )
                        
                        if tickets:
                            st.balloons()
                            st.success("🎉 ¡Pago registrado con éxito! Tus tickets asignados son:")
                            for t in tickets:
                                st.code(t, language="text")
                            st.rerun()

    with col_info:
        price_fmt = f"${draw['price']:,.0f}".replace(",", ".")
        st.markdown(f"""
        <div style="background-color: #1e222d; padding: 20px; border-radius: 8px; border: 1px solid #333;">
            <h4 style="margin-top:0;">Detalles del Sorteo</h4>
            • <b>Sorteo:</b> {draw['name']}<br>
            • <b>Estado:</b> {draw['status']}<br>
            • <b>Valor por ticket:</b> {price_fmt} ARS<br>
            • <b>Tickets emitidos:</b> {len(participants)}
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# PESTAÑA 2: GANADORES
# ==========================================
with tab_ganadores:
    st.subheader("🏆 Ganadores")
    if draw.get("status") == "CLOSED" and draw.get("winning_ticket"):
        st.success(f"🎟 **Ticket Ganador del Sorteo:** `{draw['winning_ticket']}`")
    else:
        st.info("El sorteo actual está activo. El ganador se publicará al momento del cierre.")

# ==========================================
# PESTAÑA 3: ADMINISTRACIÓN
# ==========================================
with tab_admin:
    st.subheader("⚙️ Panel de Administración")
    
    col_admin1, col_admin2 = st.columns([2, 1])
    
    with col_admin1:
        st.write("### Participantes Registrados")
        if participants:
            st.dataframe(participants, use_container_width=True)
        else:
            st.write("Aún no hay participantes registrados.")

    with col_admin2:
        st.write("### Acciones")
        if draw.get("status") == "ACTIVE":
            if st.button("🎲 Realizar Sorteo / Elegir Ganador", type="primary"):
                winner = draw_winner(draw["id"])
                if winner:
                    st.balloons()
                    st.success(f"¡Ganador seleccionado! Ticket: {winner['ticket']} - Nombre: {winner['name']}")
                    st.rerun()
                else:
                    st.warning("No se puede realizar el sorteo sin participantes.")
