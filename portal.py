import streamlit as st
import pandas as pd
import gdown
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

# --- 1. CONFIGURAÇÕES DE LINKS ---
URL_CLIENTES_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT4dCgWCWMhrPNgrSMkXDd2s2FA9eP_gSu9pL8c1MfuJk3YvcQw0kVMq6i8p_FA2Zz7IhAYEexg3CoI/pub?gid=1923834729&single=true&output=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzH2C-ski7ARq9XC6YweSMKf1VpSuxGvJHjAKSyL85ILsjLxGg6hDTxUHxLk40iEW7HTg/exec"
LINK_MERCADO_PAGO_BASICO = "https://www.mercadopago.com.br" 
LINK_MERCADO_PAGO_PREMIUM = "https://www.mercadopago.com.br" 

# --- 2. IMPORTAÇÃO DOS MÓDULOS ---
import radar_emendas_2026
import recursos2026
import revisor_estatuto

# --- 3. FUNÇÕES DE APOIO ---

def obter_creds():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    nome_da_chave = 'ponto-facial-oseiascarveng-cd7b1ab54295.json'
    if os.path.exists(nome_da_chave):
        return Credentials.from_service_account_file(nome_da_chave, scopes=scope)
    return None

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
    except: return False

# --- 4. MÓDULO GESTÃO DE CLIENTES ---

def gerenciar_clientes():
    st.header("💼 Gestão de Clientes Atendidos")
    user_ref = st.session_state.get('usuario_nome', '').lower()

    try:
        df = pd.read_csv(URL_CLIENTES_CSV)
        meus_clientes = df[df['Consultor'].astype(str).str.lower() == user_ref]
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        meus_clientes = pd.DataFrame()

    t1, t2, t3 = st.tabs(["👥 Minha Carteira", "➕ Novo Cadastro", "📊 Relatórios"])

    with t1:
        if meus_clientes.empty:
            st.info("Você ainda não possui clientes vinculados ao seu usuário.")
        else:
            st.dataframe(meus_clientes, use_container_width=True, hide_index=True)

    with t2:
        with st.form("add_client", clear_on_submit=True):
            st.subheader("Cadastrar Novo Cliente")
            st.warning("⚠️ A ativação de cada cliente gerará uma taxa adicional de R$ 450,00.")
            c_cnpj = st.text_input("CNPJ")
            c_nome = st.text_input("Nome do Cliente / Ente")
            c_tel = st.text_input("Telefone")
            if st.form_submit_button("Salvar na Planilha"):
                if c_cnpj and c_nome:
                    payload = {
                        "acao": "incluir", 
                        "consultor": user_ref, 
                        "cnpj": c_cnpj, 
                        "nome": c_nome,
                        "telefone": c_tel
                    }
                    try:
                        requests.post(WEBHOOK_URL, json=payload)
                        st.success(f"Cliente {c_nome} enviado com sucesso!")
                        st.balloons()
                    except:
                        st.error("Erro ao conectar com o servidor.")
                else:
                    st.warning("Preencha CNPJ e Nome.")

# --- 5. INTERFACE PRINCIPAL ---

