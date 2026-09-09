# D&R Engineering Dashboard — demonstração local

Base atualizada: backend `fix/dpa5-program-filter-snapshot` (`6bcd7ae`) e frontend `develop` (`f24ae41`), de 31/08/2026. Queries BigQuery e scripts originais foram recuperados e preservados; a execução local continua com dados sintéticos.

**[Panorama completo de dados, queries, alimentação e guia para Mac](docs/PANORAMA-DADOS.md)** — inclui um catálogo automático de SQL com links para a função de origem. [Manifesto da importação](docs/SOURCE-VERSIONS.json).

Case de dashboard de engenharia com **Angular + FastAPI**, preservando o layout, logo, fonte e organização `front/` e `back/` do projeto original. Todos os registros exibidos nesta versão são fictícios. A autenticação institucional foi retirada; BigQuery e o banco original não são acessados.

## Rodar em localhost

Requisitos: Python 3.11+, Node.js 22.12+ e pnpm 11. No Mac com o runtime do Codex já instalado, o script também o encontra automaticamente.

```bash
./run-demo.sh
```

O script instala dependências se necessário, compila o Angular e inicia os dois serviços. A primeira instalação requer internet; a demonstração depois funciona localmente. `Ctrl+C` encerra ambos.

- Dashboard: http://localhost:4200
- API e documentação: http://localhost:8000/docs
- Saúde da API: http://localhost:8000/health

Na tela, preencha `Model Year = 2026`, `Program Code = AU-01` e `Program Name = Aurora EV`, depois clique em **Search**. Outra opção é `OR-02 / Orion Hybrid`. Os painéis CAE, Costs, Design Rules, DPA5, DVP e HIR continuam no menu lateral. Exportações geram arquivos Excel com registros sintéticos.

## Estrutura preservada

```text
front/dandr-web/           Angular: componentes, telas, serviços, estilos e imagens
back/app/main.py           API FastAPI da demonstração
back/app/routes/           Rotas originais + adaptador de demonstração
back/app/services/         Serviços originais + geração e agregação de mocks
back/app/models/           Modelos originais preservados
back/app/schemas/          Contratos originais preservados
back/app/controllers/     Controladores originais preservados
back/tests/                Verificação da API e dos mocks
```

Fluxo: **Angular → API HTTP em localhost → registros sintéticos → agregações → gráficos e Excel**. O mock reside em `back/app/services/demo_service.py`, no backend. As rotas originais ficam preservadas para leitura arquitetural, mas o ponto de entrada da demonstração registra o adaptador de mocks.

Os registros têm granularidade de programa, snapshot, equipe, commodity, PMT e avaliação. Filtros e snapshots alteram os resultados; totais são calculados a partir dos registros. As curvas por marco são projeções demonstrativas. Os exports de engenharia entregam os registros de avaliação usados pelo mock; não reproduzem eventuais templates Excel do sistema institucional.

## Desenvolvimento separado

```bash
# Backend, a partir da raiz
back/.venv/bin/python -m uvicorn app.main:app --app-dir back --host 127.0.0.1 --port 8000

# Frontend, em outro terminal
cd front/dandr-web
pnpm start --host 127.0.0.1
```

## Validação

```bash
cd back
.venv/bin/python -m unittest discover -s tests -p test_demo.py -v
cd ../front/dandr-web
pnpm build
```

O repositório não inclui o banco, credenciais, ambientes virtuais ou histórico Git institucional. Os arquivos visuais originais foram mantidos conforme solicitado. Esta versão é uma demonstração com dados fictícios, sem conexão com os sistemas da empresa.
