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

# Aplicar filtro de motos se houver
if filtered_moto_list:
    mdf_filtered = mdf[mdf["Moto"].isin(filtered_moto_list)]
    info_msg = f"📊 Exibindo dados de {len(filtered_moto_list)} moto(s) selecionada(s)"
else:
    mdf_filtered = mdf
    info_msg = "📊 Exibindo dados de todas as motos"

# Container agrupador para Visão Macro do Negócio
with st.container(border=True):
    st.header("Visão Macro do Negócio")
    st.info(info_msg)
    
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

# Gráfico 3 - Evolução Temporal de Entradas e Saídas
with st.container(border=True):
    st.header("📈 Evolução Temporal: Entradas vs Saídas")
    
    # Criar lista de períodos no intervalo selecionado
    if len(date) == 2:
        start_date, end_date = date[0], date[1]
    else:
        start_date = end_date = date[0]
    
    # Gerar lista de períodos (YYYY-MM) entre as datas selecionadas
    periodos = pd.date_range(
        start=f"{start_date.year}-{start_date.month:02d}-01",
        end=f"{end_date.year}-{end_date.month:02d}-01",
        freq='MS'
    ).strftime('%Y-%m').tolist()
    
    # Filtrar dados pelo período
    df_temporal = mdf_filtered[mdf_filtered['Periodo'].isin(periodos)].copy()
    
    if len(df_temporal) > 0:
        # Agrupar por Período e Tipo, somando os valores
        df_grouped = df_temporal.groupby(['Periodo', 'Tipo'])['Valor'].sum().reset_index()
        
        # Formatar o período para exibição (MM/AAAA)
        df_grouped['Periodo_Format'] = pd.to_datetime(df_grouped['Periodo'] + '-01').dt.strftime('%m/%Y')
        
        # Formatar períodos para o título
        periodo_inicio = pd.to_datetime(periodos[0] + '-01').strftime('%m/%Y')
        periodo_fim = pd.to_datetime(periodos[-1] + '-01').strftime('%m/%Y')
        
        # Criar gráfico de linhas
        fig = px.line(
            df_grouped, 
            x='Periodo_Format', 
            y='Valor', 
            color='Tipo',
            markers=True,
            title=f"Evolução de Entradas e Saídas ({periodo_inicio} a {periodo_fim})",
            labels={'Periodo_Format': 'Período (Mês/Ano)', 'Valor': 'Valor Total (R$)', 'Tipo': 'Tipo'},
            color_discrete_map={'Entrada': '#2ecc71', 'Saída': '#e74c3c'}
        )
        
        # Melhorar layout
        fig.update_layout(
            hovermode='x unified',
            xaxis_title="Período (Mês/Ano)",
            yaxis_title="Valor Total (R$)",
            legend_title="Tipo",
            xaxis=dict(type='category')  # Forçar eixo x como categórico para não interpretar como data
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar resumo
        col_a, col_b, col_c = st.columns(3)
        total_entrada = df_grouped[df_grouped['Tipo'] == 'Entrada']['Valor'].sum()
        total_saida = df_grouped[df_grouped['Tipo'] == 'Saída']['Valor'].sum()
        saldo = total_entrada - total_saida
        
        with col_a:
            st.metric("Total Entradas", f"R$ {total_entrada:,.2f}", delta=None)
        with col_b:
            st.metric("Total Saídas", f"R$ {total_saida:,.2f}", delta=None)
        with col_c:
            st.metric("Saldo", f"R$ {saldo:,.2f}", delta=f"R$ {saldo:,.2f}" if saldo >= 0 else f"-R$ {abs(saldo):,.2f}")
    else:
        st.info("Nenhum dado disponível para o período selecionado.")

#adiciona uma linha horizontal para separar os gráficos
st.markdown("---")

# Gráfico 4 - Histórico Completo de Entradas e Saídas
with st.container(border=True):
    st.header("📜 Histórico Completo: Todas as Entradas e Saídas")
    st.write("Visualização detalhada de todas as transações ao longo do tempo.")
    
    # Usar os mesmos dados filtrados
    if len(df_temporal) > 0:
        # Agrupar por Período, Tipo e Categoria
        df_historico = df_temporal.groupby(['Periodo', 'Tipo', 'Categoria'])['Valor'].sum().reset_index()
        
        # Formatar o período para exibição
        df_historico['Periodo_Format'] = pd.to_datetime(df_historico['Periodo'] + '-01').dt.strftime('%m/%Y')
        
        # Criar gráfico de barras com categorias empilhadas, separado por Tipo
        fig_historico = px.bar(
            df_historico,
            x='Periodo_Format',
            y='Valor',
            color='Categoria',
            facet_col='Tipo',
            title=f"Histórico de Entradas e Saídas por Categoria ({periodo_inicio} a {periodo_fim})",
            labels={'Periodo_Format': 'Período (Mês/Ano)', 'Valor': 'Valor (R$)', 'Categoria': 'Categoria'},
            barmode='stack',
            height=600
        )
        
        fig_historico.update_layout(
            hovermode='x unified',
            xaxis_title="Período (Mês/Ano)",
            yaxis_title="Valor (R$)",
            xaxis=dict(type='category'),
            xaxis2=dict(type='category')
        )
        
        # Atualizar títulos dos subplots
        fig_historico.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        
        # Calcular totais por período e tipo para adicionar anotações
        totais_por_periodo_tipo = df_historico.groupby(['Periodo_Format', 'Tipo'])['Valor'].sum().reset_index()
        
        # Adicionar anotações com o valor total no topo de cada barra
        for idx, row in totais_por_periodo_tipo.iterrows():
            tipo = row['Tipo']
            periodo = row['Periodo_Format']
            valor_total = row['Valor']
            
            # Determinar qual subplot (Entrada=1, Saída=2)
            xref = 'x' if tipo == 'Entrada' else 'x2'
            yref = 'y' if tipo == 'Entrada' else 'y2'
            
            fig_historico.add_annotation(
                x=periodo,
                y=valor_total,
                text=f'R$ {valor_total:,.0f}',
                showarrow=False,
                yshift=10,
                xref=xref,
                yref=yref,
                font=dict(size=9, color='black')
            )
        
        st.plotly_chart(fig_historico, use_container_width=True)
        
        # Adicionar tabela resumo detalhada
        st.subheader("📊 Detalhamento por Categoria")
        
        col_d, col_e = st.columns(2)
        
        with col_d:
            st.write("**Entradas por Categoria**")
            entradas_cat = df_temporal[df_temporal['Tipo'] == 'Entrada'].groupby('Categoria')['Valor'].sum().sort_values(ascending=False)
            if len(entradas_cat) > 0:
                df_entradas_display = pd.DataFrame({
                    'Categoria': entradas_cat.index,
                    'Valor (R$)': entradas_cat.values
                })
                df_entradas_display['Valor (R$)'] = df_entradas_display['Valor (R$)'].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_entradas_display, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma entrada no período")
        
        with col_e:
            st.write("**Saídas por Categoria**")
            saidas_cat = df_temporal[df_temporal['Tipo'] == 'Saída'].groupby('Categoria')['Valor'].sum().sort_values(ascending=False)
            if len(saidas_cat) > 0:
                df_saidas_display = pd.DataFrame({
                    'Categoria': saidas_cat.index,
                    'Valor (R$)': saidas_cat.values
                })
                df_saidas_display['Valor (R$)'] = df_saidas_display['Valor (R$)'].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_saidas_display, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma saída no período")
    else:
        st.info("Nenhum dado disponível para o período selecionado.")
