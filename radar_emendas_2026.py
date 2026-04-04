import streamlit as st
import pandas as pd
import gdown
import os
import re

def formatar_moeda(valor):
    try:
        v = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_radar_final_26")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    
    # Criamos o nome do arquivo baseado no ID para garantir que ele baixe o novo
    nome_arquivo = f"base_{file_id}.csv" if file_id else "base_erro.csv"

    if st.button("🔄 Sincronizar Novos Dados (Limpar Cache)"):
        for f in os.listdir():
            if f.endswith(".csv"): os.remove(f)
        st.cache_data.clear()
        st.rerun()

    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("ID não configurado nos Secrets."); return
        with st.spinner("Baixando nova base do Drive..."):
            # Remove arquivos antigos antes de baixar o novo
            for f in os.listdir():
                if f.startswith("base_") and f.endswith(".csv"): os.remove(f)
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        # Leitura
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        if len(df.columns) < 5:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip', dtype=str)

        df.columns = [c.replace('"', '').strip() for c in df.columns]
        col_ano = next((c for c in df.columns if "Ano" in c), df.columns[1])

        # Limpeza e Filtro
        df[col_ano] = df[col_ano].astype(str).apply(lambda x: re.sub(r'\D', '', x))
        df_2026 = df[df[col_ano] == "2026"].copy()
            
    except Exception as e:
        st.error(f"Erro: {e}"); return

    # Lógica de Exibição
    if not df_2026.empty:
        st.success(f"✅ Sucesso! {len(df_2026)} registros de 2026 carregados.")
        st.dataframe(df_2026, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ O arquivo baixado (ID: {file_id}) ainda não contém 2026.")
        st.write("Anos encontrados nesta versão:", df[col_ano].unique())
