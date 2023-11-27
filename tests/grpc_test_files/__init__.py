# To ensure that the proto files do find their dependencies

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
