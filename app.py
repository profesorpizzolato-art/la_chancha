import sys
import os
import time
import random
from datetime import datetime

import streamlit as st

# Asegurar path correcto para Streamlit Cloud
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_db,
    get_draw,
    create_draw,
    add_demo_participants,
    draw_winner,
    get_participants
)

# Configuración de la página
st.set_page_config(page_title="LA CHANCHA 🐷", page_icon="🐷", layout="wide")
init_db()

# Estilos CSS dinámicos
st.markdown("""
<style>
.main-title { font-size: 3.5rem; font-weight: 900; color: #E63946; line-height: 1; }
.subtitle { font-size: 1.1rem; color: #6c757d; margin-bottom: 1rem; }
.pozo-box {
    background: linear-gradient(135deg, #11998e, #38ef7d);
    color: white;
    padding: 1.5rem;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}
.premio-box {
    background: linear-gradient(135deg, #FF416C, #FF4B2B);
    color: white;
    padding: 1.5rem;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}
.timer-box {
    background: linear-gradient(135deg, #8A2387, #E94057, #F27121);
    color: white;
    padding: 1.5rem;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}
.value-num { font-size: 2.8rem; font-weight: 900; }
.card { padding: 1.2rem; border-radius: 15px; background: #f8f9fa; border: 1px solid #e9ecef; }
</style>
""", unsafe_allow_html=True)

# Encabezado
st.markdown('<div class="main-title">🐷 LA CHANCHA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">La suerte se junta. Sorteos transparentes en tiempo real.</div>', unsafe_allow_html=True)
st.divider()

draw = get_draw()

# Si no hay sorteo activo
if not draw:
    st.info("👋 No hay ningún sorteo activo en este momento.")
    if st.button("🐷 Crear primer sorteo demo", type="primary", use_container_width=True):
        create_draw(
            name="El Primer Chanchazo 🚀",
            price=1000,
            start=datetime.now().isoformat(),
            end=(datetime.now() + timedelta(hours=24)).isoformat(),
            prize_percent=50
        )
        st.rerun()
    st.stop()

# Datos del sorteo activo
participants = get_participants(draw["id"])
recaudado = len(participants) * draw["price"]
premio = recaudado * draw["prize_percent"] / 100

# Cálculo de tiempo restante
end_time = datetime.fromisoformat(draw["end"])
ahora = datetime.now()
restante = max(0, int((end_time - ahora).total_seconds()))

horas, rem = divmod(restante, 3600)
minutos, segundos = divmod(rem, 60)

# Métrica e Indicadores Principales
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="pozo-box">
        <div style="font-size:1.1rem;">💰 Pozo Acumulado</div>
        <div class="value-num">$ {recaudado:,.0f}</div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="premio-box">
        <div style="font-size:1.1rem;">🏆 Premio ({draw['prize_percent']:.0f}%)</div>
        <div class="value-num">$ {premio:,.0f}</div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="timer-box">
        <div style="font-size:1.1rem;">⏱️ Tiempo Restante</div>
        <div class="value-num">{horas:02d}:{minutos:02d}:{segundos:02d}</div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

st.write("")

# Si el sorteo ya fue cerrado
if draw.get("status") == "CLOSED":
    st.balloons()
    st.success(f"🎉 **SORTEO CERRADO** — Ticket Ganador: **{draw.get('winning_ticket')}**")

# Navegación por Pestañas (Tabbed UI)
tab_participar, tab_participantes, tab_admin = st.tabs([
    "🎟️ Participar / Registro",
    "👥 Lista de Participaciones",
    "🧪 Panel de Control / Demo"
])

