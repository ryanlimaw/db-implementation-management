"""OpenF1 Data Explorer - interface Streamlit (Prática 04).

Executar a partir da pasta exercise-4:
    streamlit run src/streamlit_app.py
"""

import plotly.express as px
import streamlit as st
from pymongo.errors import PyMongoError

import services

st.set_page_config(page_title="OpenF1 Data Explorer", layout="wide")
st.title("OpenF1 Data Explorer")
st.write("Visualização dos tempos de volta armazenados no MongoDB (banco openf1_data).")

try:
    anos = services.listar_anos()
except PyMongoError as erro:
    st.error("Não foi possível conectar ao MongoDB. Verifique se o servidor está rodando "
             "e o MONGO_URI em .streamlit/secrets.toml.")
    with st.expander("Detalhes técnicos"):
        st.code(str(erro), language=None)
    st.stop()

if not anos:
    st.info("Nenhuma sessão no banco. Rode antes o coletor do exercise-1.")
    st.stop()

# ---- Seleção de ano e sessão ----
with st.sidebar:
    st.header("Filtros")
    ano = st.selectbox("Ano", anos)
    somente_corridas = st.checkbox("Mostrar só corridas (Race)", value=True)
    sessoes = services.listar_sessoes(ano, somente_corridas)
    if not sessoes:
        st.info("Nenhuma sessão encontrada para esse filtro.")
        st.stop()
    sessao_escolhida = st.selectbox("Sessão", sessoes, format_func=services.rotulo_sessao)

session_key = sessao_escolhida["session_key"]
sessao = services.obter_sessao(session_key)

# ---- Detalhes da sessão ----
st.subheader(services.rotulo_sessao(sessao))
c1, c2, c3, c4 = st.columns(4)
c1.metric("País", sessao.get("country_name", "-"))
c2.metric("Circuito", sessao.get("circuit_short_name", "-"))
c3.metric("Data", (sessao.get("date_start") or "-")[:10])
c4.metric("Sessão", f"{sessao.get('session_name', '-')} ({session_key})")

# ---- Seleção de pilotos ----
pilotos = services.listar_pilotos(session_key)
if not pilotos:
    st.info("Não há pilotos salvos para essa sessão.")
    st.stop()

nomes = {p["driver_number"]: services.nome_piloto(p) for p in pilotos}
escolhidos = st.multiselect("Pilotos", list(nomes), format_func=lambda n: nomes[n])
if not escolhidos:
    st.info("Selecione um ou mais pilotos para ver os tempos de volta.")
    st.stop()

# ---- Gráfico e tabela ----
voltas = services.buscar_voltas(session_key, escolhidos)
if voltas.empty:
    st.info("Não há voltas salvas para os pilotos selecionados.")
    st.stop()

voltas.insert(0, "piloto", voltas["driver_number"].map(nomes))
grafico = voltas.dropna(subset=["lap_duration"])
descartadas = len(voltas) - len(grafico)

if grafico.empty:
    st.info("Nenhuma volta com tempo registrado para os pilotos selecionados.")
else:
    fig = px.line(grafico, x="lap_number", y="lap_duration", color="piloto", markers=True,
                  labels={"lap_number": "Volta", "lap_duration": "Tempo de volta (s)",
                          "piloto": "Piloto"},
                  title="Tempo de volta por volta")
    st.plotly_chart(fig, width="stretch")
st.caption(f"{descartadas} volta(s) sem lap_duration (dado ausente na API, ex.: última volta) "
           "ficaram fora do gráfico, mas aparecem na tabela.")

with st.expander("Ver tabela de dados"):
    st.dataframe(voltas, width="stretch", hide_index=True)
