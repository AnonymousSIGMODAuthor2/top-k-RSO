import sys
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Adjust path to find sibling directories (src/)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from log.logger import ExperimentLogger
from log.runner import ExperimentRunner
from config import COMBO, GAMMAS, NUM_CELLS, DATASET_NAMES
from models import SquareGrid

# --- ALGORITHM IMPORTS ---
# Note: We import plot_selected to reuse the drawing logic
from alg.baseline_iadu import iadu, load_dataset, plot_selected
from alg.extension_sampling import grid_sampling, grid_weighted_sampling
from alg.biased_sampling import biased_sampling

# --- PLOTTING LOGIC ---
pdf_pages = None # Global or passed via closure

def plot_experiment_results(S, shape, K, k, G, algo_results):
    """
    Callback function executed by the Runner after every grid iteration.
    algo_results: {'base_iadu': {'R': ..., 'score': ...}, ...}
    """
    global pdf_pages
    if pdf_pages is None: return

    # Recreate Grid object for visualization
    try:
        grid = SquareGrid(S, G)
        lenCL = len(grid.get_full_cells())
    except:
        grid = None
        lenCL = "N/A"

    # Setup Figure
    fig, axes = plt.subplots(1, 3, figsize=(21, 7))
    fig.suptitle(f"Shape: {shape}  |  K={K}, k={k}  |  G={G}  |  lenCL={lenCL}", fontsize=16)
    
    # 1. Plot Base IAdU
    if 'base_iadu' in algo_results:
        res = algo_results['base_iadu']
        plot_selected(S, res['R'], f"Base IAdU\nHPFR: {res['score']: .4f}", axes[0], grid=grid)
    
    # 2. Plot Grid Standard
    if 'grid_sampling' in algo_results:
        res = algo_results['grid_sampling']
        # Try to extract cell_stats if it exists (it was index 7 in the old file)
        # In runner we saved the full tuple in 'raw_res'
        full_tuple = res['raw_res']
        cell_stats = full_tuple[7] if len(full_tuple) > 7 else None
        
        plot_selected(S, res['R'], f"Grid Sampling\nHPFR: {res['score']: .4f}", axes[1], grid=grid, cell_stats=cell_stats)
    
    # 3. Plot Biased
    if 'biased' in algo_results:
        res = algo_results['biased']
        plot_selected(S, res['R'], f"Biased Sampling\nHPFR: {res['score']: .4f}", axes[2], grid=grid)

    pdf_pages.savefig(fig)
    plt.close(fig)

def run():
    global pdf_pages
    
    # 1. Setup PDF
    pdf_filename = "test_results.pdf"
    pdf_pages = PdfPages(pdf_filename)
    
    # 2. Setup Logger & Runner
    logger = ExperimentLogger("test")
    
    # Pass the plotting callback here!
    runner = ExperimentRunner(load_dataset, logger, plot_callback=plot_experiment_results)

    # 3. Register Algorithms
    runner.register("base_iadu", iadu) 
    
    runner.register(
        "grid_sampling", 
        grid_sampling, 
        params={'G': 'dynamic'}
    )
    
    runner.register(
        "biased", 
        biased_sampling
    )

    # 4. Run Experiments
    print(f"Starting experiments on {len(DATASET_NAMES)} datasets...")
    
    try:
        runner.run_all(
            datasets=DATASET_NAMES,
            combos=COMBO,
            gammas=GAMMAS,
            G_values=NUM_CELLS
        )
    finally:
        # Ensure PDF closes even if error
        pdf_pages.close()
        print(f"✔ PDF Plots saved to: {pdf_filename}")

if __name__ == "__main__":
    run()