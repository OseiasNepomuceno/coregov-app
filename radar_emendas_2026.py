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
    
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_final_topo")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = "base_emendas_limpa.csv"

    if not os.path.exists(nome_arquivo) or st.button("🔄 Forçar Atualização de Dados"):
        if not file_id:
            st.error("ID do arquivo não configurado."); return
        with st.spinner("Baixando base de dados..."):
            url = f'https://drive.google.com/uc?id={file_id}'
            if os.path.exists(nome_arquivo): os.remove(nome_arquivo)
            gdown.download(url, nome_arquivo, quiet=False)

    try:
        # Lendo com tratamento de erro para linhas problemáticas
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        
        # Limpeza absoluta de nomes de colunas
        df.columns = [str(c).strip() for c in df.columns]

        # --- ESTRATÉGIA DE FILTRO POR POSIÇÃO (Caso o nome falhe) ---
        # A segunda coluna (índice 1) no seu arquivo é o Ano
        col_ano = "Ano da Emenda"
        
        if col_ano not in df.columns:
            col_ano = df.columns[1] # Tenta a segunda coluna se o nome falhar

        # Limpeza do Ano: Mantém apenas números
        df[col_ano] = df[col_ano].astype(str).str.extract('(\d+)', expand=False)
        
        # Filtro definitivo
        df = df[df[col_ano] == "2026"]
            
    except Exception as e:
        st.error(f"Erro crítico na leitura: {e}"); return

    # Lógica de Plano
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    
    if plano in ["PREMIUM", "DIAMANTE", "OURO"]:
        st.success("🔓 **Acesso Premium:** Brasil (2026)")
    else:
        # Busca UF (Geralmente coluna 10 ou 11)
        col_uf = next((c for c in df.columns if c.upper() in ["UF", "ESTADO"]), df.columns[10])
        sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
        df = df[df[col_uf].astype(str).str.contains(sigla, na=False, case=False)]
        st.info(f"📍 Localidade: {sigla}")

    if not df.empty:
        if tipo_visao == "Visão Geral":
            def somar(termo):
                col = next((c for c in df.columns if termo.upper() in c.upper()), None)
                if col:
                    # Converte padrão BR (1.234,56) para float (1234.56)
                    v = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(v, errors='coerce').sum()
                return 0.0

            v_emp = somar("Empenhado")
            v_liq = somar("Liquidado")
            v_pag = somar("Pago")

            c1, c2, c3 = st.columns(3)
            c1.metric("EMPENHADO", formatar_moeda(v_emp))
            c2.metric("LIQUIDADO", formatar_moeda(v_liq))
            c3.metric("PAGO", formatar_moeda(v_pag))
            st.divider()

        st.write(f"📊 Registros de 2026 encontrados: **{len(df)}**")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ O arquivo foi lido, mas o ano '2026' não foi detectado nas colunas.")
        # Ajuda a identificar o que está errado
        st.write("Primeiras linhas detectadas para análise:", df.head(2))
