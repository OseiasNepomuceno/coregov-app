import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

MAPA_ESTADOS = {
    'AC': 'ACRE', 'AL': 'ALAGOAS', 'AP': 'AMAPA', 'AM': 'AMAZONAS', 'BA': 'BAHIA',
    'CE': 'CEARA', 'DF': 'DISTRITO FEDERAL', 'ES': 'ESPIRITO SANTO', 'GO': 'GOIAS',
    'MA': 'MARANHAO', 'MT': 'MATO GROSSO', 'MS': 'MATO GROSSO DO SUL', 'MG': 'MINAS GERAIS',
    'PA': 'PARA', 'PB': 'PARAIBA', 'PR': 'PARANA', 'PE': 'PERNAMBUCO', 'PI': 'PIAUI',
    'RJ': 'RIO DE JANEIRO', 'RN': 'RIO GRANDE DO NORTE', 'RS': 'RIO GRANDE DO SUL',
    'RO': 'RONDONIA', 'RR': 'RORAIMA', 'SC': 'SANTA CATARINA', 'SP': 'SAO PAULO',
    'SE': 'SERGIPE', 'TO': 'TOCANTINS'
}

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').upper().strip()

def formatar_moeda(valor):
    """Formata o valor para o padrão brasileiro R$"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def exibir_radar():
    col_titulo, col_filtro = st.columns([2, 1])
    with col_titulo:
        st.title("🏛️ Radar de Emendas 2026")
    with col_filtro:
        tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="filtro_visao_topo")

    # IDs do Drive
    if tipo_visao == "Visão Geral":
        file_id = st.secrets.get("id_emendas_geral")
        nome_arquivo = "2026_Emendas_Geral.csv"
    else:
        file_id = st.secrets.get("id_emendas_favorecido")
        nome_arquivo = "2026_Emendas_Favorecido.csv"

    # 1. Download
    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error(f"ID de arquivo não configurado para {tipo_visao}.")
            return
        with st.spinner(f"Baixando base de {tipo_visao}..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    # 2. Leitura e Limpeza Inicial
    try:
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]

        # --- BLOCO DE DEPURAÇÃO (OPCIONAL) ---
        with st.expander("🛠️ Debug: Diagnóstico da Planilha"):
            st.write(f"Arquivo lido: {nome_arquivo}")
            st.write(f"Total de linhas brutas: {len(df)}")
            col_ano_debug = next((c for c in df.columns if "ANO" in c), None)
            if col_ano_debug:
                anos_unicos = df[col_ano_debug].unique()
                st.write(f"Anos encontrados na coluna {col_ano_debug}: {anos_unicos}")

        # --- SOLUÇÃO: CORREÇÃO DE FILTRO ---
        coluna_ano = next((c for c in df.columns if "ANO" in c), None)
        if coluna_ano:
            # Convertemos para numérico (int) para garantir a comparação exata
            df[coluna_ano] = pd.to_numeric(df[coluna_ano], errors='coerce')
            df = df[df[coluna_ano] == 2026]
            
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return

    # 3. Lógica de Segurança por Estado (UF)
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    sigla_usuario = str(usuario.get('LOCALIDADE') or "RJ").strip().upper()
    nome_completo_busca = remover_acentos(MAPA_ESTADOS.get(sigla_usuario, sigla_usuario))
    acesso_nacional = (plano in ["PREMIUM", "DIAMANTE", "OURO"])

    coluna_uf = next((c for c in ["UF", "ESTADO", "UF_BENEFICIARIO", "UF_FAVORECIDO", "SG_UF", "SIGLA_UF"] if c in df.columns), None)

    if coluna_uf and not acesso_nacional:
        df['UF_AUX'] = df[coluna_uf].apply(remover_acentos)
        df = df[df['UF_AUX'] == nome_completo_busca]
        df = df.drop(columns=['UF_AUX'])
        st.info(f"📍 Exibindo: **{nome_completo_busca}**")

    # 4. Cards Financeiros (Somente para Visão Geral)
    if tipo_visao == "Visão Geral" and not df.empty:
        col_emp = next((c for c in df.columns if "EMPENHADO" in c), None)
        col_liq = next((c for c in df.columns if "LIQUIDADO" in c), None)
        col_pag = next((c for c in df.columns if "PAGO" in c), None)

        def limpar_valor(col):
            if
