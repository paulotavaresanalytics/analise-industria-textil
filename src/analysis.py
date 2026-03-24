import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
REPORTS_DIR = BASE_DIR / 'reports'
FIG_DIR = REPORTS_DIR / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    produtos = pd.read_csv(DATA_DIR / 'produtos.csv')
    vendas = pd.read_csv(DATA_DIR / 'vendas_mensais.csv')
    estoque = pd.read_csv(DATA_DIR / 'estoque_mensal.csv')
    devolucoes = pd.read_csv(DATA_DIR / 'devolucoes.csv')
    return produtos, vendas, estoque, devolucoes

def giro_estoque_por_colecao(estoque):
    estoque = estoque.copy()
    estoque['estoque_medio'] = (estoque['estoque_inicial'] + estoque['estoque_final']) / 2
    resultado = estoque.groupby('colecao', as_index=False).agg(quantidade_vendida=('quantidade_vendida', 'sum'), estoque_medio=('estoque_medio', 'mean'))
    resultado['giro_estoque'] = (resultado['quantidade_vendida'] / resultado['estoque_medio']).round(2)
    return resultado.sort_values('giro_estoque', ascending=False)

def previsao_demanda_estacao(vendas):
    historico = vendas.groupby('estacao', as_index=False)['quantidade_vendida'].sum()
    ordem = ['Verão', 'Outono', 'Inverno', 'Primavera']
    historico['ord'] = historico['estacao'].map({s: i for i, s in enumerate(ordem)})
    historico = historico.sort_values('ord').drop(columns='ord')
    historico['previsao_proxima_temporada'] = (historico['quantidade_vendida'] * 1.08).round().astype(int)
    return historico

def produtos_mais_vendidos(vendas, produtos):
    base = vendas.merge(produtos, on='sku', how='left')
    return base.groupby(['sku', 'produto'], as_index=False).agg(quantidade_vendida=('quantidade_vendida', 'sum'), receita_bruta=('receita_bruta', 'sum')).sort_values(['quantidade_vendida', 'receita_bruta'], ascending=False)

def devolucoes_por_produto(vendas, devolucoes, produtos):
    vendidos = vendas.groupby('sku', as_index=False)['quantidade_vendida'].sum()
    devolvidos = devolucoes.groupby('sku', as_index=False)['quantidade_devolvida'].sum()
    resultado = vendidos.merge(devolvidos, on='sku', how='left').fillna(0)
    resultado = resultado.merge(produtos[['sku', 'produto']], on='sku', how='left')
    resultado['taxa_devolucao_pct'] = (resultado['quantidade_devolvida'] / resultado['quantidade_vendida'] * 100).round(2)
    return resultado.sort_values('taxa_devolucao_pct', ascending=False)

def margem_por_peca(produtos):
    resultado = produtos.copy()
    resultado['margem_unitaria_rs'] = (resultado['preco_venda'] - resultado['custo_unitario']).round(2)
    resultado['margem_pct'] = ((resultado['margem_unitaria_rs'] / resultado['preco_venda']) * 100).round(2)
    return resultado.sort_values('margem_unitaria_rs', ascending=False)

def salvar_graficos(giro, top_produtos, devolucoes, previsao):
    plt.figure(figsize=(8, 4.5))
    plt.bar(giro['colecao'], giro['giro_estoque'])
    plt.title('Giro de estoque por coleção')
    plt.ylabel('Índice de giro')
    plt.xticks(rotation=20, ha='right')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'giro_estoque_por_colecao.png', dpi=160)
    plt.close()

    top10 = top_produtos.head(10).sort_values('quantidade_vendida')
    plt.figure(figsize=(8, 5))
    plt.barh(top10['produto'], top10['quantidade_vendida'])
    plt.title('Top 10 produtos mais vendidos')
    plt.xlabel('Unidades vendidas em 2025')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'top_produtos.png', dpi=160)
    plt.close()

    top_ret = devolucoes.head(10).sort_values('taxa_devolucao_pct')
    plt.figure(figsize=(8, 5))
    plt.barh(top_ret['produto'], top_ret['taxa_devolucao_pct'])
    plt.title('Top 10 maiores taxas de devolução')
    plt.xlabel('Taxa de devolução (%)')
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'devolucoes_por_produto.png', dpi=160)
    plt.close()

    plt.figure(figsize=(8, 4.5))
    plt.plot(previsao['estacao'], previsao['quantidade_vendida'], marker='o', label='Histórico 2025')
    plt.plot(previsao['estacao'], previsao['previsao_proxima_temporada'], marker='o', label='Previsão próxima temporada')
    plt.title('Demanda por estação: histórico e previsão')
    plt.ylabel('Unidades')
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / 'previsao_demanda_estacao.png', dpi=160)
    plt.close()

def main():
    produtos, vendas, estoque, devolucoes = load_data()
    giro = giro_estoque_por_colecao(estoque)
    previsao = previsao_demanda_estacao(vendas)
    top_produtos = produtos_mais_vendidos(vendas, produtos)
    ret = devolucoes_por_produto(vendas, devolucoes, produtos)
    margem = margem_por_peca(produtos)
    giro.to_csv(REPORTS_DIR / 'giro_estoque_por_colecao.csv', index=False)
    previsao.to_csv(REPORTS_DIR / 'previsao_demanda_estacao.csv', index=False)
    top_produtos.to_csv(REPORTS_DIR / 'produtos_mais_vendidos.csv', index=False)
    ret.to_csv(REPORTS_DIR / 'devolucoes_por_produto.csv', index=False)
    margem.to_csv(REPORTS_DIR / 'margem_por_peca.csv', index=False)
    salvar_graficos(giro, top_produtos, ret, previsao)
    print('Análise concluída. Arquivos salvos em /reports.')

if __name__ == '__main__':
    main()
