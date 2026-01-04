import sys
import os
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Ensure parent directory is in path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config as cfg
from log.logger import ExperimentLogger
from log.runner import ExperimentRunner
from models import SquareGrid

# --- ALGORITHM IMPORTS ---
from alg.baseline_iadu import iadu, load_dataset, plot_selected
from alg.grid_iadu import grid_iadu
from alg.extension_sampling import grid_weighted_sampling, quadtree_sampling
from alg.biased_sampling import biased_sampling

# Global PDF object
pdf_pages = None 

def plot_comparison_results(S, shape, K, k, G, algo_results):
    """
    Visualizes multiple algorithms side-by-side in the PDF.
    Grid-based algorithms show the grid overlay.
    """
    global pdf_pages
    if pdf_pages is None: return

    # We will create a grid of plots. 
    # Row 1: Baseline, Grid IAdU, Grid Weighted
    # Row 2: QuadTree, Biased Sampling
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f"Dataset: {shape} | K={K}, k={k}, G={G} (Cells)", fontsize=16)
    
    # Flatten axes for easy iteration
    ax = axes.flatten()

    # Shared grid object for visualization
    try:
        grid = SquareGrid(S, G)
    except:
        grid = None

    # Helper to plot if algorithm succeeded
    def plot_helper(algo_name, title, index, show_grid=True):
        if algo_name in algo_results:
            res = algo_results[algo_name]
            # Some functions return extra stats at specific indices
            cell_stats = None
            if algo_name in ['grid_weighted', 'quadtree']:
                # extension_sampling functions return cell_stats at index 7 of raw_res
                cell_stats = res['raw_res'][7] if len(res['raw_res']) > 7 else None
            
            plot_selected(S, res['R'], f"{title}\nScore: {res['score']:.4f}", ax[index], 
                          grid=grid if show_grid else None, 
                          cell_stats=cell_stats)
        else:
            ax[index].text(0.5, 0.5, f"{title}\nNot Found/Failed", ha='center')
            ax[index].set_axis_off()

    # 1. Baseline IAdU
    plot_helper('base_iadu', "Baseline IAdU", 0, show_grid=False)

    # 2. Grid IAdU
    plot_helper('grid_iadu', "Grid IAdU", 1, show_grid=True)

    # 3. Grid Weighted Sampling
    plot_helper('grid_weighted', "Grid Weighted", 2, show_grid=True)

    # 4. QuadTree Sampling
    plot_helper('quadtree', "QuadTree Sampling", 3, show_grid=False)

    # 5. Biased Sampling (Random)
    plot_helper('biased_sampling', "Biased Sampling", 4, show_grid=False)

    # 6. Information Text or Blank
    ax[5].axis('off')
    info_text = (f"Experiment Summary:\n"
                 f"Shape: {shape}\n"
                 f"K: {K}, k: {k}\n"
                 f"Grid: {G} cells")
    ax[5].text(0.1, 0.5, info_text, fontsize=12, verticalalignment='center')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    pdf_pages.savefig(fig)
    plt.close(fig)

def run():
    global pdf_pages
    output_pdf = "results.pdf"
    pdf_pages = PdfPages(output_pdf)
    
    # Initialize Logger
    logger = ExperimentLogger("hardcore_comparison")
    
    # Initialize Runner
    runner = ExperimentRunner(load_dataset, logger, plot_callback=plot_comparison_results)

    # --- Register All Algorithms ---
    runner.register("base_iadu", iadu) 
    runner.register("grid_iadu", grid_iadu)
    runner.register("grid_weighted", grid_weighted_sampling)
    
    # QuadTree requires m (max capacity) and d (max depth)
    runner.register("quadtree", quadtree_sampling, params={'m': 30, 'd': 6})
    
    runner.register("biased_sampling", biased_sampling)

    print(f"=== Starting Comprehensive Comparison ===")
    print(f"Datasets: {cfg.DATASET_NAMES}")
    print(f"Combos (K, k): {cfg.COMBO}")
    print(f"Grid Sizes: {cfg.NUM_CELLS}")
    
    try:
        runner.run_all(
            datasets=cfg.DATASET_NAMES, 
            combos=cfg.COMBO, 
            gammas=cfg.GAMMAS, 
            G_values=cfg.NUM_CELLS
        )
    except KeyboardInterrupt:
        print("\nExperiment interrupted.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pdf_pages.close()
        logger.save()
        print(f"\n✔ PDF Plots saved to: {output_pdf}")
        print(f"✔ Excel Logs saved to: comprehensive_comparison.xlsx")

if __name__ == "__main__":
    run()