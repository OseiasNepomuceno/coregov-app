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
    uf_sessao = st.session_state.get("uf_liberada", "RJ").strip().upper()
    mapeamento_uf = {"RJ": "RIO DE JANEIRO", "SP": "SAO PAULO", "MG": "MINAS GERAIS"}
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
        # Carregamento
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]

        # --- NOMES EXATOS DAS COLUNAS (CONFORME SUA MENSAGEM) ---
        col_pago = "Valor Pago"
        col_empenhado = "Valor Empenhado"
        col_liquidado = "Valor Liquidado"
        col_autor = "Nome do Autor da Emenda"
        col_local = "Localidade de aplicação do recurso"
        col_ano = "Ano da Emenda"
        col_programa = "Nome Programa"
        
        # 1. FILTRO DE UF
        if "UF" in df.columns and uf_sessao != "BRASIL":
            df["UF"] = df["UF"].fillna('').str.strip().str.upper()
            df = df[(df["UF"] == uf_sessao) | (df["UF"] == uf_busca)].copy()

        # 2. FILTRO DE ANO
        if col_ano in df.columns:
            df = df[df[col_ano].astype(str).str.contains("2026")].copy()

        # 3. CONVERSÃO FINANCEIRA
        for col in [col_pago, col_empenhado, col_liquidado]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 4. SELEÇÃO DE COLUNAS (Garantindo que todas as necessárias para os gráficos estejam aqui)
        colunas_necessarias = [col_ano, col_autor, col_local, "UF", col_programa, col_empenhado, col_liquidado, col_pago]
        # Filtra apenas as que existem no arquivo para não dar erro de coluna inexistente
        df_exibir = df[[c for c in colunas_necessarias if c in df.columns]].copy()

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return

    if not df_exibir.empty:
        st.success(f"✅ Dados carregados para: {uf_busca}")
        
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Empenhado", formatar_moeda(df_exibir[col_empenhado].sum() if col_empenhado in df_exibir.columns else 0))
            with c2: st.metric("💸 Liquidado", formatar_moeda(df_exibir[col_liquidado].sum() if col_liquidado in df_exibir.columns else 0))
            with c3: st.metric("✅ Pago", formatar_moeda(df_exibir[col_pago].sum() if col_pago in df_exibir.columns else 0))
            
            st.divider()
            if col_local in df_exibir.columns and col_pago in df_exibir.columns:
                df_loc = df_exibir.groupby(col_local)[col_pago].sum().sort_values(ascending=False).head(10).reset_index()
                fig_loc = px.bar(df_loc, x=col_local, y=col_pago, title="Top 10 Localidades (Valor Pago)", color_discrete_sequence=['#2ecc71'])
                st.plotly_chart(fig_loc, use_container_width=True)
        
        else:
            # --- VISÃO POR FAVORECIDO (GRÁFICOS) ---
            st.divider()
            cl, cr = st.columns(2)
            with cl:
                if col_autor in df_exibir.columns and col_pago in df_exibir.columns:
                    df_aut = df_exibir.groupby(col_autor)[col_pago].sum().sort_values(ascending=False).head(10).reset_index()
                    fig1 = px.bar(df_aut, x=col_autor, y=col_pago, title="Top 10 Autores", color=col_pago, color_continuous_scale="Viridis")
                    fig1.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.warning("Dados insuficientes para gerar o gráfico de Autores.")

            with cr:
                if col_programa in df_exibir.columns and col_pago in df_exibir.columns:
                    df_p = df_exibir.groupby(col_programa)[col_pago].sum().sort_values(ascending=False).head(8).reset_index()
                    fig2 = px.pie(df_p, names=col_programa, values=col_pago, title="Distribuição por Programa", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning("Dados insuficientes para gerar o gráfico de Programas.")

        st.divider()
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Não encontramos registros para '{uf_busca}' em 2026.")
