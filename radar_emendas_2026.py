import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').upper().strip()

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_final_2026")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    
    # 1. NOME DE ARQUIVO DINÂMICO PARA EVITAR CACHE DO SERVIDOR
    # Usamos o ID no nome para que, se o ID mudar, o arquivo antigo seja ignorado
    nome_arquivo = f"base_radar_{file_id}.csv" if file_id else "base_temp.csv"

    # 2. LÓGICA DE LIMPEZA FORÇADA (BOTÃO)
    if st.button("🔄 Sincronizar Base de Dados"):
        # Remove todos os arquivos CSV da pasta temporária do servidor
        for f in os.listdir():
            if f.endswith(".csv"):
                try:
                    os.remove(f)
                except:
                    pass
        st.success("Cache limpo! Baixando versão mais recente do Drive...")
        st.rerun()

    # 3. DOWNLOAD COM BYPASS DE CACHE
    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("Configure o ID do arquivo no Streamlit Secrets."); return
        
        with st.spinner("Conectando ao Google Drive..."):
            # A URL com 'export=download' ajuda a forçar a versão mais atual
            url = f'https://drive.google.com/uc?export=download&id={file_id}'
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        # Leitura Robusta (Tenta ponto e vírgula, depois vírgula)
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        if len(df.columns) < 2:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip', dtype=str)

        # Limpeza de nomes de colunas
        df.columns = [str(c).strip() for c in df.columns]

        # Localização automática da coluna de Ano
        col_ano = next((c for c in df.columns if "Ano" in c or "ANO" in c), df.columns[1])

        # Extração apenas de números (corrige 2026.0 ou formatos científicos)
        df[col_ano] = df[col_ano].astype(str).str.extract('(\d+)', expand=False)
        
        # Filtro de 2026
        df_filtrado = df[df[col_ano] == "2026"].copy()
            
    except Exception as e:
        st.error(f"Erro ao processar: {e}"); return

    # Verificação de Plano / Acesso
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    
    if plano in ["PREMIUM", "DIAMANTE", "OURO"]:
        st.success("🔓 **Acesso Premium:** Dados Nacionais")
    else:
        col_uf = next((c for c in df_filtrado.columns if "UF" in c.upper() or "ESTADO" in c.upper()), None)
        if col_uf:
            sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
            df_filtrado = df_filtrado[df_filtrado[col_uf].astype(str).str.contains(sigla, na=False, case=False)]
            st.info(f"📍 Localidade: {sigla}")

    # Exibição dos Resultados
    if not df_filtrado.empty:
        if tipo_visao == "Visão Geral":
            def soma_valor(texto):
                col = next((c for c in df_filtrado.columns if texto.upper() in c.upper()), None)
                if col:
                    # Limpeza de formato de moeda brasileiro para cálculo
                    v = df_filtrado[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v1, v2, v3 = soma_valor("Empenhado"), soma_valor("Liquidado"), soma_valor("Pago")
            m1, m2, m3 = st.columns(3)
            m1.metric("EMPENHADO", formatar_moeda(v1))
            m2.metric("LIQUIDADO", formatar_moeda(v2))
            m3.metric("PAGO", formatar_moeda(v3))
            st.divider()

        st.write(f"📊 Foram encontrados **{len(df_filtrado)}** registros para 2026.")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Nenhum registro de 2026 encontrado nesta versão do arquivo.")
        # Diagnóstico para o desenvolvedor
        if col_ano in df.columns:
            st.write("Anos identificados no arquivo baixado:", df[col_ano].unique())
