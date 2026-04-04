import streamlit as st
import pandas as pd
import gdown
import os
import re
import plotly.express as px

def formatar_moeda(valor):
    try:
        v = float(valor)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_radar_dashboard_26")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = f"base_{file_id}.csv" if file_id else "base_erro.csv"

    if st.button("🔄 Sincronizar Novos Dados (Limpar Cache)"):
        for f in os.listdir():
            if f.endswith(".csv"): 
                try: os.remove(f)
                except: pass
        st.cache_data.clear()
        st.rerun()

    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("ID não configurado nos Secrets."); return
        with st.spinner(f"Baixando base de {tipo_visao}..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        if len(df.columns) < 5:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip', dtype=str)

        df.columns = [str(c).replace('"', '').strip() for c in df.columns]
        
        # Identifica coluna de tempo
        col_ano = next((c for c in df.columns if "Ano/Mês" in c or "ANO/MÊS" in c), None)
        if not col_ano:
            col_ano = next((c for c in df.columns if "Ano" in c), df.columns[1])

        # Extração do Ano 2026
        df[col_ano] = df[col_ano].fillna('').astype(str).str.strip()
        df['ANO_PROCESSO'] = df[col_ano].str[:4]
        df_2026 = df[df['ANO_PROCESSO'] == "2026"].copy()

        # Conversão de Valores para números (essencial para os gráficos)
        def limpar_valor(col):
            if col in df_2026.columns:
                df_2026[col] = df_2026[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df_2026[col] = pd.to_numeric(df_2026[col], errors='coerce').fillna(0)

        # Colunas de valores financeiros
        limpar_valor("Valor Empenhado")
        limpar_valor("Valor Liquidado")
        limpar_valor("Valor Pago")
        limpar_valor("Valor Recebido") # Caso a coluna de favorecido use esse nome

        # --- RETIRADA DE COLUNAS (Filtro por Favorecido) ---
        if tipo_visao == "Por Favorecido":
            colunas_remover = ["Código da Emenda", "Código do Favorecido"]
            df_exibir = df_2026.drop(columns=[c for c in colunas_remover if c in df_2026.columns])
        else:
            df_exibir = df_2026.copy()
            
    except Exception as e:
        st.error(f"Erro no processamento: {e}"); return

    if not df_exibir.empty:
        # --- TOP DASHBOARD ---
        st.divider()
        col_card, col_pizza = st.columns([1, 1])

        # 1. Card Valor Total Recebido (ou Pago)
        with col_card:
            col_v = "Valor Pago" if "Valor Pago" in df_exibir.columns else "Valor Recebido"
            total_recebido = df_exibir[col_v].sum() if col_v in df_exibir.columns else 0
            st.metric("💰 TOTAL RECEBIDO (2026)", formatar_moeda(total_recebido))
            
            # 2. Gráfico de Emendas por UF
            col_uf = next((c for c in df_exibir.columns if "UF" in c.upper()), None)
            if col_uf:
                df_uf = df_exibir[col_uf].value_counts().reset_index()
                df_uf.columns = ['UF', 'Quantidade']
                fig_uf = px.bar(df_uf, x='UF', y='Quantidade', title="Qtd de Emendas por UF", color_discrete_sequence=['#004a8d'])
                st.plotly_chart(fig_uf, use_container_width=True)

        # 3. Gráfico de Pizza (Natureza Jurídica)
        with col_pizza:
            col_nat = next((c for c in df_exibir.columns if "Natureza Jurídica" in c or "NATUREZA" in c.upper()), None)
            if col_nat:
                fig_pie = px.pie(df_exibir, names=col_nat, title="Natureza Jurídica (%)", hole=0.4)
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()

        # 4. Gráfico de Barras: Top 10 Autores (Quantidade e Valores)
        col_autor = next((c for c in df_exibir.columns if "Autor" in c), None)
        if col_autor:
            # Agrupa por Autor somando valores e contando ocorrências
            top_autores = df_exibir.groupby(col_autor).agg({col_v: 'sum', col_ano: 'count'}).rename(columns={col_ano: 'Qtd'}).sort_values(by=col_v, ascending=False).head(10).reset_index()
            
            fig_autores = px.bar(top_autores, x=col_autor, y=col_v, 
                                 text='Qtd', title="Top 10 Autores: Valor Total vs Quantidade",
                                 labels={col_v: 'Valor Total', 'Qtd': 'Nº Emendas'},
                                 color_discrete_sequence=['#2ecc71'])
            st.plotly_chart(fig_autores, use_container_width=True)

        # --- TABELA FINAL ---
        st.success(f"✅ Exibindo {len(df_exibir)} registros filtrados de 2026.")
        busca = st.text_input("🔍 Pesquisar na tabela:")
        if busca:
            mask = df_exibir.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            st.dataframe(df_exibir[mask], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado encontrado para gerar o Dashboard.")
