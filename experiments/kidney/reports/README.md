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
| 09 | [Internações Desnecessárias](09_unnecessary_admissions.md) | Como identificar internações desnecessárias? | 3,2% alta suspeita (R$937k), infraestrutura é o driver |
| 10 | [Realocação de Pacientes](10_patient_reallocation.md) | Como realocar pacientes? | Migrou→eficiente: −0,7d LOS, capacidade limita impacto |
| 11 | [Modelo de Risco Geográfico](11_city_risk_model.md) | Quais municípios falham? | 6/6 validação. 227/489 municípios com gap significativo |
| 12 | [Hospital Report Card](12_hospital_report_card.md) | Quais hospitais falham? | 49 para revisão, 66 referências. ρ=−0,836 vs eficiência simples |
| 13 | [Resumo Executivo](13_executive_summary.md) | Síntese para decisores | Recomendações em 3 horizontes temporais |

---

## Como Ler

1. **Comece pelo [Resumo Executivo](13_executive_summary.md)** — visão em 5 minutos
2. Para entender o contexto, leia a [Visão Geral](02_general_overview.md) e os [Drivers de Volume](03_volume_drivers.md)
3. Para recomendações de política pública, foque nos relatórios 09 e 10 (internações desnecessárias e realocação)
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
