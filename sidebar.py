import streamlit as st
import datetime
import re

def extract_moto_number(moto_name):
    """Extrai o número inicial do nome da moto para ordenação numérica"""
    match = re.match(r'^(\d+)', str(moto_name))
    return int(match.group(1)) if match else 0

def inicializar_session_state():
    """Inicializa as variáveis de session_state para controle de filtros"""
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
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = None  # None, 'visualizar', 'atualizar'


def render_sidebar(mdf, total_motos):
    """
    Renderiza o sidebar com todos os filtros
    
    Args:
        mdf: DataFrame com os dados das motos
        total_motos: Total de motos no dataset
    
    Returns:
        tuple: (filtered_moto_list, date) - Lista de motos filtradas e intervalo de datas
    """
    
    with st.sidebar:
        # Logo da empresa
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

        # Seleção de intervalo de datas para análise
        inicial_year = 2025
        current_year = datetime.date.today().year
        jan_1 = datetime.date(inicial_year, 1, 1)
        dec_31 = datetime.date(current_year, 12, 31)
        
        # Datas padrão para o dataset
        default_start_date = datetime.date(2025, 9, 1)
        default_end_date = datetime.date.today()

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
        all_motos = sorted(mdf["Moto"].unique(), key=extract_moto_number)
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
                st.session_state.saved_search = search_term
        else:
            filtered_motos = all_motos
            st.session_state.saved_search = search_term
        
        st.markdown("---")
        
        # Seleção de motos via multiselect
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
            st.session_state.saved_multiselect = options

        st.markdown("---")
        st.write("**3) Escolha as Motos na lista abaixo:**")
        
        # Criar DataFrame para seleção com data_editor
        import pandas as pd
        motos_sorted = sorted(mdf["Moto"].unique(), key=extract_moto_number)
        motos_df = pd.DataFrame({
            "Moto": motos_sorted,
            "Selecionar": [moto in st.session_state.saved_dataeditor for moto in motos_sorted]
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
            st.session_state.saved_dataeditor = selected_motos
        
        st.write(f"Motos selecionadas: {len(selected_motos)}")
    
    # Determinar quais motos foram filtradas
    filtered_moto_list = []
    if st.session_state.last_filter == "search" and st.session_state.saved_search:
        filtered_moto_list = [moto for moto in all_motos if st.session_state.saved_search.lower() in moto.lower()]
    elif st.session_state.last_filter == "multiselect" and st.session_state.saved_multiselect:
        filtered_moto_list = st.session_state.saved_multiselect
    elif st.session_state.last_filter == "dataeditor" and st.session_state.saved_dataeditor:
        filtered_moto_list = st.session_state.saved_dataeditor
    
    return filtered_moto_list, date
