import unittest
from aeris.registry import Module, normalize
from aeris.catalog_index import CatalogIndex


class CatalogIndexTests(unittest.TestCase):
    def setUp(self):
        self.modules=tuple(Module(i,f'Tool{i}','Dados' if i%2 else 'Texto','Análise de relatório','ready') for i in range(50))
        self.names={'Tool1':'Indicadores'}
        self.categories={'Dados':'Métricas'}
        self.help={'Tool1':('Calcular média','Exemplo de CSV')}
        self.goals={'Analisar':('Tool1','Tool3')}
        self.index=CatalogIndex(self.modules,self.names,self.categories,self.help,self.goals)

    def old(self,query,category,goal):
        words=normalize(query).split()
        return tuple(m for m in self.modules if (goal=='Todas' or m.name in self.goals.get(goal,())) and (category=='Todas' or m.category==category) and all(q in normalize(' '.join((m.name,self.names.get(m.name,m.name),m.description,m.category,self.categories.get(m.category,m.category),*self.help.get(m.name,('',''))))) for q in words))

    def test_equivalence(self):
        for query in ('','ANALISE','indicadores csv','metricas','Tool1','sem resultado','relatório média'):
            for category in ('Todas','Dados','Texto','Outra'):
                for goal in ('Todas','Analisar','Outro'):
                    with self.subTest(query=query,category=category,goal=goal):
                        self.assertEqual(self.index.search(query,category,goal),self.old(query,category,goal))

    def test_order_and_empty(self):
        self.assertEqual(self.index.search(),self.modules)
        self.assertEqual(self.index.search('missing'),())

    def test_no_query_cache(self):
        before=dict(vars(self.index))
        self.index.search('private example')
        self.assertEqual(vars(self.index),before)


if __name__=='__main__':
    unittest.main()
