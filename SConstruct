import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path("./jcbuilder").absolute()))

ARGUMENTS["DIST_PATH"] = Dir("./tests")

SConscript(Glob("tests_src/**/SConstruct"))
