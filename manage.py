#!/usr/bin/env python
from django.core.management import execute_manager
import sys

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    do_clean_noreload = not sys.modules.has_key("pydevd")
    if do_clean_noreload:
        try:
            n = sys.argv.index("--noreload")
            if n>=0:
                sys.argv[n:n+1]=[]
                print '"--noreload" cleaned'
        except: pass

    execute_manager(settings)
