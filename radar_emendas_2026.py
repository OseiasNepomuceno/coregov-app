import streamlit as st
import pandas as pd
import gdown
import os

def formatar_moeda(valor):
    try:
        v = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_final_universal")

    # IDs dos Secrets
    id_geral = st.secrets.get("id_emendas_geral")
    id_favorecido = st.secrets.get("id_emendas_favorecido")
    file_id = id_geral if tipo_visao == "Visão Geral" else id_favorecido
    
    nome_arquivo = f"base_{tipo_visao.lower().replace(' ', '_')}.csv"

    if st.button("🔄 Sincronizar Tudo (Limpar Cache)"):
        for f in os.listdir():
            if f.endswith(".csv"): os.remove(f)
        st.cache_data.clear()
        st.rerun()

    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("ID não configurado nos Secrets."); return
        with st.spinner(f"Baixando base de {tipo_visao}..."):
            gdown.download(f'https://drive.google.com/uc?export=download&id={file_id}', nome_arquivo, quiet=False)

    try:
        # TESTE DE SEPARADOR (Tenta ; depois ,)
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        if len(df.columns) < 3:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip', dtype=str)

        # Limpeza de colunas
        df.columns = [str(c).strip() for c in df.columns]

        # --- BUSCA DE COLUNA POR POSIÇÃO (Caso o nome falhe) ---
        # No seu arquivo: Coluna 0 = Código, Coluna 1 = Ano, Coluna 4 = Nome Autor
        try:
            col_ano = next((c for c in df.columns if "Ano" in c or "ANO" in c), df.columns[1])
        except:
            col_ano = df.columns[1]

        # Limpeza do Ano
        df[col_ano] = df[col_ano].astype(str).str.strip().str.replace('.0', '', regex=False)
        
        # FILTRO DE 2026
        df_2026 = df[df[col_ano] == "2026"].copy()
            
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}"); return

    # Verificação de Permissão
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    
    if plano in ["PREMIUM", "DIAMANTE", "OURO"]:
        df_exibir = df_2026
        st.success(f"🔓 **Acesso Premium:** {tipo_visao} (Brasil)")
    else:
        # Filtro de Localidade (UF)
        col_uf = next((c for c in df_2026.columns if "UF" in c.upper() or "ESTADO" in c.upper()), None)
        if col_uf:
            sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
            df_exibir = df_2026[df_2026[col_uf].astype(str).str.contains(sigla, na=False, case=False)]
            st.info(f"📍 Localidade: {sigla}")
        else:
            df_exibir = df_2026

    if not df_exibir.empty:
        if tipo_visao == "Visão Geral":
            def soma(termo):
                c = next((col for col in df_exibir.columns if termo.upper() in col.upper()), None)
                if c:
                    v = df_exibir[c].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v1, v2, v3 = soma("Empenhado"), soma("Liquidado"), soma("Pago")
            c1, c2, c3 = st.columns(3)
            c1.metric("EMPENHADO", formatar_moeda(v1))
            c2.metric("LIQUIDADO", formatar_moeda(v2))
            c3.metric("PAGO", formatar_moeda(v3))
            st.divider()

        st.write(f"📊 Foram encontrados **{len(df_exibir)}** registros para 2026.")
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Nenhum registro de 2026 encontrado com estes filtros.")
        # Se estiver vazio, vamos mostrar o que o Python está 'enxergando'
        st.write("Colunas detectadas:", list(df.columns))
        st.write("Amostra dos anos no arquivo:", df[col_ano].unique() if col_ano in df.columns else "Nenhum")