# --- TAB 1: REGISTRO DINÁMICO DE PARTICIPANTE ---
with tab_participar:
    st.subheader("¡Sumate al Pozo!")
    col_f1, col_f2 = st.columns([2, 1])
    
    with col_f1:
        nombre_usuario = st.text_input("Tu Nombre / Apodo:", placeholder="Ej: Fabricio P.")
        if st.button("🎟️ Comprar 1 Participación ($ " + f"{draw['price']:,.0f}".replace(",", ".") + ")", type="primary"):
            if nombre_usuario.strip():
                # Reutilizamos add_demo para insertar participant o creamos uno directo
                from database import conn
                c = conn()
                cur = c.cursor()
                t_num = f"LC-{random.randint(100000, 999999)}-{random.randint(10, 99)}"
                cur.execute(
                    "INSERT INTO participants(draw_id, ticket, name, created_at) VALUES(?, ?, ?, ?)",
                    (draw["id"], t_num, nombre_usuario.strip(), datetime.now().isoformat())
                )
                c.commit()
                c.close()
                st.toast(f"¡Ticket generado con éxito! Tu número es {t_num}", icon="🎉")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Por favor ingresa un nombre para la participación.")

    with col_f2:
        st.markdown(f"""
        <div class="card">
            <b>Detalles de la Ronda:</b><br>
            • Evento: <b>{draw['name']}</b><br>
            • Estado: <b>{draw['status']}</b><br>
            • Total Tickets: <b>{len(participants)}</b>
        </div>
        """, unsafe_allow_html=True)

# --- TAB 2: TABLA DE PARTICIPANTES ---
with tab_participantes:
    st.subheader(f"🎟️ Participaciones Registradas ({len(participants)})")
    if participants:
        st.dataframe(
            [{"Ticket N°": p["ticket"], "Participante": p["name"], "Fecha / Hora": p["created_at"]} for p in participants],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aún no hay participaciones registradas en este sorteo.")

# --- TAB 3: PANEL DE CONTROL Y SIMULACIÓN ANIMADA ---
with tab_admin:
    st.subheader("🧪 Herramientas de Simulación")
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("➕ Cargar 10 Participaciones Demo"):
            add_demo_participants(draw["id"], 10, draw["price"])
            st.toast("10 Participaciones agregadas.", icon="🎟️")
            st.rerun()
            
    with c_btn2:
        if st.button("🚀 Cargar 50 Participaciones Demo"):
            add_demo_participants(draw["id"], 50, draw["price"])
            st.toast("50 Participaciones agregadas.", icon="🚀")
            st.rerun()

    st.divider()
    st.subheader("🎲 Ejecución con Animación (Ruleta)")
    
    if st.button("🔥 ¡EJECUTAR GRAN SORTEO EN VIVO!", type="primary", use_container_width=True):
        if len(participants) == 0:
            st.error("No hay participaciones registradas para realizar el sorteo.")
        else:
            # --- ANIMACIÓN DE RULETA ---
            placeholder = st.empty()
            st.toast("Iniciando selección aleatoria...", icon="🎲")
            
            # Efecto ruleta rápida
            for _ in range(25):
                temp_pick = random.choice(participants)
                placeholder.markdown(f"""
                <div style="text-align:center; padding: 20px; background: #FFF3CD; border-radius: 15px;">
                    <h2 style="color: #856404; margin:0;">Mezclando boletos... 🎰</h2>
                    <h1 style="color: #D39E00; font-size: 3rem; margin:0;">{temp_pick['ticket']}</h1>
                    <p style="font-size:1.5rem; margin:0;">👤 {temp_pick['name']}</p>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.08)
                
            # Elección definitiva usando motor seguro
            result = draw_winner(draw["id"])
            placeholder.empty()
            
            if result:
                st.balloons()
                st.markdown(f"""
                <div style="text-align:center; padding: 25px; background: #D4EDDA; border-radius: 18px; border: 2px solid #28A745;">
                    <h1 style="color: #155724; margin:0;">🎉 ¡TENEMOS GANADOR! 🎉</h1>
                    <h1 style="color: #28A745; font-size: 3.5rem; margin:10px 0;">Ticket: {result['ticket']}</h1>
                    <h2 style="color: #155724; margin:0;">👤 Ganador/a: {result['name']}</h2>
                </div>
                """, unsafe_allow_html=True)

st.divider()
st.caption("🔒 MVP Educativo / Demo interactivo. Los datos se almacenan en SQLite local.")
