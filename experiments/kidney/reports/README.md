# Relatórios — Litíase Renal no SUS-SP

Série de relatórios baseados na análise de 206.500 internações por cálculo renal (CID-10 N20) no Estado de São Paulo, 2016–2025.

---

## Índice

| # | Relatório | Pergunta de Pesquisa | Achado Principal |
|---|---|---|---|
| 02 | [Visão Geral](02_general_overview.md) | Como é o cenário? | CAGR 9,2%, LOS caiu 25%, mortalidade estável |
| 03 | [Drivers de Volume](03_volume_drivers.md) | O que impulsiona o volume? | Portaria 1.127/2020 (ureteroscopia) = 63,7% do crescimento |
| 04 | [Eficiência Hospitalar](04_hospital_efficiency.md) | O que é um hospital eficiente? | Hospital importa 1,9x mais que procedimento |
| 05 | [Análise Financeira](05_financial_analysis.md) | Onde se perde dinheiro? | R$41,8M em custo excedente (22%), prêmio de internação até 22x |
| 06 | [Economia de Leitos](06_bed_savings.md) | Quantos leitos se libera? | 268.608 leitos-dia (cenário conservador, 52,9%) |
| 07 | [Mortalidade](07_mortality_outcomes.md) | Podemos reduzir mortes? | LOS >7d = mortalidade 21x maior, ~340 vidas salvávies |
| 08 | [Velocidade de Resolução](08_resolution_speed.md) | O que torna o tratamento mais rápido? | Eletiva + cirúrgica + hospital com capacidade |
| 09 | [Modelos ML](09_ml_models.md) | O que os modelos predizem? | AUC 0,78 para longa permanência, idade é principal fator |
| 10 | [Resumo Executivo](10_executive_summary.md) | Síntese para decisores | 9 recomendações em 3 horizontes temporais |
| 11 | [Penalidade de Urgência](11_emergency_penalty.md) | Urgência é falha do sistema? | Todas as 20 comparações significativas, 114K leitos-dia excedentes |
| 12 | [Incentivo vs Qualidade](12_incentive_quality.md) | Incentivos desalinhados degradam? | Q4 desperdício = LOS 75% maior, diagnóstico-heavy = cirurgia 64% pior |

---

## Como Ler

1. **Comece pelo [Resumo Executivo](10_executive_summary.md)** — visão em 5 minutos
2. Para entender o contexto, leia a [Visão Geral](02_general_overview.md) e os [Drivers de Volume](03_volume_drivers.md)
3. Para recomendações de política pública, foque nos relatórios 11 e 12 (novas perguntas de pesquisa)
4. Para detalhes técnicos, consulte cada relatório individual

## Reprodutibilidade

Todos os números traçam de volta a uma célula de notebook. Os notebooks estão em `notebooks/` e podem ser re-executados com:

```bash
cd experiments/kidney/notebooks
jupyter nbconvert --to notebook --execute XX_notebook_name.ipynb
```

## Dados

- **Fonte primária:** SIH AIH Reduzida (DATASUS), filtrado para CID-10 N20
- **Período:** Janeiro 2016 – Dezembro 2025
- **Estado:** São Paulo
- **Enriquecimento:** CNES (unidades), SIA (ambulatorial)
