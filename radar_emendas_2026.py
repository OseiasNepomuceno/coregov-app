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
    # --- REGRA DE NEGÓCIO: ID_LICENÇAS ---
    # Aqui simulamos a captura dos dados da licença do usuário logado
    plano_usuario = st.session_state.get("plano", "Básico")  # Básico ou Premium
    uf_liberada = st.session_state.get("uf_liberada", "RJ")  # Sigla do Estado ou "Brasil"

    # Estilização dos Cards
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

    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v26")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = f"base_dados_{file_id}.csv"

    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando dados da licença..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]
        
        # --- APLICAÇÃO DA TRAVA DE UF (Lógica de Licenciamento) ---
        col_uf_dados = next((c for c in df.columns if "UF" in c), None)
        
        if uf_liberada != "Brasil" and col_uf_dados:
            # Cliente Básico: Filtra apenas o estado escolhido
            df = df[df[col_uf_dados] == uf_liberada].copy()
            status_msg = f"📍 Licença Ativa: {uf_liberada} ({plano_usuario})"
        else:
            # Cliente Premium (Brasil): Não filtra UF
            status_msg = f"🌍 Licença Premium: Visão Brasil Liberada"

        # Filtro de Ano 2026
        col_ano = next((c for c in df.columns if "Ano" in c or "ANO" in c), None)
        df_2026 = df[df[col_ano].fillna('').astype(str).str.contains("2026")].copy() if col_ano else df.copy()

        # Limpeza de Valores Financeiros
        mapeamento = {
            "Valor Empenhado": ["Valor Empenhado", "Valor Total Empenhado"],
            "Valor Liquidado": ["Valor Liquidado", "Valor Total Liquidado"],
            "Valor Pago": ["Valor Pago", "Valor Total Pago", "Valor Recebido", "VALOR RECEBIDO"]
        }

        for destino, origens in mapeamento.items():
            for origem in origens:
                if origem in df_2026.columns:
                    df_2026[destino] = df_2026[origem].astype(str).str.replace('R$', '', regex=False).str.strip()
                    df_2026[destino] = df_2026[destino].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    df_2026[destino] = pd.to_numeric(df_2026[destino], errors='coerce').fillna(0)
                    break

        # Filtro de Colunas por Visão
        if tipo_visao == "Visão Geral":
            cols = ["Ano da Emenda", "Localidade de aplicação do recurso", "Município", "UF", "Região", "Nome do Programa", "Valor Empenhado", "Valor Liquidado", "Valor Pago"]
            df_exibir = df_2026[[c for c in cols if c in df_2026.columns]].copy()
        else:
            cols_fora = ["Código da Emenda", "Código do Favorecido"]
            df_exibir = df_2026.drop(columns=[c for c in cols_fora if c in df_2026.columns]).copy()

    except Exception as e:
        st.error(f"Erro ao validar licença: {e}"); return

    if not df_exibir.empty:
        st.info(status_msg)
        
        # --- CARDS ---
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Total Empenhado", formatar_moeda(df_exibir["Valor Empenhado"].sum() if "Valor Empenhado" in df_exibir.columns else 0))
            with c2: st.metric("💸 Total Liquidado", formatar_moeda(df_exibir["Valor Liquidado"].sum() if "Valor Liquidado" in df_exibir.columns else 0))
            with c3: st.metric("✅ Total Pago", formatar_moeda(df_exibir["Valor Pago"].sum() if "Valor Pago" in df_exibir.columns else 0))
            
            # Gráfico de Região (Só para visão Nacional/Brasil)
            if uf_liberada == "Brasil" and "Região" in df_exibir.columns:
                st.divider()
                df_reg = df_exibir[~df_exibir["Região"].isin(["Nacional", "Múltiplo", "Exterior"])]
                fig = px.bar(df_reg.groupby("Região")["Valor Empenhado"].sum().reset_index(), x="Região", y="Valor Empenhado", title="Distribuição por Região", color_discrete_sequence=['#31333F'])
                st.plotly_chart(fig, use_container_width=True)
        else:
            # --- VISÃO POR FAVORECIDO (GRÁFICOS RJ/ESTADUAIS) ---
            st.divider()
            cl, cr = st.columns(2)
            with cl:
                c_aut = next((c for c in df_exibir.columns if "Autor" in c), None)
                if c_aut:
                    df_aut = df_exibir.groupby(c_aut)["Valor Pago"].sum().sort_values(ascending=False).head(10).reset_index()
                    fig1 = px.bar(df_aut, x=c_aut, y="Valor Pago", title="Top 10 Autores (Valor Recebido)", color="Valor Pago", color_continuous_scale="Blues")
                    fig1.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
                    st.plotly_chart(fig1, use_container_width=True)
            with cr:
                c_nat = next((c for c in df_exibir.columns if "Natureza Jurídica" in c), None)
                if c_nat:
                    df_nat = df_exibir.groupby(c_nat)["Valor Pago"].sum().sort_values(ascending=False).reset_index()
                    fig2 = px.pie(df_nat, names=c_nat, values="Valor Pago", title="Natureza Jurídica (%)", hole=0.4)
                    fig2.update_layout(legend=dict(orientation="h", y=-0.2))
                    st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Não foram encontrados dados para a licença: {uf_liberada}")
