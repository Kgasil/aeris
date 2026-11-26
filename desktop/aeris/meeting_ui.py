"""Meeting editor with draft isolation and explicit minutes copy."""
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from dataclasses import replace
from aeris.meeting import Action, MAX_ACTIONS, minutes
from aeris.permissions import MEETING_COPY, INTEGRATION_RUN

class MeetingWindow:
    def __init__(self,hub):
        self.hub=hub; self.store=hub.meeting_store; self.selected_id=None; self.actions=[]; self.editing_action=None
        self.window=w=tk.Toplevel(hub.root); w.title('Aeris Meeting'); w.geometry('860x760'); w.minsize(640,560)
        w.protocol('WM_DELETE_WINDOW',self.close); w.bind('<Escape>',lambda _:self.close())
        f=ttk.Frame(w,padding=18); f.pack(fill='both',expand=True)
        ttk.Label(f,text='Minhas reuniões',font=('Segoe UI',21,'bold')).pack(anchor='w')
        ttk.Label(f,text='Organize pautas, decisões e tarefas nesta sessão. Esta janela não grava áudio nem acessa calendários.').pack(anchor='w')
        ttk.Label(f,text='Encontre uma reunião salva',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(8,0))
        row=ttk.Frame(f); row.pack(fill='x',pady=4); self.query=tk.StringVar(w)
        ttk.Entry(row,textvariable=self.query).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Pesquisar',command=self.render).pack(side='left'); ttk.Button(row,text='Limpar busca',command=self.clear_search).pack(side='left')
        ttk.Button(row,text='Abrir selecionada',command=self.load).pack(side='left')
        self.tree=ttk.Treeview(f,columns=('title','date','progress'),show='headings',height=4,selectmode='browse')
        for col,label,width in [('title','Reunião',320),('date','Data',110),('progress','Atividades',100)]: self.tree.heading(col,text=label); self.tree.column(col,width=width)
        self.tree.pack(fill='x'); self.tree.bind('<Double-1>',lambda _:self.load()); self.tree.bind('<Return>',lambda _:self.load())
        self.title=tk.StringVar(w); self.day=tk.StringVar(w); self.editor=tk.StringVar(w,'Nova reunião')
        ttk.Label(f,textvariable=self.editor,font=('Segoe UI',12,'bold')).pack(anchor='w',pady=3)
        for label,var in [('Título',self.title),('Data (AAAA-MM-DD)',self.day)]:
            row=ttk.Frame(f); row.pack(fill='x'); ttk.Label(row,text=label,width=22).pack(side='left'); ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True)
        tabs=ttk.Notebook(f); tabs.pack(fill='both',expand=True,pady=4)
        for attr,label in [('participants','Participantes'),('agenda','Pauta'),('notes','Anotações e decisões')]:
            tab=ttk.Frame(tabs,padding=4); tabs.add(tab,text=label); text=tk.Text(tab,height=5,wrap='word',padx=10,pady=8,relief='flat',highlightthickness=1); sb=ttk.Scrollbar(tab,command=text.yview); text.configure(yscrollcommand=sb.set); text.pack(side='left',fill='both',expand=True); sb.pack(side='right',fill='y'); setattr(self,attr,text)
        tab=ttk.Frame(tabs,padding=4); tabs.add(tab,text='Plano de ação')
        self.action_tree=ttk.Treeview(tab,columns=('title','owner','due','done'),show='headings',height=4,selectmode='browse')
        for col,label,width in [('title','Atividade',240),('owner','Responsável',130),('due','Prazo',105),('done','Estado',85)]: self.action_tree.heading(col,text=label); self.action_tree.column(col,width=width)
        self.action_tree.pack(fill='both',expand=True); self.action_tree.bind('<Double-1>',lambda _:self.load_action())
        self.action_title=tk.StringVar(w); self.owner=tk.StringVar(w); self.due=tk.StringVar(w)
        for label,var in [('Atividade',self.action_title),('Responsável',self.owner),('Prazo (AAAA-MM-DD)',self.due)]:
            row=ttk.Frame(tab); row.pack(fill='x'); ttk.Label(row,text=label,width=22).pack(side='left'); ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True)
        row=ttk.Frame(tab); row.pack(fill='x')
        for label,cmd in [('Adicionar',self.add_action),('Carregar',self.load_action),('Atualizar',self.edit_action),('Alternar conclusão',self.toggle_action),('Excluir',self.delete_action),('Limpar campos',self.clear_action_fields)]: ttk.Button(row,text=label,command=cmd).pack(side='left',padx=2)
        transfer=ttk.Frame(tab); transfer.pack(fill='x',pady=2)
        ttk.Button(transfer,text='Enviar para tarefas',command=lambda:self.transfer('Checklist')).pack(side='left',padx=2)
        ttk.Button(transfer,text='Criar lembrete',command=lambda:self.transfer('Reminder')).pack(side='left',padx=2)
        self.progress=tk.StringVar(w); ttk.Label(tab,textvariable=self.progress).pack(anchor='w')
        row=ttk.Frame(f); row.pack(fill='x',pady=4)
        for label,cmd in [('Nova reunião',self.new),('Salvar reunião',self.save),('Excluir reunião',self.delete),('Prévia da ata salva',self.preview)]: ttk.Button(row,text=label,command=cmd,style='Aeris.Primary.TButton' if label=='Salvar reunião' else 'TButton').pack(side='left',padx=2)
        self.status=tk.StringVar(w); ttk.Label(f,textvariable=self.status,wraplength=600).pack(anchor='w')
        self.preview_window=None; self.copy_button=None; self.render(); self.render_actions()
    def values(self): return (self.title.get(),self.day.get(),*(getattr(self,n).get('1.0','end-1c') for n in ('participants','agenda','notes')),tuple(self.actions))
    def action_fields(self): return tuple(v.get() for v in (self.action_title,self.owner,self.due))
    def clear_action_fields(self):
        self.editing_action=None
        for v in (self.action_title,self.owner,self.due): v.set('')
    def dirty(self):
        try: item=self.store.get(self.selected_id) if self.selected_id is not None else None
        except KeyError: return True
        return self.values()!=((item.title,item.day,item.participants,item.agenda,item.notes,item.actions) if item else ('','','','','',())) or self.editing_action is not None or any(self.action_fields())
    def discard_ok(self): return not self.dirty() or messagebox.askyesno('Descartar rascunho?','Descartar alterações não salvas?',parent=self.window)
    def close(self):
        if self.discard_ok(): self.window.destroy()
        return 'break'
    def clear_search(self):
        self.query.set(''); self.render()

    def render(self):
        selected=self.tree.selection()
        try: items=self.store.search(self.query.get())
        except ValueError as exc: self.status.set(str(exc)); return
        self.tree.delete(*self.tree.get_children())
        for m in items: self.tree.insert('','end',iid=str(m.id),values=(m.title,m.day or '—',f'{m.completed}/{len(m.actions)}'))
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0]); self.tree.focus(selected[0]); self.tree.see(selected[0])
    def set_editor(self,item=None):
        self.close_preview(); self.selected_id=item.id if item else None; self.editor.set('Editar reunião' if item else 'Nova reunião')
        self.title.set(item.title if item else ''); self.day.set(item.day if item else '')
        for name in ('participants','agenda','notes'):
            t=getattr(self,name); t.delete('1.0','end'); t.insert('1.0',getattr(item,name) if item else '')
        self.actions=list(item.actions) if item else []; self.clear_action_fields(); self.render_actions()
    def new(self):
        if self.discard_ok(): self.set_editor(); self.status.set('Nova reunião.')
    def load(self):
        ids=self.tree.selection()
        if not ids: return
        try: item=self.store.get(int(ids[0]))
        except KeyError: self.render(); self.status.set('Reunião removida.'); return
        before=(self.selected_id,self.values(),self.action_fields(),self.editing_action)
        if not self.discard_ok() or not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.tree.selection()!=ids or before!=(self.selected_id,self.values(),self.action_fields(),self.editing_action):
            self.render(); self.status.set('Seleção alterada. Revise novamente.'); return
        self.set_editor(item); self.status.set('Reunião aberta.')
    def refresh(self):
        self.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()
    def save(self):
        if self.editing_action is not None or any(self.action_fields()): self.status.set('Adicione ou atualize a atividade em edição antes de salvar a reunião.'); return
        try: item=self.store.add(*self.values()) if self.selected_id is None else self.store.edit(self.selected_id,*self.values())
        except (ValueError,KeyError) as exc: self.status.set(str(exc)); return
        self.set_editor(item); self.refresh(); self.status.set('Reunião salva somente na sessão.')
    def delete(self):
        if self.selected_id is None: return
        try: item=self.store.get(self.selected_id)
        except KeyError: self.render(); self.status.set('Reunião removida.'); return
        before=(self.values(),self.action_fields(),self.editing_action)
        if not messagebox.askyesno('Excluir reunião?','Excluir reunião salva e rascunho?',parent=self.window): return
        if not self.window.winfo_exists(): return
        try: same=self.store.get(item.id) is item
        except KeyError: same=False
        if not same or self.selected_id!=item.id or before!=(self.values(),self.action_fields(),self.editing_action):
            self.render(); self.status.set('Reunião alterada. Revise novamente.'); return
        self.store.delete(item.id); self.set_editor(); self.refresh(); self.status.set('Reunião excluída.')
    def render_actions(self,select=None):
        self.action_tree.delete(*self.action_tree.get_children())
        for i,a in enumerate(self.actions): self.action_tree.insert('','end',iid=str(i),values=(a.title,a.owner,a.due,'Concluída' if a.done else 'Pendente'))
        if select is not None: self.action_tree.selection_set(str(select))
        self.progress.set(f'{sum(a.done for a in self.actions)}/{len(self.actions)} atividades concluídas')
    def action_index(self):
        ids=self.action_tree.selection(); return int(ids[0]) if ids else None
    def add_action(self):
        if self.editing_action is not None: self.status.set('Finalize a edição ou limpe os campos antes de adicionar.'); return
        if len(self.actions)>=MAX_ACTIONS: self.status.set('Limite de 50 atividades.'); return
        try: a=Action(*self.action_fields())
        except ValueError as exc: self.status.set(str(exc)); return
        self.actions.append(a); self.clear_action_fields(); self.render_actions(len(self.actions)-1); self.close_preview()
    def load_action(self):
        i=self.action_index()
        if i is None: return
        if (self.editing_action is not None or any(self.action_fields())) and not messagebox.askyesno('Descartar atividade em edição?','Substituir os campos da atividade?',parent=self.window): return
        self.editing_action=i; a=self.actions[i]; self.action_title.set(a.title); self.owner.set(a.owner); self.due.set(a.due)
    def edit_action(self):
        i=self.action_index()
        if i is None or i!=self.editing_action: self.status.set('Carregue a atividade selecionada antes de atualizá-la.'); return
        try: a=Action(*self.action_fields(),self.actions[i].done)
        except ValueError as exc: self.status.set(str(exc)); return
        self.actions[i]=a; self.clear_action_fields(); self.render_actions(i); self.close_preview()
    def toggle_action(self):
        i=self.action_index()
        if i is not None: self.actions[i]=replace(self.actions[i],done=not self.actions[i].done); self.render_actions(i); self.close_preview()
    def delete_action(self):
        i=self.action_index()
        if self.editing_action is not None or any(self.action_fields()): self.status.set('Finalize a edição ou limpe os campos antes de excluir.'); return
        if i is None: return
        reviewed=tuple(self.actions); selected_id=self.selected_id
        if not messagebox.askyesno('Excluir atividade?','Excluir atividade do rascunho?',parent=self.window): return
        if not self.window.winfo_exists(): return
        if self.selected_id!=selected_id or tuple(self.actions)!=reviewed or self.action_index()!=i or self.editing_action is not None or any(self.action_fields()):
            self.status.set('Atividade alterada. Revise novamente.'); return
        self.actions.pop(i); self.clear_action_fields(); self.render_actions(); self.close_preview()
    def close_preview(self):
        if self.preview_window is not None and self.preview_window.winfo_exists(): self.preview_window.destroy()
        self.preview_window=None; self.copy_button=None
    def permissions_changed(self):
        if self.copy_button is not None and self.copy_button.winfo_exists(): self.copy_button.configure(state='normal' if self.hub.permissions.allowed(MEETING_COPY) else 'disabled')
    def preview(self):
        if self.selected_id is None or self.dirty(): self.status.set('Salve a reunião e finalize os campos em edição antes da prévia.'); return
        self.close_preview(); item=self.store.get(self.selected_id); w=self.preview_window=tk.Toplevel(self.window); w.title('Prévia da ata salva'); w.geometry('620x520'); w.protocol('WM_DELETE_WINDOW',self.close_preview)
        f=ttk.Frame(w,padding=10); f.pack(fill='both',expand=True); t=tk.Text(f,wrap='word'); sb=ttk.Scrollbar(f,command=t.yview); t.configure(yscrollcommand=sb.set); sb.pack(side='right',fill='y'); t.pack(fill='both',expand=True); t.insert('1.0',minutes(item)); t.configure(state='disabled'); t.bind('<<Copy>>',lambda _:'break'); t.bind('<Control-c>',lambda _:'break'); t.bind('<Control-Insert>',lambda _:'break')
        self.copy_button=ttk.Button(f,text='Copiar ata revisada',command=lambda:self.copy(item)); self.copy_button.pack(fill='x'); self.permissions_changed()
        from aeris.theme import apply_tree
        apply_tree(w,self.hub.settings.appearance.theme)
    def copy(self,item):
        if self.preview_window is None or not self.preview_window.winfo_exists() or self.dirty() or self.selected_id!=item.id or self.store.get(item.id) is not item or not self.hub.permissions.allowed(MEETING_COPY): return
        if not messagebox.askyesno('Copiar ata?','O clipboard pode manter informações pessoais. Confirma a cópia?',parent=self.preview_window): return
        if not self.window.winfo_exists() or self.preview_window is None or not self.preview_window.winfo_exists() or self.dirty() or self.selected_id!=item.id or self.store.get(item.id) is not item or not self.hub.permissions.allowed(MEETING_COPY): return
        try: self.hub.root.clipboard_clear(); self.hub.root.clipboard_append(minutes(item))
        except tk.TclError: self.status.set('Falha ao copiar.'); return
        self.status.set('Ata copiada. Cole manualmente no destino.')

    def transfer(self,target):
        from aeris.integration import prepare, execute
        try:
            self.hub.permissions.require(INTEGRATION_RUN)
            if self.selected_id is None or self.dirty(): raise ValueError('Salve a reunião e finalize o rascunho.')
            index=self.action_index()
            item=self.store.get(self.selected_id)
            if index is None: raise ValueError('Selecione uma atividade salva.')
            if not self.hub.enabled(target): raise ValueError('Ative a ferramenta de destino.')
            dest=getattr(self.hub,target.lower()+'_store')
            if dest is None: raise ValueError('Abra a ferramenta de destino primeiro.')
            if target=='Checklist':
                names=dest.names()
                if not names: raise ValueError('Crie uma lista no Checklist primeiro.')
                value=simpledialog.askstring('Lista de destino','Informe o nome exato de uma lista existente:\n'+ '\n'.join(names),parent=self.window)
            else:
                value=simpledialog.askstring('Horário do lembrete','Data da atividade: '+(item.actions[index].due or 'não definida')+'\nInforme o horário local (HH:MM).',parent=self.window)
            if value is None or not self.window.winfo_exists(): return
            if self.dirty() or self.selected_id!=item.id or self.action_index()!=index: raise ValueError('Seleção alterada. Prepare novamente.')
            proposal=prepare(self.hub,item,index,target,value)
            if not messagebox.askyesno('Confirmar integração?',proposal.preview,parent=self.window): return
            if not self.window.winfo_exists(): return
            if self.dirty() or self.selected_id!=item.id or self.action_index()!=index: raise ValueError('Seleção alterada. Prepare novamente.')
            execute(self.hub,proposal,value)
        except (ValueError,KeyError,PermissionError) as exc:
            if self.window.winfo_exists(): self.status.set(str(exc))
            return
        self.status.set('Registro criado em '+target+' na sessão. A reunião permanece inalterada.')
        if target=='Checklist' and self.hub.alive(self.hub.checklist_window): self.hub.checklist_window.render()
        if target=='Reminder':
            self.hub.schedule_reminders()
            if self.hub.alive(self.hub.reminder_window): self.hub.reminder_window.render()
        if self.hub.alive(self.hub.privacy_window): self.hub.privacy_window.refresh()
