import streamlit as st
import pandas as pd
import gdown
import os

# --- 1. CONFIGURAÇÕES DE LINKS ---
LINK_MERCADO_PAGO_BASICO = "https://www.mercadopago.com.br" 
LINK_MERCADO_PAGO_PREMIUM = "https://www.mercadopago.com.br" 

# --- 2. SEÇÃO DE PLANOS (ATUALIZADA COM AS NOVAS REGRAS) ---

def exibir_planos():
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Licenças de Uso Profissional</h2>", unsafe_allow_html=True)
    
    p1, p2 = st.columns(2)
    
    with p1:
        st.markdown("""
            <div style="background-color: #ffffff; padding: 30px; border-radius: 15px; border: 2px solid #e0e0e0; text-align: center; min-height: 550px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);">
                <h2 style="color: #4A5568;">Plano Básico</h2>
                <h1 style="color: #2D3748; font-size: 32px;">R$ 1.250,00<small style="font-size: 14px;">/mês</small></h1>
                <p style="color: #718096; font-size: 14px;">Faturamento Mensal Fixo</p>
                <hr>
                <ul style="text-align: left; list-style-type: none; padding: 0; font-size: 15px; line-height: 2.2;">
                    <li>✅ <b>Radar de Emendas 2026</b></li>
                    <li>✅ <b>Consulta de Recursos (Transferegov)</b></li>
                    <li>✅ <b>Revisor de Estatuto IA:</b> 10 revisões</li>
                    <li>❌ <del style="color: #a0aec0;">Gestão de Clientes e Relatórios</del></li>
                    <li>❌ <del style="color: #a0aec0;">Acesso ao Portal do Ente (CNPJ)</del></li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        st.link_button("Assinar Plano Básico", LINK_MERCADO_PAGO_BASICO, use_container_width=True)

    with p2:
        st.markdown("""
            <div style="background-color: #f7fafc; padding: 30px; border-radius: 15px; border: 2px solid #4299e1; text-align: center; min-height: 550px; box-shadow: 0px 8px 16px rgba(0,0,0,0.1);">
                <h2 style="color: #2B6CB0;">Plano Premium 🔥</h2>
                <h1 style="color: #2C5282; font-size: 32px;">R$ 2.300,00<small style="font-size: 14px;">/mês</small></h1>
                <p style="color: #718096; font-size: 14px;">Faturamento Mensal Fixo</p>
                <hr>
                <ul style="text-align: left; list-style-type: none; padding: 0; font-size: 15px; line-height: 2.2;">
                    <li>✅ <b>Tudo do Plano Básico</b></li>
                    <li>✅ <b>Gestão de Clientes Atendidos</b></li>
                    <li>✅ <b>Relatórios de Captação (Modelo ACESV)</b></li>
                    <li>✅ <b>Portal do Cliente (Acesso via CNPJ)</b></li>
                    <li>✅ <b>Revisor de Estatuto IA:</b> 15 revisões</li>
                    <li>⚠️ <b>Taxa Operacional:</b> R$ 450,00/cliente</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        st.link_button("Assinar Plano Premium", LINK_MERCADO_PAGO_PREMIUM, use_container_width=True)
    
    if st.button("⬅️ Voltar para a Vitrine", use_container_width=True):
        st.session_state['secao'] = 'home'
        st.rerun()

# --- 3. GESTÃO DE ACESSO (TRAVA DE PLANO) ---

def gerenciar_clientes():
    # Recupera o plano do usuário logado
    plano_usuario = st.session_state.get('usuario_plano', 'BÁSICO')
    
    if plano_usuario == 'BÁSICO':
        st.warning("⚠️ **Módulo Restrito.** O Plano Básico não inclui a Gestão de Clientes e Relatórios.")
        st.info("Faça o upgrade para o **Plano Premium** para gerenciar sua carteira e liberar o acesso dos seus clientes via CNPJ.")
        if st.button("Ver Benefícios do Plano Premium"):
            st.session_state['secao'] = 'planos'
            st.rerun()
    else:
        st.header("💼 Gestão de Clientes e Relatórios (Premium)")
        t1, t2, t3 = st.tabs(["👥 Minha Carteira", "➕ Novo Cadastro", "📊 Relatório ACESV"])
        with t3:
            # Função do relatório que criamos anteriormente
            st.write("Interface de elaboração de relatório liberada.")

# --- 4. EXECUÇÃO PRINCIPAL ---

def executar():
    if 'logado' not in st.session_state: st.session_state['logado'] = False
    if 'secao' not in st.session_state: st.session_state['secao'] = 'home'

    if not st.session_state['logado'] and st.session_state['secao'] != 'cliente':
        # ... (Código da Vitrine permanece o mesmo) ...
        if st.session_state['secao'] == 'home':
            # Vitrine com os 4 cards
            pass 
        elif st.session_state['secao'] == 'planos':
            exibir_planos()
        # ... (Login e etc) ...
    
    elif st.session_state['logado']:
        with st.sidebar:
            st.title("CoreGov")
            opcao = st.radio("Navegação:", ["🏠 Home", "📊 Recursos 2026", "🏛️ Radar de Emendas", "📜 Revisor de Estatuto", "💼 Gestão de Clientes"])
            if st.button("Sair"): st.session_state.clear(); st.rerun()

        if opcao == "💼 Gestão de Clientes":
            gerenciar_clientes()
        # ... (Outros módulos) ...

if __name__ == "__main__":
    executar()
