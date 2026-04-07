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

# --- 3. FUNÇÕES DE SUPORTE E AUTENTICAÇÃO ---

def autenticar_usuario(usuario_digitado, senha_digitada):
    """Valida o login consultando o arquivo Excel no Google Drive"""
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
        st.error(f"Erro na conexão com o banco de dados: {e}")
        return False

# --- 4. FUNÇÕES DE INTERFACE ---

def exibir_planos():
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Licenças de Uso Profissional</h2>", unsafe_allow_html=True)
    st.write("")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        with st.container(border=True):
            st.markdown("### 📄 Plano Básico")
            st.markdown("## R$ 1.250,00 <small style='font-size:15px'>/mês</small>", unsafe_allow_html=True)
            st.write("---")
            st.write("✅ **Radar de Emendas 2026**")
            st.write("✅ **Consulta de Recursos**")
            st.write("✅ **Revisor de Estatuto IA (10 rev)**")
            st.write("❌ ~~Gestão de Clientes e Relatórios~~")
            st.write("❌ ~~Acesso ao Portal do Ente (CNPJ)~~")
            st.write("")
            st.link_button("Assinar Plano Básico", "https://www.mercadopago.com.br", use_container_width=True)

    with col_p2:
        with st.container(border=True):
            st.markdown("### 🚀 Plano Premium 🔥")
            st.markdown("## R$ 2.300,00 <small style='font-size:15px'>/mês</small>", unsafe_allow_html=True)
            st.write("---")
            st.write("✅ **Tudo do Plano Básico**")
            st.write("✅ **Gestão de Clientes Atendidos**")
            st.write("✅ **Relatórios de Captação**")
            st.write("✅ **Portal do Cliente (Acesso CNPJ)**")
            st.write("✅ **Revisor de Estatuto IA (15 rev)**")
            st.write("⚠️ **Taxa Operacional: R$ 450/cliente**")
            st.link_button("Assinar Plano Premium", "https://www.mercadopago.com.br", use_container_width=True)

    st.write("")
    if st.button("⬅️ Voltar para a Vitrine", use_container_width=True):
        st.session_state['secao'] = 'home'
        st.rerun()

def exibir_home():
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>Portal CoreGov</h1>", unsafe_allow_html=True)
    st.write("---")
    
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

# --- 5. LÓGICA DE RENDERIZAÇÃO PRINCIPAL ---

def main():
    if not st.session_state['logado']:
        if st.session_state['secao'] == 'home':
            exibir_home()
        
        elif st.session_state['secao'] == 'planos':
            exibir_planos()
            
        elif st.session_state['secao'] == 'login':
            st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔐 Acesso do Consultor</h2>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                with st.form("login_form"):
                    u = st.text_input("Usuário")
                    p = st.text_input("Senha", type="password")
                    if st.form_submit_button("Entrar", use_container_width=True):
                        if autenticar_usuario(u, p):
                            st.rerun()
                        else:
                            st.error("Credenciais inválidas ou licença inativa.")
                if st.button("Voltar", use_container_width=True): 
                    st.session_state['secao'] = 'home'
                    st.rerun()
                
        elif st.session_state['secao'] == 'cliente':
            st.markdown("<h2 style='text-align: center;'>🏛️ Portal do Ente</h2>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.text_input("Digite o CNPJ da Instituição")
                st.button("Consultar", use_container_width=True)
                if st.button("Voltar", use_container_width=True): 
                    st.session_state['secao'] = 'home'
                    st.rerun()
    
    else:
        st.sidebar.title("CoreGov")
        st.sidebar.write(f"Plano: **{st.session_state['usuario_plano']}**")
        if st.sidebar.button("Sair"):
            st.session_state.clear()
            st.rerun()
        st.write(f"### Bem-vindo ao Painel Administrativo, {st.session_state.get('usuario_nome', 'Consultor')}!")

if __name__ == "__main__":
    main()
