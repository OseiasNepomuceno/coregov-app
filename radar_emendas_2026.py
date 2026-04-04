import streamlit as st
import pandas as pd
import gdown
import os
import re

def formatar_moeda(valor):
    try:
        # Limpeza para converter padrão brasileiro (1.234,56) em float
        v = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_radar_final_26")

    # Busca o ID correto nos Secrets baseado na escolha do menu
    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    
    # Nome do arquivo vinculado ao ID para evitar conflito de cache
    nome_arquivo = f"base_{file_id}.csv" if file_id else "base_erro.csv"

    # Botão para forçar atualização manual
    if st.button("🔄 Sincronizar Novos Dados (Limpar Cache)"):
        for f in os.listdir():
            if f.endswith(".csv"): 
                try: os.remove(f)
                except: pass
        st.cache_data.clear()
        st.rerun()

    # Verifica se o arquivo existe localmente no servidor, se não, baixa do Drive
    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("ID não configurado nos Secrets."); return
        with st.spinner(f"Baixando base de {tipo_visao}..."):
            # Limpa qualquer resquício de arquivos base_ antes de baixar o novo
            for f in os.listdir():
                if f.startswith("base_") and f.endswith(".csv"): 
                    try: os.remove(f)
                    except: pass
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        # Leitura robusta forçando dtypes iniciais como string
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        if len(df.columns) < 5:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip', dtype=str)

        # 1. Limpeza de Cabeçalhos
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]
        
        # 2. Identificação da coluna de Ano
        col_ano = "Ano da Emenda"
        if col_ano not in df.columns:
            col_ano = next((c for c in df.columns if "Ano" in c), df.columns[1])

        # 3. AJUSTE DE SEGURANÇA (Resolve o erro: expected string, got float)
        # fillna('') transforma células vazias em texto, evitando o erro no re.sub
        df[col_ano] = df[col_ano].fillna('').astype(str).apply(lambda x: re.sub(r'\D', '', x))
        
        # 4. Filtro de 2026
        df_2026 = df[df[col_ano] == "2026"].copy()
            
    except Exception as e:
        st.error(f"Erro no processamento dos dados: {e}"); return

    # --- EXIBIÇÃO DOS RESULTADOS ---
    if not df_2026.empty:
        # Se estiver na Visão Geral, mostra os cards de resumo financeiro
        if tipo_visao == "Visão Geral":
            def soma_col(termo):
                c = next((col for col in df_2026.columns if termo.upper() in col.upper()), None)
                if c:
                    v = df_2026[c].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v1, v2, v3 = soma_col("Empenhado"), soma_col("Liquidado"), soma_col("Pago")
            m1, m2, m3 = st.columns(3)
            m1.metric("EMPENHADO", formatar_moeda(v1))
            m2.metric("LIQUIDADO", formatar_moeda(v2))
            m3.metric("PAGO", formatar_moeda(v3))
            st.divider()

        st.success(f"✅ Sucesso! {len(df_2026)} registros de 2026 carregados ({tipo_visao}).")
        
        # Barra de pesquisa para facilitar a navegação
        busca = st.text_input(f"🔍 Pesquisar em {tipo_visao}:")
        if busca:
            mask = df_2026.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            st.dataframe(df_2026[mask], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_2026, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ Nenhum registro de 2026 encontrado nesta base.")
        if not df.empty:
            st.write("Anos detectados no arquivo:", df[col_ano].unique())
