import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Tarjeta de Presentación",
    page_icon="🛢️",
    layout="centered"
)

# Renderizado del HTML sin espacios invisibles de sangría
st.markdown(
"""
<style>
.card {
    background-color: #1e1e1e;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    border: 1px solid #333;
    color: #ffffff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin-bottom: 20px;
}
.card-header {
    font-size: 22px;
    font-weight: 700;
    color: #00adb5;
    margin-bottom: 8px;
}
.card-subtitle {
    font-size: 14px;
    color: #aaaaaa;
    margin-bottom: 16px;
}
.card-body {
    font-size: 15px;
    line-height: 1.6;
    color: #dddddd;
}
</style>

<div class="card">
    <div class="card-header">MENFA Capacitaciones</div>
    <div class="card-subtitle">Simuladores Operativos & Formación Técnica Industrial</div>
    <div class="card-body">
        Plataforma interactiva para la formación en perforación, producción de hidrocarburos,
        sistemas SCADA y control de pozos.
    </div>
</div>
""",
    unsafe_allow_html=True
)
