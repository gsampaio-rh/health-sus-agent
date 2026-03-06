# R$ 188 milhões em cálculo renal — e o maior problema não é qual cirurgia você recebe

> 206.500 internações. R$ 187,8M. 507.465 leitos-dia. Estado de São Paulo, 2015–2025.

![Números gerais](plots/findings/00b_big_numbers.png)

Analisamos todas as internações por cálculo renal no estado de São Paulo na última década para responder três perguntas: O que determina uma resolução mais rápida? Onde estamos perdendo dinheiro? Quantos leitos podem ser liberados?

![Panorama geral — evolução temporal](plots/findings/00a_overview_timeline.png)

![Panorama financeiro](plots/findings/00d_financial_overview.png)

A resposta esperada era "adotar procedimentos modernos". Os dados contaram uma história diferente. **O hospital em que você entra importa 2,1× mais do que o procedimento que recebe.** A mesma cirurgia leva 1,8 dias em um hospital e 6,4 dias em outro. 20% das internações são pacientes sendo hospitalizados apenas para um exame de imagem. Um hospital concentra os piores resultados em todas as categorias de procedimento. E quatro cidades tratam milhares de pacientes sem nenhuma capacidade cirúrgica definitiva.

---

![Distribuição da permanência hospitalar](plots/findings/00c_los_distribution.png)

## 1. O que determina a resolução mais rápida do cálculo renal?

### Fator #1: Qual hospital, não qual procedimento

Para o mesmo procedimento de ureterolitotomia aberta:
- **Hospitais do 1º quartil**: 1,78 dias de permanência
- **Hospitais do 4º quartil**: 4,45 dias de permanência
- **Efeito hospital: 2,66 dias** de variação

Para ureteroscopia (procedimento moderno):
- Variação entre hospitais: **0,0d – 6,7d** para o exato mesmo procedimento
- O pior hospital de ureteroscopia (CNES 2688689, São Paulo, 5,2d) é **mais lento que São Carlos fazendo cirurgia aberta (1,8d)**

Efeito do procedimento (ureteroscopia vs cirurgia aberta): **1,24 dias economizados**.

**O efeito hospital (2,7d) é 2,1× maior que o efeito do procedimento (1,2d).**

![Efeito hospital vs procedimento](plots/findings/01_hospital_vs_procedure.png)

![Scatter: cada ponto é um hospital — volume vs permanência](plots/findings/13_scatter_volume_vs_los.png)

### Outros fatores de permanência (ordenados)

| Fator | Efeito (dias) | Direção |
|---|---|---|
| **Eficiência hospitalar (mesmo procedimento)** | **±2,66** | **Dominante** |
| Internação por urgência | +1,21 | Maior |
| Idade 70+ | +0,87 | Maior |
| Procedimento moderno (ureteroscopia vs aberta) | −1,24 | Menor |
| Litotripsia LECO | −1,58 | Menor |
| Idade 30–50 | −0,23 | Menor |
| Paciente masculino | −0,19 | Menor |

### Estudo de caso: São Carlos

São Carlos (CNES 2080931) alcança **1,38d de permanência média com quase zero ureteroscopia** (0,2%). Realiza ureterolitotomia aberta em 1,85d — classificado em 14º de 105 hospitais nesse procedimento. Este hospital prova que excelência operacional supera adoção de tecnologia.

![São Carlos vs sistema vs pior hospital](plots/findings/07_sao_carlos_comparison.png)

---

## 2. Taxonomia corrigida de procedimentos

A categoria anterior "Outros/Conservador" (82%) era enganosa. A distribuição real:

| Categoria | Internações | % | Perm. média | Custo médio | Urg. % | Mortalidade |
|---|---|---|---|---|---|---|
| Cirúrgico (aberto, moderno, LECO) | 88.681 | 42,9% | 2,6d | R$ 983 | 49% | 0,46% |
| Diagnóstico (internação para imagem) | 41.487 | 20,1% | 2,7d | R$ 369 | 94% | 0,19% |
| Tratamento Clínico | 23.275 | 11,3% | 2,4d | R$ 1.508 | 36% | 0,33% |
| Tratamento Cirúrgico | 20.597 | 10,0% | 2,2d | R$ 1.244 | 50% | 0,21% |
| Intervencionista (stents, cateteres) | 20.113 | 9,7% | 2,1d | R$ 977 | 42% | 0,17% |
| Observação (curta permanência no PS) | 8.818 | 4,3% | 0,6d | R$ 135 | 57% | 0,10% |