st.set_page_config(page_title="CoreGov", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'secao' not in st.session_state: st.session_state['secao'] = 'home'

    if not st.session_state['logado']:
        # --- CABEÇALHO ---
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            if os.path.exists("logocoregov.png"):
                st.image("logocoregov.png", use_container_width=True)
            st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Portal CoreGov</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: #64748B;'>Inteligência Estratégica em Recursos Públicos</h3>", unsafe_allow_html=True)
        
        st.write("---")

        # --- HOME / VITRINE ---
        if st.session_state['secao'] == 'home':
            st.markdown("""
                <style>
                .card-v { padding: 25px; border-radius: 15px; box-shadow: 5px 5px 15px rgba(0,0,0,0.1); height: 280px; margin-bottom: 10px; }
                .card-green { background-color: #f0fff4; border-left: 8px solid #48bb78; }
                .card-yellow { background-color: #fffff0; border-left: 8px solid #ecc94b; }
                .card-blue { background-color: #ebf8ff; border-left: 8px solid #4299e1; }
                </style>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="card-v card-green"><h3>👤 Sou Consultor</h3><p>Acesse sua carteira de clientes, radar de emendas e ferramentas de gestão consultiva.</p></div>', unsafe_allow_html=True)
                if st.button("Acessar Painel", use_container_width=True):
                    st.session_state['secao'] = 'login'
                    st.rerun()
            with col2:
                st.markdown('<div class="card-v card-yellow"><h3>📝 Solicitar Licença</h3><p>Ainda não é parceiro? Escolha seu plano e obtenha acesso imediato às ferramentas.</p></div>', unsafe_allow_html=True)
                if st.button("Ver Planos", use_container_width=True):
                    st.session_state['secao'] = 'planos'
                    st.rerun()
            with col3:
                st.markdown('<div class="card-v card-blue"><h3>🚀 Tecnologia</h3><p>Automatização de dados do Transferegov e monitoramento de emendas para alta performance.</p></div>', unsafe_allow_html=True)
                st.button("Saiba Mais", use_container_width=True)

        # --- SEÇÃO DE LOGIN ---
        elif st.session_state['secao'] == 'login':
            col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
            with col_l2:
                st.markdown("### 🔑 Login de Consultor")
                with st.form("login_form"):
                    u = st.text_input("Usuário")
                    p = st.text_input("Senha", type="password")
                    if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                        if autenticar_usuario(u, p): st.rerun()
                        else: st.error("Usuário ou senha incorretos.")
                if st.button("Voltar para Início", use_container_width=True):
                    st.session_state['secao'] = 'home'
                    st.rerun()

        # --- SEÇÃO DE PLANOS ATUALIZADA ---
        elif st.session_state['secao'] == 'planos':
            st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Licenças de Uso Profissional</h2>", unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            
            with p1:
                st.markdown("""
                    <div style="background-color: #ffffff; padding: 30px; border-radius: 15px; border: 2px solid #e0e0e0; text-align: center; min-height: 550px;">
                        <h2 style="color: #4A5568;">Plano Básico</h2>
                        <h1 style="color: #2D3748;">R$ 1.250,00<small style="font-size: 14px;">/mês</small></h1>
                        <p style="color: #718096;"><b>+ R$ 450,00 por cliente atendido</b></p>
                        <hr>
                        <ul style="text-align: left; list-style-type: none; padding: 0;">
                            <li>✅ Radar de Emendas 2026</li>
                            <li>✅ Consulta de Recursos</li>
                            <li>✅ Gestão de Clientes Atendidos</li>
                            <li>✅ Revisor de Estatuto (Até 10 revisões)</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
                st.link_button("Assinar Básico", LINK_MERCADO_PAGO_BASICO, use_container_width=True)

            with p2:
                st.markdown("""
                    <div style="background-color: #f7fafc; padding: 30px; border-radius: 15px; border: 2px solid #4299e1; text-align: center; min-height: 550px;">
                        <h2 style="color: #2B6CB0;">Plano Premium</h2>
                        <h1 style="color: #2C5282;">R$ 2.300,00<small style="font-size: 14px;">/mês</small></h1>
                        <p style="color: #718096;"><b>+ R$ 450,00 por cliente atendido</b></p>
                        <hr>
                        <ul style="text-align: left; list-style-type: none; padding: 0;">
                            <li>✅ Todos os Recursos do Plano Básico</li>
                            <li>✅ Revisor de Estatuto (Até 15 revisões)</li>
                            <li>✅ Carteira Expandida (Até 15 clientes)</li>
                            <li>✅ Inteligência de Dados Prioritária</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
                st.link_button("Assinar Premium 🔥", LINK_MERCADO_PAGO_PREMIUM, use_container_width=True)
            
            st.write("")
            if st.button("Voltar para Início", use_container_width=True):
                st.session_state['secao'] = 'home'
                st.rerun()

    else:
        # --- ÁREA LOGADA ---
        with st.sidebar:
            if os.path.exists("logocoregov.png"): st.image("logocoregov.png", use_container_width=True)
            st.title("CoreGov")
            user = st.session_state.get('usuario_nome', 'admin')
            st.info(f"👤 CONSULTOR: {user.upper()}")
            st.subheader("Navegação")
            opcoes_menu = ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto", "💼 Clientes Atendidos"]
            if user.lower() == "admin": opcoes_menu.append("🔧 Gestão Admin")
            escolha = st.radio("Selecione o Módulo:", opcoes_menu)
            st.divider()
            if st.button("🚪 Sair do Sistema", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        if escolha == "🏠 Home":
            st.markdown(f"### 👋 Bem-vindo, {user.capitalize()}!")
            st.info("Utilize o menu lateral para gerenciar sua operação.")
        elif escolha == "💼 Clientes Atendidos": gerenciar_clientes()
        elif escolha == "🏛️ Radar de Emendas": radar_emendas_2026.exibir_radar()
        elif escolha == "📊 Recursos 2026": recursos2026.exibir_recursos()
        elif escolha == "📜 Revisor de Estatuto": revisor_estatuto.exibir_revisor()
        elif escolha == "🔧 Gestão Admin": st.title("🔧 Painel Administrativo")

if __name__ == "__main__":
    executar()
