"""Build a source-linked catalog without importing or executing production code."""
import ast
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sections = [(root/'docs/GUIA-DADOS.md').read_text(), '\n# Apêndice A — funções, filtros e rotas\n']
sql_sections = ['\n# Apêndice B — SQL original\n',
    'Extração estática de statements e fragmentos. F-strings mantêm `{expressões}` literalmente; '
    'não são SQL já renderizado. Siga a função de origem para parâmetros e montagem condicional. '
    'Scripts de patch são identificados pelo caminho e não equivalem a jobs executados.\n']
count = 0
for path in sorted((root/'back').rglob('*.py')):
    rel = path.relative_to(root).as_posix()
    if not (rel.startswith('back/app/') or rel.startswith('back/scripts/')): continue
    if path.name in ['demo_service.py','demo_routes.py']: continue
    src = path.read_text(encoding='utf-8-sig')
    try: tree=ast.parse(src)
    except SyntaxError: continue
    functions = [n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    if functions:
        sections.append(f'\n## [{rel}](../{rel})\n\n| Função | Parâmetros | Decoradores/rota |\n| --- | --- | --- |\n')
        for fn in sorted(functions,key=lambda n:n.lineno):
            args=ast.unparse(fn.args).replace('|','\\|').replace('\n',' ')
            dec='; '.join(ast.unparse(d) for d in fn.decorator_list).replace('|','\\|')
            sections.append(f'| [{fn.name}](../{rel}#L{fn.lineno}) | `{args}` | `{dec}` |\n')
    parents={child:node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in sorted(ast.walk(tree),key=lambda n:getattr(n,'lineno',0)):
        if not isinstance(node,(ast.Constant,ast.JoinedStr)): continue
        if isinstance(node,ast.Constant) and not isinstance(node.value,str): continue
        if isinstance(parents.get(node),ast.JoinedStr): continue
        value=ast.get_source_segment(src,node) or ''
        if not re.search(r'\b(SELECT\s+|CREATE\s+(?:OR|TABLE)|INSERT\s+INTO|DELETE\s+FROM|MERGE\s+INTO)',value,re.I): continue
        parent=parents.get(node)
        if isinstance(parent,ast.Expr):
            grand=parents.get(parent)
            if hasattr(grand,'body') and grand.body and grand.body[0] is parent: continue
        owner=node
        while owner in parents and not isinstance(owner,(ast.FunctionDef,ast.AsyncFunctionDef)): owner=parents[owner]
        count+=1
        sql_sections.append(f'\n## Q{count:03} — `{getattr(owner,"name","module")}`\n\nFonte: [{rel}:{node.lineno}](../{rel}#L{node.lineno}).\n\n```python\n{value}\n```\n')
sections.append(f'\nTemplates/fragmentos SQL identificados: **{count}**.\n')
(root/'docs/PANORAMA-DADOS.md').write_text(''.join(sections+sql_sections))
(root/'docs/INVENTARIO-CODIGO.md').write_text('# Inventário atualizado\n\nFunções, contratos e queries: [Panorama de dados](PANORAMA-DADOS.md).\n')
(root/'docs/PIPELINE-ENTREVISTA.md').write_text('# Pipeline para entrevista — corrigida\n\nVeja o [Panorama completo](PANORAMA-DADOS.md). As queries BigQuery foram recuperadas da branch `fix/dpa5-program-filter-snapshot`, commit `6bcd7ae`. A análise anterior considerava a main local antiga e foi substituída.\n')
print(f'Panorama gerado com {count} templates/fragmentos SQL, sem acesso à nuvem.')