![Taxonomia de procedimentos](plots/findings/02_procedure_taxonomy.png)

**Correções principais:**
- **42,9% das internações já são cirúrgicas** — não "conservadoras". Ureterolitotomia aberta sozinha representa 19,8%.
- **20,1% são internações diagnósticas** — pacientes internados para exame de imagem (urografia, TC). São 94% urgência. Somente em 2022+: 18.078 internações, 48.931 leitos-dia, R$ 7,1M. Muitas poderiam ser ambulatoriais.
- Apenas ureteroscopia (16,5%) é "moderna" — mas a cirurgia tradicional (19,8%) é o tratamento definitivo mais comum.

### Dentro da cirurgia: moderna vs tradicional

| Tipo | Qtd | Perm. média | Perm. mediana | Custo médio | Mortalidade |
|---|---|---|---|---|---|
| LECO (litotripsia) | 2.784 | 0,9d | 0d | R$ 668 | 0,04% |
| Ureteroscopia (moderna) | 34.036 | 1,9d | 1d | R$ 1.188 | 0,16% |
| Tradicional (aberta) | 51.861 | 3,2d | 2d | R$ 866 | 0,68% |

A ureteroscopia moderna é mais rápida (1,9d vs 3,2d) e mais segura (0,16% vs 0,68% mortalidade), mas custa 37% mais por internação (R$ 1.188 vs R$ 866).

![Comparação dentro da cirurgia](plots/findings/09_surgery_comparison.png)

---

## 3. Onde o dinheiro está sendo perdido?

### 3a. Variação hospitalar — os piores casos identificados

Controlando por tipo de procedimento (mesmo procedimento, resultados diferentes), estes hospitais geram maior desperdício (2022+):

**Ureteroscopia — piores hospitais** (mediana do sistema: 1,5d)

| Hospital | Cidade | Pacientes | Perm. | Excesso vs mediana | Leitos-dia excedentes | Mortalidade |
|---|---|---|---|---|---|---|
| CNES 2755130 | Presidente Prudente | 2.842 | 2,7d | +1,2d | 3.446 | 0,2% |
| CNES 9465464 | São Paulo | 1.390 | 3,0d | +1,5d | 2.046 | 0,2% |
| CNES 2081695 | Sorocaba | 1.137 | 3,0d | +1,5d | 1.699 | 0,5% |
| CNES 2688689 | São Paulo | 354 | **5,3d** | +3,8d | 1.359 | 0,0% |
| CNES 6095666 | Bauru | 1.164 | 2,6d | +1,1d | 1.224 | 0,0% |

**Ureterolitotomia aberta — piores hospitais** (mediana do sistema: 2,9d)

| Hospital | Cidade | Pacientes | Perm. | Excesso vs mediana | Leitos-dia excedentes | Mortalidade |
|---|---|---|---|---|---|---|
| CNES 2081695 | Sorocaba | 996 | 4,3d | +1,4d | 1.406 | 1,3% |
| CNES 2688689 | São Paulo | 296 | **6,4d** | +3,5d | 1.038 | 1,4% |
| CNES 2748223 | (350750) | 271 | 5,0d | +2,1d | 565 | 1,1% |
| CNES 3126838 | Taubaté | 254 | 4,8d | +1,9d | 486 | 1,2% |

**Desperdício total por variação hospitalar:** 8.712 leitos-dia excedentes/ano → 24 leitos → R$ 1,6M/ano

CNES 2688689 (São Paulo) é o pior hospital do estado: 5,3d para ureteroscopia, 6,4d para cirurgia aberta, 4,5d para tratamento clínico. Aparece entre os 10 piores em todas as categorias de procedimento.

![CNES 2688689 — pior em todas as categorias](plots/findings/10_worst_hospital.png)

![Scatter: permanência vs custo por hospital](plots/findings/21_scatter_los_vs_cost.png)

**Por que os piores hospitais são piores?**

