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
    nome_arquivo = "base_temp.csv"

    # Botão para forçar o download se algo estiver errado
    if st.button("🔄 Sincronizar Base de Dados"):
        if os.path.exists(nome_arquivo):
            os.remove(nome_arquivo)
        st.rerun()

    if not os.path.exists(nome_arquivo):
        if not file_id:
            st.error("Configure o ID do arquivo no Streamlit Secrets."); return
        with st.spinner("Baixando dados..."):
            gdown.download(f'https://drive.google.com/uc?id={file_id}', nome_arquivo, quiet=False)

    try:
        # TENTATIVA 1: Ponto e vírgula (Padrão BR)
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        
        # Se ele leu tudo como uma coluna só, tenta vírgula
        if len(df.columns) < 2:
            df = pd.read_csv(nome_arquivo, sep=',', encoding='latin1', on_bad_lines='skip', dtype=str)

        # Limpeza de nomes de colunas
        df.columns = [str(c).strip() for c in df.columns]

        # --- LOCALIZAÇÃO AUTOMÁTICA DA COLUNA DE ANO ---
        # Procura por "Ano", se não achar, pega a segunda coluna
        col_ano = next((c for c in df.columns if "Ano" in c or "ANO" in c), df.columns[1])

        # Limpeza do Ano (Remove .0, espaços e extrai apenas números)
        df[col_ano] = df[col_ano].astype(str).str.extract('(\d+)', expand=False)
        
        # FILTRO
        df_filtrado = df[df[col_ano] == "2026"].copy()
            
    except Exception as e:
        st.error(f"Erro ao processar: {e}"); return

    # Verificação de Plano
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

    if not df_filtrado.empty:
        if tipo_visao == "Visão Geral":
            def soma_valor(texto):
                col = next((c for c in df_filtrado.columns if texto.upper() in c.upper()), None)
                if col:
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
        st.warning("⚠️ Nenhum registro de 2026 encontrado.")
        # Se não achar nada, mostra o que existe no arquivo para diagnóstico
        st.write("Anos disponíveis no arquivo:", df[col_ano].unique()[:5] if col_ano in df.columns else "Coluna não encontrada")
