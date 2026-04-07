import streamlit as st
import pandas as pd
import gdown
import os
import requests
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAÇÕES DE LINKS E APIs ---
URL_CLIENTES_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT4dCgWCWMhrPNgrSMkXDd2s2FA9eP_gSu9pL8c1MfuJk3YvcQw0kVMq6i8p_FA2Zz7IhAYEexg3CoI/pub?gid=1923834729&single=true&output=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzH2C-ski7ARq9XC6YweSMKf1VpSuxGvJHjAKSyL85ILsjLxGg6hDTxUHxLk40iEW7HTg/exec"
LINK_MERCADO_PAGO_BASICO = "https://www.mercadopago.com.br" 
LINK_MERCADO_PAGO_PREMIUM = "https://www.mercadopago.com.br" 

# --- 2. IMPORTAÇÃO DOS MÓDULOS ---
import radar_emendas_2026
import recursos2026
import revisor_estatuto

# --- 3. FUNÇÃO DO RELATÓRIO MODELO ACESV ---

def exibir_relatorio_acesv(editavel=False):
    """Estrutura baseada no arquivo Word da ACESV"""
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>RELATÓRIO CAPTAÇÃO DE RECURSOS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'><b>Referência: Março 2026</b></p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("### 🏛️ Identificação do Ente")
        if editavel:
            ente = st.text_input("Instituição:", value="OBRA SAGRADOS CORAÇÕES DE JESUS E MARIA")
            cnpj = st.text_input("CNPJ:", value="30.045.561/0001-78")
        else:
            st.write("**Instituição:** OBRA SAGRADOS CORAÇÕES DE JESUS E MARIA")
            st.write("**CNPJ:** 30.045.561/0001-78")

        col1, col2 = st.columns(2)
        opcoes = ["Aguardando resultado", "Projeto em análise", "Cadastro", "Concluído", "Emendas parlamentares"]

        with col1:
            st.markdown("#### 🏛️ CAPTAÇÃO PÚBLICA")
            if editavel:
                st.selectbox("Edital Estadual Cultura&Fé", opcoes, index=0)
                st.selectbox("MPRJ (Verbas Pecuniárias)", opcoes, index=1)
                st.selectbox("TJRJ", opcoes, index=1)
                st.multiselect("Outros", ["Emendas parlamentares", "Extraemendas"], default=["Emendas parlamentares", "Extraemendas"])
            else:
                st.write("• Edital Estadual Cultura&Fé: **Aguardando resultado**")
                st.write("• MPRJ: **Projeto em análise**")
                st.write("• TJRJ: **Projeto em análise**")
                st.write("• Emendas parlamentares / Extraemendas")

        with col2:
            st.markdown("#### 🏢 CAPTAÇÃO PRIVADA")
            if editavel:
                st.selectbox("Itaú Social", opcoes, index=2)
                st.selectbox("Fundo Social SICREDI", opcoes, index=2)
                st.selectbox("Reckitt Super Repelex", ["Cadastro e doação realizada", "Em análise"], index=0)
                st.text_area("Empresas em análise:", value="Casa Andorinha, Elson’s, Guaracamp, Havaianas, Rio Brasil Terminal")
            else:
                st.write("• Itaú Social: **Cadastro**")
                st.write("• Fundo Social SICREDI: **Cadastro**")
                st.write("• Reckitt Super Repelex: **Cadastro e doação**")
                st.write("• Empresas em análise: *Casa Andorinha, Elson’s, Guaracamp, Havaianas*")

    st.markdown("""
        <div style="background-color: #f1f5f9; padding: 15px; border-radius: 10px; font-size: 14px; color: #475569;">
        Este relatório é parte de cada parceria firmada para fortalecer a missão institucional e amplia o alcance das nossas ações. 
        Seguimos com responsabilidade, transparência e propósito.
        </div>
    """, unsafe_allow_html=True)

    if editavel:
        if st.button("💾 Publicar Relatório para Cliente"):
            st.success("Relatório atualizado com sucesso!")

# --- 4. ÁREA DO CLIENTE (CNPJ) ---

