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
    # Mapeamento para garantir que "RJ" encontre "RIO DE JANEIRO"
    mapeamento_uf = {"RJ": "RIO DE JANEIRO", "SP": "SAO PAULO", "MG": "MINAS GERAIS"}
    uf_busca = mapeamento_uf.get(uf_sessao, uf_sessao)

    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v26")

    key_id = "id_emendas_geral" if tipo_visao == "Visão Geral" else "id_emendas_favorecido"
    file_id = st.secrets.get(key_id)
    nome_arquivo = f"base_{key_id}.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=True)

    try:
        # Carregamento do CSV
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]

        # --- DEFINIÇÃO DAS COLUNAS (NOMES EXATOS DA PLANILHA) ---
        col_uf_fav = "UF Favorecido"
        col_mun_fav = "Munícipio Favorecido"
        col_valor_rec = "Valor Recebido"
        col_autor = "Nome do Autor da Emenda"
        col_nat = "Natureza Jurídica"
        col_ano_mes = "Ano/Mês"

        if tipo_visao == "Visão Geral":
            # Lógica para Visão Geral (Usa as colunas UF e Município padrão)
            c_uf_geral = "UF"
            if c_uf_geral in df.columns and uf_sessao != "BRASIL":
                df = df[(df[c_uf_geral].str.upper() == uf_sessao) | (df[c_uf_geral].str.upper() == uf_busca)].copy()
            
            for c in ["Valor Empenhado", "Valor Liquidado", "Valor Pago"]:
                if c in df.columns:
                    df[c] = df[c].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            df_exibir = df.copy()

        else:
            # --- LÓGICA POR FAVORECIDO (COLUNAS ESPECÍFICAS) ---
            
            # 1. Filtro de UF (Uf Favorecido)
            if col_uf_fav in df.columns and uf_sessao != "BRASIL":
                df[col_uf_fav] = df[col_uf_fav].fillna('').str.strip().str.upper()
                # Filtra por RJ ou RIO DE JANEIRO
                df = df[(df[col_uf_fav] == uf_sessao) | (df[col_uf_fav] == uf_busca)].copy()

            # 2. Conversão Financeira (Valor Recebido)
            if col_valor_rec in df.columns:
                df[col_valor_rec] = df[col_valor_rec].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                df[col_valor_rec] = pd.to_numeric(df[col_valor_rec], errors='coerce').fillna(0)

            # 3. Filtro de Ano (Opcional, se quiser travar em 2026 no Ano/Mês)
            if col_ano_mes in df.columns:
                df = df[df[col_ano_mes].astype(str).str.contains("2026", na=False)].copy()

            # 4. Seleção das colunas interessantes que você pediu
            cols_fav = [
                col_autor, "Tipo de Emenda", col_ano_mes, "Favorecido", 
                col_nat, "Tipo Favorecido", col_uf_fav, col_mun_fav, col_valor_rec
            ]
            df_exibir = df[[c for c in cols_fav if c in df.columns]].copy()

    except Exception as e:
        st.error(f"Erro no processamento das colunas: {e}")
        return

    if not df_exibir.empty:
        st.success(f"✅ Exibindo dados de: {uf_busca}")
        
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Empenhado", formatar_moeda(df_exibir["Valor Empenhado"].sum() if "Valor Empenhado" in df_exibir.columns else 0))
            with c2: st.metric("💸 Liquidado", formatar_moeda(df_exibir["Valor Liquidado"].sum() if "Valor Liquidado" in df_exibir.columns else 0))
            with c3: st.metric("✅ Pago", formatar_moeda(df_exibir["Valor Pago"].sum() if "Valor Pago" in df_exibir.columns else 0))
        else:
            # --- GRÁFICOS DA VISÃO POR FAVORECIDO ---
            st.divider()
            cl, cr = st.columns(2)
            with cl:
                if col_autor in df_exibir.columns and col_valor_rec in df_exibir.columns:
                    df_aut = df_exibir.groupby(col_autor)[col_valor_rec].sum().sort_values(ascending=False).head(10).reset_index()
                    fig1 = px.bar(df_aut, x=col_autor, y=col_valor_rec, title="Top 10 Autores (Valor Recebido)", color=col_valor_rec, color_continuous_scale="Blues")
                    fig1.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
                    st.plotly_chart(fig1, use_container_width=True)
            with cr:
                if col_nat in df_exibir.columns and col_valor_rec in df_exibir.columns:
                    df_nat_graf = df_exibir.groupby(col_nat)[col_valor_rec].sum().sort_values(ascending=False).reset_index()
                    if len(df_nat_graf) > 8:
                        top = df_nat_graf.head(8).copy()
                        outros = pd.DataFrame({col_nat: ["Outros"], col_valor_rec: [df_nat_graf.iloc[8:][col_valor_rec].sum()]})
                        df_nat_graf = pd.concat([top, outros], ignore_index=True)
                    fig2 = px.pie(df_nat_graf, names=col_nat, values=col_valor_rec, title="Natureza Jurídica (%)", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Não foram encontrados dados de 2026 para {uf_busca} neste arquivo.")
