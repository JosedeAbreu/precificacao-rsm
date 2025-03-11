#streamlit run interface.py
import streamlit as st
import pandas as pd
from impostos import impostos
from custos import Custos
import plotly.express as px
import plotly.graph_objects as go
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)


authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login()

if st.session_state["authentication_status"]:
    # Carregar arquivos
    ARQUIVO_IMPOSTOS = "ALÍQUOTAS.xlsx"
    ARQUIVO_BATERIAS = "preco BATERIAS.xlsx"
    unidades = "Cadastro unidade.xlsx"

    df_unidades = pd.read_excel(unidades, sheet_name='cadastro')
    df_baterias = pd.read_excel(ARQUIVO_BATERIAS)
    df_meio_pag = pd.read_excel(ARQUIVO_IMPOSTOS, sheet_name="custos financeiros")

    unidades_rsm = list(df_unidades['UNIDADES'])
    UFs = ['AC', 'AL','AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']

    meios_pagamento = df_meio_pag.drop(columns='Parcelas').columns

    pam_lme = ['PAM', 'LME']
    valor_BIN = 0

    st.set_page_config(layout="wide", page_title= "Precificação RSM")


    #SIDEBAR
    st.sidebar.header("Parametros venda")
    lista_cod = df_baterias.apply(lambda x: f'{x["Código SAP"]} | {x["Descrição"]}', axis=1)
    cod_nome = st.sidebar.selectbox("Código do Produto",lista_cod)
    unidade_rsm = st.sidebar.selectbox("Unidade RSM", unidades_rsm)
    uf_origem = unidade_rsm[-2:] if unidade_rsm != "RSM IND" else "SP"
    uf_destino = st.sidebar.selectbox("UF destino", UFs)
    tipo_venda = st.sidebar.radio("Tipo de venda", pam_lme)
    if tipo_venda == 'LME':
        valor_BIN = st.sidebar.number_input("Custo BIN (R$ / Kg)", value=4.20)
    else:
        valor_BIN = 0
    frete_fabrica = st.sidebar.number_input("Frete fábrica (R$)")
    frete_cliente = st.sidebar.number_input("Frete cliente (R$)")
    MARGEM = st.sidebar.number_input("Margem (%)", value=12.0) / 100
    selected_pagamento = st.sidebar.selectbox("Selecione um meio de pagamento:", meios_pagamento)
    selected_parcelas = st.sidebar.selectbox("Parcelas:",df_meio_pag[df_meio_pag[selected_pagamento].notna()]["Parcelas"])

    # Tela principal
    header1, header2, header3 = st.columns(3)
    header1.image('imagens/logo-moura.png')
    st.title(f"Precificação {unidade_rsm}")

    #Detalhamento geral
    cod_produto, nome_produto = cod_nome.split("|")
    cod_produto = int(cod_produto.strip())

    df_bateria_selecionada = df_baterias[df_baterias['Código SAP'] == cod_produto]
    VALOR = df_bateria_selecionada['Preço sem impostos'].iloc[0]
    peso_BIN = df_bateria_selecionada['Peso da Bateria'].iloc[0]
    tipo_bateria = df_bateria_selecionada['Tipo'].iloc[0]

    #Detalhamento impostos
    impostos = impostos(ARQUIVO_IMPOSTOS,unidade_rsm, uf_destino, tipo_bateria)
    IPI = impostos.taxa_IPI()
    ICMS_compra = impostos.taxa_icms('PE', uf_origem)
    ICMS_venda = impostos.taxa_icms(uf_origem, uf_destino)
    IRPJ = impostos.taxa_IRPJ(unidade_rsm, 0)
    CSLL = impostos.taxa_CSLL(unidade_rsm, 0)

    regime = df_unidades[df_unidades['UNIDADES'] == unidade_rsm]['REGIME'].iloc[0]

    COFINS = impostos.taxa_cofins()
    PIS = impostos.taxa_pis()

    COFINS_venda = COFINS if regime != "Lucro presumido" else(impostos.taxa_cofins_presumido())
    PIS_venda = PIS if regime != "Lucro presumido" else(impostos.taxa_pis_presumido())

    CUSTO_FINANCEIRO = impostos.custo_financeiro(selected_pagamento, selected_parcelas)

    df_clm4 = pd.DataFrame({
        'Tributo': ['IPI','COFINS','PIS','ICMS','IRPJ','CSLL'], 
        'Alíquotas': [f"{(IPI*100):.2f}%",f"{COFINS*100:.2f}%", f"{PIS*100:.2f}%", f"{ICMS_compra*100:.2f}%",f"{IRPJ*100:.2f}%",f"{CSLL*100:.2f}%"]
    })
    compra_valor_PIS_COFINS = (VALOR/(1-(PIS+COFINS)))*(PIS+COFINS)
    compra_valor_ICMS = ((VALOR + compra_valor_PIS_COFINS)-(1-ICMS_compra))*(ICMS_compra)
    compra_valor_IPI = (VALOR+compra_valor_PIS_COFINS+compra_valor_ICMS)*IPI
    _PIS_COFINS = compra_valor_PIS_COFINS if regime == 'Lucro presumido' else 0
    df_precificacao = pd.DataFrame({
        'Contas': ['Preço bateria (Fábrica)','Frete fábrica','IPI','PIS/COFINS'],
        'Valores': [ VALOR,frete_fabrica, compra_valor_IPI, _PIS_COFINS],
        'Tipo': ['Custo bateria','Custo bateria','Custo bateria','Custo bateria']
    })

    #Seção precificação
    CUSTOS = Custos(VALOR,regime, COFINS, PIS, ICMS_compra, ICMS_venda, IRPJ, CSLL, IPI, CUSTO_FINANCEIRO)
    
    CUSTO_BIN = CUSTOS.custo_BIN(valor_BIN, peso_BIN)
    CUSTO_NF = CUSTOS.custo_total()
    CUSTO_TOTAL = CUSTO_NF + CUSTO_BIN + frete_cliente + frete_fabrica

    PRECO_FINAL = CUSTOS.precificacao(CUSTO_TOTAL, MARGEM)

    #Detalhamento do resultado
    valor_ICMS = ICMS_venda * PRECO_FINAL
    valor_PIS = (PRECO_FINAL - valor_ICMS)*PIS_venda
    valor_COFINS = (PRECO_FINAL - valor_ICMS)*COFINS_venda
    valor_impostos = valor_ICMS + valor_PIS + valor_COFINS

    receita_pos_deducoes = PRECO_FINAL - valor_impostos

    custo_Baterias = CUSTO_NF

    lucro_bruto = receita_pos_deducoes - custo_Baterias

    CUSTO_BIN = CUSTO_BIN
    despesa_financeira = CUSTO_FINANCEIRO * PRECO_FINAL
    frete_unidade = frete_fabrica
    frete_cliente = frete_cliente
    despesas_operacionais = CUSTO_BIN + despesa_financeira + frete_unidade + frete_cliente

    lucroliquido_antesdoir = lucro_bruto - despesas_operacionais

    valor_CSLL = (PRECO_FINAL * CSLL) if regime == "Lucro presumido" else (lucroliquido_antesdoir * CSLL)
    valor_IRPJ = (PRECO_FINAL * IRPJ) if regime == "Lucro presumido" else (lucroliquido_antesdoir * IRPJ)
    despesas_tributarias = valor_CSLL + valor_IRPJ

    lucro_liquido_apos_IR = lucroliquido_antesdoir - despesas_tributarias

    df_detalhamento_resultado = pd.DataFrame({
        'Conta': ['Receita bruta', '(-) IMPOSTOS', 'COFINS', 'PIS', 'ICMS', 'RECEITA APÓS DEDUÇÕES', '(-) CUSTO DAS BATERIAS', 'LUCRO BRUTO', '(-) DESPESAS OPERACIONAIS', 'Custo BIN', 'DESPESA FINANCEIRA', 'FRETE P/ UNIDADE', 'FRETE P/ CLIENTE', 'LUCRO LÍQUIDO ANTES DO IR/CSLL', 'DESPESAS TRIBUTÁRIAS', 'CSLL', 'IRPJ', 'LUCRO LÍQUIDO APÓS IR/CSLL'],
        'Valores': [PRECO_FINAL, valor_impostos, valor_COFINS, valor_PIS, valor_ICMS, receita_pos_deducoes, custo_Baterias, lucro_bruto, despesas_operacionais, CUSTO_BIN, despesa_financeira, frete_unidade, frete_cliente, lucroliquido_antesdoir, despesas_tributarias, valor_CSLL, valor_IRPJ, lucro_liquido_apos_IR]
    })

    # Conta_dre = ['Receita bruta', '(-) IMPOSTOS', '(-) CUSTO DAS BATERIAS', '(-) DESPESAS OPERACIONAIS', 'DESPESAS TRIBUTÁRIAS', 'LUCRO LÍQUIDO APÓS IR/CSLL']
    # Valores_dre = [PRECO_FINAL, -valor_impostos, -custo_Baterias, -despesas_operacionais, -despesas_tributarias, lucro_liquido_apos_IR]
    Conta_dre = ['Receita bruta','COFINS', 'PIS', 'ICMS','CUSTO DAS BATERIAS', 'Custo BIN', 'DESPESA FINANCEIRA', 'FRETE P/ UNIDADE', 'FRETE P/ CLIENTE', 'CSLL', 'IRPJ']
    Valores_dre = [PRECO_FINAL, -valor_COFINS, -valor_PIS, -valor_ICMS, -custo_Baterias,-CUSTO_BIN, -despesa_financeira, -frete_unidade, -frete_cliente, -valor_CSLL, -valor_IRPJ]

    clm1, clm2 = st.columns(2)
    container_dre = st.container()
    clm_dre, clmtable_dre = container_dre.columns([0.7,0.3], vertical_alignment= 'center')
    container_custos = st.container()
    container_custos.subheader("Custos aquisição bateria")
    clm3, clm4= container_custos.columns([0.7, 0.3], vertical_alignment= 'center')
    
    # Verificação dos dados
    if len(Conta_dre) == len(Valores_dre):
        # Criando o gráfico de cascata
        fig_dre = go.Figure(go.Waterfall(
            name="DRE",  # Nome do gráfico
            orientation="v",  # Orientação vertical
            x=Conta_dre,  # Eixo X com as categorias
            y=Valores_dre,  # Eixo Y com os valores
            textposition="outside",  # Posição do texto (fora das barras)
            text=[f"R${v:,.2f}" for v in Valores_dre],  # Texto exibido nas barras
            connector={"line": {"color": "gray"}},  # Linha de conexão entre as barras
        ))

        # Personalizando o layout
        fig_dre.update_layout(
            title="Demonstração do Resultado do Exercício (DRE)",
            xaxis_title="Categorias",
            yaxis_title="Valores (R$)",
            showlegend=False,
        )

        # Exibindo o gráfico no Streamlit
        container_dre.subheader("Detalhamento resultado")
        container_dre.plotly_chart(fig_dre)
    else:
        container_dre.error("Erro: As listas 'Conta_dre' e 'Valores_dre' têm tamanhos diferentes.")

    clm1.text(f"UF destino: {uf_destino}")
    clm1.text(f"Código do produto: {cod_produto}")
    clm1.text(f"Nome do produto: {nome_produto}")
    clm1.text(f"Tipo de venda: {tipo_venda}")

    clm2.metric("Preço sugerido:", f"R$ {PRECO_FINAL:,.2f}")
    clm2.metric("Lucro Líquido Após IR/CSLL:", f"R$ {lucro_liquido_apos_IR:,.2f}")


    clm3.metric("Custo total:",f"R$ {(CUSTO_NF+frete_fabrica):.2f}")
    fig_custos = px.bar(df_precificacao, barmode='group', color='Contas',x='Tipo', y='Valores', text='Valores')
    fig_custos.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
    clm3.plotly_chart(fig_custos)

    clm4.dataframe(df_clm4, hide_index=True)

elif st.session_state["authentication_status"] is False:
    st.error('Usuário/Senha é inválido')
elif st.session_state["authentication_status"] is None:
    st.warning('Por Favor, utilize seu usuário e senha!')
