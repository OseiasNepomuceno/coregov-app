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
    # --- REGRA DE NEGÓCIO ---
    plano_usuario = st.session_state.get("plano", "Básico")  
    uf_liberada = st.session_state.get("uf_liberada", "RJ").strip().upper()

    st.markdown("""
        <style>
        [data-testid="stMetricValue"] { font-size: 1.8rem; }
        div[data-testid="metric-container"] {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px 10px;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Escolha a Visualização:", ["Visão Geral", "Por Favorecido"], key="select_dashboard_v26")

    # Busca o ID correto no Secrets
    key_id = "id_emendas_geral" if tipo_visao == "Visão Geral" else "id_emendas_favorecido"
    file_id = st.secrets.get(key_id)
    
    if not file_id:
        st.error(f"Erro: Secret '{key_id}' não configurado.")
        return

    nome_arquivo = f"base_{key_id}.csv"

    # Download se não existir
    if not os.path.exists(nome_arquivo):
        with st.spinner("Sincronizando base de dados..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=True)

    try:
        # Carregamento com detecção automática de separador
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]
        
        # --- BUSCA INTELIGENTE PELA COLUNA DE UF ---
        # Procura por 'UF' exato, depois por colunas que contenham 'UF' ou 'SIGLA'
        col_uf = next((c for c in df.columns if c.upper() == "UF"), 
                      next((c for c in df.columns if "UF" in c.upper() or "SIGLA" in c.upper()), None))
        
        if uf_liberada != "BRASIL" and col_uf:
            # Limpa espaços e garante que a comparação seja em maiúsculas
            df[col_uf] = df[col_uf].fillna('').str.strip().str.upper()
            df = df[df[col_uf] == uf_liberada].copy()
            status_msg = f"📍 Filtro Ativo: {uf_liberada} ({plano_usuario})"
        else:
            status_msg = f"🌍 Visão Nacional Liberada"

        # --- FILTRO DE ANO 2026 ---
        col_ano = next((c for c in df.columns if "ANO" in c.upper()), None)
        if col_ano:
            df = df[df[col_ano].fillna('').astype(str).str.contains("2026")].copy()

        # --- LIMPEZA FINANCEIRA ---
        mapeamento = {
            "Valor Empenhado": ["Valor Empenhado", "VALOR EMPENHADO", "Valor Total Empenhado"],
            "Valor Liquidado": ["Valor Liquidado", "VALOR LIQUIDADO", "Valor Total Liquidado"],
            "Valor Pago": ["Valor Pago", "VALOR PAGO", "Valor Recebido", "VALOR RECEBIDO"]
        }

        for destino, origens in mapeamento.items():
            for origem in origens:
                if origem in df.columns:
                    df[destino] = df[origem].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                    df[destino] = pd.to_numeric(df[destino], errors='coerce').fillna(0)
                    break

    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return

    if not df.empty:
        st.info(status_msg)
        
        if tipo_visao == "Visão Geral":
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Empenhado", formatar_moeda(df["Valor Empenhado"].sum() if "Valor Empenhado" in df.columns else 0))
            with c2: st.metric("💸 Liquidado", formatar_moeda(df["Valor Liquidado"].sum() if "Valor Liquidado" in df.columns else 0))
            with c3: st.metric("✅ Pago", formatar_moeda(df["Valor Pago"].sum() if "Valor Pago" in df.columns else 0))
        else:
            # --- GRÁFICOS REFINADOS (AUTOR POR NOME E NATUREZA TOP 10) ---
            st.divider()
            cl, cr = st.columns(2)
            
            with cl:
                c_aut = next((c for c in df.columns if "AUTOR" in c.upper() and "CÓDIGO" not in c.upper()), None)
                if c_aut:
                    df_aut = df.groupby(c_aut)["Valor Pago"].sum().sort_values(ascending=False).head(10).reset_index()
                    fig1 = px.bar(df_aut, x=c_aut, y="Valor Pago", title="Top 10 Autores", color="Valor Pago", color_continuous_scale="Blues")
                    fig1.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
                    st.plotly_chart(fig1, use_container_width=True)

            with cr:
                c_nat = next((c for c in df.columns if "NATUREZA JURÍDICA" in c.upper()), None)
                if c_nat:
                    df_nat = df.groupby(c_nat)["Valor Pago"].sum().sort_values(ascending=False).reset_index()
                    if len(df_nat) > 10:
                        top_10 = df_nat.head(10).copy()
                        outros_val = df_nat.iloc[10:]["Valor Pago"].sum()
                        df_final = pd.concat([top_10, pd.DataFrame({c_nat: ["Outros"], "Valor Pago": [outros_val]})], ignore_index=True)
                    else:
                        df_final = df_nat
                    fig2 = px.pie(df_final, names=c_nat, values="Valor Pago", title="Natureza Jurídica (Top 10)", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Atenção: Não há dados de 2026 para {uf_liberada} nesta visão.")
        # Ajuda para debug: mostra as colunas se não encontrar dados
        if st.checkbox("Verificar colunas do arquivo"):
            st.write(df.columns.tolist())
