import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from models import SquareGrid
from alg.baseline_iadu import plot_selected

class ExperimentPlotter:
    def __init__(self, filename="results.pdf"):
        self.filename = filename
        self.pdf = PdfPages(filename)
        print(f"   -> Plotter initialized. Saving to: {self.filename}")

    def plot_results(self, S, shape, K, k, G, algo_results):
        """
        Universal plotter that adapts to ANY number of algorithms and settings.
        Handles errors gracefully (e.g. if Grid generation fails).
        """
        if not algo_results:
            return

        # 1. Determine Grid Dimensions (Rows x Cols) based on number of algorithms
        n = len(algo_results)
        
        # Aesthetic logic for subplot layout
        if n == 1: cols = 1
        elif n == 2: cols = 2
        elif n == 4: cols = 2 # 2x2 looks better than 1x4
        else: cols = min(n, 3) # Max 3 columns
        
        rows = math.ceil(n / cols)

        # 2. Create Figure
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
        
        # 3. Safe Grid Creation (Fail-safe)
        grid_info = f"G={G}"
        grid_obj = None
        try:
            if S and G > 0:
                grid_obj = SquareGrid(S, G)
                Ax, Ay = grid_obj.dims()
                grid_info += f" ({Ax}x{Ay})"
        except Exception as e:
            # If grid fails (e.g. empty S), we just log it and proceed without grid lines
            print(f"Warning: Could not create visualization grid for G={G}: {e}")
            grid_obj = None
            
        fig.suptitle(f"Dataset: {shape} | K={K}, k={k} | {grid_info}", fontsize=16)

        # 4. Flatten axes for easy iteration
        if n == 1:
            ax_list = [axes]
        else:
            ax_list = axes.flatten()

        # 5. Plot Each Algorithm
        for i, (algo_key, res) in enumerate(algo_results.items()):
            ax = ax_list[i]
            
            # Title Formatting: "grid_weighted" -> "Grid Weighted"
            display_title = algo_key.replace("_", " ").title()
            
            # Heuristic: Show grid lines only for grid/tree based methods
            name_lower = algo_key.lower()
            show_grid_lines = any(x in name_lower for x in ['grid', 'tree', 'quad', 'strata'])
            
            # Heuristic: Check for cell selection stats in the result tuple
            cell_stats = None
            if 'raw_res' in res and isinstance(res['raw_res'], tuple):
                if len(res['raw_res']) > 7:
                    cell_stats = res['raw_res'][7]

            try:
                score_val = res.get('score', 0.0)
                plot_selected(
                    S, 
                    res['R'], 
                    f"{display_title}\nScore: {score_val:.4f}", 
                    ax, 
                    grid=(grid_obj if show_grid_lines else None), 
                    cell_stats=cell_stats
                )
            except Exception as e:
                # If a specific plot fails, show error text but don't crash entire script
                ax.text(0.5, 0.5, f"Error Plotting\n{e}", ha='center', color='red')
                ax.set_axis_off()

        # 6. Hide unused subplots
        for j in range(n, len(ax_list)):
            ax_list[j].axis('off')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        self.pdf.savefig(fig)
        plt.close(fig)

    def close(self):
        """Closes the PDF file properly."""
        if self.pdf:
            self.pdf.close()
            print(f"✔ PDF Plots saved/closed: {self.filename}")