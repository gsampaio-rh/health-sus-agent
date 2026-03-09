# Relatório 05 — Análise Financeira (RQ3)

> **Pergunta de Pesquisa:** Onde o sistema está perdendo dinheiro?

**Notebook:** `notebooks/05_financial_analysis.ipynb`
**Tipo:** Análise de custos com decomposição por categoria e comparação SIH/SIA
**Escopo:** R$187,8M em custo total · 206.500 internações · 13 procedimentos com comparação ambulatorial

---

## Método

1. **Custo por categoria de procedimento** — decomposição do custo total por categoria funcional
2. **Custo excedente de longas permanências** — para cada internação, computar os dias acima da mediana da categoria e estimar o custo excedente
3. **Prêmio de internação SIH vs SIA** — comparar a remuneração do mesmo procedimento quando realizado em internação (SIH) vs ambulatorial (SIA)
4. **Variação de custo entre hospitais** — distribuição do custo médio por hospital dentro de grupos de comparabilidade

---

## Principais Achados

### 1. Distribuição de Custos por Categoria

O custo total do sistema para litíase renal no SUS-SP é de **R$187,8 milhões** (2016–2025).

| Categoria | Custo Total | Participação | Custo Médio | LOS Médio |
|---|---|---|---|---|
| CIRÚRGICO | R$87,2M | **46,4%** | R$983 | 2,61d |
| MANEJO CLÍNICO | R$35,1M | 18,7% | R$1.508 | 2,39d |
| MANEJO CIRÚRGICO | R$25,6M | 13,6% | R$1.244 | 2,25d |
| INTERVENCIONISTA | R$19,6M | 10,5% | R$977 | 2,13d |
| DIAGNÓSTICO | R$15,3M | **8,1%** | R$369 | 2,69d |
| OUTROS | R$3,8M | 2,0% | R$1.074 | 4,03d |
| OBSERVAÇÃO | R$1,2M | 0,6% | R$135 | 0,58d |

Procedimentos cirúrgicos dominam o custo (46,4%), mas o Manejo Clínico tem o maior custo médio por internação (R$1.508) — são pacientes complexos que demandam cuidado prolongado sem resolução cirúrgica.

Internações diagnósticas representam apenas 8,1% do custo, mas 20,1% do volume — são baratas por unidade (R$369), mas sua quantidade massiva gera ocupação de leitos.

![Custo por Categoria](../outputs/notebook-plots/05_cost_by_category.png)

### 2. R$41,8M em Custo Excedente (22,2%)

Estimamos que **22,2%** do custo total é excedente — proveniente de dias de internação acima da mediana para cada categoria de procedimento.

| Métrica | Valor |
|---|---|
| Custo total do sistema | R$187,8M |
| Custo excedente estimado | **R$41,8M** |
| Participação excedente | **22,2%** |
| Leitos-dia excedentes | **212.761** |

Isso significa que mais de um quinto de todo o gasto com litíase renal financia dias de internação além do necessário. A redução do LOS para a mediana de cada categoria geraria uma economia teórica de R$41,8M e liberaria 212.761 leitos-dia.

![Custo Excedente](../outputs/notebook-plots/05_excess_cost.png)

### 3. Prêmio de Internação — Até 22x Mais Caro que Ambulatorial

13 procedimentos realizados em internações por cálculo renal também são realizados ambulatorialmente. A comparação de remuneração revela incentivos perversos:

| Procedimento | Custo SIH | Custo SIA | Prêmio |
|---|---|---|---|
| Manejo Clínico | R$718 | R$33 | **22,0x** |
| Exploração Renal | R$2.030 | R$105 | **19,3x** |
| Ureterolitotomia Aberta | R$735 | R$132 | **5,6x** |

A Ureterolitotomia Aberta — o procedimento mais realizado (40.973 internações) — custa 5,6x mais quando feito em internação comparado ao ambulatorial. Para os 40.973 casos, isso representa uma diferença potencial de R$24,7M em remuneração.

**Ressalva importante:** Nem toda internação é evitável. Muitos casos requerem internação por razões clínicas legítimas (anestesia geral, monitoramento pós-operatório, complicações). A comparação SIH/SIA identifica o **incentivo financeiro**, não necessariamente o **desperdício real**.

![Prêmio de Internação](../outputs/notebook-plots/05_admission_premium.png)

### 4. Variação de Custo Entre Hospitais

O custo médio por internação varia significativamente entre hospitais dentro do mesmo grupo de comparabilidade, refletindo diferenças no mix de procedimentos, na gravidade dos casos e na eficiência operacional.

![Variação de Custo Hospitalar](../outputs/notebook-plots/05_hospital_cost_variation.png)

---

## Discussão

**Resposta à RQ3:** O sistema perde dinheiro em duas frentes: (1) **longas permanências** que geram R$41,8M em custo excedente (22,2% do total), e (2) **incentivos de faturamento** que tornam a internação até 22x mais lucrativa que o atendimento ambulatorial para os mesmos procedimentos.

O custo excedente de R$41,8M é uma estimativa conservadora — usa a mediana da categoria como referência, não o melhor resultado possível. Se hospitais com LOS acima do percentil 75 igualassem a mediana, a economia real seria menor que os R$41,8M teóricos, mas ainda assim substancial.

O prêmio de internação é o achado mais preocupante do ponto de vista de política pública. Quando o SUS paga R$735 por uma Ureterolitotomia em internação mas apenas R$132 pelo mesmo procedimento ambulatorial, há um incentivo estrutural para internar. Isso não significa que hospitais estão agindo de má-fé — o sistema de remuneração é que está desalinhado.

**Implicação acionável:** Duas alavancas principais: (1) reduzir longas permanências nos hospitais com pior desempenho (ver RQ2), e (2) rever a tabela SIGTAP para reduzir o diferencial de remuneração entre internação e ambulatorial para procedimentos diagnósticos.

## Ameaças à Validade

- **Custo excedente é estimativa teórica:** Usar a mediana como referência assume que metade das internações são "excessivas", o que não é clinicamente verdadeiro. Muitos pacientes acima da mediana têm justificativa clínica para maior permanência
- **Amostragem do SIA:** A comparação SIH/SIA usa 6 meses de dados ambulatoriais — uma amostra parcial do volume real
- **Custo SIH ≠ custo real:** O `VAL_TOT` do SIH é o valor pago pelo SUS, não o custo real do hospital. Hospitais filantrópicos e públicos frequentemente operam com custos superiores ao reembolso
- **Mix de procedimentos confunde custo hospitalar:** Hospitais com maior custo médio podem simplesmente realizar procedimentos mais complexos (ex.: nefrectomias vs urografias)
- **Prêmio de internação não mede desperdício:** Alguns procedimentos classificados como ambulatoriais no SIA podem requerer internação em casos específicos (complicações, idade avançada, comorbidades)

---

## Glossário

| Sigla | Significado |
|---|---|
| **LOS** | Length of Stay — tempo de permanência hospitalar (em dias) |
| **SUS** | Sistema Único de Saúde — sistema público de saúde brasileiro |
| **SIH** | Sistema de Informações Hospitalares — base de dados de internações |
| **SIA** | Sistema de Informações Ambulatoriais — base de dados ambulatoriais |
| **SIGTAP** | Sistema de Gerenciamento da Tabela de Procedimentos do SUS |
| **CNES** | Cadastro Nacional de Estabelecimentos de Saúde |
| **VAL_TOT** | Valor total da internação — campo do SIH com o valor pago pelo SUS |
| **BRL / R$** | Real brasileiro — moeda corrente |
| **RQ** | Research Question — pergunta de pesquisa |
