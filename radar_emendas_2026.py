import streamlit as st
import pandas as pd
import gdown
import os
import re
import plotly.express as px

def formatar_moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026 - Dashboard")
    
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v17")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = f"base_dados_{file_id}.csv"

    if st.button("🔄 ATUALIZAR DASHBOARD (Limpar Cache)"):
        for f in os.listdir():
            if f.endswith(".csv"): 
                try: os.remove(f)
                except: pass
        st.cache_data.clear()
        st.rerun()

    if not os.path.exists(nome_arquivo):
        with st.spinner("Buscando dados atualizados..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        if len(df.columns) < 5:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip', dtype=str)

        df.columns = [str(c).replace('"', '').strip() for c in df.columns]
        
        # Filtro de Ano 2026
        col_ano = next((c for c in df.columns if "Ano" in c or "ANO" in c), df.columns[1])
        df[col_ano] = df[col_ano].fillna('').astype(str).str.strip()
        df_2026 = df[df[col_ano].str.startswith("2026")].copy()

        # Função interna para limpar valores financeiros
        def limpar_valor(col):
            if col in df_2026.columns:
                df_2026[col] = df_2026[col].astype(str).str.replace('R$', '', regex=False).str.strip()
                df_2026[col] = df_2026[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df_2026[col] = pd.to_numeric(df_2026[col], errors='coerce').fillna(0)

        # Colunas de valores para a Visão Geral
        cols_financeiras = ["Valor Empenhado", "Valor Liquidado", "Valor Pago"]
        for c in cols_financeiras:
            limpar_valor(c)

        # --- LÓGICA ESPECÍFICA DE COLUNAS ---
        if tipo_visao == "Visão Geral":
            colunas_permitidas = [
                "Ano da Emenda", "Localidade de aplicação do recurso", "Município", 
                "UF", "Região", "Nome do Programa", 
                "Valor Empenhado", "Valor Liquidado", "Valor Pago"
            ]
            # Filtra apenas as colunas que existem no arquivo
            df_exibir = df_2026[[c for c in colunas_permitidas if c in df_2026.columns]].copy()
            col_referencia_grafico = "Valor Empenhado" # Usado para os rankings nesta visão
        else:
            # Mantém a lógica do "Por Favorecido" intacta
            cols_fora = ["Código da Emenda", "Código do Favorecido"]
            df_exibir = df_2026.drop(columns=[c for c in cols_fora if c in df_2026.columns])
            col_referencia_grafico = next((c for c in ["Valor Recebido", "Valor Pago"] if c in df_exibir.columns), "Valor Pago")

    except Exception as e:
        st.error(f"Erro no processamento: {e}"); return

    if not df_exibir.empty:
        st.markdown(f"### 📊 Indicadores Estratégicos 2026 ({tipo_visao})")
        
        # --- CARDS DO TOPO (VISÃO GERAL) ---
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Total Empenhado", formatar_moeda(df_exibir["Valor Empenhado"].sum() if "Valor Empenhado" in df_exibir.columns else 0))
            with c2: st.metric("💸 Total Liquidado", formatar_moeda(df_exibir["Valor Liquidado"].sum() if "Valor Liquidado" in df_exibir.columns else 0))
            with c3: st.metric("✅ Total Pago", formatar_moeda(df_exibir["Valor Pago"].sum() if "Valor Pago" in df_exibir.columns else 0))
        else:
            total_fin = df_exibir[col_referencia_grafico].sum() if col_referencia_grafico in df_exibir.columns else 0
            st.metric(f"💰 TOTAL ACUMULADO (2026)", formatar_moeda(total_fin))
        
        st.divider()

        # 1. GRÁFICO: NATUREZA JURÍDICA (Se existir na Visão Geral ou Favorecido)
        col_nat = "Natureza Jurídica"
        if col_nat in df_2026.columns: # Buscamos no DF original pois a Visão Geral pode ter filtrado essa coluna da tabela
            df_nat_counts = df_2026[col_nat].value_counts().reset_index().head(10)
            df_nat_counts.columns = ['Natureza', 'Qtd']
            fig_pie = px.pie(df_nat_counts, names='Natureza', values='Qtd', title="Natureza Jurídica (%)", hole=0.4, height=450)
            fig_pie.update_layout(legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_pie, use_container_width=True)
            st.divider()

        # 2. GRÁFICO POR UF
        col_uf = "UF" if tipo_visao == "Visão Geral" else "UF Favorecido"
        if col_uf in df_exibir.columns:
            df_uf = df_exibir[col_uf].value_counts().reset_index().head(15)
            df_uf.columns = ['UF', 'Qtd']
            fig_uf = px.bar(df_uf, x='UF', y='Qtd', title=f"Volume de Emendas por {col_uf}", 
                            color='Qtd', color_continuous_scale='Viridis', height=400)
            fig_uf.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_uf, use_container_width=True)
            st.divider()

        # 3. RANKING (Top 10 Programa ou Autor)
        col_rank = "Nome do Programa" if tipo_visao == "Visão Geral" else next((c for c in df_exibir.columns if "Autor" in c and "Código" not in c), None)
        
        if col_rank and col_referencia_grafico in df_exibir.columns:
            top10 = df_exibir.groupby(col_rank)[col_referencia_grafico].sum().sort_values(ascending=False).head(10).reset_index()
            fig_rank = px.bar(top10, x=col_rank, y=col_referencia_grafico, title=f"Top 10: {col_rank}",
                             height=500, color=col_referencia_grafico, color_continuous_scale='Blues')
            fig_rank.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False, margin=dict(b=150))
            st.plotly_chart(fig_rank, use_container_width=True)

        st.success(f"✅ Dados de 2026 carregados com sucesso.")
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado encontrado para os critérios selecionados.")
