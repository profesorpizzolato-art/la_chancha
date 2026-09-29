import streamlit as st
from datetime import datetime, timedelta
from database import init_db, get_draw, create_draw, add_demo_participants, draw_winner, get_participants

st.set_page_config(page_title="LA CHANCHA", page_icon="🐷", layout="wide")
init_db()

st.markdown("""
<style>
.main-title {font-size: 4rem; font-weight: 900; line-height: .9;}
.subtitle {font-size: 1.2rem; opacity: .75;}
.pozo {font-size: 3.2rem; font-weight: 900;}
.card {padding: 1.2rem; border-radius: 20px; background: #f4f4f6; margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🐷 LA CHANCHA</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">La suerte se junta.</div>', unsafe_allow_html=True)
st.divider()

draw = get_draw()

if not draw:
    st.info("Todavía no existe un sorteo demo.")
    if st.button("🐷 Crear primer sorteo demo", type="primary"):
        create_draw(
            name="El Primer Chanchazo",
            price=1000,
            start=datetime.now().isoformat(),
            end=(datetime.now() + timedelta(hours=24)).isoformat(), 
            prize_percent=50
        )
        st.rerun()
    st.stop()

participants = get_participants(draw["id"])
recaudado = len(participants) * draw["price"]
premio = recaudado * draw["prize_percent"] / 100
restante = max(0, int((datetime.fromisoformat(draw["end"]) - datetime.now()).total_seconds()))
horas, rem = divmod(restante, 3600)
minutos, segundos = divmod(rem, 60)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### 💰 Pozo actual")
    st.markdown(f'<div class="pozo">$ {recaudado:,.0f}</div>'.replace(",", "."), unsafe_allow_html=True)
with c2:
    st.markdown("### 🏆 Premio")
    st.markdown(f'<div class="pozo">$ {premio:,.0f}</div>'.replace(",", "."), unsafe_allow_html=True)
with c3:
    st.markdown("### ⏱️ Tiempo restante")
    st.markdown(f'<div class="pozo">{horas:02d}:{minutos:02d}:{segundos:02d}</div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="card">
<b>{draw["name"]}</b><br>
Participaciones: {len(participants)}<br>
Valor por participación demo: $ {draw["price"]:,.0f}<br>
Premio configurado: {draw["prize_percent"]:.0f}% del pozo
</div>
""".replace(",", "."), unsafe_allow_html=True)

st.subheader("🧪 Panel de prueba")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🎟️ Agregar 10 participaciones demo"):
        add_demo_participants(draw["id"], 10, draw["price"])
        st.rerun()
with col2:
    if st.button("🎟️ Agregar 100 participaciones demo"):
        add_demo_participants(draw["id"], 100, draw["price"])
        st.rerun()
with col3:
    if st.button("🎲 Ejecutar sorteo demo", type="primary"):
        result = draw_winner(draw["id"])
        if result:
            st.success(f"Ganador demo: Ticket N° {result['ticket']} — {result['name']}")
        else:
            st.warning("No hay participaciones para sortear.")

st.caption("MVP educativo/demo. No procesa pagos ni constituye un sistema habilitado para juegos de azar.")

st.subheader("🎟️ Participaciones")
if participants:
    st.dataframe(
        [{"Número": p["ticket"], "Participante": p["name"], "Fecha": p["created_at"]} for p in participants],
        use_container_width=True,
        hide_index=True
    )
else:
    st.write("No hay participaciones todavía.")
