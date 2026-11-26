"""Offline interview practice; self-assessment, not an automated hiring score."""
from dataclasses import dataclass
from unicodedata import category

CRITERIA = ('Respondi diretamente à pergunta', 'Expliquei com clareza', 'Usei exemplos ou justificativas', 'Revisei a precisão da resposta')
@dataclass(frozen=True)
class Question:
    id: str
    area: str
    prompt: str
    hint: str

QUESTIONS = (
    Question('c1','Comportamental','Conte um pouco sobre sua trajetória profissional.','Conecte experiências reais, habilidades e o objetivo da vaga. Evite inventar resultados.'),
    Question('c2','Comportamental','Descreva uma situação em que resolveu um problema complexo.','Estruture em situação, tarefa, ação e resultado (STAR).'),
    Question('c3','Comportamental','Como você organiza atividades com prazos concorrentes?','Explique critérios de prioridade, comunicação e acompanhamento.'),
    Question('d1','Dados e BI','Qual é a diferença entre INNER JOIN e LEFT JOIN?','INNER JOIN mantém correspondências; LEFT JOIN preserva também linhas da tabela esquerda sem correspondência, preenchendo o lado direito com NULL.'),
    Question('d2','Dados e BI','Como trataria valores ausentes em uma base de dados?','Investigue causas, padrões e impacto; escolha tratamento conforme o contexto e documente a decisão.'),
    Question('d3','Dados e BI','Como escolher indicadores para um dashboard?','Parta da decisão a apoiar, defina métricas, fontes, granularidade e validação.'),
    Question('e1','Engenharia','Como identificaria gargalos em um processo produtivo?','Mapeie o fluxo, meça capacidade, filas e tempos e valide a restrição com dados.'),
    Question('e2','Engenharia','Explique o conceito de melhoria contínua.','Descreva ciclos de avaliação, experimentação, medição e padronização.'),
    Question('e3','Engenharia','Como avaliaria a viabilidade de um projeto?','Considere requisitos, custo, prazo, riscos, benefícios e restrições.'),
    Question('s1','Software','Como investigaria um erro intermitente em uma aplicação?','Reproduza quando possível, examine logs, hipóteses, mudanças e testes controlados.'),
    Question('s2','Software','Qual é a finalidade de testes unitários?','Explique isolamento de unidades, regressões e limites de cobertura.'),
    Question('s3','Software','Como protegeria credenciais de uma aplicação?','Evite segredos no código e logs; utilize armazenamento apropriado, acesso mínimo e rotação.'),
)
AREAS = tuple(dict.fromkeys(q.area for q in QUESTIONS))
_BY_ID = {q.id:q for q in QUESTIONS}
MAX_ANSWER = 4000

@dataclass(frozen=True)
class Practice:
    question_id: str
    answer: str
    criteria: tuple[bool, ...]
    @property
    def count(self): return sum(self.criteria)

class InterviewStore:
    def __init__(self): self._items = {}
    def list(self): return tuple(self._items.values())
    def get(self, question_id): return self._items.get(question_id)
    def save(self, question_id, answer, criteria):
        if not isinstance(question_id,str) or question_id not in _BY_ID: raise ValueError('Pergunta inválida.')
        if not isinstance(answer,str) or not answer.strip() or len(answer)>MAX_ANSWER or any(category(c) in ('Cc','Cs') and c not in '\n\t' for c in answer):
            raise ValueError('Informe uma resposta válida de até 4.000 caracteres.')
        if not isinstance(criteria,(tuple,list)) or len(criteria)!=len(CRITERIA) or any(type(v) is not bool for v in criteria): raise ValueError('Autoavaliação inválida.')
        item=Practice(question_id,answer,tuple(criteria)); self._items[question_id]=item; return item
    def delete(self, question_id): self._items.pop(question_id,None)
    def clear(self): self._items.clear()
    def progress(self, area):
        if area not in AREAS: raise ValueError('Área inválida.')
        questions=tuple(q for q in QUESTIONS if q.area==area)
        return sum(q.id in self._items for q in questions),len(questions)