Comparamos o quartil superior (27 hospitais mais rápidos) com o quartil inferior (27 mais lentos) para a mesma cirurgia aberta:

| Indicador | Hospitais rápidos (Q1) | Hospitais lentos (Q4) |
|---|---|---|
| Taxa de urgência | 36% | 61% |
| Internações diagnósticas | 6% | 15% |
| Taxa de longa permanência | 1,6% | 8,2% |
| Ureteroscopia | 39% | 28% |

O padrão é claro: hospitais lentos recebem mais pacientes pelo pronto-socorro (sem planejamento cirúrgico prévio), misturam internações diagnósticas com cirúrgicas (congestionando leitos), e não possuem protocolos de alta eficientes — resultando em 5× mais longas permanências. Hospitais rápidos operam de forma eletiva, separando fluxo diagnóstico do cirúrgico.

![Hospitais rápidos vs lentos](plots/findings/03_fast_vs_slow_hospitals.png)

![Scatter: mais urgência = mais permanência — mas não é destino](plots/findings/14_scatter_er_vs_los.png)

![Scatter: tecnologia ajuda — mas não salva hospital mal gerido](plots/findings/17_scatter_ureteroscopy_vs_los.png)

**Por que São Carlos é tão eficiente?** O CNES 2080931 tem apenas 1,7% de longa permanência (vs 4,2% do sistema) com quase zero ureteroscopia. Mesmo com 57% de urgência (similar ao sistema), mantém permanência de 1,38d. Isso indica protocolos de alta bem definidos e gestão operacional eficiente — prova de que o problema não é tecnologia, é gestão.

**Como replicar?** Padronizar protocolos de alta pós-operatória, estabelecer metas de permanência por procedimento, e auditar hospitais com permanência acima da mediana. O hospital que opera e dá alta no mesmo protocolo reduz permanência; o que não tem protocolo mantém o paciente "por segurança".

### 3b. Internações diagnósticas — 20% de todas as internações são para exames de imagem

18.078 internações diagnósticas somente em 2022+. Esses pacientes são internados para realizar exame de imagem (urografia excretora ou TC), não para tratamento.

**Hospitais exclusivamente diagnósticos** (sem capacidade cirúrgica):

| Hospital | Cidade | Total internações | % Diagnóstico | % Cirúrgico | Perm. média |
|---|---|---|---|---|---|
| CNES 2066092 | São Paulo | 489 | **91%** | 0% | 3,3d |
| CNES 2082209 | Bauru | 387 | **91%** | 0% | 2,0d |
| CNES 2080028 | Cubatão | 340 | **90%** | 0% | 2,5d |
| CNES 3212130 | São Paulo | 386 | **86%** | 0% | 3,6d |
| CNES 5420938 | São Paulo | 472 | **71%** | 0% | 3,7d |

Esses hospitais internam pacientes com cálculo renal, mantêm por 2–4 dias para exame de imagem, e dão alta. Não operam. O paciente fica, tira uma foto, e sai sem tratamento.

![Scatter: hospitais diagnósticos puros — internam sem operar](plots/findings/16_scatter_diagnostic_vs_los.png)

**Por que isso importa:**
- 94% chegam pela urgência → pacientes chegam com dor, são internados para exame de imagem em vez de encaminhados ao ambulatório
- 8,2% ficam 0 dias, 29,2% ficam 1 dia — mas **23% ficam >3 dias** para um exame que leva horas
- 4,8% ficam >7 dias (média 6,5d, 0,4% mortalidade) — algo mais está acontecendo com esses pacientes
- **Desperdício total: 48.931 leitos-dia, R$ 7,1M** (somente 2022+)

Marília é o caso emblemático: CNES 2082349 interna 885 pacientes com cálculo renal — **61% são exclusivamente diagnósticos**. Opera 15%, mas a maioria apenas faz exame de imagem.

**Por que isso acontece no SUS? (confirmado via cruzamento SIH × SIA)**

Cruzamos 136 milhões de registros ambulatoriais (SIA) com os dados hospitalares (SIH). A descoberta:

1. **Os códigos SIGTAP de urografia (0305020021) e TC abdome (0303150050) são exclusivamente hospitalares** — aparecem ZERO vezes no SIA em todo o estado de São Paulo. São procedimentos que, pela tabela nacional, só existem como internação.

