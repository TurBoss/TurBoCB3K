import os
import sys
from cx_Freeze import setup, Executable

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

files = {"include_files": ["dlls/tcl86t.dll",
                           "dlls/tk86t.dll",
                           "tex/",
                           "images/",
                           "bg-image.png",
                           "Portada.png"],
         "packages": ["asyncio", "jinja2"]
         }

base = None

if sys.platform == "win32":
    base = "Win32GUI"

executables = Executable(script="TBCB3K.py",
                         base=base,
                         icon="icon.ico"
                         )

setup(name="TurBoCB3K",
      version="0.1",
      author="TurBoss",
      description="TurBo Catalog Builder 3000",
      options={"build_exe": files},
      executables=[executables]
      )
