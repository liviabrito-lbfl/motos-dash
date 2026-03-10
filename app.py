import pandas as pd
import streamlit as st
import os
from sidebar import inicializar_session_state
from data_processing import tratarDados
from dashboard import render_dashboard

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


# Inicializar session_state
inicializar_session_state()


def render_home():
    """Renderiza a página inicial com opções de navegação"""
    st.title("🏍️ Sistema LocMotos")
    st.markdown("### Bem-vindo ao Dashboard de Gestão de Motos")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="border: 2px solid #1f77b4; border-radius: 10px; padding: 20px; text-align: center; height: 250px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 4rem; margin-bottom: 10px;">📊</div>
            <h3 style="margin: 10px 0;">Visualizar Dados Existentes</h3>
            <p style="color: #666;">Acesse o dashboard completo com análises e gráficos dos dados já cadastrados</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Acessar Dashboard", use_container_width=True, type="primary"):
            st.session_state.app_mode = 'visualizar'
            st.rerun()
    
    with col2:
        st.markdown("""
        <div style="border: 2px solid #ff7f0e; border-radius: 10px; padding: 20px; text-align: center; height: 250px; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 4rem; margin-bottom: 10px;">📤</div>
            <h3 style="margin: 10px 0;">Atualizar Arquivo CSV</h3>
            <p style="color: #666;">Faça upload de um novo arquivo CSV para atualizar os dados do sistema</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📁 Upload de Dados", use_container_width=True, type="secondary"):
            st.session_state.app_mode = 'atualizar'
            st.rerun()


def render_upload():
    """Renderiza a página de upload de arquivos CSV"""
    st.title("📤 Atualizar Arquivo CSV")
    
    # Botão para voltar à página inicial
    if st.button("⬅️ Voltar", type="secondary"):
        st.session_state.app_mode = None
        st.rerun()
    
    st.markdown("---")
    
    st.info("📋 Faça upload de um novo arquivo CSV para substituir os dados existentes. O arquivo deve seguir o mesmo formato do arquivo atual.")
    
    # Upload de arquivo
    uploaded_file = st.file_uploader(
        "Escolha o arquivo CSV", 
        type=['csv'],
        help="O arquivo deve estar no formato CSV com as colunas: Moto, Tipo, Categoria, Valor, Periodo"
    )
    
    if uploaded_file is not None:
        try:
            # Ler o arquivo enviado
            df_new = pd.read_csv(uploaded_file)
            
            # Mostrar preview dos dados
            st.success("✅ Arquivo carregado com sucesso!")
            
            #chama o tratarDados para verificar se o arquivo tem as colunas necessárias e se os dados estão no formato correto
            df_new = tratarDados(df_new)

            st.subheader("📋 Preview dos Dados")
            st.dataframe(df_new.head(10), use_container_width=True)
            
            # Mostrar informações do arquivo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Linhas", len(df_new))
            with col2:
                st.metric("Total de Colunas", len(df_new.columns))
            with col3:
                if 'Moto' in df_new.columns:
                    st.metric("Motos Únicas", df_new['Moto'].nunique())            

            # Verificar colunas necessárias
            required_columns = ['Moto', 'Tipo', 'Categoria', 'Valor', 'Periodo']
            missing_columns = [col for col in required_columns if col not in df_new.columns]
            
            if missing_columns:
                st.error(f"❌ Colunas faltando no arquivo: {', '.join(missing_columns)}")
            else:
                st.success("✅ Todas as colunas necessárias estão presentes!")
                
                # Botão para confirmar atualização
                st.markdown("---")
                st.warning("⚠️ **Atenção:** Esta ação irá substituir o arquivo CSV existente. Esta operação não pode ser desfeita.")
                
                col_a, col_b, col_c = st.columns([1, 1, 1])
                
                with col_b:
                    if st.button("💾 Confirmar e Atualizar", use_container_width=True, type="primary"):
                        # Salvar o novo arquivo
                        df_new.to_csv('assets/Motos2_limpo.csv', index=False)
                        
                        # Limpar cache
                        st.cache_data.clear()
                        
                        st.success("✅ Arquivo atualizado com sucesso!")
                        st.balloons()
                        
                        st.info("🔄 Redirecionando para o dashboard...")
                        
                        # Redirecionar para o dashboard após 2 segundos
                        import time
                        time.sleep(2)
                        st.session_state.app_mode = 'visualizar'
                        st.rerun()
        
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo '{uploaded_file.name}': {str(e)}")
            st.info("💡 Verifique se o arquivo está no formato CSV correto.")


# ========== MAIN APP LOGIC ==========

# Verificar o modo atual da aplicação
if st.session_state.app_mode is None:
    # Mostrar página inicial
    render_home()

elif st.session_state.app_mode == 'visualizar':
    # Carregar e exibir dashboard
    mdf = load_moto_data()
    mdf = tratarDados(mdf)
    
    # Botão no topo para voltar à página inicial
    with st.sidebar:
        st.markdown("---")
        if st.button("🏠 Voltar ao Início", use_container_width=True, type="secondary"):
            st.session_state.app_mode = None
            st.rerun()
    
    render_dashboard(mdf)

elif st.session_state.app_mode == 'atualizar':
    # Exibir página de upload
    render_upload()


