import sys
from aeris.distribution import application_lock, self_test


def main():
    if sys.argv[1:] in (['--self-test'], ['--self-test-full']):
        try:
            return self_test(full=True) if sys.argv[1:] == ['--self-test-full'] else self_test()
        except Exception:
            return 1
    from aeris.terms import forget, require_acceptance
    if sys.argv[1:] == ['--forget-terms']:
        try:
            forget()
            return 0
        except OSError:
            return 1
    configure = sys.argv[1:] == ['--configure-ai']
    if sys.argv[1:] and not configure:
        return 2
    from aeris.experience import main as run_hub
    try:
        with application_lock() as acquired:
            if not acquired:
                from tkinter import messagebox
                messagebox.showinfo('Aeris', 'O Aeris já está aberto. Utilize a instância existente.')
                return 3
            if not require_acceptance():
                return 4
            run_hub(configure=configure)
    except (OSError, ValueError):
        from tkinter import messagebox
        messagebox.showerror('Aeris', 'Não foi possível iniciar o aplicativo.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
