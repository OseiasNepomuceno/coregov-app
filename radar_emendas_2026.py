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
    plano_usuario = st.session_state.get("plano", "Básico")  
    uf_liberada = st.session_state.get("uf_liberada", "RJ").strip().upper()

    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v26")

    # IDs do Secrets
    key_id = "id_emendas_geral" if tipo_visao == "Visão Geral" else "id_emendas_favorecido"
    file_id = st.secrets.get(key_id)
    nome_arquivo = f"base_{key_id}.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando dados..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=True)

    try:
        # Carregando com os nomes de colunas confirmados
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]

        # 1. FILTRO DE UF (Coluna exata: "UF")
        if "UF" in df.columns and uf_liberada != "BRASIL":
            df["UF"] = df["UF"].fillna('').str.strip().str.upper()
            df = df[df["UF"] == uf_liberada].copy()
            status_msg = f"📍 Filtro Ativo: {uf_liberada}"
        else:
            status_msg = "🌍 Visão Brasil Liberada"

        # 2. FILTRO DE ANO (Coluna exata: "Ano da Emenda")
        if "Ano da Emenda" in df.columns:
            df = df[df["Ano da Emenda"].fillna('').astype(str).str.contains("2026")].copy()

        # 3. TRATAMENTO FINANCEIRO
        for col in ["Valor Empenhado", "Valor Liquidado", "Valor Pago"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 4. SELEÇÃO DE COLUNAS INTERESSANTES (Conforme sua lista)
        colunas_interessantes = [
            "Ano da Emenda", "Tipo de Emenda", "Nome do Autor da Emenda", 
            "Localidade de aplicação do recurso", "Município", "UF", "Região", 
            "Nome Função", "Nome Subfunção", "Nome Programa", "Nome Ação", 
            "Valor Empenhado", "Valor Liquidado", "Valor Pago"
        ]
        
        # Filtra apenas as colunas que realmente existem no arquivo atual
        df_exibir = df[[c for c in colunas_interessantes if c in df.columns]].copy()

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return

    if not df_exibir.empty:
        st.info(status_msg)
        
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Empenhado", formatar_moeda(df_exibir["Valor Empenhado"].sum()))
            with c2: st.metric("💸 Liquidado", formatar_moeda(df_exibir["Valor Liquidado"].sum()))
            with c3: st.metric("✅ Pago", formatar_moeda(df_exibir["Valor Pago"].sum()))
            
            # Gráfico de Região para Visão Brasil
            if uf_liberada == "BRASIL" and "Região" in df_exibir.columns:
                st.divider()
                df_reg = df_exibir[~df_exibir["Região"].isin(["Nacional", "Múltiplo", "Exterior"])]
                fig_reg = px.bar(df_reg.groupby("Região")["Valor Empenhado"].sum().reset_index(), x="Região", y="Valor Empenhado", title="Empenho por Região", color_discrete_sequence=['#007bff'])
                st.plotly_chart(fig_reg, use_container_width=True)
        
        else:
            # --- VISÃO POR FAVORECIDO / AUTOR ---
            st.divider()
            cl, cr = st.columns(2)
            
            with cl:
                # Top 10 Autores pelo NOME (conforme solicitado)
                col_autor = "Nome do Autor da Emenda"
                if col_autor in df_exibir.columns:
                    df_aut = df_exibir.groupby(col_autor)["Valor Pago"].sum().sort_values(ascending=False).head(10).reset_index()
                    fig1 = px.bar(df_aut, x=col_autor, y="Valor Pago", title="Top 10 Autores (Valor Pago)", color="Valor Pago", color_continuous_scale="Blues")
                    fig1.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
                    st.plotly_chart(fig1, use_container_width=True)

            with cr:
                # Natureza Jurídica (Se disponível no arquivo de favorecidos) ou Função
                col_grafico_2 = "Nome Função" # Usando Função como alternativa se Natureza não estiver na lista interessantes
                if col_grafico_2 in df_exibir.columns:
                    df_fun = df_exibir.groupby(col_grafico_2)["Valor Pago"].sum().sort_values(ascending=False).reset_index()
                    # Agrupamento Outros
                    if len(df_fun) > 8:
                        top = df_fun.head(8).copy()
                        outros = pd.DataFrame({col_grafico_2: ["Outros"], "Valor Pago": [df_fun.iloc[8:]["Valor Pago"].sum()]})
                        df_fun = pd.concat([top, outros], ignore_index=True)
                    
                    fig2 = px.pie(df_fun, names=col_grafico_2, values="Valor Pago", title="Distribuição por Função (%)", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        # Exibe a tabela apenas com as colunas interessantes
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Sem dados de 2026 para {uf_liberada}. Verifique se o arquivo contém registros para este ano/estado.")
