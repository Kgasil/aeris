"""Explicit study transfers; no automatic source sharing."""
from tkinter import messagebox, simpledialog
from aeris.integration import prepare_study, execute_study
from aeris.permissions import INTEGRATION_RUN


def send_topic(ui):
    h=ui.hub
    h.permissions.require(INTEGRATION_RUN)
    p=ui.store.get(ui.plan_id()); topic=next((t for t in p.topics if t.id==ui.selected()),None)
    if topic is None: raise ValueError('Selecione um tópico salvo.')
    if not h.enabled('Flashcards'): raise ValueError('Ative Flashcards antes de continuar.')
    answer=simpledialog.askstring('Resposta do cartão','Escreva a resposta para: '+topic.title,parent=ui.window)
    if answer is None: return False
    h.open_tool('Flashcards')
    if not h.alive(h.flashcards_window): raise ValueError('Destino indisponível.')
    proposal=prepare_study(h,'Learn-Flashcards',p,answer,topic)
    if not messagebox.askyesno('Criar cartão?',proposal.preview,parent=ui.window): return False
    execute_study(h,proposal,answer); h.flashcards_window.render()
    return True


def send_reference(ui):
    h=ui.hub; h.permissions.require(INTEGRATION_RUN)
    if ui.selected_id is None or ui.dirty(): raise ValueError('Abra e salve a referência antes de continuar.')
    record=ui.store.get(ui.selected_id)
    if not h.enabled('Learn'): raise ValueError('Ative Learn antes de continuar.')
    h.open_tool('Learn')
    if not h.alive(h.learn_window): raise ValueError('Destino indisponível.')
    plans=h.learn_store.list()
    if not plans: raise ValueError('Crie uma trilha no Learn primeiro.')
    label='Escolha o número da trilha:\n'+'\n'.join(f'{i+1}. {p.title}' for i,p in enumerate(plans))
    idx=simpledialog.askinteger('Trilha de destino',label,minvalue=1,maxvalue=len(plans),parent=ui.window)
    if idx is None: return False
    mins=simpledialog.askinteger('Estimativa','Minutos planejados:',initialvalue=25,minvalue=1,maxvalue=1440,parent=ui.window)
    if mins is None: return False
    value=(plans[idx-1].id,mins)
    proposal=prepare_study(h,'Research-Learn',record,value)
    if not messagebox.askyesno('Criar tópico?',proposal.preview,parent=ui.window): return False
    execute_study(h,proposal,value); h.learn_window.refresh(value[0]); return True
