import streamlit as st
import pandas as pd
import gdown
import os

# =================================================================
# 1. CONFIGURAÇÕES TÉCNICAS E ESTABILIDADE (NÃO ALTERAR)
# =================================================================
st.set_page_config(page_title="CoreGov", page_icon="🛰️", layout="wide")

# Inicialização de variáveis de estado para evitar "resets" acidentais
if 'secao' not in st.session_state: st.session_state['secao'] = 'home'
if 'logado' not in st.session_state: st.session_state['logado'] = False
if 'usuario_plano' not in st.session_state: st.session_state['usuario_plano'] = 'BÁSICO'
if 'usuario_nome' not in st.session_state: st.session_state['usuario_nome'] = ''

# =================================================================
# 2. FUNÇÕES DE SUPORTE (LOGIN E DADOS)
# =================================================================
def autenticar_usuario(u, p):
    file_id = st.secrets.get("file_id_licencas")
    url = f'https://drive.google.com/uc?id={file_id}'
    try:
        nome_arq = "licencas_login.xlsx"
        if os.path.exists(nome_arq): os.remove(nome_arq)
        gdown.download(url, nome_arq, quiet=True)
        df = pd.read_excel(nome_arq, sheet_name='usuario')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        u_clean = str(u).strip().lower()
        p_clean = str(p).strip()
        
        user_row = df[(df['USUARIO'].astype(str).str.strip().str.lower() == u_clean) & 
                      (df['SENHA'].astype(str).str.strip() == p_clean)]
        
        if not user_row.empty:
            dados = user_row.iloc[0]
            if str(dados.get('STATUS')).lower().strip() == 'ativo':
                st.session_state['logado'] = True
                st.session_state['usuario_nome'] = u_clean
                st.session_state['usuario_plano'] = str(dados.get('PLANO')).upper().strip()
                return True
        return False
    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return False

# =================================================================
# 3. MÓDULOS INTERNOS (RECHEIO DO SISTEMA)
# =================================================================

def modulo_gestao_clientes():
    st.header("💼 Gestão de Clientes e Relatórios")
    if st.session_state['usuario_plano'] == 'BÁSICO':
        st.warning("⚠️ Módulo disponível apenas no Plano Premium.")
    else:
        # Abas internas que mantêm o estado dentro do módulo
        aba_ativa = st.tabs(["👥 Minha Carteira", "➕ Novo Cadastro", "📊 Relatórios de Captação"])
        
        with aba_ativa[0]:
            st.subheader("Entidades Atendidas")
            st.info("Lista de clientes carregada do banco de dados.")

        with aba_ativa[1]:
            st.subheader("Cadastrar Nova Entidade")
            with st.form("form_novo_cliente"):
                nome = st.text_input("Nome da Instituição")
                cnpj = st.text_input("CNPJ")
                if st.form_submit_button("Salvar Registro"):
                    st.success(f"{nome} cadastrado!")

        with aba_ativa[2]:
            st.subheader("Relatórios de Captação")
            st.info("Preencha os dados que o cliente visualizará no portal.")
            st.text_area("Captação Pública", placeholder="Editais, emendas...")
            st.text_area("Captação Privada", placeholder="Fundos, doações...")
            st.button("Publicar Relatório")

# =================================================================
# 4. INTERFACES DE NAVEGAÇÃO (ESQUELETO)
# =================================================================

def exibir_home():
    st.markdown("<h1 style='text-align: center;'>Portal CoreGov</h1>", unsafe_allow_html=True)
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("👤 Consultor", use_container_width=True): 
            st.session_state['secao'] = 'login'; st.rerun()
    with c2:
        if st.button("📝 Licenças", use_container_width=True): 
            st.session_state['secao'] = 'planos'; st.rerun()
    with c3:
        st.button("🚀 Tecnologia", use_container_width=True)
    with c4:
        if st.button("🏛️ Sou Cliente", use_container_width=True): 
            st.session_state['secao'] = 'cliente'; st.rerun()

def exibir_planos():
    st.markdown("<h2 style='text-align: center;'>Planos Profissionais</h2>", unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        with st.container(border=True):
            st.markdown("### Plano Básico\n**R$ 1.250,00/mês**")
            st.write("✅ Radar de Emendas\n✅ Recursos Gov\n❌ Gestão de Clientes")
            st.link_button("Assinar Básico", "https://mercadopago.com.br")
    with p2:
        with st.container(border=True):
            st.markdown("### Plano Premium 🔥\n**R$ 2.300,00/mês**")
            st.write("✅ Tudo do Básico\n✅ Gestão de Clientes\n✅ Relatórios de Captação")
            st.link_button("Assinar Premium", "https://mercadopago.com.br")
    if st.button("⬅️ Voltar"): st.session_state['secao'] = 'home'; st.rerun()

# =================================================================
# 5. ORQUESTRAÇÃO PRINCIPAL (MAIN)
# =================================================================

def main():
    if not st.session_state['logado']:
        # Fluxo Público
        if st.session_state['secao'] == 'home':
            exibir_home()
        elif st.session_state['secao'] == 'planos':
            exibir_planos()
        elif st.session_state['secao'] == 'login':
            st.markdown("### 🔑 Acesso ao Painel")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                with st.form("f_login"):
                    u = st.text_input("Usuário")
                    p = st.text_input("Senha", type="password")
                    if st.form_submit_button("Entrar"):
                        if autenticar_usuario(u, p): st.rerun()
                        else: st.error("Login inválido.")
                if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()
        elif st.session_state['secao'] == 'cliente':
            st.markdown("### 🏛️ Portal do Ente")
            st.text_input("CNPJ da Instituição")
            st.button("Consultar")
            if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()
    
    else:
        # Fluxo Logado (Sidebar + Módulos)
        with st.sidebar:
            st.title("🛰️ CoreGov")
            st.write(f"Plano: **{st.session_state['usuario_plano']}**")
            menu = st.radio("Menu:", ["🏠 Início", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto", "💼 Gestão de Clientes"])
            st.divider()
            if st.button("🚪 Sair"): 
                st.session_state.clear(); st.rerun()

        # RENDERIZAÇÃO DO CONTEÚDO
        if menu == "🏠 Início":
            st.write(f"### Bem-vindo, {st.session_state['usuario_nome'].upper()}!")
            st.info("Selecione um módulo no menu lateral.")
        elif menu == "💼 Gestão de Clientes":
            modulo_gestao_clientes()
        else:
            st.write(f"### Módulo {menu}")
            st.write("Módulo ativo e pronto para receber o código específico.")

if __name__ == "__main__":
    main()