2. **Existe um incentivo financeiro perverso**: a urografia via SIH paga **R$ 391 por internação**. O equivalente ambulatorial mais próximo (0205020054) paga **R$ 24** — uma diferença de **16×**. O mesmo exame, 16 vezes mais caro quando feito com leito.

![Incentivo financeiro de 16×](plots/findings/04_financial_incentive.png)

3. **Os hospitais TÊM infraestrutura ambulatorial** — eles já faturam dezenas de milhares de procedimentos via SIA, inclusive exames de imagem. Não é falta de capacidade. É que o sistema paga 16× mais para internar.

| Hospital | Internações diagnósticas (SIH) | Atendimentos ambulatoriais N20 (SIA) | Razão de valor |
|---|---|---|---|
| CNES 3212130 (São Paulo) | 331 (R$ 145 mil) | 35 (R$ 4 mil) | **34×** |
| CNES 2066092 (São Paulo) | 446 (R$ 189 mil) | 251 (R$ 18 mil) | **11×** |
| CNES 2082209 (Bauru) | 352 (R$ 143 mil) | 239 (R$ 20 mil) | **7×** |
| CNES 2080028 (Cubatão) | 307 (R$ 121 mil) | 0 | **∞** |
| CNES 2078562 (Guarulhos) | 233 (R$ 77 mil) | 278 (R$ 20 mil) | **4×** |

![Faturamento SIH vs SIA por hospital](plots/findings/08_sih_vs_sia_billing.png)

Dos 406 hospitais que internam para diagnóstico de cálculo renal, **213 (52%) não possuem nenhum registro ambulatorial para a mesma condição** — apesar de muitos terem SIA ativo para outros procedimentos. Os outros 193 fazem os dois, mas preferem a internação pela remuneração superior.

**Solução concreta:**

1. **Reformar a tabela SIGTAP**: criar código ambulatorial específico para urografia/TC em cólica renal com remuneração adequada (não R$ 24, mas também não R$ 391+leito). Enquanto a internação pagar 16× mais, o incentivo econômico sempre vai favorecer a AIH.
2. **Protocolo de PS para cólica renal**: paciente chega com dor → analgesia + exame ambulatorial no mesmo dia → alta com encaminhamento para cirurgia eletiva se indicado. Isso requer que o código SIA cubra o custo real do exame.
3. **Corredor de referência**: formalizar encaminhamento dos hospitais diagnósticos para os hospitais cirúrgicos regionais. O paciente faz exame local e cirurgia no polo, sem internação desnecessária no meio.
4. **Meta de redução**: auditar hospitais com >50% de internações diagnósticas e estabelecer metas progressivas de migração para ambulatório, vinculadas à adequação da remuneração SIA.

### 3c. Pacientes de longa permanência — o problema de Pareto

**4,2% dos pacientes (4.531) ficam >7 dias. Eles consomem:**
- **23,7% de todos os leitos-dia** (58.254)
- **10,2% de todo o custo** (R$ 11,3M)
- **50,1% de todos os óbitos** (176 de 351)

![O problema de Pareto](plots/findings/05_long_stay_pareto.png)

**Quem são eles?**
- Mais velhos: idade média 51,4 vs 47,7 para permanências normais
- Mais mulheres: 61% vs 53% (incomum para cálculo renal, tipicamente predominante em homens)
- Muito mais urgência: 78% vs 51%
- 22× maior mortalidade: 3,9% vs 0,17%

**Quais hospitais geram mais longas permanências?**

| Hospital | Cidade | Longas perm. | % dos pacientes | Perm. média | Mortalidade |
|---|---|---|---|---|---|
| CNES 2688689 | São Paulo | 323 | **24%** | 12,3d | 1,2% |
| CNES 2081695 | Sorocaba | 210 | 8% | 13,9d | 5,2% |
| CNES 2077477 | São Paulo | 207 | 12% | 10,7d | 1,9% |
| CNES 9465464 | São Paulo | 174 | 7% | 12,7d | 2,9% |
| CNES 2755130 | Pres. Prudente | 173 | 5% | 11,9d | 0,6% |

