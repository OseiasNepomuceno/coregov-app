import streamlit as st
import pandas as pd
import gdown
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTADO (ESTABILIDADE) ---
st.set_page_config(page_title="CoreGov", page_icon="🛰️", layout="wide")

if 'secao' not in st.session_state: st.session_state['secao'] = 'home'
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_plano' not in st.session_state: st.session_state['usuario_plano'] = 'BÁSICO'

# --- 2. FUNÇÃO DE AUTENTICAÇÃO REAL ---
def autenticar_usuario(usuario_digitado, senha_digitada):
    file_id = st.secrets.get("file_id_licencas") 
    nome_arquivo = "licencas_login.xlsx"
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        if os.path.exists(nome_arquivo): os.remove(nome_arquivo)
        gdown.download(url, nome_arquivo, quiet=True)
        df = pd.read_excel(nome_arquivo, sheet_name='usuario')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        u_clean = str(usuario_digitado).strip().lower()
        p_clean = str(senha_digitada).strip()
        user_row = df[(df['USUARIO'].astype(str).str.strip().str.lower() == u_clean) & 
                      (df['SENHA'].astype(str).str.strip() == p_clean)]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            if str(dados.get('STATUS', 'pendente')).lower().strip() == 'ativo':
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = u_clean
                st.session_state['usuario_plano'] = str(dados.get('PLANO', 'BÁSICO')).upper()
                return True
        return False
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return False

# --- 3. MÓDULOS INTERNOS (RECHEIO PROTEGIDO) ---

def modulo_gestao_clientes():
    if st.session_state['usuario_plano'] == 'BÁSICO':
        st.warning("⚠️ **Módulo Restrito ao Plano Premium**")
        st.info("Sua licença atual não permite a gestão de clientes. Faça o upgrade para liberar.")
        if st.button("Consultar Planos para Upgrade"):
            st.session_state['logado'] = False
            st.session_state['secao'] = 'planos'
            st.rerun()
    else:
        st.header("💼 Gestão de Clientes e Relatórios")
        tab1, tab2, tab3 = st.tabs(["👥 Minha Carteira", "➕ Novo Cadastro", "📊 Relatório de Captação"])
        
        with tab1:
            st.subheader("Entidades em Atendimento")
            st.write("Aqui aparecerá a lista dos seus clientes cadastrados.")
            
        with tab2:
            st.subheader("Cadastrar Novo Ente")
            with st.form("cad_cliente"):
                st.text_input("Nome da Instituição")
                st.text_input("CNPJ")
                st.form_submit_button("Confirmar Cadastro")
                
        with tab3:
            st.subheader("Elaboração de Relatórios")
            st.info("Dados inseridos aqui serão visualizados pelo cliente no Portal do Ente.")
            st.text_area("Captação Pública", placeholder="Ex: Editais, Emendas Parlamentares...")
            st.text_area("Captação Privada", placeholder="Ex: Fundos Sociais, Doações...")
            st.button("Publicar Relatório")

# --- 4. TELAS DE ACESSO (VITRINE E PLANOS) ---

def exibir_planos():
    st.markdown("<h2 style='text-align: center;'>Licenças de Uso Profissional</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("### Plano Básico\n**R$ 1.250,00/mês**")
            st.write("✅ Radar de Emendas\n✅ Consulta de Recursos\n❌ Gestão de Clientes")
            st.link_button("Assinar Básico", "https://www.mercadopago.com.br")
    with col2:
        with st.container(border=True):
            st.markdown("### Plano Premium 🔥\n**R$ 2.300,00/mês**")
            st.write("✅ Tudo do Básico\n✅ Gestão de Clientes\n✅ Relatórios de Captação")
            st.link_button("Assinar Premium", "https://www.mercadopago.com.br")
    if st.button("⬅️ Voltar"): st.session_state['secao'] = 'home'; st.rerun()

def exibir_home():
    st.markdown("<h1 style='text-align: center;'>Portal CoreGov</h1>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("👤 Consultor", use_container_width=True): st.session_state['secao'] = 'login'; st.rerun()
    with c2: 
        if st.button("📝 Licenças", use_container_width=True): st.session_state['secao'] = 'planos'; st.rerun()
    with c3: st.button("🚀 Tecnologia", use_container_width=True)
    with c4: 
        if st.button("🏛️ Sou Cliente", use_container_width=True): st.session_state['secao'] = 'cliente'; st.rerun()

# --- 5. LÓGICA DE NAVEGAÇÃO (ESQUELETO FINAL) ---

def main():
    if not st.session_state['logado']:
        if st.session_state['secao'] == 'home': exibir_home()
        elif st.session_state['secao'] == 'planos': exibir_planos()
        elif st.session_state['secao'] == 'login':
            st.markdown("### 🔐 Login")
            with st.form("f_login"):
                u = st.text_input("Usuário")
                p = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar"):
                    if autenticar_usuario(u, p): st.rerun()
                    else: st.error("Erro no login.")
            if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()
        elif st.session_state['secao'] == 'cliente':
            st.markdown("### 🏛️ Portal do Ente")
            st.text_input("CNPJ da Instituição")
            st.button("Ver Relatório")
            if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()
    else:
        # MENU LATERAL (SIDEBAR)
        with st.sidebar:
            st.title("🛰️ CoreGov")
            st.write(f"Plano: **{st.session_state['usuario_plano']}**")
            escolha = st.radio("Menu:", ["🏠 Início", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto", "💼 Gestão de Clientes"])
            if st.button("🚪 Sair"): st.session_state.clear(); st.rerun()

        # NAVEGAÇÃO DOS MÓDULOS
        if escolha == "🏠 Início": st.write(f"### Bem-vindo, {st.session_state.get('usuario_nome')}!")
        elif escolha == "💼 Gestão de Clientes": modulo_gestao_clientes()
        else: st.write(f"Módulo {escolha} pronto para integração.")

if __name__ == "__main__":
    main()
