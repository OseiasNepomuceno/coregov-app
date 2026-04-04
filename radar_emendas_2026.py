import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

def formatar_moeda(valor):
    try:
        v = float(valor)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_final_limpo")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = f"base_limpa_{file_id}.csv"

    if st.button("🔄 Sincronizar Base de Dados"):
        if os.path.exists(nome_arquivo): os.remove(nome_arquivo)
        st.cache_data.clear()
        st.rerun()

    if not os.path.exists(nome_arquivo):
        with st.spinner("Baixando e limpando dados..."):
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        # Lê o arquivo forçando tudo como texto
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        
        # --- LIMPEZA DE COLUNAS DESNECESSÁRIAS ---
        # Remove a primeira coluna (Código) que está vindo com erro científico
        df = df.iloc[:, 1:] 
        
        # Limpa os nomes das colunas que sobraram
        df.columns = [str(c).strip() for c in df.columns]
        
        # Localiza a coluna de Ano (agora deve ser a primeira ou segunda)
        col_ano = next((c for c in df.columns if "Ano" in c), df.columns[0])

        # Limpa o dado do ano (remove espaços e o .0 do Excel)
        df[col_ano] = df[col_ano].astype(str).str.strip().str.replace('.0', '', regex=False)
        
        # Filtra apenas 2026
        df_2026 = df[df[col_ano] == "2026"].copy()
            
    except Exception as e:
        st.error(f"Erro no processamento: {e}"); return

    # Lógica de Permissão
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    acesso_nacional = plano in ["PREMIUM", "DIAMANTE", "OURO"]

    if not acesso_nacional:
        # Tenta achar a coluna de UF para filtrar pelo estado do usuário
        col_uf = next((c for c in df_2026.columns if "UF" in c.upper()), None)
        if col_uf:
            sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
            df_2026 = df_2026[df_2026[col_uf].astype(str).str.contains(sigla, na=False, case=False)]

    if not df_2026.empty:
        if tipo_visao == "Visão Geral":
            def calcular_total(termo):
                c = next((col for col in df_2026.columns if termo.upper() in col.upper()), None)
                if c:
                    # Converte valores brasileiros "1.234,56" para float
                    v = df_2026[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v1, v2, v3 = calcular_total("Empenhado"), calcular_total("Liquidado"), calcular_total("Pago")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("EMPENHADO", formatar_moeda(v1))
            c2.metric("LIQUIDADO", formatar_moeda(v2))
            c3.metric("PAGO", formatar_moeda(v3))
            st.divider()

        st.success(f"✅ Exibindo {len(df_2026)} registros de 2026.")
        st.dataframe(df_2026, use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum dado de 2026 encontrado com os filtros atuais.")
        if not df.empty:
            st.write("Anos disponíveis no arquivo:", df[col_ano].unique())
