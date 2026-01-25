import math
import numpy as np
import matplotlib.pyplot as plt
from models import SquareGrid

class DynamicPlotter:
    def __init__(self, S, title="Experiment Results"):
        """
        Args:
            S (List[Place]): The full dataset (Blue points). 
                             Must match the Place object from models.py.
            title (str): Global title for the figure.
        """
        self.S = S
        self.title = title
        self.experiments = []
        
        # Pre-convert S to numpy for faster plotting [N, 2]
        self.S_coords = np.array([p.coords for p in S])
        
    def register(self, method_name, R, score=None, G=None):
        """
        Registers an experiment to be plotted.
        
        Args:
            method_name (str): Label for the subplot (e.g., "Grid IAdU").
            R (List[Place]): The selected points (Red points).
            score (float, optional): The HPFR or other score to display in title.
            G (int, optional): If provided, draws the grid lines and 
                               cell stats (Selected/Total).
        """
        self.experiments.append({
            'name': method_name,
            'R': R,
            'score': score,
            'G': G
        })

    def plot(self, filename=None):
        """Generates and shows (or saves) the plot."""
        n = len(self.experiments)
        if n == 0:
            print("No experiments registered to plot.")
            return

        # 1. Dynamic Layout Calculation
        cols = 2 if n >= 2 else 1
        if n > 4: cols = 3
        rows = math.ceil(n / cols)
        
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
        if n == 1: axes = [axes] # Handle single subplot case
        else: axes = axes.flatten()

        fig.suptitle(self.title, fontsize=16, y=0.98)

        # 2. Iterate through registered experiments
        for i, exp in enumerate(self.experiments):
            ax = axes[i]
            
            # --- A. Plot Base Dataset (S) ---
            # Blue, faint background
            ax.scatter(self.S_coords[:,0], self.S_coords[:,1], 
                       c='lightblue', s=10, alpha=0.6, label='S', edgecolors='none')

            # --- B. Plot Selected Points (R) ---
            # Red, prominent foreground
            if exp['R']:
                R_coords = np.array([p.coords for p in exp['R']])
                if len(R_coords) > 0:
                    ax.scatter(R_coords[:,0], R_coords[:,1], 
                               c='red', s=25, label='R', zorder=5, edgecolors='black', linewidth=0.5)

            # --- C. Grid Logic (if G is provided) ---
            if exp['G'] and exp['G'] > 0:
                self._draw_grid_and_stats(ax, exp['G'], exp['R'])

            # --- D. Titles and Styling ---
            title_text = exp['name']
            if exp['score'] is not None:
                # Handle both float scores and string descriptions
                if isinstance(exp['score'], (float, int)):
                    title_text += f"\nScore: {exp['score']:.4f}"
                else:
                    title_text += f"\n{exp['score']}"
            
            ax.set_title(title_text, fontsize=11)
            ax.set_aspect('equal') # Crucial for spatial data correctness
            ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False) # Clean look

        # 3. Hide unused subplots
        for j in range(n, len(axes)):
            axes[j].axis('off')

        plt.tight_layout()
        
        if filename:
            plt.savefig(filename)
            print(f"Saved plot to {filename}")
        else:
            plt.show()

    def _draw_grid_and_stats(self, ax, G, R):
        """
        Uses models.SquareGrid logic to draw lines and calculate 
        'Selected / Total' counts per cell.
        """
        # 1. Instantiate SquareGrid with S to get exact geometry used in algorithms
        # We assume 'S' defines the bounds, just like in your models.py logic
        grid = SquareGrid(self.S, G) 
        Ax, Ay = grid.dims()
        
        # 2. Draw Grid Lines
        # SquareGrid calculates cell_w and cell_h based on tight S bounds
        x_min, y_min = grid.x_min, grid.y_min
        cell_w, cell_h = grid.cell_w, grid.cell_h
        
        for r in range(Ay + 1):
            y = y_min + r * cell_h
            ax.axhline(y=y, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
            
        for c in range(Ax + 1):
            x = x_min + c * cell_w
            ax.axvline(x=x, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)

        # 3. Calculate Stats (R_count / S_count)
        # We rely on grid internal logic to map (x,y) -> (gx, gy)
        
        # Count S (Base)
        # grid.get_grid() returns populated cells with .size() being count of S
        s_counts = {k: v.size() for k, v in grid.get_grid().items()}
        
        # Count R (Selected) - We must map R points to the same grid structure
        r_counts = {}
        for p in R:
            # Use the exact helper from SquareGrid to ensure consistency
            gx, gy = grid._to_index(p.coords[0], p.coords[1])
            r_counts[(gx, gy)] = r_counts.get((gx, gy), 0) + 1

        # 4. Annotate Cells
        for gx in range(Ax):
            for gy in range(Ay):
                n_s = s_counts.get((gx, gy), 0)
                n_r = r_counts.get((gx, gy), 0)
                
                # Only annotate if there is data in the cell
                if n_s > 0:
                    cx = x_min + (gx + 0.5) * cell_w
                    cy = y_min + (gy + 0.5) * cell_h
                    
                    label = f"{n_r}/{n_s}"
                    ax.text(cx, cy, label, 
                            fontsize=7, ha='center', va='center', weight='bold',
                            bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none", alpha=0.6))