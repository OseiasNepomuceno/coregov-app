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
            st.error("ID do arquivo não encontrado nos Secrets.")
            return
        with st.spinner("Baixando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False, fuzzy=True)

    try:
        # Lendo com separador ';' e forçando leitura de colunas como texto para evitar erros científicos
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # --- FILTRO DE ANO RESILIENTE ---
        coluna_ano = next((c for c in df.columns if "ANO" in c), None)
        
        if coluna_ano:
            # Mantém apenas as linhas onde '2026' aparece em qualquer lugar da célula
            df = df[df[coluna_ano].str.contains("2026", na=False)]
            
    except Exception as e:
        st.error(f"Erro na leitura: {e}")
        return

    # LÓGICA DE PERMISSÃO (PREMIUM)
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    acesso_nacional = plano in ["PREMIUM", "DIAMANTE", "OURO"]

    if acesso_nacional:
        st.success("🔓 **Acesso Premium:** Visualizando dados nacionais de 2026")
    else:
        coluna_uf = next((c for c in ["UF", "ESTADO", "SG_UF"] if c in df.columns), None)
        if coluna_uf:
            sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
            estado = remover_acentos(MAPA_ESTADOS.get(sigla, sigla))
            df = df[df[coluna_uf].astype(str).apply(remover_acentos) == estado]
            st.info(f"📍 Exibindo: {estado}")

    if not df.empty:
        # Cards Financeiros
        if tipo_visao == "Visão Geral":
            def soma_valor(termo):
                col = next((c for c in df.columns if termo in c), None)
                if col:
                    # Limpa R$, pontos e converte vírgula em ponto para somar
                    v = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v_emp = soma_valor("EMPENHADO")
            v_liq = soma_valor("LIQUIDADO")
            v_pag = soma_valor("PAGO")

            c1, c2, c3 = st.columns(3)
            c1.metric("EMPENHADO", formatar_moeda(v_emp))
            c2.metric("LIQUIDADO", formatar_moeda(v_liq))
            c3.metric("PAGO", formatar_moeda(v_pag))
            st.divider()

        st.write(f"📊 Foram encontrados **{len(df)}** registros para 2026.")
        
        busca = st.text_input("🔍 Filtrar na tabela:", key="busca_final")
        if busca:
            mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            st.dataframe(df[mask], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ O filtro foi aplicado, mas a planilha não retornou dados para 2026.")
        # Debug para você ver o que o código está lendo (apenas para teste)
        if coluna_ano:
             st.write("Anos encontrados na planilha (Top 5):", df[coluna_ano].unique()[:5] if not df.empty else "Nenhum")
