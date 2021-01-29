import sys
from pathlib import Path

path = Path(__file__).parent.absolute()
sys.path.append(str(path))

def run_simulation():
    import run_simulation
