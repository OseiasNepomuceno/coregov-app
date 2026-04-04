import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_final_ajuste")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = f"base_final_{file_id}.csv"

    # Botão de Sincronização Forçada
    if st.button("🔄 Sincronizar Agora"):
        if os.path.exists(nome_arquivo): 
            os.remove(nome_arquivo)
        st.cache_data.clear()
        st.rerun()

    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando base definitiva..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        # Leitura com separador ';' e encoding latin1
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        
        # Limpa nomes das colunas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identifica a coluna de Ano
        col_ano = "Ano da Emenda"
        if col_ano not in df.columns:
            col_ano = next((c for c in df.columns if "Ano" in c), df.columns[1])

        # Limpeza de dados na coluna de ano
        df[col_ano] = df[col_ano].astype(str).str.strip()
        
        # FILTRO DE 2026
        df_exibir = df[df[col_ano] == "2026"].copy()
        
        # CONTINGÊNCIA: Se 2026 estiver vazio, mostra o que tem no arquivo
        mostrar_aviso_antigo = False
        if df_exibir.empty:
            df_exibir = df.copy()
            mostrar_aviso_antigo = True
            
    except Exception as e:
        st.error(f"Erro ao processar: {e}"); return

    # Lógica de Acesso
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    acesso_nacional = plano in ["PREMIUM", "DIAMANTE", "OURO"]

    if not acesso_nacional:
        col_uf = next((c for c in df_exibir.columns if "UF" in c.upper()), None)
        if col_uf:
            sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
            df_exibir = df_exibir[df_exibir[col_uf].astype(str).str.contains(sigla, na=False, case=False)]

    # Exibição dos Alertas
    if mostrar_aviso_antigo:
        st.warning(f"⚠️ Atenção: A base de dados atual contém registros de {df[col_ano].min()} a {df[col_ano].max()}. O ano 2026 não foi localizado.")
    elif acesso_nacional:
        st.success("🔓 **Acesso Premium:** Visualizando base nacional")

    if not df_exibir.empty:
        if tipo_visao == "Visão Geral":
            def calcular(termo):
                c = next((col for col in df_exibir.columns if termo.upper() in col.upper()), None)
                if c:
                    v = df_exibir[c].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v1, v2, v3 = calcular("Empenhado"), calcular("Liquidado"), calcular("Pago")
            m1, m2, m3 = st.columns(3)
            m1.metric("EMPENHADO", formatar_moeda(v1))
            m2.metric("LIQUIDADO", formatar_moeda(v2))
            m3.metric("PAGO", formatar_moeda(v3))
            st.divider()

        st.write(f"📊 Registros exibidos: **{len(df_exibir)}**")
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.error("Nenhum dado encontrado para exibição.")
