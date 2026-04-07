import streamlit as st
import pandas as pd
import gdown
import os
import requests

# --- 1. CONFIGURAÇÕES DE LINKS ---
LINK_MERCADO_PAGO_BASICO = "https://www.mercadopago.com.br" 
LINK_MERCADO_PAGO_PREMIUM = "https://www.mercadopago.com.br" 

# --- 2. FUNÇÕES DE APOIO ---

def autenticar_usuario(u, p):
    # Lógica de autenticação recuperada na etapa anterior
    return True # Placeholder para manter o fluxo

# --- 3. SEÇÃO DE PLANOS (RESTAURADA) ---

def exibir_planos():
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Licenças de Uso Profissional</h2>", unsafe_allow_html=True)
    st.write("")
    
    p1, p2 = st.columns(2)
    
    with p1:
        st.markdown("""
            <div style="background-color: #ffffff; padding: 30px; border-radius: 15px; border: 2px solid #e0e0e0; text-align: center; min-height: 520px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);">
                <h2 style="color: #4A5568;">Plano Básico</h2>
                <h1 style="color: #2D3748; font-size: 32px;">R$ 1.250,00<small style="font-size: 14px;">/mês</small></h1>
                <p style="color: #718096; font-size: 14px;">Faturamento Mensal Fixo</p>
                <hr>
                <ul style="text-align: left; list-style-type: none; padding: 0; font-size: 15px; line-height: 2.0;">
                    <li>✅ <b>Radar de Emendas 2026</b></li>
                    <li>✅ <b>Consulta de Recursos</b></li>
                    <li>✅ <b>Gestão de Clientes</b> (Relatórios ACESV)</li>
                    <li>⚠️ <b>Taxa:</b> R$ 450,00/mês por Cliente</li>
                    <li>✅ <b>Revisor de Estatuto IA:</b> 10 revisões</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        st.link_button("Assinar Plano Básico", LINK_MERCADO_PAGO_BASICO, use_container_width=True)

    with p2:
        st.markdown("""
            <div style="background-color: #f7fafc; padding: 30px; border-radius: 15px; border: 2px solid #4299e1; text-align: center; min-height: 520px; box-shadow: 0px 8px 16px rgba(0,0,0,0.1);">
                <h2 style="color: #2B6CB0;">Plano Premium</h2>
                <h1 style="color: #2C5282; font-size: 32px;">R$ 2.300,00<small style="font-size: 14px;">/mês</small></h1>
                <p style="color: #718096; font-size: 14px;">Faturamento Mensal Fixo</p>
                <hr>
                <ul style="text-align: left; list-style-type: none; padding: 0; font-size: 15px; line-height: 2.0;">
                    <li>✅ <b>Tudo do Plano Básico</b></li>
                    <li>✅ <b>Revisor de Estatuto IA:</b> 15 revisões</li>
                    <li>✅ <b>Suporte VIP e Inteligência Prioritária</b></li>
                    <li>⚠️ <b>Taxa:</b> R$ 450,00/mês por Cliente</li>
                    <li>🚀 <b>Acesso antecipado a novas funções</b></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        st.link_button("Assinar Plano Premium 🔥", LINK_MERCADO_PAGO_PREMIUM, use_container_width=True)
    
    st.write("")
    if st.button("⬅️ Voltar para a Vitrine", use_container_width=True):
        st.session_state['secao'] = 'home'
        st.rerun()

# --- 4. EXECUÇÃO PRINCIPAL ---

st.set_page_config(page_title="CoreGov", page_icon="🛰️", layout="wide")

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'secao' not in st.session_state: st.session_state['secao'] = 'home'

    if not st.session_state['logado']:
        # Cabeçalho
        col_logo = st.columns([1, 2, 1])[1]
        with col_logo:
            st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Portal CoreGov</h1>", unsafe_allow_html=True)
        
        # --- VITRINE ---
        if st.session_state['secao'] == 'home':
            st.write("---")
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.markdown('<div style="background:#f0fff4; padding:20px; border-radius:15px; height:280px; text-align:center; border-bottom:5px solid #48bb78;"><h3>👤 Consultor</h3><p>Painel de gestão.</p></div>', unsafe_allow_html=True)
                if st.button("Entrar no Painel", use_container_width=True):
                    st.session_state['secao'] = 'login'; st.rerun()
            
            with c2:
                st.markdown('<div style="background:#fffff0; padding:20px; border-radius:15px; height:280px; text-align:center; border-bottom:5px solid #ecc94b;"><h3>📝 Licenças</h3><p>Planos profissionais.</p></div>', unsafe_allow_html=True)
                if st.button("Ver Planos", use_container_width=True):
                    st.session_state['secao'] = 'planos'; st.rerun()
            
            with c3:
                st.markdown('<div style="background:#ebf8ff; padding:20px; border-radius:15px; height:280px; text-align:center; border-bottom:5px solid #4299e1;"><h3>🚀 Tecnologia</h3><p>IA e Monitoramento.</p></div>', unsafe_allow_html=True)
                st.button("Saiba Mais", use_container_width=True)
            
            with c4:
                st.markdown('<div style="background:#fff5f5; padding:20px; border-radius:15px; height:280px; text-align:center; border-bottom:5px solid #f56565;"><h3>🏛️ Sou Cliente</h3><p>Acesso via CNPJ.</p></div>', unsafe_allow_html=True)
                if st.button("Acessar Relatórios", use_container_width=True):
                    st.session_state['secao'] = 'cliente'; st.rerun()

        # --- TELAS INTERMEDIÁRIAS ---
        elif st.session_state['secao'] == 'planos':
            exibir_planos()
            
        elif st.session_state['secao'] == 'login':
            # Formulário de login já recuperado anteriormente...
            if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()

        elif st.session_state['secao'] == 'cliente':
            # Área do cliente já recuperada anteriormente...
            if st.button("Voltar"): st.session_state['secao'] = 'home'; st.rerun()

    else:
        st.sidebar.title("CoreGov Logado")
        if st.sidebar.button("Sair"): st.session_state.clear(); st.rerun()

if __name__ == "__main__":
    executar()
