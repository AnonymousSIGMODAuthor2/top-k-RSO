import sys
import os

# --- 1. Import your new class ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from log.logger import ExperimentLogger
from log.runner import ExperimentRunner
from log.plotter import DynamicPlotter  


# --- ALGORITHMS ---
from alg.baseline_iadu import iadu, iadu_no_r, load_dataset
from alg.biased_sampling import biased_sampling
from alg.extension_sampling import grid_weighted_sampling, stratified_sampling
import config as cfg

# --- UPDATED BRIDGE FUNCTION ---
def plot_bridge(S, shape, K, k, G, algo_results, context=None):
    """
    Args:
        context (dict): Contains 'W', 'g', etc. passed from Runner.
    """
    if not algo_results:
        return

    # 1. Extract W and g for the title and filename
    W = context.get('W', 0) if context else 0
    g = context.get('g', 0) if context else 0
    
    # 2. Setup Plotter
    plot_title = f"{shape} | K={K}, k={k}, G={G} | W={W:.2f} (g={g})"
    dp = DynamicPlotter(S, title=plot_title)

    # 3. Register Algorithms
    for algo_name, res in algo_results.items():
        clean_name = algo_name.replace("_", " ").title()
        
        # Only draw grid lines for grid-based methods
        use_grid = G if "grid" in algo_name.lower() else None
        
        dp.register(
            method_name=clean_name,
            R=res.get('R', []),
            score=res.get('score', 0),
            G=use_grid
        )

    # 4. Save with Detailed Filename
    # Filename format: shape_K_k_G_W_g.pdf
    os.makedirs("plots", exist_ok=True)
    filename = f"plots/{shape}_K{K}_k{k}_G{G}_W{W:.2f}_g{g}.pdf"
    
    dp.plot(filename)

# --- MAIN ---
def run():
    logger = ExperimentLogger("optical_test_results", baseline_name="base_iadu")
    
    # Pass the updated bridge
    runner = ExperimentRunner(load_dataset, logger, plot_callback=plot_bridge)

    print("Registering algorithms...")
    runner.register("base_iadu", iadu)
    runner.register("stratified_sampling", stratified_sampling)
    runner.register("biased_sampling", biased_sampling)
    runner.register("grid_weighted", grid_weighted_sampling)

    print(f"=== Starting Experiment ===")
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
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.save()

if __name__ == "__main__":
    run()