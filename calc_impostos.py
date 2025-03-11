import pandas as pd

class Precificacao:
    def __init__(self, impostos_path, arquivo_path, unidade, UF_venda, MARGEM, preco_BIN, cod_produto, PAGAMENTO_modalidade, PAGAMENTO_parcelas):
        self.impostos = impostos_path
        self.arquivo = arquivo_path
        self.unidade = unidade
        self.UF_compra = unidade[-2:]
        self.UF_venda = UF_venda
        self.MARGEM = MARGEM
        self.preco_BIN = preco_BIN
        self.cod_produto = cod_produto
        self.PAGAMENTO_modalidade = PAGAMENTO_modalidade
        self.PAGAMENTO_parcelas = PAGAMENTO_parcelas

        df = pd.read_excel(self.arquivo)
        df = df[df['Código SAP'] == self.cod_produto]

        self.nome = df['Descrição'].iloc[0]
        self.tipo_bateria = df['Tipo'].iloc[0]
        self.VALOR = df['Preço sem impostos'].iloc[0]
        self.peso_BIN = df['Peso da Bateria'].iloc[0]

    def custo_financeiro(self, modalidade, parcelas):
        df_custosfinanceiros = pd.read_excel(self.impostos, sheet_name="custos financeiros")
        taxa_financeira = df_custosfinanceiros[modalidade][df_custosfinanceiros['Parcelas'] == parcelas].iloc[0]
        return taxa_financeira

    def taxa_IPI(self, unidade):
        df_impostos = pd.read_excel(self.impostos, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_IPI = df_impostos['IPI'][df_impostos['UNIDADES'] == unidade].iloc[0]
        return taxa_IPI

    def taxa_cofins(self, unidade):
        df_impostos = pd.read_excel(self.impostos, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_cofins = df_impostos['COFINS'][df_impostos['UNIDADES'] == unidade].iloc[0]
        return taxa_cofins
    
    def taxa_cofins_presumido(self):
        df_impostos = pd.read_excel(self.impostos, sheet_name="presumido")
        taxa_cofins_presumido = df_impostos['Alíquota'][df_impostos['Apuração Presumido'] == 'COFINS'].iloc[0]
        return taxa_cofins_presumido

    def taxa_pis(self, unidade):
        df_impostos = pd.read_excel(self.impostos, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_pis = df_impostos['PIS'][df_impostos['UNIDADES'] == unidade].iloc[0]
        return taxa_pis
    
    def taxa_pis_presumido(self):
        df_impostos = pd.read_excel(self.impostos, sheet_name="presumido")
        taxa_pis_presumido = df_impostos['Alíquota'][df_impostos['Apuração Presumido'] == 'PIS'].iloc[0]
        return taxa_pis_presumido

    def taxa_IRPJ(self, unidade, produtoOUservico):
        df_impostos = pd.read_excel(self.impostos, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_IRPJ = df_impostos['IRPJ PRODUTO' if produtoOUservico == 0 else 'IRPJ SERVIÇO'][df_impostos['UNIDADES'] == unidade].iloc[0]
        return taxa_IRPJ

    def taxa_CSLL(self, unidade, produtoOUservico):
        df_impostos = pd.read_excel(self.impostos, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_CSLL = df_impostos['CSLL PRODUTO' if produtoOUservico == 0 else 'CSLL SERVIÇO'][df_impostos['UNIDADES'] == unidade].iloc[0]
        return taxa_CSLL

    def taxa_icms(self, uf_origem, uf_destino):
        df_impostos = pd.read_excel(self.impostos, sheet_name="ICMS")
        taxa_ICMS = df_impostos[uf_destino][df_impostos['UF'] == uf_origem].iloc[0]
        return taxa_ICMS

    def custo_total(self,REGIME, valor, IPI, ICMS, PIS, COFINS):
        PIS_COFINS = PIS + COFINS

        valor_PIS_COFINS = (valor / (1 - PIS_COFINS)) * PIS_COFINS
        valor_ICMS = ((valor + valor_PIS_COFINS) / (1 - ICMS)) * ICMS
        valor_IPI = (valor + valor_PIS_COFINS + valor_ICMS) * IPI

        preco_minimo = valor + valor_ICMS + valor_PIS_COFINS + valor_IPI

        if REGIME == 'Lucro presumido':
            custo_final = preco_minimo - valor_ICMS
            return custo_final
        else:
            custo_final = preco_minimo - valor_ICMS - valor_PIS_COFINS
            return custo_final

    def precificacao(self, REGIME, CUSTO_TOTAL, COFINS, PIS, ICMS, IRPJ, CSLL, MARGEM, CUSTO_FINANCEIRO):
        if REGIME == 'Lucro presumido':
            preco = CUSTO_TOTAL / (1 - (ICMS + ((COFINS + PIS) * (1 - ICMS)) + (CUSTO_FINANCEIRO) + (MARGEM) + (IRPJ + CSLL)))
            return preco
        elif REGIME == 'Lucro real':
            preco = CUSTO_TOTAL / (1 - (ICMS + ((COFINS + PIS) * (1 - ICMS)) + (CUSTO_FINANCEIRO) + (MARGEM / (1 - (IRPJ + CSLL)))))
            return preco

    def custo_BIN(self, preco_BIN, peso_BIN):
        custo_BIN = preco_BIN * peso_BIN
        return custo_BIN

    def calcular_preco_final(self):
        IPI = self.taxa_IPI(self.unidade)
        COFINS = self.taxa_cofins(self.unidade)
        PIS = self.taxa_pis(self.unidade)
        ICMS_compra = self.taxa_icms('PE', self.UF_compra)
        ICMS_venda = self.taxa_icms(self.UF_compra, self.UF_venda)
        IRPJ = self.taxa_IRPJ(self.unidade, 0)
        CSLL = self.taxa_CSLL(self.unidade, 0)
        CUSTO_FINANCEIRO = self.custo_financeiro(self.PAGAMENTO_modalidade, self.PAGAMENTO_parcelas)

        CUSTO_BIN = self.custo_BIN(self.preco_BIN, self.peso_BIN)
        CUSTO_TOTAL = self.custo_total('Lucro presumido', self.VALOR, IPI, ICMS_compra, PIS, COFINS) + CUSTO_BIN

        PRECO_FINAL = self.precificacao('Lucro presumido', CUSTO_TOTAL, COFINS, PIS, ICMS_venda, IRPJ, CSLL, self.MARGEM, CUSTO_FINANCEIRO)
        return PRECO_FINAL