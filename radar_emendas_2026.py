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
    
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v13")

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
        
        col_ano = next((c for c in df.columns if "Ano" in c or "ANO" in c), df.columns[1])
        df[col_ano] = df[col_ano].fillna('').astype(str).str.strip()
        df_2026 = df[df[col_ano].str.startswith("2026")].copy()

        possibilidades = ["Valor Recebido", "Valor Pago", "Valor Liquidado", "Valor Empenhado"]
        col_valor = next((c for c in possibilidades if c in df_2026.columns), None)

        if col_valor:
            df_2026[col_valor] = df_2026[col_valor].astype(str).str.replace('R$', '', regex=False).str.strip()
            df_2026[col_valor] = df_2026[col_valor].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_2026[col_valor] = pd.to_numeric(df_2026[col_valor], errors='coerce').fillna(0)
        
        if tipo_visao == "Por Favorecido":
            cols_fora = ["Código da Emenda", "Código do Favorecido"]
            df_exibir = df_2026.drop(columns=[c for c in cols_fora if c in df_2026.columns])
        else:
            df_exibir = df_2026.copy()

    except Exception as e:
        st.error(f"Erro: {e}"); return

    if not df_exibir.empty:
        st.markdown("### 📊 Indicadores Estratégicos 2026")
        
        total_fin = df_exibir[col_valor].sum() if col_valor else 0
        st.metric(f"💰 TOTAL ACUMULADO (2026)", formatar_moeda(total_fin))
        st.divider()

        # 1. GRÁFICO: TOP 10 NATUREZA JURÍDICA
        col_nat = "Natureza Jurídica"
        if col_nat in df_exibir.columns:
            df_nat_counts = df_exibir[col_nat].value_counts().reset_index()
            df_nat_counts.columns = ['Natureza', 'Qtd']
            
            top_10_nat = df_nat_counts.head(10).copy()
            outros_qtd = df_nat_counts.iloc[10:]['Qtd'].sum()
            
            if outros_qtd > 0:
                novo_outro = pd.DataFrame([{'Natureza': 'Outras Naturezas', 'Qtd': outros_qtd}])
                top_10_nat = pd.concat([top_10_nat, novo_outro], ignore_index=True)

            fig_pie = px.pie(top_10_nat, names='Natureza', values='Qtd', 
                             title="Top 10 Naturezas Jurídicas (%)", 
                             hole=0.4, height=500,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            
            fig_pie.update_layout(legend=dict(orientation="h", y=-0.2, xanchor="center", x=0.5))
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # 2. GRÁFICO POR UF (LIMPO - SEM DUPLICIDADE DE ESCALA)
        col_uf = "UF Favorecido"
        if col_uf in df_exibir.columns:
            df_uf = df_exibir[col_uf].value_counts().reset_index().head(15)
            df_uf.columns = ['UF', 'Qtd']
            fig_uf = px.bar(df_uf, x='UF', y='Qtd', title="Volume de Emendas por UF (Top 15)", 
                            color='Qtd', color_continuous_scale='Viridis', height=400)
            
            # Remove a barra lateral repetida para limpar o layout
            fig_uf.update_layout(coloraxis_showscale=False, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_uf, use_container_width=True)

        st.divider()

        # 3. TOP
