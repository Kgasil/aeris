"""Deterministic plain-text reports from bounded CSV profile and aggregation."""
from aeris.dashboard import aggregate
from aeris.organizer import safe_name


def label(text, limit=120):
    text=safe_name(text)
    return text if len(text)<=limit else text[:limit-1]+'…'


def number(value):
    return '—' if value is None else format(value,'.12g')


def build_report(dataset, group_index=None, mode='Contagem', metric_index=None):
    p=dataset.profile
    cells=p.rows*len(p.columns)
    missing=f'{100*p.missing/cells:.2f}%' if cells else '—'
    duplicates=f'{100*p.duplicates/p.rows:.2f}%' if p.rows else '—'
    lines=['AERIS REPORT — Análise descritiva de CSV','', '1. Resumo da base',
           f'Registros: {p.rows} | Colunas: {len(p.columns)}',
           f'Células ausentes: {p.missing} | Duplicatas exatas adicionais: {p.duplicates}',
           f'Taxa de células ausentes: {missing} | Duplicatas adicionais por registro: {duplicates}',
           'Ausentes = campos vazios ou somente espaços. Duplicatas mantidas nos cálculos.',
           '', '2. Qualidade e estatísticas por coluna']
    for i,c in enumerate(p.columns,1):
        lines.append(f'{i}. {label(c.name)} | {c.kind} | Ausentes: {c.missing} | Distintos: {c.distinct}')
        if c.mean is not None:
            lines.append(f'   Mínimo: {number(c.minimum)} | Máximo: {number(c.maximum)} | Média: {number(c.mean)}')
    lines.extend(['','3. Indicadores por categoria'])
    if group_index is None:
        lines.append('Agregação não selecionada.')
    else:
        summary=aggregate(dataset,group_index,mode,metric_index)
        lines.append(f'Categoria: {label(p.columns[group_index].name)} | Agregação: {mode}')
        if mode!='Contagem': lines.append(f'Métrica: {label(p.columns[metric_index].name)}')
        lines.append(f'Registros usados: {summary.included} | Ignorados: {summary.skipped} | Categorias: {len(summary.groups)}')
        total=summary.included+summary.skipped
        coverage=f'{100*summary.included/total:.2f}%' if total else '—'
        lines.append(f'Cobertura dos registros: {coverage}')
        lines.append(f'{"Média global por registro" if mode=="Média" else "Total global"}: {number(summary.overall)}')
        lines.extend(f'- {label(g.name)}: {number(g.value)} ({g.count} registros)' for g in summary.groups)
        if not summary.groups: lines.append('Nenhuma categoria válida.')
    lines.extend(['','4. Pontos de revisão'])
    if p.missing: lines.append('- Revise os campos ausentes antes de utilizar os indicadores.')
    if p.duplicates: lines.append('- Investigue as duplicatas; nem toda repetição é um erro.')
    if not p.missing and not p.duplicates: lines.append('- Nenhum campo ausente ou duplicata exata detectado; isso não comprova a qualidade da base.')
    lines.extend(['- Confira tipos inferidos, identificadores numéricos e separadores.',
                  '- Números exibidos com até 12 algarismos significativos; rótulos longos abreviados.',
                  '- Relatório descritivo determinístico; não é auditoria nem recomendação de negócio.', '', 'Aeris · K&G Vision'])
    return '\n'.join(lines)
