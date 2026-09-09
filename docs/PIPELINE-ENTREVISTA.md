# Pipeline de dados e guia para entrevista

## O que esta documentação comprova

Este documento descreve o código disponível nesta cópia. O frontend Angular contém os contratos HTTP e as transformações usadas nas telas. O backend Python original disponível é parcial: contém consultas SQLAlchemy a SQLite e um serviço que já simulava dados. As queries SQL do BigQuery, jobs de ingestão, agendamentos, tabelas completas, permissões e infraestrutura de produção **não estão nesta base**. Não é possível recuperar ou afirmar quais eram as queries exatas de produção a partir dos gráficos.

O comentário do serviço original menciona `vpp001_glb_integrator_prj_vw`, `vpp002_mfg_veh_pgm_vw` e `vpp005_prj_timing_pivot_vw` como possíveis fontes de consolidação. Isso é evidência de uma intenção documentada, não de queries executadas ou de joins implementados. Consulte o inventário de código ao lado para os trechos integrais.

## Arquitetura e rastreabilidade

Fluxo observado no frontend: interação → componente → serviço Angular → GET com filtros → resposta JSON → transformação/agregação → gráfico, tabela ou Excel.

Fluxo executável nesta demonstração: Angular em `localhost:4200` → FastAPI em `127.0.0.1:8000` → `routes/demo_routes.py` → `services/demo_service.py` → registros sintéticos em memória → agregações → JSON. A exportação usa os mesmos registros, serializados com openpyxl. Nenhuma chamada ao BigQuery ocorre.

A organização `front/dandr-web/src/app/{dashboard,services,shared,core}` e `back/app/{routes,controllers,services,models,schemas,core}` foi preservada. As rotas antigas permanecem para consulta, mas `back/app/main.py` registra o adaptador mock. O login MSAL/Entra foi removido da demonstração. Logo, fonte e estilos foram mantidos.

## Chaves e filtros

| Campo | Papel no frontend |
| --- | --- |
| `model_year` | Ano de modelo, usado na pesquisa e classificação de Design Rules |
| `program_codes`, `program_names` | Seleção do programa na pesquisa; observar plural no contrato Angular |
| `gi_code` | Identificador propagado do resumo para os painéis de engenharia |
| `effectivein` | Effective Point usado pelas consultas de custos |
| `pmt_code` ou `pmt` | Recorte de PMT; o nome do parâmetro varia por endpoint |
| `cpsc` | Recorte de commodity |
| `dvp_team` | Equipe de validação |
| `snapshot_date` | Recorte histórico de dados nos endpoints que o recebem |
| `milestone` / `milestone_date` | Marco ou data; não são intercambiáveis automaticamente |

`shared/state.service.ts` distribui programa, GI, marcos, equipe, PMT e painel ativo por observáveis. `dashboard/home/home.ts` coordena os filtros e dispara cargas. O mock trata ausência de alguns filtros como total do programa e usa o último snapshot quando a data não é informada.

## Tela inicial, resumo e cronograma

`VehicleLineService` consulta `/search/model-years`, `/search/program-names` e `/search/program-codes`. A resposta alimenta autocompletes; o frontend aceita anos numéricos no formato YYYY ou YYYY.fração. Search chama `/vehicle-line/` com ano, código e nome opcional.

O frontend exige `summary` e `gi_code`. `parseSummary()` divide o texto por `|` e cada par por `:`; extrai Project Description, PTVL e Effective Point. A planta pode vir do sufixo entre parênteses da descrição. A resposta também fornece `milestones`, `vehicle_line`, `program_code`, `affected_plant`, `plant_code`, `model_year` e `wers_plant`.

O cronograma remove datas vazias/inválidas, transforma os marcos em datas e os ordena para exibição. Key Engineering Dates usa os mesmos marcos disponíveis. No mock, horários locais ao meio-dia evitam que datas do cronograma recuem um dia por conversão UTC.

Limitação importante: o `/vehicle-line/` original em Python recebe parâmetros no singular e retorna um schema diferente do consumido pela versão Angular disponível. Isso comprova que as duas cópias não representam um contrato de produção completo e sincronizado.

## CAE Status