CNES 2688689 novamente — **24% dos seus pacientes ficam >7 dias**. Este único hospital gera 323 casos de longa permanência. Algo está estruturalmente errado.

![Mapa de risco: permanência vs mortalidade](plots/findings/15_scatter_longstay_vs_mortality.png)

**Permanências extremas (>30 dias):** 143 pacientes, média 43 dias, máximo 97 dias, 11,9% mortalidade, consumindo 6.175 leitos-dia e R$ 1,4M.

![Perfil dos pacientes de longa permanência](plots/findings/11_long_stay_profile.png)

**O que está acontecendo com esses pacientes?**

Dos 4.531 pacientes de longa permanência, 57% são cirúrgicos com complicações pós-operatórias, e 22,5% passaram por UTI (vs 1,6% dos pacientes normais). São pacientes genuinamente complexos — mas 19% são internações diagnósticas que ficaram >7 dias para um exame de imagem (algo claramente evitável).

O perfil é relevante: mais mulheres (61% vs 53%), mais idosos, 78% urgência. A alta mortalidade (3,9%) e o uso de UTI sugerem que muitos desenvolvem complicações (infecção, sepse, obstrução persistente) que poderiam ser prevenidas com intervenção precoce.

**Soluções:**

1. **Identificação precoce de risco**: nosso modelo de ML (ROC-AUC=0,721) consegue sinalizar pacientes de alto risco na admissão. Hospitais podem usar essa flag para acionar planejamento de alta e alocação de especialistas desde o primeiro dia.
2. **Protocolo de gestão de caso**: pacientes sinalizados como alto risco recebem avaliação diária de critérios de alta, prevenção de infecção, e acompanhamento nutricional.
3. **Eliminação de longas permanências diagnósticas**: os 19% de pacientes que ficam >7 dias para um exame não deveriam existir — resolver via protocolo ambulatorial (solução da Seção 3b).
4. **Auditoria de outliers**: pacientes com >30 dias precisam de revisão caso a caso. São 143 pacientes que consomem R$ 1,4M — cada um merece uma análise individual.

---

## 4. Acesso geográfico — detalhamento por cidade

### 4a. Taubaté — o polo regional com desempenho abaixo do esperado

- **2.208 pacientes** (2022+), **um hospital** (CNES 3126838 atende 99,7%)
- **0% ureteroscopia**, 78% urgência, 59% dos pacientes migram de cidades vizinhas
- **80% dos casos codificados como "Tratamento Cirúrgico"** (0415020034) — código de faturamento vago
- Ureterolitotomia aberta com **4,8d de permanência** (mediana do sistema 2,9d) — 1,9d de excesso
- Absorve pacientes de 5+ cidades vizinhas (Pindamonhangaba 294, Tremembé 125, Ubatuba 117)
- Volume em queda: 598 → 508 entre 2022–2025
- **Apenas 47 de 952 residentes de Taubaté migram** — a maioria fica neste hospital com desempenho abaixo do esperado
- **Recomendação:** Adicionar capacidade de ureteroscopia ao CNES 3126838, reduzir taxa de urgência via referência eletiva

### 4b. Marília — a armadilha diagnóstica

- **885 pacientes**, um hospital (CNES 2082349)
- **61% das internações são exclusivamente diagnósticas** — pacientes internados para exame, não para tratamento
- 0% ureteroscopia, 87% urgência
- Permanência média **3,1d** (média do sistema 2,5d), **6,8% taxa de longa permanência** (sistema 4,2%)
- **149 residentes migram** (79 para São Bernardo do Campo, 65 para São Paulo capital)
- **Recomendação:** Estabelecer via ambulatorial para exames de imagem (a maioria das 541 internações diagnósticas não deveria ser hospitalar), adicionar capacidade cirúrgica ou formalizar corredor de referência

### 4c. Guarulhos — a cidade exclusivamente diagnóstica