def area_do_cliente():
    st.markdown("<h2 style='text-align: center;'>🛰️ Portal do Cliente - Acompanhamento</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        cnpj_input = st.text_input("Digite o CNPJ para acessar os relatórios:", placeholder="00.000.000/0000-00")
        btn = st.button("Acessar Painel", use_container_width=True)

    if btn and cnpj_input:
        st.divider()
        exibir_relatorio_acesv(editavel=False)
        if st.button("⬅️ Sair da Área do Cliente"):
            st.session_state['secao'] = 'home'
            st.rerun()

# --- 5. GESTÃO DE CLIENTES (CONSULTOR) ---

def gerenciar_clientes():
    st.header("💼 Gestão de Clientes Atendidos")
    t1, t2, t3 = st.tabs(["👥 Minha Carteira", "➕ Novo Cadastro", "📊 Elaborar Relatório (Editável)"])
    
    with t1:
        st.info("Sua lista de clientes ativos aparecerá aqui.")
    with t2:
        with st.form("add"):
            st.text_input("CNPJ do Cliente")
            st.text_input("Nome/Ente")
            st.form_submit_button("Cadastrar")
    with t3:
        exibir_relatorio_acesv(editavel=True)

# --- 6. INTERFACE PRINCIPAL (VITRINE) ---

st.set_page_config(page_title="CoreGov", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'secao' not in st.session_state: st.session_state['secao'] = 'home'

    if not st.session_state['logado'] and st.session_state['secao'] != 'cliente':
        # CABEÇALHO
        col_c2 = st.columns([1, 2, 1])[1]
        with col_c2:
            st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Portal CoreGov</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: #64748B;'>Inteligência em Recursos Públicos</h3>", unsafe_allow_html=True)
        st.write("---")

        if st.session_state['secao'] == 'home':
            # ESTILO DOS CARDS
            st.markdown("""
                <style>
                .card-v { padding: 25px; border-radius: 15px; box-shadow: 5px 5px 15px rgba(0,0,0,0.05); height: 280px; text-align: center; transition: 0.3s; }
                .card-v:hover { transform: translateY(-5px); }
                </style>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown('<div class="card-v" style="background:#f0fff4; border-bottom: 5px solid #48bb78;"><h3>👤 Consultor</h3><p>Painel de controle para gestão de emendas e clientes.</p></div>', unsafe_allow_html=True)
                if st.button("Entrar no Painel", key="btn_cons", use_container_width=True):
                    st.session_state['secao'] = 'login'; st.rerun()
            with c2:
                st.markdown('<div class="card-v" style="background:#fffff0; border-bottom: 5px solid #ecc94b;"><h3>📝 Licenças</h3><p>Escolha seu plano e ative sua conta profissional.</p></div>', unsafe_allow_html=True)
                if st.button("Ver Planos", key="btn_plan", use_container_width=True):
                    st.session_state['secao'] = 'planos'; st.rerun()
            with c3:
                st.markdown('<div class="card-v" style="background:#ebf8ff; border-bottom: 5px solid #4299e1;"><h3>🚀 Tecnologia</h3><p>Conheça nossa IA de monitoramento e revisão.</p></div>', unsafe_allow_html=True)
                st.button("Saiba Mais", key="btn_tec", use_container_width=True)
            with c4:
                st.markdown('<div class="card-v" style="background:#fff5f5; border-bottom: 5px solid #f56565;"><h3>🏛️ Sou Cliente</h3><p>Acesse com seu CNPJ para ver relatórios de captação.</p></div>', unsafe_allow_html=True)
                if st.button("Acessar Relatórios", key="btn_cli", use_container_width=True):
                    st.session_state['secao'] = 'cliente'; st.rerun()

        elif st.session_state['secao'] == 'login':
            # Tela de Login do Consultor (Simplificada aqui)
            if st.button("Simular Login"): st.session_state['logado'] = True; st.rerun()
            if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()

        elif st.session_state['secao'] == 'planos':
            st.markdown("## Planos Profissionais")
            # Conteúdo dos planos conforme sua orientação (R$1.250 / R$2.300 + R$450/cliente)
            if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()

    elif st.session_state['secao'] == 'cliente':
        area_do_cliente()
    
    else:
        # ÁREA LOGADA
        with st.sidebar:
            st.title("CoreGov")
            escolha = st.radio("Módulo:", ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto", "💼 Gestão de Clientes"])
            if st.button("🚪 Sair"): st.session_state.clear(); st.rerun()
        
        if escolha == "💼 Gestão de Clientes": gerenciar_clientes()
        else: st.write(f"Você está no módulo: {escolha}")

if __name__ == "__main__":
    executar()
