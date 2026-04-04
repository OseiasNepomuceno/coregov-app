import streamlit as st
import pandas as pd
import gdown
import os
import unicodedata

# Configurações de UI e Auxiliares
MAPA_ESTADOS = {'AC':'ACRE','AL':'ALAGOAS','AP':'AMAPA','AM':'AMAZONAS','BA':'BAHIA','CE':'CEARA','DF':'DISTRITO FEDERAL','ES':'ESPIRITO SANTO','GO':'GOIAS','MA':'MARANHAO','MT':'MATO GROSSO','MS':'MATO GROSSO DO SUL','MG':'MINAS GERAIS','PA':'PARA','PB':'PARAIBA','PR':'PARANA','PE':'PERNAMBUCO','PI':'PIAUI','RJ':'RIO DE JANEIRO','RN':'RIO GRANDE DO NORTE','RS':'RIO GRANDE DO SUL','RO':'RONDONIA','RR':'RORAIMA','SC':'SANTA CATARINA','SP':'SAO PAULO','SE':'SERGIPE','TO':'TOCANTINS'}

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').upper().strip()

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def exibir_radar():
    st.title("🏛️ Radar de Emendas 2026")
    tipo_visao = st.selectbox("Visualização:", ["Visão Geral", "Por Favorecido"], key="v_topo")

    file_id = st.secrets.get("id_emendas_geral") if tipo_visao == "Visão Geral" else st.secrets.get("id_emendas_favorecido")
    nome_arquivo = "base_emendas.csv"

    if not os.path.exists(nome_arquivo) or st.button("🔄 Atualizar Dados"):
        if not file_id:
            st.error("ID do arquivo não configurado."); return
        with st.spinner("Baixando base atualizada..."):
            gdown.download(f'https://drive.google.com/uc?id={file_id}', nome_arquivo, quiet=False)

    try:
        # LEITURA ROBUSTA: Forçamos o separador e o encoding
        df = pd.read_csv(nome_arquivo, sep=';', encoding='latin1', on_bad_lines='skip', dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # --- FILTRO DE ANO (TENTATIVA POR NOME OU POSIÇÃO) ---
        coluna_ano = next((c for c in df.columns if "ANO" in c), df.columns[1] if len(df.columns) > 1 else None)
        
        if coluna_ano:
            # Limpeza total: remove tudo que não é número
            df[coluna_ano] = df[coluna_ano].astype(str).str.extract('(\d+)', expand=False)
            df = df[df[coluna_ano] == "2026"]
            
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}"); return

    # LÓGICA DE PERMISSÃO
    usuario = st.session_state.get('usuario_logado', {})
    plano = str(usuario.get('PLANO', 'BRONZE')).upper()
    acesso_nacional = plano in ["PREMIUM", "DIAMANTE", "OURO"]

    if acesso_nacional:
        st.success("🔓 **Acesso Premium:** Brasil")
    else:
        col_uf = next((c for c in ["UF", "ESTADO"] if c in df.columns), None)
        if col_uf:
            sigla = str(usuario.get('LOCALIDADE') or "SP").upper()
            estado = remover_acentos(MAPA_ESTADOS.get(sigla, sigla))
            df = df[df[col_uf].astype(str).apply(remover_acentos) == estado]
            st.info(f"📍 Localidade: {estado}")

    if not df.empty:
        if tipo_visao == "Visão Geral":
            def limpar_e_somar(termo):
                col = next((c for c in df.columns if termo in c), None)
                if col:
                    # O segredo para valores brasileiros: remove ponto e troca vírgula por ponto
                    nums = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                    return pd.to_numeric(nums, errors='coerce').sum()
                return 0.0

            v1, v2, v3 = limpar_e_somar("EMPENHADO"), limpar_e_somar("LIQUIDADO"), limpar_e_somar("PAGO")
            c1, c2, c3 = st.columns(3)
            c1.metric("EMPENHADO", formatar_moeda(v1))
            c2.metric("LIQUIDADO", formatar_moeda(v2))
            c3.metric("PAGO", formatar_moeda(v3))
            st.divider()

        st.write(f"📊 Registros encontrados: **{len(df)}**")
        busca = st.text_input("🔍 Pesquisar na tabela:", key="f_final")
        if busca:
            mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            st.dataframe(df[mask], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Nenhum dado de 2026 encontrado. Verifique se o arquivo CSV está correto.")
        # Verificação técnica para você
        st.write("Colunas detectadas:", list(df.columns)[:5])
