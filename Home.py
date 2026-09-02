import streamlit as st

st.set_page_config(page_title="ATLAS Escolar", layout="wide")

st.title("ATLAS Escolar")
st.caption("Diagnóstico de Desigualdades Educacionais — Coelho Neto/MA")

st.markdown(
    """
### Como usar o site

1. **Pesquise** um indicador, escola ou bairro na barra abaixo — ou use o **menu lateral**
   para navegar diretamente entre os módulos.
2. **Painel de Diagnóstico** — visão geral dos indicadores educacionais do município.
3. **Consulta em Linguagem Natural** — faça uma pesquisa e veja o painel de resultados
   (gráficos só aparecem depois que uma busca é feita).
4. **Recomendações** — sugestões geradas a partir dos dados analisados.

> Os dados exibidos são fictícios até a integração com a equipe de dados.
"""
)

st.divider()

busca = st.text_input(
    "Pesquisar",
    placeholder="🔍  Pesquisar indicadores, escolas, bairros...",
    label_visibility="collapsed",
    key="busca_home",
)

if busca:
    st.session_state["termo_busca"] = busca
    st.info(
        f"Para ver os resultados de **{busca}**, acesse **Consulta em Linguagem "
        "Natural** no menu lateral."
    )
