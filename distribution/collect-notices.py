"""Copy license texts from installed build metadata for review, not certification."""
from importlib.metadata import distribution
from pathlib import Path
import shutil
import sys


def main():
    destination = Path(sys.argv[1])
    for name in ('pyinstaller', 'pyinstaller-hooks-contrib'):
        dist = distribution(name)
        copied = 0
        for entry in dist.files or ():
            if entry.name.lower().startswith(('license', 'copying', 'notice')):
                source = Path(dist.locate_file(entry))
                if source.is_file():
                    copied += 1
                    shutil.copyfile(source, destination / f'{name}-{copied}-{entry.name}')
        if name == 'pyinstaller' and not copied:
            raise RuntimeError('PyInstaller license not found; inspect distribution before proceeding')


if __name__ == '__main__':
    main()