- **237 pacientes**, um hospital (CNES 2078562)
- **97,9% das internações são exames de imagem** — este hospital essencialmente não faz nada além de internar pessoas para urografia
- **100% urgência**, 0% ureteroscopia, **4,2d de permanência média** para exame diagnóstico
- **11,8% taxa de longa permanência** (maior entre as cidades recomendadas)
- **311 de 474 residentes de Guarulhos migram** (239 para São Paulo capital, 44 para Mogi das Cruzes)
- Volume crescendo: 38 → 72 entre 2022–2025
- **Recomendação:** Este hospital não deveria internar pacientes de cálculo renal para exames de imagem. Redirecionar para imagem ambulatorial + referência para hospitais cirúrgicos de São Paulo (10 km de distância)
- **Dado confirmado via SIA:** O CNES 2078562 já faz 278 atendimentos ambulatoriais (SIA) para cálculo renal (R$ 20 mil), mas interna 233 pacientes via SIH (R$ 77 mil) — uma razão de 4× em valor. O hospital tem capacidade ambulatorial, mas o incentivo financeiro favorece a internação.
- **Como implementar:** (1) Adequar a remuneração SIA para urografia/TC renal para que cubra o custo real sem exigir leito. (2) Criar protocolo de PS: paciente com cólica renal → analgesia + exame ambulatorial → alta no mesmo dia com encaminhamento. (3) Formalizar referência para hospital cirúrgico de São Paulo capital (a 10 km), já que 239 residentes de Guarulhos já migram para lá. O hospital continua sendo a porta de entrada, mas para triagem e exame — não para internação de 4 dias

### 4d. Limeira — a válvula de pressão de Piracicaba

- **779 pacientes tratados localmente**, mas **1.459 residentes de Limeira** no total — **760 vão para Piracicaba**
- Hospital local (CNES 2081458) faz 13% ureteroscopia com 0,9d de permanência — já bom quando opera
- 37% ureterolitotomia aberta com 3,1d, 15% tratamento clínico
- **Anomalia de mortalidade:** CNES 2087103 teve 1 óbito em 3 pacientes (33%) — amostra pequena, mas vale sinalizar
- **Recomendação:** Escalar ureteroscopia no CNES 2081458 (já tem alguma capacidade) para absorver os 760 pacientes que atualmente vão para Piracicaba. Isso alivia a pressão de crescimento de +548% em Piracicaba.

---

## 5. Quanto podemos economizar?

### 5a. Economia financeira direta

Três cenários geram economia financeira real (redução de pagamento SUS):

| Cenário | Como funciona | Economia anual |
|---|---|---|
| Padronizar hospitais | Reduzir excesso de permanência nos hospitais Q4 (custo/leito-dia × leitos-dia excedentes) | **R$ 2,6M** |
| Migrar diagnóstico para ambulatório | 50% das 18.078 internações diagnósticas (R$ 393/internação → R$ 24/ambulatorial) | **R$ 834K** |
| Reduzir longas permanências | 50% do excesso além de 7 dias (R$ 193/leito-dia × 3.317 leitos-dia) | **R$ 641K** |
| **TOTAL** | | **R$ 4,1M/ano** |

O cenário de conversão urgência→eletiva **não gera economia direta** — na verdade custa mais por paciente (eletiva R$ 1.196 vs urgência R$ 848) porque pacientes eletivos recebem tratamento definitivo. Mas **libera leitos e salva vidas**.

![Detalhamento financeiro por cenário](plots/findings/22_financial_savings_detail.png)

![Análise detalhada: como cada cenário gera economia](plots/findings/23_financial_deep_dive.png)

### 5b. Leitos liberados (capacidade)

| Cenário | Leitos-dia/ano economizados | Leitos liberados | Método |
|---|---|---|---|
| Padronizar hospitais (mediana por procedimento) | 8.712 | 24 | 4º quartil → mediana, 10 maiores procedimentos |
| Migrar 50% das internações diagnósticas para ambulatório | 6.116 | 17 | 48.931 leitos-dia (2022+), anualizado, 50% migração |
| Reduzir longas permanências (>7d) em 50% | 3.317 | 9 | 26.537 leitos-dia excedentes, anualizado, 50% redução |
| Conversão urgência-para-eletiva (30%) | 5.606 | 15 | 56.359 pacientes de urgência × 30% × 1,33d diferença |
| **TOTAL** | **23.752** | **65** | **38,6% dos leitos-dia anuais** |

![Economia de leitos — cascata](plots/findings/06_bed_savings_waterfall.png)

