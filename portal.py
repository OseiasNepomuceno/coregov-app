import streamlit as st
import pandas as pd
import gdown
import os
import requests
from datetime import datetime

# --- CONFIGURAÇÕES E MÓDULOS ---
URL_CLIENTES_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT4dCgWCWMhrPNgrSMkXDd2s2FA9eP_gSu9pL8c1MfuJk3YvcQw0kVMq6i8p_FA2Zz7IhAYEexg3CoI/pub?gid=1923834729&single=true&output=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzH2C-ski7ARq9XC6YweSMKf1VpSuxGvJHjAKSyL85ILsjLxGg6hDTxUHxLk40iEW7HTg/exec"

# --- MÓDULO DE RELATÓRIO (ESTILO ACESV) ---

def exibir_relatorio_acesv(editavel=False, dados=None):
    """Gera a interface do relatório baseada no modelo Word da ACESV"""
    
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.title("📄 RELATÓRIO CAPTAÇÃO DE RECURSOS")
    st.subheader(f"Mês de Referência: Março 2026") # Baseado no documento [cite: 1]
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # 1. IDENTIFICAÇÃO DO ENTE
    st.markdown("### 🏛️ Identificação")
    if editavel:
        ente_nome = st.text_input("Instituição:", value="OBRA SAGRADOS CORAÇÕES DE JESUS E MARIA") # [cite: 2]
        ente_cnpj = st.text_input("CNPJ:", value="30.045.561/0001-78") # 
    else:
        st.write(f"**Instituição:** {dados.get('ente', 'OBRA SAGRADOS CORAÇÕES DE JESUS E MARIA')}")
        st.write(f"**CNPJ:** {dados.get('cnpj', '30.045.561/0001-78')}")

    col1, col2 = st.columns(2)

    # 2. CAPTAÇÃO PÚBLICA [cite: 4]
    with col1:
        st.markdown("#### 🏛️ CAPTAÇÃO PÚBLICA")
        opcoes_status = ["Aguardando Resultado", "Projeto em Análise", "Cadastro", "Aprovado", "N/A"]
        
        if editavel:
            st.selectbox("Edital Estadual Cultura&Fé", opcoes_status, index=0) # [cite: 5]
            st.selectbox("MPRJ (Verbas Pecuniárias)", opcoes_status, index=1) # [cite: 6]
            st.selectbox("TJRJ", opcoes_status, index=1) # [cite: 7]
            st.multiselect("Outros:", ["Emendas Parlamentares", "Extraemendas"], default=["Emendas Parlamentares", "Extraemendas"]) # [cite: 8, 9]
        else:
            st.write("• Edital Estadual Cultura&Fé: **Aguardando resultado**") [cite: 5]
            st.write("• MPRJ: **Projeto em análise**") [cite: 6]
            st.write("• TJRJ: **Projeto em análise**") [cite: 7]
            st.write("• Emendas Parlamentares") [cite: 8]
            st.write("• Extraemendas") [cite: 9]

    # 3. CAPTAÇÃO PRIVADA [cite: 10]
    with col2:
        st.markdown("#### 🏢 CAPTAÇÃO PRIVADA")
        if editavel:
            st.selectbox("Itaú Social", opcoes_status, index=2) # [cite: 11]
            st.selectbox("Fundo Social SICREDI", opcoes_status, index=2) # [cite: 13]
            st.selectbox("Reckitt Super Repelex", ["Doação Realizada", "Em Análise"], index=0) # [cite: 14]
            st.selectbox("Empresas (Andorinha/Guaracamp/Havaianas)", opcoes_status, index=1) # [cite: 15, 17, 18]
        else:
            st.write("• Itaú Social: **Cadastro**") [cite: 11]
            st.write("• Fundo Social SICREDI: **Cadastro**") [cite: 13]
            st.write("• Reckitt Super Repelex: **Cadastro e Doação**") [cite: 14]
            st.write("• Projetos em Análise: Casa Andorinha, Elson’s, Guaracamp, Havaianas, Rio Brasil Terminal") [cite: 15, 16, 17, 18, 19]

    st.divider()
    
    # MENSAGEM INSTITUCIONAL [cite: 20, 21, 23]
    st.info("Este relatório fortalece nossa missão institucional e amplia o alcance das nossas ações. Seguimos com transparência e propósito.")

    if editavel:
        if st.button("💾 Salvar e Publicar Relatório"):
            st.success("Relatório salvo! O cliente já pode visualizar via CNPJ.")

# --- INTERFACE DE ACESSO ---

def gerenciar_clientes():
    st.header("💼 Gestão de Clientes Atendidos")
    t1, t2, t3 = st.tabs(["👥 Minha Carteira", "➕ Novo Cadastro", "📊 Elaborar Relatório (ACESV)"])
    
    with t3:
        exibir_relatorio_acesv(editavel=True)

def area_do_cliente():
    st.markdown("<h2 style='text-align: center;'>🛰️ Área do Ente (ACESV)</h2>", unsafe_allow_html=True)
    cnpj_login = st.text_input("Acesse com seu CNPJ:", placeholder="30.045.561/0001-78")
    
    if st.button("Visualizar Meu Relatório"):
        if cnpj_login == "30.045.561/0001-78": # Exemplo com o CNPJ do documento 
            exibir_relatorio_acesv(editavel=False)
        else:
            st.error("Nenhum relatório encontrado para este CNPJ.")

# --- EXECUÇÃO PRINCIPAL ---

def executar():
    if 'secao' not in st.session_state: st.session_state['secao'] = 'home'

    if st.session_state['secao'] == 'home':
        col1, col2 = st.columns(2)
        if col1.button("👤 Acesso Consultor"): st.session_state['secao'] = 'login'; st.rerun()
        if col2.button("🏛️ Acesso Cliente (CNPJ)"): st.session_state['secao'] = 'cliente'; st.rerun()
    
    elif st.session_state['secao'] == 'cliente':
        area_do_cliente()
        if st.button("Sair"): st.session_state['secao'] = 'home'; st.rerun()
    
    elif st.session_state['secao'] == 'login':
        gerenciar_clientes()
        if st.button("Sair"): st.session_state['secao'] = 'home'; st.rerun()

if __name__ == "__main__":
    executar()
