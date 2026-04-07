import streamlit as st
import pandas as pd
import gdown
import os
import requests
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAÇÕES DE LINKS E APIs ---
URL_CLIENTES_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT4dCgWCWMhrPNgrSMkXDd2s2FA9eP_gSu9pL8c1MfuJk3YvcQw0kVMq6i8p_FA2Zz7IhAYEexg3CoI/pub?gid=1923834729&single=true&output=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzH2C-ski7ARq9XC6YweSMKf1VpSuxGvJHjAKSyL85ILsjLxGg6hDTxUHxLk40iEW7HTg/exec"

# --- 2. FUNÇÕES DE AUTENTICAÇÃO RECUPERADAS ---

def autenticar_usuario(usuario_digitado, senha_digitada):
    """Recupera a lógica original de validação via Excel no Drive"""
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

# --- 3. MÓDULOS DE INTERFACE ---

def exibir_relatorio_acesv(editavel=False):
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>RELATÓRIO CAPTAÇÃO DE RECURSOS</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### 🏛️ Identificação do Ente")
        if editavel:
            st.text_input("Instituição:", value="OBRA SAGRADOS CORAÇÕES DE JESUS E MARIA")
            st.text_input("CNPJ:", value="30.045.561/0001-78")
            if st.button("💾 Publicar Relatório"):
                st.success("Relatório atualizado!")
        else:
            st.write("**Instituição:** OBRA SAGRADOS CORAÇÕES DE JESUS E MARIA")
            st.write("**CNPJ:** 30.045.561/0001-78")

def area_do_cliente():
    st.markdown("<h2 style='text-align: center;'>🛰️ Portal do Cliente</h2>", unsafe_allow_html=True)
    cnpj_input = st.text_input("CNPJ para acesso:", placeholder="00.000.000/0000-00")
    if st.button("Acessar Painel"):
        st.divider()
        exibir_relatorio_acesv(editavel=False)

def gerenciar_clientes():
    st.header("💼 Gestão de Clientes")
    user_ref = st.session_state.get('usuario_nome', '').upper()
    st.info(f"Consultor logado: {user_ref}")
    t1, t2, t3 = st.tabs(["👥 Minha Carteira", "➕ Novo Cadastro", "📊 Elaborar Relatório"])
    with t3: exibir_relatorio_acesv(editavel=True)

# --- 4. EXECUÇÃO PRINCIPAL (VITRINE + LOGIN REAL) ---

st.set_page_config(page_title="CoreGov", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'secao' not in st.session_state: st.session_state['secao'] = 'home'

    # Fluxo Deslogado
    if not st.session_state['logado'] and st.session_state['secao'] != 'cliente':
        
        # Cabeçalho
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Portal CoreGov</h1>", unsafe_allow_html=True)
        st.write("---")

        if st.session_state['secao'] == 'home':
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown('<div style="background:#f0fff4; padding:20px; border-radius:15px; height:250px; text-align:center;"><h3>👤 Consultor</h3><p>Painel de controle.</p></div>', unsafe_allow_html=True)
                if st.button("Entrar no Painel", use_container_width=True):
                    st.session_state['secao'] = 'login'; st.rerun()
            with c2: st.markdown('<div style="background:#fffff0; padding:20px; border-radius:15px; height:250px; text-align:center;"><h3>📝 Licenças</h3></div>', unsafe_allow_html=True)
            with c3: st.markdown('<div style="background:#ebf8ff; padding:20px; border-radius:15px; height:250px; text-align:center;"><h3>🚀 Tecnologia</h3></div>', unsafe_allow_html=True)
            with c4:
                st.markdown('<div style="background:#fff5f5; padding:20px; border-radius:15px; height:250px; text-align:center;"><h3>🏛️ Sou Cliente</h3></div>', unsafe_allow_html=True)
                if st.button("Acessar Relatórios", use_container_width=True):
                    st.session_state['secao'] = 'cliente'; st.rerun()

        # TELA DE LOGIN REAL RECUPERADA
        elif st.session_state['secao'] == 'login':
            col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
            with col_l2:
                st.markdown("### 🔑 Login de Consultor")
                with st.form("login_form"):
                    u = st.text_input("Usuário")
                    p = st.text_input("Senha", type="password")
                    if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                        if autenticar_usuario(u, p):
                            st.success("Acesso autorizado!")
                            st.rerun()
                        else:
                            st.error("Usuário, senha ou licença inválida.")
                if st.button("Voltar para Início"):
                    st.session_state['secao'] = 'home'; st.rerun()

    # Fluxo Área do Cliente
    elif st.session_state['secao'] == 'cliente':
        area_do_cliente()
        if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()

    # Fluxo Área Logada do Consultor
    else:
        with st.sidebar:
            st.title("CoreGov")
            escolha = st.radio("Módulo:", ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto", "💼 Gestão de Clientes"])
            if st.button("🚪 Sair"):
                st.session_state.clear()
                st.rerun()
        
        if escolha == "💼 Gestão de Clientes": gerenciar_clientes()
        else: st.info(f"Módulo {escolha} selecionado.")

if __name__ == "__main__":
    executar()