Fonte do painel principal: `VehicleLineService.getCaeTotalAssessments()` → `/fede-status/metrics/cae-total-assessments`, com GI, CPSC opcional e PMT opcional. `/fede-status/cpsc/list` fornece commodities.

`cae-metrics.ts` soma os registros retornados em `data`: `meet`, `unassessed`, `approved_deviation`, `does_not_meet`, carryover/CO e `total_assessments`. As contagens alimentam cards e donut; percentuais dividem a categoria pelo total. A seleção de commodity restringe a consulta.

Há componentes adicionais `cae-status`, `cae-total` e `cae-commodity`. `/metrics/cae-graph` fornece dados por `assessment_id` e `cpsc_code` ao componente de gráfico. Sua existência no código não implica que todos sejam montados simultaneamente pela tela principal.

## DVP Status

Assessment consulta `/fede-status/metrics/conf-state` e lê `conf_state_summary`. Estados: Meet, Unassessed, Approved Deviation, Does Not Meet, Cannot Assess e Not Applicable. O total é a soma das categorias; o percentual de cada categoria usa esse total.

O seletor de equipes usa `/fede-status/dvp-teams/autocomplete/by-gi-code`. O recorte por equipe usa `/fede-status/metrics/dvp-team-list`, procurando a equipe em `dvp_teams_metrics`. Existe ainda `/fede-status/metrics/conf-state-by-dvp-team` e a leitura detalhada `/fede-status/by-dvp-team/row`.

Classification consulta `/api/v1/fede-status/dvp-classification`, com GI, CPSC, snapshot e PMT opcionais conforme o serviço. Campos: `total`, `classified`, `not_classified`, `percentage`. O breakdown por commodity usa `/fede-status/metrics/cpsc-conf-state-breakdown` e `cpsc_metrics`.

Glidepath usa `/api/v1/dvp-glidepath/{pmts,milestones,data,snapshots}`. Cada registro fornece GI, PMT, ano, marco, `scheduled_finished`, `actual_finished` e métricas. O componente transforma datas de término em curvas cumulativas de conclusão. Na demo, datas planejadas e realizadas são sintéticas; as curvas não comprovam desempenho histórico real.

## Design Rules

Evidences consulta `/fede-status/metrics/dr-evidences-by-assessment` com GI, CPSC e PMT. O componente soma `meet`, `does_not_meet` e `unassessed` em `data`. O denominador visual é a soma dessas três categorias.

Classification consulta `/fede-status/metrics/design-rule-classification` com ano, programa e PMT. Soma `applicable`, `carryover`, `not_applicable` e `unclassified`. A soma forma o total e o denominador dos percentuais. Esses estados representam classificação, não o mesmo conceito que conformidade/evidência.

## HIR Status

`FedeStatusService.getHirCompletion()` consulta `/api/v1/fede-status/hir-completion`. Filtros: GI, CPSC, PMT, data do marco e equipe. Registros: `with_evidence`, `without_evidence`, `total_items`, `completion_percentage`, além das dimensões.

`hir-metrics.ts` agrega as contagens e calcula a conclusão a partir de evidências/total. Para totais de vários grupos, a razão entre somas evita a média simples de percentuais com denominadores diferentes. `hir-total` e `hir-commodity` também contêm mocks antigos locais; não confundir esses componentes legados com a fonte HTTP do painel principal.

## DPA5 Status

`Dpa5Service` consulta `/dpa5/summary`, `/dpa5/snapshots` e `/dpa5/cpsc-list`. Parâmetros: GI, commodity, PMT e snapshot conforme o método.

Resumo: `compliant`, `not_compliant`, `not_assessable`, `total`. Glidepath: data e nome do marco, três contagens, `assessment_goal_curve`, `compliance_goal_curve` e `compliance_prediction`. O gráfico converte contagens em percentuais e combina barras de status com curvas de metas/previsão. Valores de meta ausentes permanecem nulos, não significam zero.

Na demo, o resumo é agregado dos registros do snapshot; as curvas de marcos são projeções fictícias. Não apresentar a previsão sintética como um modelo estatístico treinado ou como a regra original do BigQuery.

## Costs Status

