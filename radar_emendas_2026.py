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
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_topo")

    # IDs dos arquivos nos Secrets
    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = "base_emendas_2026.csv"

    # Download
    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("Erro: ID do arquivo não configurado nos Secrets."); return
        with st.spinner("Sincronizando dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    try:
        # Leitura com separador ';' e encoding latin1 (padrão de arquivos exportados de sistemas gov)
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        
        # Limpeza de nomes de colunas
        df.columns = [str(c).strip().upper() for c in df.columns]

        # --- FILTRO DE ANO 2026 ---
        # Usando o nome exato que você enviou: "ANO DA EMENDA"
        col_ano = "ANO DA EMENDA"
        if col_ano in df.columns:
            # Remove decimais como .0 e filtra apenas por 2026
            df[col_ano] = df[col_ano].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df = df[df[col_ano] == "2026"]
            
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}"); return

    # LÓGICA DE PERMISSÃO (PREMIUM)
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    acesso_nacional = plano in ["PREMIUM", "DIAMANTE", "OURO"]

    if acesso_nacional:
        st.success("🔓 **Acesso Premium:** Visualizando dados nacionais")
    else:
        col_uf = next((c for c in ["UF", "ESTADO", "LOCALIDADE"] if c in df.columns), None)
        if col_uf:
            sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
            estado_nome = remover_acentos(MAPA_ESTADOS.get(sigla, sigla))
            df = df[df[col_uf].astype(str).apply(remover_acentos) == estado_nome]
            st.info(f"📍 Localidade: {estado_nome}")

    # Exibição dos Dados
    if not df.empty:
        if tipo_visao == "Visão Geral":
            # Função para somar valores monetários brasileiros (99.999,41)
            def somar_coluna(termo):
                col = next((c for c in df.columns if termo in c), None)
                if col:
                    v = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v_emp = somar_coluna("EMPENHADO")
            v_liq = somar_coluna("LIQUIDADO")
            v_pag = somar_coluna("PAGO")

            c1, c2, c3 = st.columns(3)
            c1.metric("EMPENHADO", formatar_moeda(v_emp))
            c2.metric("LIQUIDADO", formatar_moeda(v_liq))
            c3.metric("PAGO", formatar_moeda(v_pag))
            st.divider()

        st.write(f"📊 Foram encontrados **{len(df)}** registros para 2026.")
        
        busca = st.text_input("🔍 Pesquisar na tabela:", key="busca_final_radar")
        if busca:
            mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            st.dataframe(df[mask], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Nenhum registro de 2026 encontrado na base.")
