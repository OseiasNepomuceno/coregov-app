import streamlit as st
import pandas as pd
import gdown
import os
import re

def formatar_moeda(valor):
    try:
        v = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_final_universal")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = f"base_{tipo_visao.lower().replace(' ', '_')}.csv"

    if st.button("🔄 Sincronizar Tudo (Limpar Cache)"):
        for f in os.listdir():
            if f.endswith(".csv"): os.remove(f)
        st.cache_data.clear()
        st.rerun()

    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("ID não configurado nos Secrets."); return
        with st.spinner("Baixando base de dados..."):
            gdown.download(f'https://drive.google.com/uc?export=download&id={file_id}', nome_arquivo, quiet=False)

    try:
        # Leitura inicial
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        if len(df.columns) < 5:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip', dtype=str)

        # 1. LIMPEZA TOTAL DE CABEÇALHOS (Remove aspas e espaços)
        df.columns = [c.replace('"', '').strip() for c in df.columns]

        # 2. LOCALIZAÇÃO DA COLUNA DE ANO
        col_ano = "Ano da Emenda"
        if col_ano not in df.columns:
            col_ano = next((c for c in df.columns if "Ano" in c), df.columns[1])

        # 3. LIMPEZA AGRESSIVA DO DADO (A "Mágica" para funcionar)
        # Remove qualquer coisa que não seja número (tira .0, espaços, aspas, etc)
        df[col_ano] = df[col_ano].astype(str).apply(lambda x: re.sub(r'\D', '', x))
        
        # 4. FILTRO DEFINITIVO
        df_2026 = df[df[col_ano] == "2026"].copy()
            
    except Exception as e:
        st.error(f"Erro no processamento: {e}"); return

    # Lógica de Permissão
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    acesso_nacional = plano in ["PREMIUM", "DIAMANTE", "OURO"]

    if acesso_nacional:
        df_exibir = df_2026
        st.success(f"🔓 **Acesso Premium:** {tipo_visao} (Brasil)")
    else:
        col_uf = "UF"
        if col_uf in df_2026.columns:
            sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
            df_exibir = df_2026[df_2026[col_uf].astype(str).str.strip().str.upper() == sigla]
            st.info(f"📍 Exibindo dados de: {sigla}")
        else:
            df_exibir = df_2026

    # EXIBIÇÃO
    if not df_exibir.empty:
        if tipo_visao == "Visão Geral":
            def soma_total(termo):
                c = next((col for col in df_exibir.columns if termo.upper() in col.upper()), None)
                if c:
                    v = df_exibir[c].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v_emp, v_liq, v_pag = soma_total("Empenhado"), soma_total("Liquidado"), soma_total("Pago")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("EMPENHADO", formatar_moeda(v_emp))
            c2.metric("LIQUIDADO", formatar_moeda(v_liq))
            c3.metric("PAGO", formatar_moeda(v_pag))
            st.divider()

        st.write(f"📊 Registros para 2026: **{len(df_exibir)}**")
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Nenhum registro de 2026 encontrado com estes filtros.")
        # Se não achar nada, mostra o que tem na coluna de ano para sabermos o que o Python está lendo
        st.write("Dados encontrados na coluna de Ano (Top 5):", df[col_ano].unique()[:5])
