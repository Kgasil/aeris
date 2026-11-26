"""Bounded CSV aggregation using Data's validation and read-only file reader."""
from dataclasses import dataclass
from decimal import Decimal, localcontext
import csv
import io
from aeris.data import profile_text, read_csv_file, DataProfile, Cancelled

MAX_GROUPS=100
DISPLAY_GROUPS=12
MODES=('Contagem','Soma','Média')

@dataclass(frozen=True)
class Dataset:
    profile: DataProfile
    rows: tuple[tuple[str,...],...]
    decimal_separator: str

@dataclass(frozen=True)
class Group:
    name: str
    value: Decimal
    count: int

@dataclass(frozen=True)
class Dashboard:
    groups: tuple[Group,...]
    included: int
    skipped: int
    overall: Decimal | None


def dataset_text(text, delimiter=',', decimal_separator='.', *, cancelled=lambda:False):
    profile=profile_text(text,delimiter,decimal_separator,cancelled=cancelled)
    reader=csv.reader(io.StringIO(text,newline=''),delimiter=delimiter,strict=True)
    next(reader)
    rows=[]
    for row in reader:
        if cancelled(): raise Cancelled()
        rows.append(tuple(row))
    return Dataset(profile,tuple(rows),decimal_separator)


def dataset_file(path, delimiter=',', decimal_separator='.', *, cancelled=lambda:False):
    return read_csv_file(path,lambda text:dataset_text(text,delimiter,decimal_separator,cancelled=cancelled),cancelled=cancelled)


def aggregate(dataset, group_index, mode, metric_index=None):
    cols=dataset.profile.columns
    if type(group_index) is not int or not 0<=group_index<len(cols) or mode not in MODES:
        raise ValueError('Seleção inválida.')
    if mode!='Contagem' and (type(metric_index) is not int or not 0<=metric_index<len(cols) or cols[metric_index].kind!='Numérica'):
        raise ValueError('Selecione uma coluna numérica.')
    groups={}; skipped=0; included=0
    with localcontext() as ctx:
        ctx.prec=40
        for row in dataset.rows:
            name=row[group_index]
            if not name.strip() or (mode!='Contagem' and not row[metric_index].strip()):
                skipped+=1; continue
            value=Decimal(1) if mode=='Contagem' else Decimal(row[metric_index].strip().replace(dataset.decimal_separator,'.'))
            total,count=groups.get(name,(Decimal(0),0)); groups[name]=(total+value,count+1); included+=1
            if len(groups)>MAX_GROUPS: raise ValueError('Mais de 100 categorias válidas. Escolha outra coluna.')
        total=sum((v[0] for v in groups.values()),Decimal(0))
        result=[Group(k,s/n if mode=='Média' else s,n) for k,(s,n) in groups.items()]
        result.sort(key=lambda g:(-g.value,g.name))
        overall=(total/included if mode=='Média' else total) if included else None
    return Dashboard(tuple(result),included,skipped,overall)
