import sys
import os
# Adjust path to find sibling directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from log.logger import ExperimentLogger
from log.runner import ExperimentRunner
from scripts.dataset_store import load_dataset  # Note: Check if you have a loader helper
from config import COMBO, GAMMAS, NUM_CELLS, DATASET_NAMES

# Import your actual algorithms
from alg.baseline_iadu import iadu
from alg.grid_iadu import grid_iadu
from alg.biased_sampling import biased_sampling
from alg.hybrid_sampling import hybrid

# Wrapper for dataset loading if needed (to match runner signature)
def loader_wrapper(name, K):
    # Your dataset files seem to follow specific naming conventions
    import pickle
    path = f"datasets/{name}_K{K}.pkl" 
    # Ensure this path matches where your .pkl files actually are
    with open(path, "rb") as f:
        return pickle.load(f)

def run():
    # 1. Setup
    logger = ExperimentLogger("Refactored_Hardcore_Results")
    runner = ExperimentRunner(loader_wrapper, logger)

    # 2. Register Algorithms
    runner.register("Baseline", iadu)
    runner.register("Biased", biased_sampling)
    
    # Grid: "dynamic" tells runner to loop over NUM_CELLS list
    runner.register("Grid IAdU", grid_iadu, params={'G': 'dynamic'})

    # Hybrid: Requires K_sample. We can define a wrapper or pass fixed param
    def hybrid_wrapper(S, k, W, G=None):
        # Example logic: K_sample is 20% of S
        K_sample = int(len(S) * 0.2)
        return hybrid(S, k, K_sample, W)
    
    runner.register("Hybrid", hybrid_wrapper)

    # 3. Run
    # This single line replaces all nested for-loops
    runner.run_all(
        datasets=DATASET_NAMES,
        combos=COMBO,
        gammas=GAMMAS,
        G_values=NUM_CELLS
    )

if __name__ == "__main__":
    run()