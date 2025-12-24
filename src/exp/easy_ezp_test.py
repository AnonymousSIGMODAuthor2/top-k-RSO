import sys
import os

# Adjust path to find sibling directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from log.logger import ExperimentLogger
from log.runner import ExperimentRunner
# Note: Check if you have a loader helper or keep using your custom wrapper below
from alg.baseline_iadu import load_dataset
from config import COMBO, GAMMAS, NUM_CELLS, DATASET_NAMES

# --- ALGORITHM IMPORTS ---
from alg.baseline_iadu import iadu

# IMPORANT: Ensure the functions 'grid_sampling' (Step 1) and 
# 'grid_sampling_weighted' (Step 2) are saved in alg/grid_variants.py
# or update this import to match your filename.
from alg.extension_sampling import grid_sampling, grid_weighted_sampling

def loader_wrapper(name, K):
    """
    Wrapper to load datasets matching the runner's expected signature.
    """
    import pickle
    # Ensure this path matches where your .pkl files actually are
    path = f"datasets/{name}_K{K}.pkl" 
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path}")
        
    with open(path, "rb") as f:
        return pickle.load(f)

def run():
    # 1. Setup Logger and Runner
    # Changed logger name to reflect the specific comparison
    logger = ExperimentLogger("Comparison_Baseline_vs_GridStandard_vs_GridWeighted")
    runner = ExperimentRunner(loader_wrapper, logger)

    # 2. Register Algorithms
    
    # A) Baseline IAdU
    runner.register("Baseline IAdU", iadu)

    # B) Standard Grid Sampling (Option 3 from previous context)
    # 'dynamic' tells the runner to iterate over the 'G_values' list provided in run_all
    runner.register(
        "Grid Standard", 
        grid_sampling, 
        params={'G': 'dynamic'}
    )
    
    # C) Weighted Grid Sampling (New requirement)
    # Also uses dynamic G values
    runner.register(
        "Grid Weighted", 
        grid_weighted_sampling, 
        params={'G': 'dynamic'}
    )

    # 3. Run Experiments
    print(f"Starting experiments on {len(DATASET_NAMES)} datasets...")
    print(f"Comparing: Baseline vs Grid Standard vs Grid Weighted")
    
    runner.run_all(
        datasets=DATASET_NAMES,
        combos=COMBO,      # (k, W) tuples
        gammas=GAMMAS,     # Gamma values for HPFR
        G_values=NUM_CELLS # Grid resolutions to test (e.g., [3, 4, 5])
    )

if __name__ == "__main__":
    run()