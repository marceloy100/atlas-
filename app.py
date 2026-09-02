"""
ATLAS Escolar — Dados Públicos para Diagnóstico das Desigualdades Educacionais
================================================================================

Aplicação Streamlit de página única (single-file) que integra (de forma
simulada, com dados fictícios) informações do Censo Escolar, ENEM e IBGE para
gerar um diagnóstico acessível de infraestrutura, acesso digital e desempenho
de escolas públicas — com foco na região de Coelho Neto/MA.

Como executar:
    streamlit run app.py

Todos os dados usados neste protótipo são FICTÍCIOS e servem apenas para
demonstrar o funcionamento da interface até a integração com bases reais.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="ATLAS Escolar — Diagnóstico Educacional",
    layout="wide",
)

# ==============================================================================
# 2. CSS CUSTOMIZADO (cards de KPI, badges, espaçamentos, paleta acessível)
# ==============================================================================
st.markdown(
    """
    <style>
    :root {
        --atlas-azul: #1F6FEB;
        --atlas-azul-escuro: #0B4F9E;
        --atlas-verde: #2E7D32;
        --atlas-cinza-texto: #5A6472;
        --atlas-cinza-borda: #E3E8EF;
    }

    /* Espaçamento geral e tipografia */
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }
    h1, h2, h3 { font-weight: 700; }
    [data-testid="stCaptionContainer"] { color: var(--atlas-cinza-texto); }

    /* Cards de métrica (st.metric) em formato de card */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid var(--atlas-cinza-borda);
        border-radius: 14px;
        padding: 1.1rem 1.2rem 0.9rem 1.2rem;
        box-shadow: 0 1px 3px rgba(16, 24, 40, 0.06);
    }
    [data-testid="stMetricLabel"] { font-weight: 600; color: var(--atlas-cinza-texto); }
    [data-testid="stMetricValue"] { color: var(--atlas-azul-escuro); }

    /* Cards de recomendação (Aba 3) */
    .atlas-card {
        background: #FFFFFF;
        border: 1px solid var(--atlas-cinza-borda);
        border-left: 6px solid var(--atlas-azul);
        border-radius: 14px;
        padding: 1.3rem 1.6rem;
        margin-bottom: 1.1rem;
    }
    .atlas-card.atlas-card-verde { border-left-color: var(--atlas-verde); }
    .atlas-card, .atlas-card p, .atlas-card li { color: #1F2937; }
    .atlas-card h4 { margin-top: 0; margin-bottom: 0.5rem; color: #0B1220; }
    .atlas-card ul { margin-bottom: 0; }
    .atlas-card strong { color: #0B1220; }

    /* Badges (pílulas) de status */
    .atlas-badge {
        display: inline-block;
        padding: 0.22rem 0.75rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
    }
    .badge-verde   { background: #E7F5EC; color: #1E7A34; }
    .badge-amarelo { background: #FFF4E0; color: #9A6700; }
    .badge-cinza   { background: #F1F3F5; color: #495057; }
    .badge-vermelho{ background: #FDECEC; color: #C0392B; }

    /* Botões (chips de sugestão de pergunta) */
    div[data-testid="stButton"] > button {
        border-radius: 999px;
        border: 1px solid var(--atlas-cinza-borda);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. DADOS SIMULADOS (MOCK) — Censo Escolar / ENEM / IBGE (fictícios)
# ==============================================================================
NOMES_INFRA = {
    "Computadores_por_Aluno": "Computadores por Aluno",
    "Lab_Informatica": "Laboratório de Informática",
    "Banda_Larga": "Banda Larga",
    "Lab_Ciencias": "Laboratório de Ciências",
    "Espaco_Maker": "Espaço Maker",
}
COLUNAS_INFRA = list(NOMES_INFRA.keys())

ESCOLA_FOCO = "IEMA PLENO COELHO NETO"


@st.cache_data
def carregar_base_escolas() -> pd.DataFrame:
    """Base mock de escolas com indicadores de infraestrutura, contexto
    socioeconômico (IBGE) e desempenho (ENEM). Somente o estado do Maranhão
    (MA) possui dados completos neste protótipo."""
    registros = [
        # Estado, Município, Escola, Nível Socioeconômico (0-10, INSE simplificado),
        # Desempenho ENEM (média), Matrículas, Comp./Aluno, Lab. Info, Banda Larga, Lab. Ciências, Espaço Maker
        ("MA", "Coelho Neto", ESCOLA_FOCO, 5.8, 612, 480, 8.5, 9.0, 8.0, 7.5, 6.0),
        ("MA", "Coelho Neto", "U.E. Raimunda Costa Ferreira", 3.9, 452, 620, 3.0, 4.0, 3.5, 1.0, 0.0),
        ("MA", "Coelho Neto", "U.E. Prof. Antônio Wilson Bacelar", 4.1, 468, 540, 3.5, 4.5, 4.0, 1.5, 0.0),
        ("MA", "Coelho Neto", "U.E. Centro Educacional Coelho Neto", 4.4, 481, 710, 4.0, 5.0, 5.5, 2.0, 1.0),
        ("MA", "Coelho Neto", "U.E. Rural Povoado Bacuri", 3.2, 431, 190, 1.0, 1.5, 1.0, 0.0, 0.0),
        ("MA", "Timon", "U.E. Centro de Timon", 4.6, 475, 560, 4.5, 5.0, 5.0, 2.0, 1.0),
        ("MA", "Timon", "U.E. Prof. José Ribamar Timon", 3.8, 449, 400, 2.5, 3.0, 3.0, 1.0, 0.0),
        ("MA", "Codó", "U.E. Vila Codó", 4.2, 463, 480, 3.8, 4.2, 4.5, 1.8, 0.5),
        ("MA", "Codó", "U.E. Prof. Raimunda Nunes Codó", 3.6, 441, 330, 2.0, 2.5, 2.5, 0.5, 0.0),
    ]
    colunas = [
        "Estado", "Municipio", "Escola", "Nivel_Socioeconomico", "Desempenho_ENEM",
        "Matriculas", *COLUNAS_INFRA,
    ]
    return pd.DataFrame(registros, columns=colunas)


@st.cache_data
def carregar_feature_importance() -> pd.DataFrame:
    """Importância de variáveis (mock de um modelo Random Forest) que explica
    o desempenho escolar — usado na seção de Explicabilidade (XAI)."""
    dados = [
        ("Acesso à Internet / Conectividade", 0.24,
         "Escolas com internet estável e banda larga suficiente conseguem usar mais "
         "recursos digitais em sala, o que historicamente melhora o desempenho."),
        ("Nível Socioeconômico das Famílias", 0.21,
         "O contexto socioeconômico das famílias (renda, escolaridade dos pais) "
         "influencia fortemente o desempenho — por isso comparamos escolas com "
         "perfil parecido, e não a média geral."),
        ("Formação Continuada de Professores", 0.18,
         "Professores com mais formação continuada tendem a aplicar metodologias "
         "mais eficazes, especialmente em Matemática e Ciências."),
        ("Infraestrutura de Laboratórios", 0.16,
         "Laboratórios de informática e ciências permitem aulas práticas, que "
         "aumentam o engajamento e a retenção de conteúdo."),
        ("Distorção Idade-Série", 0.13,
         "Alunos com defasagem idade-série tendem a apresentar maior dificuldade "
         "de acompanhamento, impactando o resultado médio da escola."),
        ("Tamanho Médio da Turma", 0.08,
         "Turmas muito grandes dificultam o acompanhamento individualizado dos "
         "estudantes pelo professor."),
    ]
    return pd.DataFrame(dados, columns=["Fator", "Importancia", "Explicacao"])


BASE_ESCOLAS = carregar_base_escolas()
FEATURE_IMPORTANCE = carregar_feature_importance()

# ==============================================================================
# 4. FUNÇÕES AUXILIARES (tratamento de dados / resiliência da UI)
# ==============================================================================


def obter_linha_escola(df: pd.DataFrame, escola: str) -> pd.Series | None:
    """Retorna a linha da escola no DataFrame, ou None se não encontrada."""
    linhas = df[df["Escola"] == escola]
    if linhas.empty:
        return None
    return linhas.iloc[0]


def serie_infra(linha: pd.Series) -> pd.Series:
    """Extrai apenas as colunas de infraestrutura de uma linha de escola."""
    return linha[COLUNAS_INFRA].astype(float)


def media_municipal_infra(df_municipio: pd.DataFrame) -> pd.Series:
    if df_municipio.empty:
        return pd.Series(0.0, index=COLUNAS_INFRA)
    return df_municipio[COLUNAS_INFRA].mean()


def formatar_status_conectividade(infra: pd.Series) -> tuple[str, str]:
    """Classifica o acesso à internet / lab. de informática como
    Adequado ou Crítico, com base em um limiar simples."""
    score = float(np.mean([infra.get("Banda_Larga", 0.0), infra.get("Lab_Informatica", 0.0)]))
    if score >= 6.0:
        return "Adequado", f"{score:.1f}/10"
    return "Crítico", f"{score:.1f}/10"


def indicador_socioeconomico_desempenho(nivel_socioeconomico: float, desempenho_enem: float) -> float:
    """Compara o desempenho real no ENEM com uma expectativa simples baseada
    apenas no contexto socioeconômico (linha de base fictícia). Valores
    positivos indicam desempenho ACIMA do esperado dado o contexto — um dos
    principais sinais de (des)igualdade educacional que o ATLAS busca revelar.
    """
    esperado = 400 + 35 * nivel_socioeconomico
    return desempenho_enem - esperado


def badge(texto: str, cor: str) -> str:
    """Gera o HTML de uma pílula (badge) colorida."""
    return f'<span class="atlas-badge badge-{cor}">{texto}</span>'


def slugificar(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


# ==============================================================================
# 5. GERAÇÃO DE GRÁFICOS (Plotly)
# ==============================================================================
COR_ESCOLA = "#1F6FEB"
COR_MEDIA = "#94A3B8"
COR_DESTAQUE = "#2E7D32"

LAYOUT_BASE = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    margin=dict(l=10, r=10, t=30, b=10),
    font=dict(size=12, color="#1F2937"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)


def grafico_infra_comparativo(
    infra_escola: pd.Series,
    infra_media: pd.Series | None,
    nome_escola: str,
    destacar: str | None = None,
) -> go.Figure:
    """Gráfico de barras: infraestrutura da escola vs. média municipal."""
    categorias = [NOMES_INFRA[c] for c in COLUNAS_INFRA]
    cores_escola = [
        COR_DESTAQUE if destacar == col else COR_ESCOLA for col in COLUNAS_INFRA
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=categorias,
            y=[infra_escola.get(c, 0.0) for c in COLUNAS_INFRA],
            name=nome_escola,
            marker=dict(color=cores_escola),
        )
    )
    if infra_media is not None:
        fig.add_trace(
            go.Bar(
                x=categorias,
                y=[infra_media.get(c, 0.0) for c in COLUNAS_INFRA],
                name="Média Municipal",
                marker=dict(color=COR_MEDIA),
            )
        )
    fig.update_layout(barmode="group", height=360, yaxis_title="Score (0–10)", **LAYOUT_BASE)
    fig.update_yaxes(range=[0, 10], gridcolor="rgba(0,0,0,0.06)")
    return fig


def grafico_dispersao_socioeconomico(
    df_municipio: pd.DataFrame, escola_sel: str, mostrar_tendencia: bool
) -> go.Figure:
    """Scatter: Nível Socioeconômico x Desempenho ENEM, destacando a escola."""
    outras = df_municipio[df_municipio["Escola"] != escola_sel]
    sel = df_municipio[df_municipio["Escola"] == escola_sel]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=outras["Nivel_Socioeconomico"],
            y=outras["Desempenho_ENEM"],
            mode="markers",
            name="Outras escolas",
            marker=dict(size=12, color=COR_MEDIA),
            text=outras["Escola"],
            hovertemplate="%{text}<br>Nível: %{x}<br>ENEM: %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sel["Nivel_Socioeconomico"],
            y=sel["Desempenho_ENEM"],
            mode="markers",
            name=escola_sel,
            marker=dict(size=18, color=COR_ESCOLA, line=dict(width=2, color="white")),
            text=sel["Escola"],
            hovertemplate="%{text}<br>Nível: %{x}<br>ENEM: %{y}<extra></extra>",
        )
    )

    if mostrar_tendencia and len(df_municipio) >= 2:
        coef = np.polyfit(df_municipio["Nivel_Socioeconomico"], df_municipio["Desempenho_ENEM"], 1)
        x_linha = np.linspace(df_municipio["Nivel_Socioeconomico"].min(), df_municipio["Nivel_Socioeconomico"].max(), 20)
        y_linha = coef[0] * x_linha + coef[1]
        fig.add_trace(
            go.Scatter(
                x=x_linha,
                y=y_linha,
                mode="lines",
                name="Tendência municipal",
                line=dict(color=COR_MEDIA, dash="dot"),
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        height=360,
        xaxis_title="Nível Socioeconômico (IBGE, 0–10)",
        yaxis_title="Desempenho médio ENEM",
        **LAYOUT_BASE,
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.06)")
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.06)")
    return fig


def grafico_feature_importance(df_fi: pd.DataFrame) -> go.Figure:
    df_fi = df_fi.sort_values("Importancia", ascending=True)
    fig = go.Figure(
        go.Bar(
            x=df_fi["Importancia"],
            y=df_fi["Fator"],
            orientation="h",
            marker=dict(color=COR_ESCOLA),
            hovertemplate="%{y}: %{x:.0%}<extra></extra>",
        )
    )
    fig.update_layout(height=300, xaxis_title="Importância relativa", **LAYOUT_BASE)
    fig.update_xaxes(tickformat=".0%", gridcolor="rgba(0,0,0,0.06)")
    fig.update_layout(showlegend=False)
    return fig


# ==============================================================================
# 6. BARRA LATERAL (SIDEBAR) — filtros globais
# ==============================================================================
with st.sidebar:
    st.markdown("## ATLAS Escolar - Filtros")
    st.caption("Protótipo com dados fictícios para fins de demonstração.")

    estado = st.selectbox("Estado", ["MA", "PI", "CE"], index=0)

    municipios_disponiveis = sorted(BASE_ESCOLAS["Municipio"].unique().tolist())
    idx_municipio_padrao = (
        municipios_disponiveis.index("Coelho Neto")
        if "Coelho Neto" in municipios_disponiveis
        else 0
    )
    municipio = st.selectbox("Município", municipios_disponiveis, index=idx_municipio_padrao)

    if estado != "MA":
        st.info(
            "Dados completos disponíveis apenas para o **Maranhão (MA)** neste "
            f"protótipo. Exibindo dados simulados de **{municipio}/MA** como amostra."
        )

    df_municipio = BASE_ESCOLAS[BASE_ESCOLAS["Municipio"] == municipio].reset_index(drop=True)
    escolas_disponiveis = df_municipio["Escola"].tolist()

    if not escolas_disponiveis:
        st.error("Nenhuma escola encontrada para este município.")
        st.stop()

    idx_escola_padrao = (
        escolas_disponiveis.index(ESCOLA_FOCO) if ESCOLA_FOCO in escolas_disponiveis else 0
    )
    escola_selecionada = st.selectbox("Escola", escolas_disponiveis, index=idx_escola_padrao)

    comparar_media = st.checkbox("Comparar com a Média do Município", value=True)

    perfil_usuario = st.radio(
        "Perfil do Usuário",
        ["Estudante", "Professor(a)", "Gestor(a) Escolar"],
        index=2,
    )

# ------------------------------------------------------------------------
# Resolução dos dados da escola selecionada (com tratamento de ausência)
# ------------------------------------------------------------------------
linha_escola = obter_linha_escola(df_municipio, escola_selecionada)

if linha_escola is None:
    st.error(
        "Não foi possível carregar os dados da escola selecionada. "
        "Tente escolher outra escola na barra lateral."
    )
    st.stop()

infra_escola = serie_infra(linha_escola)
infra_media = media_municipal_infra(df_municipio) if comparar_media else None
score_infra = float(infra_escola.mean())
score_infra_media = float(media_municipal_infra(df_municipio).mean())
status_conectividade, detalhe_conectividade = formatar_status_conectividade(infra_escola)
gap_socioeconomico = indicador_socioeconomico_desempenho(
    linha_escola["Nivel_Socioeconomico"], linha_escola["Desempenho_ENEM"]
)

# ==============================================================================
# 7. CABEÇALHO PRINCIPAL
# ==============================================================================
st.title("ATLAS Escolar")
st.markdown(f"#### Diagnóstico de Desigualdades Educacionais — {escola_selecionada}")
st.caption(
    f"{municipio}/{estado}  ·  Perfil: {perfil_usuario}  ·  "
    f"Matrículas: {int(linha_escola['Matriculas'])}  ·  "
    "Fontes: Censo Escolar, ENEM, IBGE (dados fictícios)"
)

aba_diagnostico, aba_assistente, aba_planos = st.tabs(
    ["Painel de Diagnóstico", "Assistente Virtual (IA)", "Planos de Intervenção"]
)

# ==============================================================================
# 8. ABA 1 — PAINEL DE DIAGNÓSTICO
# ==============================================================================
with aba_diagnostico:
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    with col_kpi1:
        st.metric(
            "Índice de Infraestrutura Tecnológica",
            f"{score_infra:.1f} / 10",
            delta=f"{score_infra - score_infra_media:+.1f} vs. média" if comparar_media else None,
        )

    with col_kpi2:
        st.metric(
            "Acesso à Internet & Lab. de Informática",
            status_conectividade,
            delta=detalhe_conectividade,
            delta_color="off",
        )

    with col_kpi3:
        st.metric(
            "Desempenho x Contexto Socioeconômico",
            f"{linha_escola['Desempenho_ENEM']:.0f} pts (ENEM)",
            delta=f"{gap_socioeconomico:+.0f} pts vs. esperado p/ o contexto",
        )

    st.divider()

    col_graf1, col_graf2 = st.columns(2, gap="large")

    with col_graf1:
        st.subheader("Infraestrutura: Escola vs. Média Municipal")
        fig_infra = grafico_infra_comparativo(
            infra_escola, infra_media, escola_selecionada,
            destacar=infra_escola.idxmin(),
        )
        st.plotly_chart(fig_infra, use_container_width=True)

    with col_graf2:
        st.subheader("Nível Socioeconômico x Desempenho (ENEM)")
        fig_scatter = grafico_dispersao_socioeconomico(
            df_municipio, escola_selecionada, mostrar_tendencia=comparar_media
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with st.expander(
        "Explicabilidade do Modelo (XAI) - Quais fatores mais afetam os resultados?",
        expanded=(perfil_usuario != "Estudante"),
    ):
        st.markdown(
            "O gráfico abaixo mostra, de forma simplificada, **quais fatores mais "
            "pesam** em um modelo (Random Forest) que tenta explicar o desempenho "
            "das escolas da região. Quanto maior a barra, maior a influência do "
            "fator no resultado final."
        )
        st.plotly_chart(grafico_feature_importance(FEATURE_IMPORTANCE), use_container_width=True)

        st.markdown("**O que cada fator significa, em linguagem simples:**")
        for _, linha in FEATURE_IMPORTANCE.sort_values("Importancia", ascending=False).iterrows():
            st.markdown(f"- **{linha['Fator']}** ({linha['Importancia']:.0%}): {linha['Explicacao']}")

# ==============================================================================
# 9. ABA 2 — ASSISTENTE VIRTUAL DE DADOS (NLQ / Chat)
# ==============================================================================
with aba_assistente:

    def responder_pergunta(pergunta: str) -> dict:
        """Simula a resposta de um assistente de linguagem natural (NLQ)
        sobre os dados da escola selecionada. Retorna texto, uma fonte
        citada e (quando aplicável) um gráfico Plotly ilustrativo."""
        p = pergunta.lower()

        if "gargalo" in p or "infraestrutura" in p:
            fator_critico = infra_escola.idxmin()
            valor = infra_escola.min()
            media_fator = media_municipal_infra(df_municipio)[fator_critico]
            diferenca_fator = valor - media_fator
            if diferenca_fator < -0.3:
                comparativo = f"abaixo da média municipal de {media_fator:.1f}/10"
            elif diferenca_fator > 0.3:
                comparativo = (
                    f"acima da média municipal de {media_fator:.1f}/10 — mesmo assim, "
                    "é o ponto mais fraco desta escola em termos relativos"
                )
            else:
                comparativo = f"próximo da média municipal de {media_fator:.1f}/10"
            texto = (
                f"O principal gargalo de infraestrutura em **{escola_selecionada}** é "
                f"**{NOMES_INFRA[fator_critico]}**, com nota **{valor:.1f}/10** — "
                f"{comparativo}. Essa é a dimensão com maior prioridade de investimento "
                "para reduzir a desigualdade de acesso."
            )
            fig = grafico_infra_comparativo(
                infra_escola, media_municipal_infra(df_municipio), escola_selecionada,
                destacar=fator_critico,
            )
            return {"texto": texto, "fig": fig, "fonte": "Censo Escolar 2024 (simulado)"}

        if "matemática" in p or "desempenho" in p or "compara" in p:
            nivel = linha_escola["Nivel_Socioeconomico"]
            pares = df_municipio[
                (df_municipio["Escola"] != escola_selecionada)
                & (df_municipio["Nivel_Socioeconomico"].sub(nivel).abs() <= 1.0)
            ]
            if pares.empty:
                texto = (
                    "Não há, neste município, escolas com perfil socioeconômico "
                    "suficientemente parecido para uma comparação justa no momento."
                )
                fig = None
            else:
                media_pares = pares["Desempenho_ENEM"].mean()
                desempenho = linha_escola["Desempenho_ENEM"]
                diferenca = desempenho - media_pares
                direcao = "acima" if diferenca >= 0 else "abaixo"
                texto = (
                    f"O desempenho médio no ENEM de **{escola_selecionada}** é "
                    f"**{desempenho:.0f} pontos**, {abs(diferenca):.0f} pontos "
                    f"**{direcao}** da média de escolas com perfil socioeconômico "
                    f"semelhante ({media_pares:.0f} pontos, n={len(pares)})."
                )
                fig = go.Figure(
                    go.Bar(
                        x=[escola_selecionada, "Média de escolas com perfil semelhante"],
                        y=[desempenho, media_pares],
                        marker=dict(color=[COR_ESCOLA, COR_MEDIA]),
                    )
                )
                fig.update_layout(height=320, yaxis_title="Desempenho ENEM", **LAYOUT_BASE)
                fig.update_layout(showlegend=False)
            return {"texto": texto, "fig": fig, "fonte": "ENEM — Microdados (simulado)"}

        if "recursos" in p or "ausentes" in p or "faltam" in p or "falta" in p:
            ausentes = [NOMES_INFRA[c] for c in COLUNAS_INFRA if infra_escola[c] < 3.0]
            if ausentes:
                texto = (
                    "Os seguintes recursos tecnológicos estão **ausentes ou muito "
                    f"limitados** em {escola_selecionada}:\n\n"
                    + "\n".join(f"- {item}" for item in ausentes)
                )
            else:
                texto = (
                    f"Não foram identificados recursos tecnológicos criticamente "
                    f"ausentes em {escola_selecionada} — todos os indicadores estão "
                    "acima do limiar mínimo considerado neste protótipo."
                )
            fig = grafico_infra_comparativo(
                infra_escola, media_municipal_infra(df_municipio), escola_selecionada
            )
            return {"texto": texto, "fig": fig, "fonte": "Censo Escolar 2024 (simulado)"}

        texto = (
            "Ainda estou aprendendo a responder esse tipo de pergunta com os dados "
            "completos. Por enquanto, posso ajudar com perguntas sobre **gargalos de "
            "infraestrutura**, **desempenho comparado a escolas semelhantes** e "
            "**recursos tecnológicos ausentes**. Tente uma das sugestões acima."
        )
        return {"texto": texto, "fig": None, "fonte": None}

    st.subheader("Converse com os dados da escola selecionada")
    st.caption(
        "Assistente experimental de Consulta em Linguagem Natural (NLQ) — "
        "respostas geradas a partir dos dados fictícios desta sessão."
    )

    perguntas_sugeridas = [
        "Qual é o principal gargalo de infraestrutura desta escola?",
        "Como o desempenho em Matemática se compara com escolas de mesmo perfil socioeconômico?",
        "Quais recursos tecnológicos estão ausentes?",
    ]

    st.session_state.setdefault("atlas_chat_historico", [])
    if not st.session_state["atlas_chat_historico"]:
        st.session_state["atlas_chat_historico"].append(
            {
                "role": "assistant",
                "texto": (
                    f"Olá! Sou o assistente de dados do ATLAS Escolar. Posso responder "
                    f"perguntas sobre **{escola_selecionada}** usando os dados "
                    "carregados nesta sessão. Use os botões abaixo ou digite sua "
                    "própria pergunta."
                ),
                "fig": None,
                "fonte": None,
            }
        )

    pergunta_disparada = None
    cols_chips = st.columns(3)
    for col, texto_chip in zip(cols_chips, perguntas_sugeridas):
        if col.button(texto_chip, use_container_width=True):
            pergunta_disparada = texto_chip

    entrada_usuario = st.chat_input("Digite sua pergunta sobre os dados desta escola...")
    if entrada_usuario:
        pergunta_disparada = entrada_usuario

    if pergunta_disparada:
        st.session_state["atlas_chat_historico"].append(
            {"role": "user", "texto": pergunta_disparada, "fig": None, "fonte": None}
        )
        resposta = responder_pergunta(pergunta_disparada)
        st.session_state["atlas_chat_historico"].append({"role": "assistant", **resposta})

    for i, msg in enumerate(st.session_state["atlas_chat_historico"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["texto"])
            if msg.get("fig") is not None:
                st.plotly_chart(msg["fig"], use_container_width=True, key=f"chat_fig_{i}")
            if msg.get("fonte"):
                st.caption(f"Fonte: {msg['fonte']}")

# ==============================================================================
# 10. ABA 3 — PLANOS DE INTERVENÇÃO
# ==============================================================================
with aba_planos:
    st.subheader("Recomendações priorizadas para esta escola")
    st.caption(
        "Sugestões geradas automaticamente a partir dos pontos fracos identificados "
        "no Painel de Diagnóstico."
    )

    fator_critico = infra_escola.idxmin()
    nome_fator_critico = NOMES_INFRA[fator_critico]
    impacto_pedagogico = "Alto" if gap_socioeconomico < -20 else ("Médio" if gap_socioeconomico < 0 else "Baixo")
    cor_impacto_pedagogico = {"Alto": "verde", "Médio": "amarelo", "Baixo": "cinza"}[impacto_pedagogico]

    st.markdown(
        f"""
        <div class="atlas-card">
            <h4>Card 1 — Inclusão Digital</h4>
            {badge("Ação Recomendada", "cinza")}
            {badge("Impacto: Alto", "verde")}
            {badge("Complexidade: Média", "amarelo")}
            <p><strong>Ação:</strong> Priorizar investimento em
            <strong>{nome_fator_critico}</strong>, o item de infraestrutura com pior
            avaliação nesta escola ({infra_escola[fator_critico]:.1f}/10).</p>
            <p><strong>Recursos necessários:</strong></p>
            <ul>
                <li>Levantamento técnico detalhado do item crítico junto à Secretaria de Educação</li>
                <li>Parceria com programas federais/estaduais de conectividade e equipamentos</li>
                <li>Capacitação da equipe para uso pedagógico do novo recurso</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="atlas-card atlas-card-verde">
            <h4>Card 2 — Desempenho Pedagógico</h4>
            {badge("Ação Recomendada", "cinza")}
            {badge(f"Impacto: {impacto_pedagogico}", cor_impacto_pedagogico)}
            {badge("Complexidade: Baixa", "verde")}
            <p><strong>Ação:</strong> Implementar reforço escolar focado em
            <strong>Matemática/STEM</strong>, usando os microdados do ENEM para
            identificar habilidades específicas com maior taxa de erro entre os
            estudantes da escola.</p>
            <p><strong>Recursos necessários:</strong></p>
            <ul>
                <li>Relatório de habilidades (TRI) por competência, a partir dos microdados do ENEM</li>
                <li>Monitorias e plantões de dúvidas em horário complementar</li>
                <li>Acompanhamento bimestral de indicadores de aprendizagem</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --------------------------------------------------------------------
    # Geração de um PDF mínimo (mockup de relatório) — sem dependências
    # externas, apenas para demonstrar o fluxo de download.
    # --------------------------------------------------------------------
    def gerar_pdf_mock(titulo: str, linhas: list[str]) -> bytes:
        """Gera um PDF de uma página simples (sem bibliotecas externas)."""

        def escapar(texto: str) -> str:
            return texto.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

        y = 760
        comandos = [f"BT /F1 16 Tf 50 {y} Td ({escapar(titulo)}) Tj ET"]
        y -= 34
        for linha in linhas:
            comandos.append(f"BT /F2 11 Tf 50 {y} Td ({escapar(linha)}) Tj ET")
            y -= 18
        stream = "\n".join(comandos).encode("latin-1", "replace")

        objetos = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        ]

        partes = [b"%PDF-1.4\n"]
        offsets = []
        for i, obj in enumerate(objetos, start=1):
            offsets.append(sum(len(p) for p in partes))
            partes.append(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")

        xref_offset = sum(len(p) for p in partes)
        partes.append(f"xref\n0 {len(objetos) + 1}\n".encode())
        partes.append(b"0000000000 65535 f \n")
        for off in offsets:
            partes.append(f"{off:010d} 00000 n \n".encode())
        partes.append(
            f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF".encode()
        )
        return b"".join(partes)

    linhas_relatorio = [
        f"Escola: {escola_selecionada}  ({municipio}/{estado})",
        f"Perfil de acesso: {perfil_usuario}",
        "",
        "--- Indicadores-chave ---",
        f"Indice de Infraestrutura Tecnologica: {score_infra:.1f} / 10",
        f"Acesso a Internet / Lab. Informatica: {status_conectividade} ({detalhe_conectividade})",
        f"Desempenho ENEM: {linha_escola['Desempenho_ENEM']:.0f} pontos",
        f"Gap vs. esperado p/ contexto socioeconomico: {gap_socioeconomico:+.0f} pontos",
        "",
        "--- Recomendacoes ---",
        f"1. Inclusao Digital: priorizar {nome_fator_critico}",
        "2. Desempenho Pedagogico: reforco de Matematica/STEM com base no ENEM",
        "",
        "Relatorio gerado automaticamente com dados ficticios (protótipo ATLAS Escolar).",
    ]
    pdf_bytes = gerar_pdf_mock(f"Relatorio de Diagnostico - {escola_selecionada}", linhas_relatorio)

    st.download_button(
        "Baixar Relatório Completo do Diagnóstico (PDF)",
        data=pdf_bytes,
        file_name=f"relatorio_atlas_{slugificar(escola_selecionada)}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    st.caption(
        "O relatório é gerado automaticamente a partir dos dados simulados "
        "exibidos nesta sessão (mockup para fins de demonstração)."
    )
