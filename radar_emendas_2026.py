import streamlit as st
import pandas as pd
import gdown
import os
import plotly.express as px

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    # --- CONFIGURAÇÃO DE ACESSO ---
    # Ajuste para aceitar "RIO DE JANEIRO" ou "RJ"
    uf_sessao = st.session_state.get("uf_liberada", "RJ").strip().upper()
    mapeamento_uf = {"RJ": "RIO DE JANEIRO", "SP": "SAO PAULO", "MG": "MINAS GERAIS"} # Expanda se necessário
    uf_busca = mapeamento_uf.get(uf_sessao, uf_sessao)

    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v26")

    key_id = "id_emendas_geral" if tipo_visao == "Visão Geral" else "id_emendas_favorecido"
    file_id = st.secrets.get(key_id)
    nome_arquivo = f"base_{key_id}.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando dados..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=True)

    try:
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]

        # 1. FILTRO DE UF (Busca por "RIO DE JANEIRO")
        if "UF" in df.columns and uf_sessao != "BRASIL":
            df["UF"] = df["UF"].fillna('').str.strip().str.upper()
            # Filtra tanto pela sigla quanto pelo nome extenso
            df = df[(df["UF"] == uf_sessao) | (df["UF"] == uf_busca)].copy()

        # 2. FILTRO DE ANO (Ano da Emenda == 2026)
        if "Ano da Emenda" in df.columns:
            df = df[df["Ano da Emenda"].astype(str).str.contains("2026")].copy()

        # 3. TRATAMENTO FINANCEIRO
        for col in ["Valor Empenhado", "Valor Liquidado", "Valor Pago"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 4. COLUNAS INTERESSANTES (Trocando Município por Localidade)
        colunas_exibir = [
            "Ano da Emenda", "Tipo de Emenda", "Nome do Autor da Emenda", 
            "Localidade de aplicação do recurso", "UF", "Região", 
            "Nome Programa", "Valor Empenhado", "Valor Liquidado", "Valor Pago"
        ]
        df_exibir = df[[c for c in colunas_exibir if c in df.columns]].copy()

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return

    if not df_exibir.empty:
        st.success(f"✅ Dados carregados para: {uf_busca}")
        
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Empenhado", formatar_moeda(df_exibir["Valor Empenhado"].sum()))
            with c2: st.metric("💸 Liquidado", formatar_moeda(df_exibir["Valor Liquidado"].sum()))
            with c3: st.metric("✅ Pago", formatar_moeda(df_exibir["Valor Pago"].sum()))
            
            # Gráfico por Localidade (Top 10 Cidades/Locais)
            st.divider()
            col_loc = "Localidade de aplicação do recurso"
            if col_loc in df_exibir.columns:
                df_loc = df_exibir.groupby(col_loc)["Valor Pago"].sum().sort_values(ascending=False).head(10).reset_index()
                fig_loc = px.bar(df_loc, x=col_loc, y="Valor Pago", title="Top 10 Localidades (Valor Pago)", color_discrete_sequence=['#2ecc71'])
                st.plotly_chart(fig_loc, use_container_width=True)
        
        else:
            # --- VISÃO POR FAVORECIDO ---
            st.divider()
            cl, cr = st.columns(2)
            with cl:
                col_aut = "Nome do Autor da Emenda"
                if col_aut in df_exibir.columns:
                    df_aut = df_exibir.groupby(col_aut)["Valor Pago"].sum().sort_values(ascending=False).head(10).reset_index()
                    fig1 = px.bar(df_aut, x=col_aut, y="Valor Pago", title="Top 10 Autores", color="Valor Pago", color_continuous_scale="Viridis")
                    st.plotly_chart(fig1, use_container_width=True)
            with cr:
                col_prog = "Nome Programa"
                if col_prog in df_exibir.columns:
                    df_p = df_exibir.groupby(col_prog)["Valor Pago"].sum().sort_values(ascending=False).head(8).reset_index()
                    fig2 = px.pie(df_p, names=col_prog, values="Valor Pago", title="Distribuição por Programa", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Não encontramos registros para '{uf_busca}' em 2026. Verifique os filtros.")
