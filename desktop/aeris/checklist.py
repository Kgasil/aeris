"""Bounded in-memory task lists. No disk, network or background activity."""
from dataclasses import dataclass, replace

PRIORITIES = ('Baixa', 'Normal', 'Alta')
MAX_LISTS = 20
MAX_TASKS = 100  # per list


def clean(value, limit):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError(f'Texto obrigatório, sem controles, até {limit} caracteres.')
    return value.strip()


@dataclass(frozen=True)
class Task:
    id: int
    title: str
    priority: str = 'Normal'
    done: bool = False


class ChecklistStore:
    def __init__(self):
        self._lists = {}
        self._next_id = 1

    def names(self):
        return tuple(self._lists)

    def list(self):
        # Privacy inventory counts tasks, not their contents.
        return tuple(t for tasks in self._lists.values() for t in tasks.values())

    def create(self, name):
        name = clean(name, 80)
        if name in self._lists:
            raise ValueError('Lista já existe.')
        if len(self._lists) >= MAX_LISTS:
            raise ValueError('Limite de 20 listas.')
        self._lists[name] = {}
        return name

    def rename(self, old, new):
        new = clean(new, 80)
        if old == new:
            if old not in self._lists: raise KeyError(old)
            return old
        if new in self._lists: raise ValueError('Lista já existe.')
        tasks = self._lists.pop(old)
        self._lists[new] = tasks
        return new

    def delete_list(self, name):
        del self._lists[name]

    def tasks(self, name):
        return tuple(self._lists[name].values())

    def add(self, name, title, priority='Normal'):
        title = clean(title, 200)
        if priority not in PRIORITIES: raise ValueError('Prioridade inválida.')
        tasks = self._lists[name]
        if len(tasks) >= MAX_TASKS: raise ValueError('Limite de 100 tarefas por lista.')
        task = Task(self._next_id, title, priority)
        tasks[task.id] = task
        self._next_id += 1
        return task

    def edit(self, name, task_id, title, priority):
        title = clean(title, 200)
        if priority not in PRIORITIES: raise ValueError('Prioridade inválida.')
        tasks = self._lists[name]
        tasks[task_id] = replace(tasks[task_id], title=title, priority=priority)
        return tasks[task_id]

    def toggle(self, name, task_id):
        tasks = self._lists[name]
        task = tasks[task_id]
        tasks[task_id] = replace(task, done=not task.done)
        return tasks[task_id]

    def delete(self, name, task_id):
        del self._lists[name][task_id]

    def progress(self, name):
        tasks = self.tasks(name)
        return sum(t.done for t in tasks), len(tasks)

    def clear(self):
        self._lists.clear()
