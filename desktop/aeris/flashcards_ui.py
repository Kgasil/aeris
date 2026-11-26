"""Local flashcard editor and explicit reveal/rate review workflow."""
import tkinter as tk
from tkinter import ttk, messagebox
from aeris.flashcards import RATINGS

class FlashcardsWindow:
    def __init__(self, hub):
        self.hub, self.store = hub, hub.flashcards_store
        self.selected_id = self.review_id = None
        self.revealed = False; self.reviewed_card=None
        self.window = tk.Toplevel(hub.root); self.window.title('Aeris Flashcards'); self.window.geometry('800x740'); self.window.minsize(620,620)
        self.window.protocol('WM_DELETE_WINDOW',self.close); self.window.bind('<Escape>',lambda _: self.close())
        f=ttk.Frame(self.window,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Cartões de estudo',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text='Pratique perguntas e respostas com revisão espaçada. Cartões mantidos nesta sessão.').pack(anchor='w')
        self.query=tk.StringVar(self.window); self.deck_filter=tk.StringVar(self.window); self.due_only=tk.BooleanVar(self.window)
        bar=ttk.Frame(f); bar.pack(fill='x',pady=5)
        ttk.Label(bar,text='Busca').pack(side='left'); ttk.Entry(bar,textvariable=self.query,width=18).pack(side='left',fill='x',expand=True)
        ttk.Label(bar,text='Baralho exato').pack(side='left',padx=4); ttk.Entry(bar,textvariable=self.deck_filter,width=15).pack(side='left')
        ttk.Checkbutton(bar,text='Disponíveis',variable=self.due_only,command=self.render).pack(side='left',padx=4)
        ttk.Button(bar,text='Atualizar',command=self.render).pack(side='left')
        ttk.Button(bar,text='Limpar filtros',command=self.clear_filters).pack(side='left',padx=2)
        self.stats=tk.StringVar(self.window); ttk.Label(f,textvariable=self.stats).pack(anchor='w')
        area=ttk.Frame(f); area.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(area,columns=('deck','question','due','reviews'),show='headings',selectmode='browse',height=5)
        for key,label,width in [('deck','Baralho',120),('question','Pergunta',260),('due','Próxima revisão (local)',145),('reviews','Revisões',65)]:
            self.tree.heading(key,text=label); self.tree.column(key,width=width,stretch=key=='question')
        sb=ttk.Scrollbar(area,command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set); self.tree.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y')
        bar=ttk.Frame(f); bar.pack(fill='x',pady=4)
        ttk.Button(bar,text='Editar selecionado',command=self.load_selected).pack(side='left',padx=2)
        ttk.Button(bar,text='Começar revisão',command=self.start_review,style='Aeris.Primary.TButton').pack(side='left',padx=2)
        self.tabs=ttk.Notebook(f); self.tabs.pack(fill='both',expand=True)
        edit=ttk.Frame(self.tabs,padding=8); review=ttk.Frame(self.tabs,padding=8); self.tabs.add(edit,text='Criar cartão'); self.tabs.add(review,text='Estudar'); self.review_tab=review; self.edit_tab=edit
        self.deck=tk.StringVar(self.window,'Geral'); self.editor_label=tk.StringVar(self.window,'Novo cartão')
        ttk.Label(edit,textvariable=self.editor_label,font=('Segoe UI',12,'bold')).pack(anchor='w')
        ttk.Label(edit,text='Baralho').pack(anchor='w'); ttk.Entry(edit,textvariable=self.deck).pack(fill='x')
        for label,attr in [('Pergunta','question'),('Resposta','answer')]:
            ttk.Label(edit,text=label).pack(anchor='w'); text=tk.Text(edit,height=3,wrap='word',padx=10,pady=8,relief='flat',highlightthickness=1); text.pack(fill='both',expand=True); setattr(self,attr,text)
        bar=ttk.Frame(edit); bar.pack(fill='x',pady=4)
        for label,cmd in [('Novo / limpar',self.new),('Salvar',self.save),('Excluir aberto',self.delete)]: ttk.Button(bar,text=label,command=cmd,style='Aeris.Primary.TButton' if label=='Salvar' else 'TButton').pack(side='left',fill='x',expand=True,padx=2)
        self.review_text=tk.Text(review,height=9,wrap='word',state='disabled',font=('Segoe UI',12),padx=16,pady=14,relief='flat',highlightthickness=1); self.review_text.pack(fill='both',expand=True)
        self.reveal_button=ttk.Button(review,text='Mostrar resposta',command=self.reveal,style='Aeris.Primary.TButton',state='disabled'); self.reveal_button.pack(fill='x',pady=4)
        bar=ttk.Frame(review); bar.pack(fill='x'); self.rating_buttons=[]
        for rating in RATINGS:
            b=ttk.Button(bar,text=rating,command=lambda r=rating:self.rate(r),state='disabled'); b.pack(side='left',fill='x',expand=True,padx=2); self.rating_buttons.append(b)
        self.status=tk.StringVar(self.window); ttk.Label(f,textvariable=self.status,wraplength=600).pack(anchor='w'); self.render()

    def values(self): return self.deck.get(),self.question.get('1.0','end-1c'),self.answer.get('1.0','end-1c')
    def dirty(self):
        if self.selected_id is None: return self.values()!=('Geral','','')
        try: c=self.store.get(self.selected_id)
        except KeyError: return True
        return self.values()!=(c.deck,c.question,c.answer)
    def discard_ok(self): return not self.dirty() or messagebox.askyesno('Descartar rascunho?','Alterações não salvas serão descartadas.',parent=self.window)
    def close(self):
        if self.discard_ok(): self.window.destroy()
    def set_editor(self,c=None):
        self.selected_id=c.id if c else None; self.editor_label.set('Editar cartão' if c else 'Novo cartão'); self.deck.set(c.deck if c else 'Geral')
        for widget,value in ((self.question,c.question if c else ''),(self.answer,c.answer if c else '')): widget.delete('1.0','end'); widget.insert('1.0',value)
    def new(self):
        if self.discard_ok(): self.set_editor(); self.status.set('Novo cartão.')
    def load_selected(self):
        ids=self.tree.selection()
        if not ids: self.status.set('Selecione um cartão.'); return
        try: item=self.store.get(int(ids[0]))
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        before=(self.selected_id,self.values())
        if not self.discard_ok() or not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or before!=(self.selected_id,self.values()) or self.tree.selection()!=ids:
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.set_editor(item); self.tabs.select(self.edit_tab)
    def clear_filters(self):
        self.query.set(''); self.deck_filter.set(''); self.due_only.set(False)
        self.render()

    def render(self):
        selected=self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        try: items=self.store.search(self.query.get(),self.deck_filter.get(),self.due_only.get())
        except ValueError as e: self.stats.set('Filtro inválido.'); self.status.set(str(e)); return
        for c in items: self.tree.insert('','end',iid=str(c.id),values=(c.deck,c.question.replace('\n',' '),c.due.astimezone().strftime('%d/%m %H:%M'),c.reviews))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])
        self.stats.set(f'{len(items)} exibidos / {len(self.store.list())} cartões · {len(self.store.search(due_only=True))} disponíveis')
    def changed(self):
        self.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()
    def save(self):
        try: c=self.store.add(*self.values()) if self.selected_id is None else self.store.edit(self.selected_id,*self.values())
        except (ValueError,KeyError) as e: self.status.set(str(e)); return
        if self.review_id==c.id: self.clear_review()
        self.set_editor(c); self.changed(); self.status.set('Cartão salvo na sessão. Alterar pergunta/resposta reinicia a revisão.')
    def delete(self):
        if self.selected_id is None: self.status.set('Abra um cartão antes de excluir.'); return
        try: item=self.store.get(self.selected_id)
        except KeyError: self.render(); self.status.set('Registro removido.'); return
        draft=self.values()
        if not messagebox.askyesno('Excluir cartão?','Excluir cartão e seu progresso?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or self.values()!=draft:
            self.render(); self.status.set('Registro alterado. Revise novamente.'); return
        if self.review_id==self.selected_id: self.clear_review()
        self.store.delete(item.id); self.set_editor(); self.changed(); self.status.set('Cartão excluído.')
    def show_review(self,text):
        self.review_text.configure(state='normal'); self.review_text.delete('1.0','end'); self.review_text.insert('1.0',text); self.review_text.configure(state='disabled')
    def clear_review(self):
        self.review_id=None; self.revealed=False; self.reviewed_card=None; self.show_review(''); self.reveal_button.configure(state='disabled')
        for b in self.rating_buttons: b.configure(state='disabled')
    def start_review(self):
        self.clear_review()
        try: items=self.store.search(self.query.get(),self.deck_filter.get(),True)
        except ValueError as e: self.status.set(str(e)); return
        if not items: self.status.set('Nenhum cartão disponível neste filtro.'); return
        c=items[0]; self.review_id=c.id; self.reviewed_card=c; self.show_review(c.question); self.tabs.select(self.review_tab); self.reveal_button.configure(state='normal'); self.status.set('Tente lembrar antes de revelar.')
    def current_review(self):
        if self.review_id is None: return None
        try: c=self.store.get(self.review_id)
        except KeyError: c=None
        if c is None or c is not self.reviewed_card or c.due>self.store.now():
            self.clear_review(); self.status.set('Cartão alterado ou indisponível. Inicie nova revisão.'); return None
        return c

    def reveal(self):
        c=self.current_review()
        if c is None: return
        self.revealed=True; self.show_review(c.question+'\n\nResposta:\n'+c.answer); self.reveal_button.configure(state='disabled')
        for b in self.rating_buttons: b.configure(state='normal')
    def rate(self,rating):
        if not self.revealed: return
        reviewed=self.current_review()
        if reviewed is None: return
        try: c=self.store.review(reviewed.id,rating)
        except (ValueError,KeyError) as e: self.clear_review(); self.status.set(str(e)); return
        self.clear_review(); self.changed(); self.status.set('Próxima revisão: '+c.due.astimezone().strftime('%d/%m/%Y %H:%M'))
