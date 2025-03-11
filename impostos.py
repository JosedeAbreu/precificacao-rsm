import pandas as pd

class impostos:
    def __init__(self, impostos_path, unidade, uf_destino, tipo_bateria):
        self.impostos_path = impostos_path
        
        self.unidade = unidade
        self.uf_origem = unidade[-2:]

        self.uf_destino = uf_destino

        self.tipo_bateria = tipo_bateria
    
    def custo_financeiro(self, meio_pagamento, parcelas):
        df_custosfinanceiros = pd.read_excel(self.impostos_path, sheet_name="custos financeiros")
        taxa_financeira = df_custosfinanceiros[meio_pagamento][df_custosfinanceiros['Parcelas'] == parcelas].iloc[0]
        return taxa_financeira

    def taxa_IPI(self):
        df_impostos = pd.read_excel(self.impostos_path, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_IPI = df_impostos['IPI'][df_impostos['UNIDADES'] == self.unidade].iloc[0]
        return taxa_IPI

    def taxa_cofins(self):
        df_impostos = pd.read_excel(self.impostos_path, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_cofins = df_impostos['COFINS'][df_impostos['UNIDADES'] == self.unidade].iloc[0]
        return taxa_cofins
    
    def taxa_cofins_presumido(self):
        df_impostos = pd.read_excel(self.impostos_path, sheet_name="presumido")
        taxa_cofins_presumido = df_impostos['Alíquota'][df_impostos['Apuração Presumido'] == 'COFINS'].iloc[0]
        return taxa_cofins_presumido

    def taxa_pis(self):
        df_impostos = pd.read_excel(self.impostos_path, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_pis = df_impostos['PIS'][df_impostos['UNIDADES'] == self.unidade].iloc[0]
        return taxa_pis
    
    def taxa_pis_presumido(self):
        df_impostos = pd.read_excel(self.impostos_path, sheet_name="presumido")
        taxa_pis_presumido = df_impostos['Alíquota'][df_impostos['Apuração Presumido'] == 'PIS'].iloc[0]
        return taxa_pis_presumido

    def taxa_IRPJ(self, unidade, produtoOUservico):
        df_impostos = pd.read_excel(self.impostos_path, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_IRPJ = df_impostos['IRPJ PRODUTO' if produtoOUservico == 0 else 'IRPJ SERVIÇO'][df_impostos['UNIDADES'] == unidade].iloc[0]
        return taxa_IRPJ

    def taxa_CSLL(self, unidade, produtoOUservico):
        df_impostos = pd.read_excel(self.impostos_path, sheet_name="baterias" if self.tipo_bateria != "Solar Lítio" else "lítio")
        taxa_CSLL = df_impostos['CSLL PRODUTO' if produtoOUservico == 0 else 'CSLL SERVIÇO'][df_impostos['UNIDADES'] == unidade].iloc[0]
        return taxa_CSLL

    def taxa_icms(self, uf_origem, uf_destino):
        df_impostos = pd.read_excel(self.impostos_path, sheet_name="ICMS")
        taxa_ICMS = df_impostos[uf_destino][df_impostos['UF'] == uf_origem].iloc[0]
        return taxa_ICMS
