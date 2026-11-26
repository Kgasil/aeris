import sys
from aeris.distribution import application_lock, self_test


def main():
    if sys.argv[1:] in (['--self-test'], ['--self-test-full']):
        try:
            return self_test(full=True) if sys.argv[1:] == ['--self-test-full'] else self_test()
        except Exception:
            return 1
    if sys.argv[1:]:
        return 2
    from aeris.experience import main as run_hub
    try:
        with application_lock() as acquired:
            if not acquired:
                from tkinter import messagebox
                messagebox.showinfo('Aeris', 'O Aeris já está aberto. Utilize a instância existente.')
                return 3
            run_hub()
    except OSError:
        from tkinter import messagebox
        messagebox.showerror('Aeris', 'Não foi possível iniciar o aplicativo.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
