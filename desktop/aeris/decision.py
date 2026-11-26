"""Bounded weighted decision matrix. Exact rational arithmetic, no external effects."""
from dataclasses import dataclass
from fractions import Fraction
from aeris.calculator import number
import unicodedata

MAX_CRITERIA = 6
MAX_ALTERNATIVES = 6

@dataclass(frozen=True)
class Ranked:
    name: str
    score: Fraction
    rank: int


def names(values, limit):
    if not 2 <= len(values) <= limit:
        raise ValueError(f'Informe de 2 a {limit} nomes.')
    if any(not isinstance(v, str) or not v.strip() or len(v)>60 or any(unicodedata.category(c).startswith('C') for c in v) for v in values):
        raise ValueError('Nomes obrigatórios, até 60 caracteres, sem caracteres de controle.')
    clean = tuple(v.strip() for v in values)
    keys = [unicodedata.normalize('NFKC', v).casefold() for v in clean]
    if len(set(keys)) != len(keys):
        raise ValueError('Nomes repetidos na mesma dimensão.')
    return clean


def limited(value, maximum):
    n = number(value)
    if not 0 <= n <= maximum:
        raise ValueError(f'Valor deve estar entre 0 e {maximum}.')
    return Fraction(n)


def rank_matrix(criteria, weights, alternatives, scores):
    """All scores are benefit-oriented (higher is better); ties share rank."""
    criteria = names(criteria, MAX_CRITERIA)
    alternatives = names(alternatives, MAX_ALTERNATIVES)
    if len(weights)!=len(criteria) or len(scores)!=len(alternatives) or any(len(row)!=len(criteria) for row in scores):
        raise ValueError('Dimensões da matriz incompatíveis.')
    w = tuple(limited(v,100) for v in weights)
    total = sum(w)
    if not total:
        raise ValueError('Pelo menos um peso deve ser positivo.')
    values = [(name, sum(limited(v,10)*weight for v,weight in zip(row,w))/total) for name,row in zip(alternatives,scores)]
    values.sort(key=lambda x:x[1], reverse=True)
    ranked = []
    for i,(name,score) in enumerate(values,1):
        rank = ranked[-1].rank if ranked and ranked[-1].score==score else i
        ranked.append(Ranked(name,score,rank))
    return tuple(ranked)


def display_score(score):
    # Exact non-negative rational -> four decimal places, half-up.
    scaled = score*10000
    n = (2*scaled.numerator+scaled.denominator)//(2*scaled.denominator)
    return f'{n//10000},{n%10000:04d}'
