import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
from utils import blue_palette
import datetime

# Configure page FIRST for better performance
st.set_page_config(layout="wide", page_title="Dashboard LocMotos", page_icon=":motorcycle:")

# Carregar CSS customizado
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/style.css")

# ----- Cached data loaders --------
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_moto_data():
    return pd.read_csv('assets/Motos2_limpo.csv')


# Load data
mdf = load_moto_data()

#apaga as motos inválidas do dataset
mdf = mdf[mdf["Moto"].notnull()] #motos com valores nulos
mdf = mdf[mdf["Moto"] != "Escolha a moto"] #motos com valor "Escolha a moto"

# UI
st.title("Dashboard LocMotos 📊")

# inserir cards informativos com as principais métricas, como total de motos, média de preço, etc.
total_motos = mdf["Moto"].unique().shape[0]
st.metric("Total de Motos", total_motos, delta=None, delta_color="normal", help="Número total de motos cadastradas no dataset", label_visibility="visible", border=True, width=150) 

# Inicializar session_state para controle de filtros
if "last_filter" not in st.session_state:
    st.session_state.last_filter = None
if "widget_key" not in st.session_state:
    st.session_state.widget_key = 0
if "saved_search" not in st.session_state:
    st.session_state.saved_search = ""
if "saved_multiselect" not in st.session_state:
    st.session_state.saved_multiselect = []
if "saved_dataeditor" not in st.session_state:
    st.session_state.saved_dataeditor = []
if "categoria_entrada" not in st.session_state:
    st.session_state.categoria_entrada = []
if "categoria_saida" not in st.session_state:
    st.session_state.categoria_saida = []

# Sidebar
with st.sidebar:
    #logo da empresa
    st.image('assets/locmotos-logo.png', width="content", caption="LocMotos - Aluguel de Motos")
    
    # Botão para limpar todos os filtros
    if st.button("🔄 Limpar Filtros", use_container_width=True, type="secondary"):
        st.session_state.last_filter = None
        st.session_state.widget_key += 1
        st.session_state.saved_search = ""
        st.session_state.saved_multiselect = []
        st.session_state.saved_dataeditor = []
        st.session_state.categoria_entrada = []
        st.session_state.categoria_saida = []
        st.rerun()
    
    st.markdown("---")

    # seleção de intervalo de datas para análise
    inicial_year = 2025
    current_year = datetime.date.today().year
    jan_1 = datetime.date(inicial_year, 1, 1)
    dec_31 = datetime.date(current_year, 12, 31)
    
    # Datas padrão para o dataset (resetar para período completo dos dados)
    default_start_date = datetime.date(2025, 9, 1)  # 01/09/2025
    default_end_date = datetime.date.today()  # Data de hoje

    date = st.date_input(
        "Selecione o intervalo de datas para análise:",
        (default_start_date, default_end_date),
        jan_1,
        dec_31,
        format="DD/MM/YYYY",
        key=f"date_input_{st.session_state.widget_key}"
    )

    # Campo de busca para filtrar motos
    search_term = st.text_input(
        "**1) Buscar moto:**", 
        placeholder="Digite parte do nome da moto...",
        value=st.session_state.saved_search,
        key=f"search_motos_{st.session_state.widget_key}"
    )
    
    # Filtrar motos com base no termo de busca
    all_motos = sorted(mdf["Moto"].unique())
    if search_term and search_term.strip():
        filtered_motos = [moto for moto in all_motos if search_term.lower() in moto.lower()]
        if len(filtered_motos) == 0:
            st.warning(f"Nenhuma moto encontrada com '{search_term}'")
        else:
            st.success(f"Encontradas {len(filtered_motos)} moto(s):")
            for moto in filtered_motos:
                st.write(f"  • {moto}")
        
        # Se o filtro de busca for usado pela primeira vez, limpar os outros
        if st.session_state.last_filter != "search":
            st.session_state.last_filter = "search"
            st.session_state.saved_search = search_term
            st.session_state.saved_multiselect = []
            st.session_state.saved_dataeditor = []
            st.session_state.widget_key += 1
            st.rerun()
        else:
            # Apenas atualizar o valor salvo
            st.session_state.saved_search = search_term
    else:
        filtered_motos = all_motos
        st.session_state.saved_search = search_term
        #if not search_term:
            #st.info(f"Todas as {len(all_motos)} motos disponíveis")
    
    st.markdown("---")
    # seleção de motos
    options = st.multiselect(
        "**2) Clique nas Motos:**",
        filtered_motos,
        default=st.session_state.saved_multiselect if st.session_state.saved_multiselect else [],
        max_selections=total_motos+1,
        accept_new_options=False,
        key=f"multiselect_motos_{st.session_state.widget_key}"
    )
    
    # Se o multiselect for usado pela primeira vez, limpar os outros
    if options and st.session_state.last_filter != "multiselect":
        st.session_state.last_filter = "multiselect"
        st.session_state.saved_search = ""
        st.session_state.saved_multiselect = options
        st.session_state.saved_dataeditor = []
        st.session_state.widget_key += 1
        st.rerun()
    else:
        # Apenas atualizar o valor salvo
        st.session_state.saved_multiselect = options

    st.markdown("---")
    st.write("**3) Escolha as Motos na lista abaixo:**")
    
    # Criar DataFrame para seleção com data_editor
    motos_df = pd.DataFrame({
        "Moto": sorted(mdf["Moto"].unique()),
        "Selecionar": [moto in st.session_state.saved_dataeditor for moto in sorted(mdf["Moto"].unique())]
    })
    
    edited_df = st.data_editor(
        motos_df,
        column_config={
            "Selecionar": st.column_config.CheckboxColumn(
                "",
                help="Marque para incluir na análise",
                default=False,
            ),
            "Moto": st.column_config.TextColumn(
                "Moto",
                disabled=True,
            )
        },
        hide_index=True,
        use_container_width=True,
        height=300,
        key=f"data_editor_motos_{st.session_state.widget_key}"
    )
    
    # Extrair motos selecionadas do data_editor
    selected_motos = edited_df[edited_df["Selecionar"] == True]["Moto"].tolist()
    
    # Se o data editor for usado pela primeira vez, limpar os outros
    if selected_motos and st.session_state.last_filter != "dataeditor":
        st.session_state.last_filter = "dataeditor"
        st.session_state.saved_search = ""
        st.session_state.saved_multiselect = []
        st.session_state.saved_dataeditor = selected_motos
        st.session_state.widget_key += 1
        st.rerun()
    else:
        # Apenas atualizar o valor salvo
        st.session_state.saved_dataeditor = selected_motos
    
    st.write(f"Motos selecionadas: {len(selected_motos)}")

