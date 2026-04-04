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
    # Mapeamento para garantir que "RJ" encontre "RIO DE JANEIRO" se necessário
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
        df = pd.read_csv(nome_arquivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]

        if tipo_visao == "Visão Geral":
            # --- LÓGICA VISÃO GERAL (Já estava funcionando) ---
            col_uf = "UF"
            col_valor = "Valor Pago"
            col_autor = "Nome do Autor da Emenda"
            col_local = "Localidade de aplicação do recurso"
            
            if col_uf in df.columns and uf_sessao != "BRASIL":
                df = df[(df[col_uf].str.upper() == uf_sessao) | (df[col_uf].str.upper() == uf_busca)].copy()
            
            # Limpeza financeira padrão
            for c in ["Valor Empenhado", "Valor Liquidado", "Valor Pago"]:
                if c in df.columns:
                    df[c] = df[c].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
            df_exibir = df.copy()

        else:
            # --- LÓGICA POR FAVORECIDO (COLUNAS NOVAS) ---
            # Colunas definidas por você: Nome do Autor da Emenda, Tipo de Emenda, Ano/Mês, 
            # Favorecido, Natureza Jurídica, Tipo Favorecido, UF Favorecido, Munícipio Favorecido, Valor Recebido
            
            col_uf_fav = "UF Favorecido"
            col_valor_rec = "Valor Recebido"
            col_autor_fav = "Nome do Autor da Emenda"
            
            # 1. Filtro de UF no Favorecido
            if col_uf_fav in df.columns and uf_sessao != "BRASIL":
                df[col_uf_fav] = df[col_uf_fav].fillna('').str.strip().str.upper()
                df = df[(df[col_uf_fav] == uf_sessao) | (df[col_uf_fav] == uf_busca)].copy()

            # 2. Conversão do Valor Recebido
            if col_valor_rec in df.columns:
                df[col_valor_rec] = df[col_valor_rec].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                df[col_valor_rec] = pd.to_numeric(df[col_valor_rec], errors='coerce').fillna(0)

            # 3. Seleção das colunas exatas que você pediu
            cols_fav = [
                "Nome do Autor da Emenda", "Tipo de Emenda", "Ano/Mês", 
                "Favorecido", "Natureza Jurídica", "Tipo Favorecido", 
                "UF Favorecido", "Munícipio Favorecido", "Valor Recebido"
            ]
            df_exibir = df[[c for c in cols_fav if c in df.columns]].copy()

    except Exception as e:
        st.error(f"Erro ao processar colunas: {e}")
        return

    if not df_exibir.empty:
        st.success(f"✅ Dados filtrados para: {uf_busca}")
        
        if tipo_visao == "Visão Geral":
            # Cards da Visão Geral
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("💰 Empenhado", formatar_moeda(df_exibir["Valor Empenhado"].sum() if "Valor Empenhado" in df_exibir.columns else 0))
            with c2: st.metric("💸 Liquidado", formatar_moeda(df_exibir["Valor Liquidado"].sum() if "Valor Liquidado" in df_exibir.columns else 0))
            with c3: st.metric("✅ Pago", formatar_moeda(df_exibir["Valor Pago"].sum() if "Valor Pago" in df_exibir.columns else 0))
        else:
            # --- GRÁFICOS DA VISÃO POR FAVORECIDO ---
            st.divider()
            cl, cr = st.columns(2)
            with cl:
                if "Nome do Autor da Emenda" in df_exibir.columns:
                    df_aut = df_exibir.groupby("Nome do Autor da Emenda")["Valor Recebido"].sum().sort_values(ascending=False).head(10).reset_index()
                    fig1 = px.bar(df_aut, x="Nome do Autor da Emenda", y="Valor Recebido", title="Top 10 Autores (Valor Recebido)", color="Valor Recebido", color_continuous_scale="Blues")
                    fig1.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
                    st.plotly_chart(fig1, use_container_width=True)
            with cr:
                if "Natureza Jurídica" in df_exibir.columns:
                    df_nat = df_exibir.groupby("Natureza Jurídica")["Valor Recebido"].sum().sort_values(ascending=False).reset_index()
                    if len(df_nat) > 8:
                        top8 = df_nat.head(8).copy()
                        outros = pd.DataFrame({"Natureza Jurídica": ["Outros"], "Valor Recebido": [df_nat.iloc[8:]["Valor Recebido"].sum()]})
                        df_nat = pd.concat([top8, outros], ignore_index=True)
                    fig2 = px.pie(df_nat, names="Natureza Jurídica", values="Valor Recebido", title="Natureza Jurídica (%)", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum dado encontrado para {uf_busca} com os critérios selecionados.")
