import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
from utils import blue_palette
from sidebar import inicializar_session_state, render_sidebar

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

# Inicializar session_state e renderizar sidebar
inicializar_session_state()
filtered_moto_list, date = render_sidebar(mdf, mdf["Moto"].unique().shape[0])

# Aplicar filtros para cálculo das métricas
if filtered_moto_list:
    mdf_for_metrics = mdf[mdf["Moto"].isin(filtered_moto_list)]
else:
    mdf_for_metrics = mdf

# Aplicar filtro de período
if len(date) == 2:
    start_date, end_date = date[0], date[1]
else:
    start_date = end_date = date[0]

periodos = pd.date_range(
    start=f"{start_date.year}-{start_date.month:02d}-01",
    end=f"{end_date.year}-{end_date.month:02d}-01",
    freq='MS'
).strftime('%Y-%m').tolist()

mdf_for_metrics = mdf_for_metrics[mdf_for_metrics['Periodo'].isin(periodos)]

# Calcular métricas principais
total_motos = mdf["Moto"].unique().shape[0]
total_entradas = mdf_for_metrics[mdf_for_metrics['Tipo'] == 'Entrada']['Valor'].sum()
total_saidas = mdf_for_metrics[mdf_for_metrics['Tipo'] == 'Saída']['Valor'].sum()
saldo_total = total_entradas - total_saidas
total_transacoes = len(mdf_for_metrics)

# Cards informativos com as principais métricas
col_metric1, col_metric2, col_metric3 = st.columns(3)

with col_metric1:
    st.metric("Total de Motos", total_motos, help="Número total de motos cadastradas no dataset", border=True)

with col_metric2:
    st.metric(
        "Saldo Geral", 
        f"R$ {saldo_total:,.2f}", 
        help="Diferença total entre entradas e saídas (período e motos filtradas)",
        border=True
    )

with col_metric3:
    # Exibir status visual do saldo
    if saldo_total >= 0:
        st.markdown(
            f"""
            <div style="border: 1px solid #d4edda; border-radius: 0.5rem; padding: 0.75rem 1rem; background-color: #d4edda; text-align: center; height: 110px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 3rem; margin-bottom: 0.2rem;">💰</div>
                <div style="font-size: 1rem; font-weight: bold; color: #155724;">Resultado Positivo</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="border: 1px solid #f8d7da; border-radius: 0.5rem; padding: 0.75rem 1rem; background-color: #f8d7da; text-align: center; height: 110px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 3rem; margin-bottom: 0.2rem;">📉</div>
                <div style="font-size: 1rem; font-weight: bold; color: #721c24;">Resultado Negativo</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Função para extrair o número inicial do nome da moto para ordenação numérica
def extract_moto_number(moto_name):
    import re
    match = re.match(r'^(\d+)', str(moto_name))
    return int(match.group(1)) if match else 0

# Conteúdo principal - Visão Macro do Negócio

# Aplicar filtro de motos para os gráficos (sem filtro de período ainda)
if filtered_moto_list:
    mdf_filtered = mdf[mdf["Moto"].isin(filtered_moto_list)]
    info_msg = f"📊 Exibindo dados de {len(filtered_moto_list)} moto(s) selecionada(s)"
else:
    mdf_filtered = mdf
    info_msg = "📊 Exibindo dados de todas as motos"

# Criar mapeamento de cores consistente para todas as categorias
all_categorias = sorted(mdf['Categoria'].dropna().unique())
color_palette = px.colors.qualitative.Plotly  # Paleta padrão do Plotly
categoria_colors = {cat: color_palette[i % len(color_palette)] for i, cat in enumerate(all_categorias)}

# Exibir informação de filtro aplicável a todos os gráficos
st.info(info_msg)

# Container agrupador para Visão Macro do Negócio
with st.expander("🎯 Visão Macro do Negócio", expanded=True):
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
            st.plotly_chart(px.bar(entrada_motos, x="Moto", y="Valor", color="Categoria", title="Valores de Entrada por Categoria", color_discrete_map=categoria_colors), use_container_width=True)

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
            st.plotly_chart(px.bar(saida_motos, x="Moto", y="Valor", color="Categoria", title="Valores de Saída por Categoria", color_discrete_map=categoria_colors), use_container_width=True)


# Gráfico 3 - Evolução Temporal de Entradas e Saídas
with st.expander("📈 Evolução Temporal: Entradas vs Saídas", expanded=True):
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


# Gráfico 4 - Histórico Completo de Entradas e Saídas
with st.expander("📜 Histórico Completo: Todas as Entradas e Saídas", expanded=True):
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
            height=600,
            color_discrete_map=categoria_colors
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
                # Adicionar linha de total
                total_entradas = entradas_cat.sum()
                df_entradas_total = pd.DataFrame({
                    'Categoria': ['TOTAL'],
                    'Valor (R$)': [total_entradas]
                })
                df_entradas_display = pd.concat([df_entradas_display, df_entradas_total], ignore_index=True)
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
                # Adicionar linha de total
                total_saidas = saidas_cat.sum()
                df_saidas_total = pd.DataFrame({
                    'Categoria': ['TOTAL'],
                    'Valor (R$)': [total_saidas]
                })
                df_saidas_display = pd.concat([df_saidas_display, df_saidas_total], ignore_index=True)
                df_saidas_display['Valor (R$)'] = df_saidas_display['Valor (R$)'].apply(lambda x: f"R$ {x:,.2f}")
                st.dataframe(df_saidas_display, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma saída no período")
    else:
        st.info("Nenhum dado disponível para o período selecionado.")
