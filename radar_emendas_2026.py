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
    st.title("🏛️ Radar de Emendas 2026 - Dashboard")
    
    # Versão v18 para garantir que o Streamlit atualize o componente
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v18")

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
        if col_ano:
            df_2026 = df[df[col_ano].fillna('').astype(str).str.contains("2026")].copy()
        else:
            df_2026 = df.copy()

        # --- PADRONIZAÇÃO DE COLUNAS DE VALOR PARA VISÃO GERAL ---
        # Mapeia nomes possíveis para os nomes que você quer
        mapeamento = {
            "Valor Empenhado": ["Valor Empenhado", "Valor Total Empenhado", "VALOR EMPENHADO"],
            "Valor Liquidado": ["Valor Liquidado", "Valor Total Liquidado", "VALOR LIQUIDADO"],
            "Valor Pago": ["Valor Pago", "Valor Total Pago", "VALOR PAGO"]
        }

        for destino, origens in mapeamento.items():
            for origem in origens:
                if origem in df_2026.columns:
                    df_2026[destino] = df_2026[origem].astype(str).str.replace('R$', '', regex=False).str.strip()
                    df_2026[destino] = df_2026[destino].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_2026[destino] = pd.to_numeric(df_2026[destino], errors='coerce').fillna(0)
                    break

        if tipo_visao == "Visão Geral":
            # Lista exata solicitada
            colunas_selecionadas = [
                "Ano da Emenda", "Localidade de aplicação do recurso", "Município", 
                "UF", "Região", "Nome do Programa", 
                "Valor Empenhado", "Valor Liquidado", "Valor Pago"
            ]
            # Só exibe as colunas que realmente existem ou foram criadas acima
            colunas_finais = [c for c in colunas_selecionadas if c in df_2026.columns]
            df_exibir = df_2026[colunas_finais].copy()
        else:
            # Lógica "Por Favorecido" mantida
            cols_fora = ["Código da Emenda", "Código do Favorecido"]
            df_exibir = df_2026.drop(columns=[c for c in cols_fora if c in df_2026.columns])
            # Garante limpeza do valor para o Favorecido também
            if "Valor Pago" in df_exibir.columns:
                df_exibir["Valor Pago"] = pd.to_numeric(df_exibir["Valor Pago"], errors='coerce').fillna(0)

    except Exception as e:
        st.error(f"Erro ao processar colunas: {e}"); return

    if not df_exibir.empty:
        st.markdown(f"## 📊 {tipo_visao} 2026")
        
        # --- CARDS DO TOPO ---
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Total Empenhado", formatar_moeda(df_exibir["Valor Empenhado"].sum() if "Valor Empenhado" in df_exibir.columns else 0))
            with c2: st.metric("💸 Total Liquidado", formatar_moeda(df_exibir["Valor Liquidado"].sum() if "Valor Liquidado" in df_exibir.columns else 0))
            with c3: st.metric("✅ Total Pago", formatar_moeda(df_exibir["Valor Pago"].sum() if "Valor Pago" in df_exibir.columns else 0))
        else:
            v_pago = df_exibir["Valor Pago"].sum() if "Valor Pago" in df_exibir.columns else 0
            st.metric("💰 TOTAL PAGO ACUMULADO", formatar_moeda(v_pago))
        
        st.divider()

        # --- GRÁFICOS ---
        # 1. Natureza Jurídica (Sempre que disponível)
        if "Natureza Jurídica" in df_2026.columns:
            df_nat = df_2026["Natureza Jurídica"].value_counts().reset_index().head(10)
            fig_nat = px.pie(df_nat, names='Natureza Jurídica', values='count', title="Natureza Jurídica (%)", hole=0.4, height=400)
            fig_nat.update_layout(legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_nat, use_container_width=True)

        # 2. Ranking de Programas (Visão Geral) ou Autores (Favorecido)
        if tipo_visao == "Visão Geral":
            col_rank = "Nome do Programa"
            col_val = "Valor Empenhado"
        else:
            col_rank = next((c for c in df_exibir.columns if "Autor" in c and "Código" not in c), None)
            col_val = "Valor Pago"

        if col_rank and col_val in df_exibir.columns:
            top10 = df_exibir.groupby(col_rank)[col_val].sum().sort_values(ascending=False).head(10).reset_index()
            fig_rank = px.bar(top10, x=col_rank, y=col_val, title=f"Top 10: {col_rank}", height=500, color=col_val, color_continuous_scale='Blues')
            fig_rank.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False, margin=dict(b=150))
            st.plotly_chart(fig_rank, use_container_width=True)

        # Tabela Final
        st.success(f"Tabela filtrada para {tipo_visao}")
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado de 2026 encontrado.")
