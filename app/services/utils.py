from fastapi import HTTPException
from datetime import datetime
import math

MAIN_CATEGORIES = [
    "astro-ph",   # Astrophysics
    "cond-mat",   # Condensed Matter
    "cs",         # Computer Science
    "econ",       # Economics
    "eess",       # Electrical Engineering and Systems Science
    "gr-qc",      # General Relativity and Quantum Cosmology
    "hep-ex",     # High Energy Physics - Experiment
    "hep-lat",    # High Energy Physics - Lattice
    "hep-ph",     # High Energy Physics - Phenomenology
    "hep-th",     # High Energy Physics - Theory
    "math-ph",    # Mathematical Physics
    "math",       # Mathematics
    "nlin",       # Nonlinear Sciences
    "nucl-ex",    # Nuclear Experiment
    "nucl-th",    # Nuclear Theory
    "physics",    # Physics
    "q-bio",      # Quantitative Biology
    "q-fin",      # Quantitative Finance
    "quant-ph",   # Quantum Physics
    "stat"        # Statistics
]


def timestamp_to_score(ts):
    min_ts = datetime(1991, 1, 1)
    max_ts = datetime.today()
    return (ts - min_ts).total_seconds() / (max_ts - min_ts).total_seconds()

def sigmoid(x):
    return round(1 / (1 + math.exp(-x)), 2)