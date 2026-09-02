import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Consulta", layout="wide")

# ----------------------------------------------------------------------------
# Paleta / helpers
# ----------------------------------------------------------------------------
GRID = "rgba(255,255,255,0.06)"
MUTED = "#8A8A93"
PURPLE = "#7C6CF6"

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=MUTED, size=12),
    margin=dict(l=10, r=10, t=10, b=10),
    showlegend=False,
)


def dados_ficticios():
    """Dados sintéticos usados até a integração com a equipe de dados."""
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul"]
    este_ano = [11, 12, 10, 15, 27, 22, 24]
    ano_passado = [7, 10, 12, 13, 18, 16, 23]
    return meses, este_ano, ano_passado


MESES, ESTE_ANO, ANO_PASSADO = dados_ficticios()

# ----------------------------------------------------------------------------
# Cabeçalho + barra de pesquisa
# ----------------------------------------------------------------------------
st.title("Consulta em Linguagem Natural")
st.caption("Pesquise um indicador, escola ou bairro para ver o painel correspondente.")

with st.form("busca_consulta"):
    busca = st.text_input(
        "Pesquisar",
        value=st.session_state.get("termo_busca", ""),
        placeholder="🔍  Pesquisar indicadores, escolas, bairros...",
        label_visibility="collapsed",
        key="busca_consulta",
    )
    pesquisar = st.form_submit_button("Buscar")

if pesquisar:
    if busca:
        st.session_state["termo_busca"] = busca
    else:
        st.warning("Digite um termo para pesquisar.")

resultado = st.session_state.get("termo_busca")

if not resultado:
    st.info("Faça uma pesquisa acima para visualizar o painel.")
    st.stop()

st.success(
    f"Resultados para: **{resultado}** — usando dados fictícios até a integração "
    "com a equipe de dados."
)

st.divider()

# ----------------------------------------------------------------------------
# Dashboard — linha 1
# ----------------------------------------------------------------------------
col_users, col_site = st.columns([2, 1], gap="large")

with col_users:
    st.subheader("Total de Usuários")
    st.caption("● Este ano   ·   ⋯ Ano passado")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=MESES,
            y=[v * 1000 for v in ANO_PASSADO],
            mode="lines",
            line=dict(color=MUTED, width=2, dash="dot", shape="spline"),
            hovertemplate="%{y:,.0f}<extra>Ano passado</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=MESES,
            y=[v * 1000 for v in ESTE_ANO],
            mode="lines",
            line=dict(color=PURPLE, width=3, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(124,108,246,0.12)",
            hovertemplate="%{y:,.0f}<extra>Este ano</extra>",
        )
    )
    fig.update_layout(height=320, **CHART_LAYOUT)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, tickformat="~s")
    st.plotly_chart(fig, use_container_width=True)

with col_site:
    st.subheader("Tráfego por Site")
    sites = ["Google", "YouTube", "Instagram", "Pinterest", "Facebook", "Twitter"]
    valores = [88, 72, 54, 100, 41, 29]
    fig = go.Figure(
        go.Bar(
            x=valores,
            y=sites,
            orientation="h",
            marker=dict(color="#D9D9DE"),
            width=0.35,
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    fig.update_layout(height=320, **CHART_LAYOUT)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# Dashboard — linha 2
# ----------------------------------------------------------------------------
col_device, col_loc = st.columns(2, gap="large")

with col_device:
    st.subheader("Tráfego por Dispositivo")
    cats = ["Linux", "Mac", "iOS", "Windows", "Android", "Outros"]
    vals = [16, 32, 21, 35, 14, 28]
    cores = ["#8FB4F2", "#5FE0C0", "#B79CF0", "#7FC8F0", "#B79CF0", "#7BE0A8"]
    fig = go.Figure(
        go.Bar(x=cats, y=[v * 1000 for v in vals], marker=dict(color=cores), width=0.55)
    )
    fig.update_layout(height=300, **CHART_LAYOUT)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, tickformat="~s")
    st.plotly_chart(fig, use_container_width=True)

with col_loc:
    st.subheader("Tráfego por Localização")
    labels = ["Estados Unidos", "Canadá", "México", "Outros"]
    pcts = [52.1, 22.8, 13.9, 11.2]
    cores = ["#B79CF0", "#8FB4F2", "#7FC8F0", "#7BE0A8"]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=pcts,
            hole=0.62,
            marker=dict(colors=cores),
            textinfo="none",
            sort=False,
            direction="clockwise",
        )
    )
    fig.update_layout(
        height=300,
        showlegend=True,
        legend=dict(orientation="v", x=1.0, y=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MUTED, size=12),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# Campo de texto abaixo do dashboard
# ----------------------------------------------------------------------------
st.divider()
anotacoes = st.text_area(
    "Anotações",
    placeholder="Escreva observações, hipóteses ou perguntas sobre os dados acima...",
    height=140,
)
if anotacoes:
    st.success("Anotação registrada (sessão atual).")
