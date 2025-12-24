import time
import inspect
from typing import Dict, List, Any, Callable

# Import the optimization target for precomputation
from alg.baseline_iadu import base_precompute

class ExperimentRunner:
    def __init__(self, load_dataset_func, logger, plot_callback=None):
        self.load_dataset = load_dataset_func
        self.logger = logger
        self.algorithms = {}
        self.plot_callback = plot_callback  # <--- NEW: Store the callback

    def register(self, name: str, func: Callable, params: Dict[str, Any] = None):
        self.algorithms[name] = {'func': func, 'params': params or {}}

    def run_all(self, datasets, combos, gammas, G_values):
        for (K, k) in combos:
            for g in gammas:
                W = K / (g * k)
                print(f"\n=== Running Combo: K={K}, k={k}, g={g} ===")

                for shape in datasets:
                    S = self.load_dataset(shape, K)
                    if not S:
                        print(f"  [Skipping] Dataset '{shape}' not found.")
                        continue

                    print(f"  > Precomputing Exact Baseline stats for {shape}...")
                    exact_psS, exact_sS, exact_base_prep_time = base_precompute(S)
                    
                    precomputed_context = {
                        'exact_psS': exact_psS, 
                        'exact_sS': exact_sS, 
                        'base_prep_time': exact_base_prep_time
                    }

                    for G in G_values:
                        row = {
                            "shape": shape, "K": K, "k": k, "W": W,
                            "K/(k*g)": f"K/(k * {g})", "G": G, "lenCL": 0 
                        }

                        # --- NEW: Dictionary to store plotting data for this iteration ---
                        current_algo_results = {}

                        for name, algo_def in self.algorithms.items():
                            # Capture the result data (R, score, extras)
                            result_data = self._run_and_record(
                                name, algo_def, S, k, W, G, 
                                row, precomputed_context
                            )
                            if result_data:
                                current_algo_results[name] = result_data

                        self.logger.log(row)

                        # --- NEW: Trigger Plotting Callback ---
                        if self.plot_callback:
                            self.plot_callback(S, shape, K, k, G, current_algo_results)
        
        self.logger.save()

    def _run_and_record(self, name, algo_def, S, k, W, G, row, context):
        func = algo_def['func']
        
        available_args = {
            'S': S, 'k': k, 'W': W, 'G': G,
            'exact_psS': context['exact_psS'],     
            'exact_sS': context['exact_sS'],       
            'prep_time': context['base_prep_time'],
            'psS': context['exact_psS'], 
            'sS': context['exact_sS'],
            'optimal_psS': context['exact_psS'], 
            'optimal_sS': context['exact_sS']
        }

        sig = inspect.signature(func)
        call_kwargs = {k: v for k, v in available_args.items() if k in sig.parameters}
        
        try:
            res = func(**call_kwargs)
            
            # Unpack standard returns
            # (R, score, sum_pss, sum_psr, prep_t, sel_t, ...)
            R = res[0]
            score = res[1]
            sum_pss = res[2] 
            sum_psr = res[3]
            prep_t = res[4]
            sel_t = res[5]

            if name == "base_iadu":
                prep_t = context['base_prep_time']

            if len(res) > 6 and name == "grid_sampling":
                row["lenCL"] = res[6]

            row[f"{name}_hpfr"] = score
            row[f"{name}_pss_sum"] = sum_pss
            row[f"{name}_psr_sum"] = sum_psr
            row[f"{name}_prep_time"] = prep_t
            row[f"{name}_sel_time"] = sel_t
            row[f"{name}_x_time"] = prep_t + sel_t

            # --- NEW: Return data needed for plotting ---
            return {
                'R': R,
                'score': score,
                'raw_res': res # Keep full tuple for custom extraction (e.g. cell_stats)
            }

        except Exception as e:
            print(f"  Error running {name} on {row['shape']} G={G}: {e}")
            for suffix in ["hpfr", "pss_sum", "psr_sum", "prep_time", "sel_time", "x_time"]:
                row[f"{name}_{suffix}"] = 0
            return None