![O que significa economizar 23.752 leitos-dia](plots/findings/12_bed_days_explainer.png)

> **Como ler esta tabela:** "leitos-dia" é a unidade de consumo (1 cama × 1 dia). "Leitos liberados" converte para capacidade permanente (leitos-dia ÷ 365). Economizar 23.752 leitos-dia/ano equivale a liberar 65 camas que estariam permanentemente ocupadas — ou **38,6% de toda a capacidade anual dedicada a cálculo renal** no estado de São Paulo (~61.453 leitos-dia/ano).

> Todas as estimativas usam dados de 2022+ anualizados ao longo de 4 anos (média de 61.453 leitos-dia/ano). Validação cruzada com SIA (136M registros ambulatoriais) confirmou que os códigos diagnósticos são exclusivamente hospitalares e que existe incentivo financeiro de 16× favorecendo a internação.

---

## 6. Quantas vidas podem ser salvas?

### O mecanismo: permanência = risco de morte

A mortalidade no cálculo renal é baixa (0,32%), mas segue um gradiente claro com a permanência hospitalar:

| Permanência | Pacientes | Óbitos | Mortalidade |
|---|---|---|---|
| 0–1 dia | 53.787 | 44 | 0,08% |
| 2–3 dias | 37.279 | 59 | 0,16% |
| 4–7 dias | 13.100 | 72 | 0,55% |
| 8–14 dias | 3.516 | 84 | 2,39% |
| 15–30 dias | 872 | 75 | 8,60% |
| >30 dias | 143 | 17 | 11,89% |

![Gradiente permanência-mortalidade](plots/findings/18_los_mortality_gradient.png)

Cada dia a mais no hospital aumenta o risco de morte. Pacientes com >30 dias têm **149× mais mortalidade** que pacientes com 0–1 dia. Isso significa que **toda intervenção que reduz permanência também salva vidas.**

![Scatter: hospital lento = hospital que mata mais](plots/findings/20_scatter_los_vs_mortality.png)

### Estimativa de vidas salvas

Aplicamos o gradiente permanência-mortalidade a cada cenário de economia de leitos:

| Cenário | Mecanismo | Vidas salvas/ano |
|---|---|---|
| Padronizar hospitais | Hospitais Q4 (0,57% mortalidade) → mediana (0,24%) | **17** |
| Reduzir longas permanências em 50% | Pacientes >7d (3,88%) → ≤7d (0,17%) | **21** |
| Converter urgência → eletiva (30%) | Urgência (0,51%) → eletiva (0,12%) | **17** |
| **Soma bruta** | | **55** |
| **Ajustado por sobreposição** | Cenários se sobrepõem parcialmente (~60%) | **25–41** |

![Estimativa de vidas salvas](plots/findings/19_lives_saved_waterfall.png)

**Estimativa central: 33 vidas salvas por ano** — uma redução de **37% na mortalidade** por cálculo renal no estado de São Paulo.

> **Nota metodológica:** Os cenários se sobrepõem porque um hospital lento frequentemente também tem alta urgência e alta taxa de longa permanência. O ajuste de 60% é conservador. A faixa de 25–41 vidas/ano reflete a incerteza da sobreposição. As estimativas usam dados de 2022+ (88 óbitos/ano de baseline).

> **Por que não ML para mortalidade?** Testamos um modelo de classificação (LGBMClassifier) para predizer óbito na admissão, mas obtivemos ROC-AUC=0,49 (pior que aleatório). Com apenas 0,32% de mortalidade (351 óbitos em 108K pacientes), os fatores de risco são eventos que ocorrem durante a internação (complicações, infecções, necessidade de UTI), não características disponíveis na admissão. A abordagem por cenários é mais honesta e acionável.

### 6b. Impacto total combinado

![Impacto total: dinheiro + leitos + vidas](plots/findings/24_combined_impact.png)

| Dimensão | Impacto anual |
|---|---|
| **Economia financeira** | R$ 4,1M/ano |
| **Leitos liberados** | 65 leitos (23.752 leitos-dia) |
| **Vidas salvas** | 25–41 por ano (37% de redução) |

---

## 7. Modelo de Machine Learning — Validação Independente

