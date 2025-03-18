import pandas as pd

class Custos:
    def __init__(self, VALOR, REGIME, COFINS, PIS, ICMS_compra, ICMS_venda, IRPJ, CSLL, IPI, CUSTO_FINANCEIRO):
        self.VALOR = VALOR
        self.REGIME = REGIME
        self.COFINS = COFINS
        self.PIS = PIS
        self.ICMS_compra = ICMS_compra
        self.ICMS_venda = ICMS_venda
        self.CSLL = CSLL
        self.IRPJ = IRPJ
        self.IPI = IPI
        self.CUSTO_FINANCEIRO = CUSTO_FINANCEIRO
        
    def precificacao(self, CUSTO_TOTAL, MARGEM):
        
        if self.REGIME == 'Lucro presumido':
            preco = CUSTO_TOTAL / (1 - (self.ICMS_venda + ((self.COFINS + self.PIS) * (1 - self.ICMS_venda)) + (self.CUSTO_FINANCEIRO) + (MARGEM) + (self.IRPJ + self.CSLL)))
            return preco
        elif self.REGIME == 'Lucro real':
            preco = CUSTO_TOTAL / (1 - (self.ICMS_venda + ((self.COFINS + self.PIS) * (1 - self.ICMS_venda)) + (self.CUSTO_FINANCEIRO) + (MARGEM / (1 - (self.IRPJ + self.CSLL)))))
            return preco

    def custo_BIN(self, preco_BIN, peso_BIN):
        custo_BIN = preco_BIN * peso_BIN
        return custo_BIN
    
    def custo_total(self):
        PIS_COFINS = self.PIS + self.COFINS

        valor_PIS_COFINS = (self.VALOR / (1 - PIS_COFINS)) * PIS_COFINS
        valor_ICMS = ((self.VALOR + valor_PIS_COFINS) / (1 - self.ICMS_compra)) * self.ICMS_compra
        valor_IPI = (self.VALOR + valor_PIS_COFINS + valor_ICMS) * self.IPI

        preco_minimo = self.VALOR + valor_ICMS + valor_PIS_COFINS + valor_IPI

        if self.REGIME == 'Lucro presumido':
            custo_final = preco_minimo - valor_ICMS
            return custo_final
        else:
            custo_final = preco_minimo - valor_ICMS - valor_PIS_COFINS
            return custo_final