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
    # Estilização para as Molduras dos Cards (Premium Look)
    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; }
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px 10px;
            border-radius: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🏛️ Radar de Emendas 2026 - Dashboard")
    
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v20")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = f"base_dados_{file_id}.csv"

    if st.button("🔄 ATUALIZAR E LIMPAR TUDO"):
        for f in os.listdir():
            if f.endswith(".csv"): 
                try: os.remove(f)
                except: pass
        st.cache_data.clear()
        st.rerun()

    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando novos dados..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]
        
        # Filtro de Ano 2026
        col_ano = next((c for c in df.columns if "Ano" in c or "ANO" in c), None)
        df_2026 = df[df[col_ano].fillna('').astype(str).str.contains("2026")].copy() if col_ano else df.copy()

        # Limpeza e Padronização de Valores
        mapeamento = {
            "Valor Empenhado": ["Valor Empenhado", "Valor Total Empenhado", "VALOR EMPENHADO"],
            "Valor Liquidado": ["Valor Liquidado", "Valor Total Liquidado", "VALOR LIQUIDADO"],
            "Valor Pago": ["Valor Pago", "Valor Total Pago", "VALOR PAGO", "Valor Recebido"]
        }

        for destino, origens in mapeamento.items():
            for origem in origens:
                if origem in df_2026.columns:
                    df_2026[destino] = df_2026[origem].astype(str).str.replace('R$', '', regex=False).str.strip()
                    df_2026[destino] = df_2026[destino].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_2026[destino] = pd.to_numeric(df_2026[destino], errors='coerce').fillna(0)
                    break

        if tipo_visao == "Visão Geral":
            colunas_solicitadas = [
                "Ano da Emenda", "Localidade de aplicação do recurso", "Município", 
                "UF", "Região", "Nome do Programa", 
                "Valor Empenhado", "Valor Liquidado", "Valor Pago"
            ]
            colunas_existentes = [c for c in colunas_solicitadas if c in df_2026.columns]
            df_exibir = df_2026[colunas_existentes].copy()
        else:
            cols_fora = ["Código da Emenda", "Código do Favorecido"]
            df_exibir = df_2026.drop(columns=[c for c in cols_fora if c in df_2026.columns])

    except Exception as e:
        st.error(f"Erro no processamento: {e}"); return

    if not df_exibir.empty:
        st.markdown(f"## 📊 {tipo_visao} 2026")
        
        # --- CARDS COM MOLDURA ---
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Total Empenhado", formatar_moeda(df_exibir["Valor Empenhado"].sum() if "Valor Empenhado" in df_exibir.columns else 0))
            with c2: st.metric("💸 Total Liquidado", formatar_moeda(df_exibir["Valor Liquidado"].sum() if "Valor Liquidado" in df_exibir.columns else 0))
            with c3: st.metric("✅ Total Pago", formatar_moeda(df_exibir["Valor Pago"].sum() if "Valor Pago" in df_exibir.columns else 0))
            st.divider()
        else:
            v_pago = df_exibir["Valor Pago"].sum() if "Valor Pago" in df_exibir.columns else 0
            st.metric("💰 TOTAL PAGO ACUMULADO", formatar_moeda(v_pago))
            st.divider()

            # Gráficos específicos apenas para a visão "Por Favorecido"
            col_rank = next((c for c in df_exibir.columns if "Autor" in c and "Código" not in c), None)
            if col_rank and "Valor Pago" in df_exibir.columns:
                top10 = df_exibir.groupby(col_rank)["Valor Pago"].sum().sort_values(ascending=False).head(10).reset_index()
                fig_rank = px.bar(top10, x=col_rank, y="Valor Pago", title="Top 10: Autores", height=500, color="Valor Pago", color_continuous_scale='Blues')
                fig_rank.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False, margin=dict(b=150))
                st.plotly_chart(fig_rank, use_container_width=True)

        # Tabela Final (Comum a ambos, mas com colunas filtradas na Visão Geral)
        st.success(f"Tabela detalhada para {tipo_visao}")
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado de 2026 encontrado.")