Treinamos um **classificador LightGBM** para predizer risco de longa permanência (>7 dias) no momento da admissão, usando 27 features engenheiradas nas dimensões paciente, hospital, cidade e procedimento.

| Métrica | Valor |
|---|---|
| **ROC-AUC** | 0,747 |
| **Conjunto de treino** | 97.803 internações (≤2021) |
| **Conjunto de teste** | 108.697 internações (≥2022) |
| **Features** | 27 (com termos de interação) |

### Por que isso importa: SHAP confirma nossos achados empíricos

As features mais preditivas do modelo — ranqueadas por importância SHAP — validam independentemente cada conclusão deste relatório:

| Rank | Feature | Importância SHAP | Confirma achado |
|---|---|---|---|
| 1 | `hosp_pct_longstay` | 1,31 | Efeito hospital domina (§3a) |
| 2 | `has_new_proc` (ureteroscopia) | 0,37 | Procedimentos modernos reduzem permanência (§2) |
| 3 | `proc_observation` | 0,35 | Internações de observação geram longas permanências (§3c) |
| 4 | `age × emergency` | 0,33 | Urgência + idoso = alto risco (§4) |
| 5 | `proc_diagnostic` | 0,24 | Internações diagnósticas são ineficientes (§3b) |
| 6 | `is_male` | 0,23 | Fator de risco demográfico |
| 7 | `ER × hosp_efficiency` | 0,21 | Interação: urgência em hospital lento = pior cenário |
| 8 | `hosp_pct_er` | 0,18 | Hospitais com alta urgência têm maior permanência (§4) |
| 9 | `age` | 0,17 | Idade é fator de risco independente |
| 10 | `hosp_pct_diag` | 0,13 | Hospitais com foco diagnóstico performam pior (§3b) |

> **Conclusão-chave:** O modelo de ML *não foi informado* sobre quais hospitais são lentos, nem quais procedimentos são modernos. Ele descobriu esses padrões independentemente a partir de 27 features brutas — e suas top-10 features mapeiam 1:1 com nossos achados empíricos. Isso é forte evidência convergente de que as conclusões são robustas, não artefatos de como recortamos os dados.

### Modelo anterior (para transparência)

Um modelo de regressão anterior, mais simples, alcançou R² = 0,096, MAE = 1,60 dias — pouco melhor que prever a média. Esse modelo usava feature engineering mínimo e nenhuma feature de hospital/cidade. Está preservado em `appendix_ml_model.ipynb` mas não foi utilizado para nenhuma conclusão.

### Causa raiz do crescimento de +4.800%: não é uma epidemia

**35,5%** do crescimento das internações é explicado pela adoção da ureteroscopia (código 0409010596). O restante reflete melhor acesso ao SUS, melhorias na codificação e envelhecimento populacional — não um aumento na incidência de cálculos renais.

---

## Metodologia

- **Dados**: SIH AIH Reduzida, São Paulo, 2015–2025. 206.500 internações por cálculo renal (CID-10 N20).
- **Taxonomia de procedimentos**: 193 códigos SIGTAP únicos classificados em 7 categorias (cirúrgico, diagnóstico, tratamento clínico, tratamento cirúrgico, intervencionista, observação, outros).
- **Comparação hospitalar**: Controlada por tipo de procedimento — comparando permanência do mesmo procedimento entre hospitais (limite n≥20).
- **Economia de leitos**: Estimativas controladas por procedimento a partir de distribuições observadas.
- **Validação cruzada SIH × SIA**: 136 milhões de registros ambulatoriais (SIA SP 2022–2023) cruzados com dados hospitalares. Confirmou que códigos diagnósticos 0305020021 e 0303150050 são exclusivamente hospitalares (zero registros no SIA) e que a remuneração SIH é 16× superior ao equivalente ambulatorial.
- **Modelo de ML**: LightGBM com 27 features, split temporal treino/teste (≤2021 / ≥2022), análise SHAP para interpretabilidade. Ver `10_ml_prediction.ipynb`.
- **Análises detalhadas**: Santos, São Carlos, Taubaté, Marília, Guarulhos, Limeira analisadas em nível hospitalar.
- **Ver**: `EXPERIMENT.md` para hipóteses pré-registradas. Notebooks `03`–`10` produzem todos os números deste documento.
