"""Generate a traceable, verbatim inventory from the checked-in source."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = [root / 'front/dandr-web/src/app/dashboard/home/home.ts',
         root / 'front/dandr-web/src/app/shared/state.service.ts']
paths += sorted((root / 'front/dandr-web/src/app/services').glob('*.ts'))
paths += sorted((root / 'back/app/controllers').glob('*.py'))
paths += [root / 'back/app/services/summary_service.py',
          root / 'back/app/services/vehicle_line_service.py',
          root / 'back/app/routes/key_datas_routes.py']
paths += sorted((root / 'back/app/models').glob('*.py'))
paths += sorted((root / 'back/app/schemas').glob('*.py'))
paths += [root / 'front/dandr-web/src/app/dashboard/components' / part / f'{part}.ts'
          for part in ['cae-metrics', 'dvp-total', 'dvp-classification', 'dvp-glidepath',
                       'design-rules-chart', 'hir-metrics', 'dpa5-metrics',
                       'milestone-readiness', 'timeline-milestones']]
paths += [root / 'front/dandr-web/src/app/dashboard/costs-status/costs-status.ts',
          root / 'front/dandr-web/src/app/dashboard/components/extract-button/extract-button.service.ts']
parts = ['# Inventário verificável de contratos, transformações e consultas\n',
         'Gerado dos arquivos desta versão. Código integral para rastrear cada parâmetro, campo e transformação. Não contém nem reconstrói SQL BigQuery ausente. Veja [o guia da pipeline](PIPELINE-ENTREVISTA.md).\n']
for path in paths:
    rel = path.relative_to(root).as_posix()
    parts += [f'\n## `{rel}`\n\n[Fonte](../{rel})\n',
              f'\n```{path.suffix[1:]}\n{path.read_text(encoding="utf-8-sig")}\n```\n']
(root / 'docs/INVENTARIO-CODIGO.md').write_text(''.join(parts))