PMTs gerais vêm de `/pmt/list`. Os endpoints `/cost/cpsc/list`, `/cost/cpsc/autocomplete` e `/cost/pmt/list` oferecem recortes. `/cost/dropdowns` retorna partnumbers, commodities e vehicle_lines; o comentário original diz que reúne três consultas em uma chamada BigQuery, mas a implementação SQL dessa otimização não foi fornecida.

`/cost/metrics/tooling` e `/cost/metrics/piece` retornam registros por peça com programa, Effective Point, PMT, partnumber, CPSC, nome da commodity, custo real, meta, gap, moeda e referência. `/cost/metrics/combined` reúne os dois conjuntos e os totais para cards.

`costs-status.ts` agrupa por CPSC e depois por peça, somando real, meta e gap para formar linhas expansíveis e total. Os seletores de commodity, Control Model e Part Number restringem a apresentação. No mock, gap = real − meta; valores negativos indicam custo abaixo da meta. Tooling e piece têm naturezas diferentes: o card combinado segue o contrato da interface, mas sua soma não deve ser defendida como custo industrial total sem explicar volumes e unidades.

## Milestone Readiness

`MilestoneReadinessService` consulta `/api/v1/milestone-readiness/{giCode}` com marco e PMT. `milestone-readiness.ts` observa GI, marco e PMT em conjunto. A resposta contém programa, marco, data e `metrics` com `source`, `target`, `actual`, `percentage` e `status`. O painel ativo seleciona a fonte pelo mapeamento CAE/DVP/Design Rules/HIR/Costs/DPA5.

Os thresholds e metas do mock são ilustrativos. O código disponível não contém a regra de negócio original de prontidão no warehouse.

## Exportação

`home.ts` escolhe endpoint, nome XLSX e parâmetros conforme o painel. `ExtractButtonService` faz GET com `responseType: blob`, cria uma URL temporária, baixa o arquivo e revoga a URL. Endpoints: `/export/cae-status`, `/export/dvp-team-assessment`, `/export/hir`, `/export/design-rule`, `/export/costs`, `/export/dpa5`.

Na demo, custos exportam os registros de custo filtrados; os demais exportam avaliações sintéticas filtradas. Uma aba About identifica o mock. Os templates e queries de exportação originais não estão disponíveis.

## Queries realmente presentes

1. `controllers/summary_controller.py`: `db.query(VehicleLine).filter(...)` por código, ano e nome, com `.first()`; depois consulta EffectivePoint por `vehicle_line_id` com `.all()`. Constrói resumo e lista de marcos. Ausência de veículo retorna 404.
2. `services/summary_service.py`: busca VehicleLine pelos mesmos filtros e lê a relação `key_datas` para evento/data.
3. `routes/key_datas_routes.py`: consulta KeyDatas, aplica os filtros implementados no arquivo e retorna a lista.
4. `services/vehicle_line_service.py`: não executa SQL; já era uma simulação na cópia original.

Os trechos integrais estão em `INVENTARIO-CODIGO.md`. Não há SQL BigQuery executável nesta base. Para documentação histórica exata ainda seriam necessários o backend que consultava o warehouse, scripts SQL/dbt/Dataform, definições das views e configuração dos jobs. Não inferir chaves de join, deduplicação, particionamento, atualização incremental ou SLA a partir dos nomes de campos.

## Como apresentar na entrevista

“Este é o dashboard que desenvolvi, preservado em uma versão local com dados sintéticos. Consigo demonstrar a navegação, contratos da API, filtros, agregações e exportação. O acesso corporativo ao warehouse não está nesta versão; o backend mock reproduz os contratos para a demonstração.”

Explique primeiro a granularidade, depois chaves/filtros, contrato HTTP, agregação e validação. Mostre CAE, troque PMT, compare snapshots de DVP, abra custos e exporte Excel. Diferencie o pipeline de apresentação comprovado pelo código do pipeline de ingestão de produção, que precisa ser relatado com base em sua experiência e evidências adicionais.

Validações existentes em `back/tests/test_demo.py`: descoberta de programa, efeito de filtros e snapshots, reconciliação de custos, XLSX sintético e cobertura dos endpoints dos painéis. Compilação Angular e navegação pelos seis painéis foram verificadas localmente. Os testes validam esta demonstração, não equivalência semântica com o warehouse original.
