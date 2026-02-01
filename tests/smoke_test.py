"""Check that basic features work before publishing on Pypi

Catch cases where e.g. files are missing so the import doesn't work. It is
recommended to check that e.g. assets are included."""

from skillsmd.cli import main

if __name__ == '__main__':
    main()