# Função para extrair o número inicial do nome da moto para ordenação numérica
def extract_moto_number(moto_name):
    import re
    match = re.match(r'^(\d+)', str(moto_name))
    return int(match.group(1)) if match else 0

# Determinar quais motos foram filtradas
filtered_moto_list = []
if st.session_state.last_filter == "search" and st.session_state.saved_search:
    # Usar o filtro de busca
    filtered_moto_list = [moto for moto in all_motos if st.session_state.saved_search.lower() in moto.lower()]
elif st.session_state.last_filter == "multiselect" and st.session_state.saved_multiselect:
    # Usar o multiselect
    filtered_moto_list = st.session_state.saved_multiselect
elif st.session_state.last_filter == "dataeditor" and st.session_state.saved_dataeditor:
    # Usar o data editor
    filtered_moto_list = st.session_state.saved_dataeditor

# Conteúdo principal - Visão Macro do Negócio
st.write("Visão Macro do Negócio")

# Aplicar filtro de motos se houver
if filtered_moto_list:
    mdf_filtered = mdf[mdf["Moto"].isin(filtered_moto_list)]
    st.info(f"📊 Exibindo dados de {len(filtered_moto_list)} moto(s) selecionada(s)")
else:
    mdf_filtered = mdf
    st.info("📊 Exibindo dados de todas as motos")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.header("Entradas")
        
        # Filtro de categoria dentro do container
        entrada_data = mdf_filtered[mdf_filtered['Tipo'] == 'Entrada']
        categorias_entrada = sorted(entrada_data['Categoria'].dropna().unique())
        
        selected_cat_entrada = st.multiselect(
            "📂 Filtrar por Categoria:",
            categorias_entrada,
            default=st.session_state.categoria_entrada,
            key="filter_cat_entrada",
            help="Selecione uma ou mais categorias"
        )
        st.session_state.categoria_entrada = selected_cat_entrada
        
        #filtra apenas os valores do tipo "Entrada" para o gráfico de barras, independente de período
        entrada_motos = entrada_data.copy()
        
        # Aplicar filtro de categoria se houver
        if selected_cat_entrada:
            entrada_motos = entrada_motos[entrada_motos['Categoria'].isin(selected_cat_entrada)]
        
        entrada_motos['_sort_key'] = entrada_motos['Moto'].apply(extract_moto_number)
        entrada_motos = entrada_motos.sort_values('_sort_key').drop(columns=['_sort_key'])
        st.plotly_chart(px.bar(entrada_motos, x="Moto", y="Valor", color="Categoria", title="Valores de Entrada por Categoria"), use_container_width=True)

with col2:
    with st.container(border=True):
        st.header("Saídas")
        
        # Filtro de categoria dentro do container
        saida_data = mdf_filtered[mdf_filtered['Tipo'] == 'Saída']
        categorias_saida = sorted(saida_data['Categoria'].dropna().unique())
        
        selected_cat_saida = st.multiselect(
            "📂 Filtrar por Categoria:",
            categorias_saida,
            default=st.session_state.categoria_saida,
            key="filter_cat_saida",
            help="Selecione uma ou mais categorias"
        )
        st.session_state.categoria_saida = selected_cat_saida
        
        #filtra apenas os valores do tipo "Saída" para o gráfico de barras, independente de período
        saida_motos = saida_data.copy()
        
        # Aplicar filtro de categoria se houver
        if selected_cat_saida:
            saida_motos = saida_motos[saida_motos['Categoria'].isin(selected_cat_saida)]
        
        saida_motos['_sort_key'] = saida_motos['Moto'].apply(extract_moto_number)
        saida_motos = saida_motos.sort_values('_sort_key').drop(columns=['_sort_key'])
        st.plotly_chart(px.bar(saida_motos, x="Moto", y="Valor", color="Categoria", title="Valores de Saída por Categoria"), use_container_width=True)

#adiciona uma linha horizontal para separar os gráficos
st.markdown("---")
st.header("Gráfico 3")
st.write("Aqui você pode colocar um terceiro gráfico ou análise relacionada aos dados de motos.")
st.line_chart(np.random.randn(100, 1))