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
    col_titulo, col_filtro = st.columns([2, 1])
    with col_titulo:
        st.title("🏛️ Radar de Emendas 2026")
    with col_filtro:
        tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="filtro_visao_topo")

    if tipo_visao == "Visão Geral":
        file_id = st.secrets.get("id_emendas_geral")
        nome_arquivo = "2026_Emendas_Geral.csv"
    else:
        file_id = st.secrets.get("id_emendas_favorecido")
        nome_arquivo = "2026_Emendas_Favorecido.csv"

    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error(f"ID de arquivo não configurado.")
            return
        with st.spinner(f"Sincronizando base..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    try:
        # Lendo com o separador CORRETO do seu arquivo (;)
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip')
        df.columns = [str(c).strip().upper() for c in df.columns]

        # FILTRO DE ANO ULTRA-FORTE
        coluna_ano = 'ANO DA EMENDA'
        if coluna_ano in df.columns:
            # Forçamos para texto e removemos qualquer coisa que não seja o número
            df[coluna_ano] = df[coluna_ano].astype(str).str.extract('(\d+)')[0]
            df = df[df[coluna_ano] == "2026"]

        # LÓGICA PREMIUM
        usuario = st.session_state.get('usuario_logado', {})
        plano = str(usuario.get('PLANO', 'BRONZE')).upper()
        acesso_nacional = plano in ["PREMIUM", "DIAMANTE", "OURO"]
        
        coluna_uf = next((c for c in ["UF", "ESTADO", "UF_BENEFICIARIO", "SG_UF"] if c in df.columns), None)

        if not acesso_nacional and coluna_uf:
            sigla_user = str(usuario.get('LOCALIDADE') or "SP").strip().upper()
            estado_busca = remover_acentos(MAPA_ESTADOS.get(sigla_user, sigla_user))
            df['UF_CHECK'] = df[coluna_uf].astype(str).apply(remover_acentos)
            df = df[df['UF_CHECK'] == estado_busca]
            st.info(f"📍 Filtro aplicado: {estado_busca}")
        else:
            st.success("🔓 **Acesso Premium:** Visualizando dados nacionais")

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return

    if not df.empty:
        if tipo_visao == "Visão Geral":
            c_emp = next((c for c in df.columns if "EMPENHADO" in c), None)
            c_liq = next((c for c in df.columns if "LIQUIDADO" in c), None)
            c_pag = next((c for c in df.columns if "PAGO" in c), None)

            def conv(c):
                if c and c in df.columns:
                    # Limpeza para padrão brasileiro (ponto no milhar, vírgula no decimal)
                    valores = df[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(valores, errors='coerce').sum()
                return 0.0

            v1, v2, v3 = conv(c_emp), conv(c_liq), conv(c_pag)
            m1, m2, m3 = st.columns(3)
            m1.metric("EMPENHADO", formatar_moeda(v1))
            m2.metric("LIQUIDADO", formatar_moeda(v2))
            m3.metric("PAGO", formatar_moeda(v3))
            st.divider()

        st.write(f"📊 Registros de 2026: **{len(df)}**")
        busca = st.text_input("🔍 Pesquisar:", key="search_radar")
        if busca:
            mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            st.dataframe(df[mask], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado encontrado. Tente atualizar a página.")
