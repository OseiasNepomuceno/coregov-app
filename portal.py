import streamlit as st
import pandas as pd
import gdown
import os

# --- 1. INICIALIZAÇÃO CRÍTICA (Evita Tela Branca) ---
if 'secao' not in st.session_state:
    st.session_state['secao'] = 'home'
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
if 'usuario_plano' not in st.session_state:
    st.session_state['usuario_plano'] = 'BÁSICO'

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="CoreGov", page_icon="🛰️", layout="wide")

# --- 3. FUNÇÕES DE NAVEGAÇÃO ---

def exibir_home():
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Portal CoreGov</h1>", unsafe_allow_html=True)
    st.write("---")
    
    # CSS dos Cards
    st.markdown("""
        <style>
        .card-v { padding: 25px; border-radius: 15px; box-shadow: 5px 5px 15px rgba(0,0,0,0.05); height: 280px; text-align: center; transition: 0.3s; }
        .card-v:hover { transform: translateY(-5px); }
        </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="card-v" style="background:#f0fff4; border-bottom: 5px solid #48bb78;"><h3>👤 Consultor</h3><p>Painel de gestão.</p></div>', unsafe_allow_html=True)
        if st.button("Entrar no Painel", use_container_width=True):
            st.session_state['secao'] = 'login'
            st.rerun()
    with c2:
        st.markdown('<div class="card-v" style="background:#fffff0; border-bottom: 5px solid #ecc94b;"><h3>📝 Licenças</h3><p>Planos profissionais.</p></div>', unsafe_allow_html=True)
        if st.button("Ver Planos", use_container_width=True):
            st.session_state['secao'] = 'planos'
            st.rerun()
    with c3:
        st.markdown('<div class="card-v" style="background:#ebf8ff; border-bottom: 5px solid #4299e1;"><h3>🚀 Tecnologia</h3><p>IA e Monitoramento.</p></div>', unsafe_allow_html=True)
        st.button("Saiba Mais", use_container_width=True, key="tec_home")
    with c4:
        st.markdown('<div class="card-v" style="background:#fff5f5; border-bottom: 5px solid #f56565;"><h3>🏛️ Sou Cliente</h3><p>Relatórios via CNPJ.</p></div>', unsafe_allow_html=True)
        if st.button("Acessar Relatórios", use_container_width=True):
            st.session_state['secao'] = 'cliente'
            st.rerun()

# --- 4. LÓGICA DE RENDERIZAÇÃO PRINCIPAL ---

def main():
    # Caso o usuário não esteja logado, mostramos a Vitrine ou Telas de Acesso
    if not st.session_state['logado']:
        if st.session_state['secao'] == 'home':
            exibir_home()
        elif st.session_state['secao'] == 'login':
            # Sua função de login aqui
            if st.button("Voltar"): 
                st.session_state['secao'] = 'home'
                st.rerun()
        elif st.session_state['secao'] == 'planos':
            # Sua função de planos aqui
            if st.button("Voltar"): 
                st.session_state['secao'] = 'home'
                st.rerun()
        elif st.session_state['secao'] == 'cliente':
            # Sua função área do cliente aqui
            if st.button("Voltar"): 
                st.session_state['secao'] = 'home'
                st.rerun()
    
    # Caso esteja logado, mostra o Painel Interno
    else:
        st.sidebar.title("Painel CoreGov")
        if st.sidebar.button("Sair"):
            st.session_state.clear()
            st.rerun()
        st.write("Bem-vindo ao sistema!")

if __name__ == "__main__":
    main()
