import time
from typing import Dict, List, Any, Callable

class ExperimentRunner:
    def __init__(self, load_dataset_func, logger):
        self.load_dataset = load_dataset_func
        self.logger = logger
        self.algorithms = {}

    def register(self, name: str, func: Callable, params: Dict[str, Any] = None):
        """
        Register an algorithm.
        params: Static parameters (e.g., {'G': 256} or {'G': 'dynamic'})
        """
        self.algorithms[name] = {'func': func, 'params': params or {}}

    def run_all(self, datasets, combos, gammas, G_values=None):
        """
        Main Loop: Iterates K/k -> Gamma -> Dataset
        """
        for (K, k) in combos:
            for g in gammas:
                W = K / (g * k)
                print(f"\n=== Running Combo: K={K}, k={k}, g={g} ===")

                for shape in datasets:
                    S = self.load_dataset(shape, K)
                    
                    # 1. Run Baseline First (Mandatory for diffs)
                    base_res = self._run_algo("Baseline", S, k, W, None)
                    self._log_entry(shape, K, k, g, W, "Baseline", base_res, None, base_res)

                    # 2. Run Other Algorithms
                    for name, algo_def in self.algorithms.items():
                        if name == "Baseline": continue

                        # Handle Dynamic G (Grid algorithms)
                        if algo_def['params'].get('G') == 'dynamic':
                            if not G_values: continue
                            for G in G_values:
                                res = self._run_algo(name, S, k, W, G, algo_def['params'])
                                self._log_entry(shape, K, k, g, W, name, res, G, base_res)
                        else:
                            # Standard algorithm
                            res = self._run_algo(name, S, k, W, None, algo_def['params'])
                            self._log_entry(shape, K, k, g, W, name, res, None, base_res)
        
        # Save finally
        self.logger.save()

    def _run_algo(self, name, S, k, W, G, extra_params=None):
        algo = self.algorithms[name]
        params = {'S': S, 'k': k, 'W': W}
        if extra_params:
            # Merge static params, filtering out 'G' if it's the marker 'dynamic'
            clean_extras = {k:v for k,v in extra_params.items() if v != 'dynamic'}
            params.update(clean_extras)
        
        if G is not None:
            params['G'] = G

        # Execute
        # Note: Adapting to your specific return signatures is crucial here.
        # Assuming your functions return: (R, score, pss, psr, t_prep, t_sel, *others)
        res = algo['func'](**params)
        
        # Normalize result to dict
        return {
            "score": res[1],
            "pss": res[2],
            "psr": res[3],
            "prep": res[4] if len(res) > 4 else 0,
            "select": res[5] if len(res) > 5 else res[4] if len(res)==5 else 0
        }

    def _log_entry(self, shape, K, k, g, W, name, res, G, base_res):
        entry = {
            "shape": shape, "K": K, "k": k, "W": W, "G": G,
            "K/(k*g)": f"K/(k*{g})",
            "algorithm": name,
            "hpfr": res['score'],
            "pss_sum": res['pss'],
            "psr_sum": res['psr'],
            "prep_time": res['prep'],
            "select_time": res['select'],
            "total_time": res['prep'] + res['select']
        }

        # Diff calculations
        if name != "Baseline" and base_res:
            if base_res['score'] != 0:
                entry["hpfr_diff_%"] = 100 * (res['score'] - base_res['score']) / base_res['score']
            if base_res['pss'] != 0:
                entry["pss_error_%"] = 100 * (res['pss'] - base_res['pss']) / base_res['pss']

        self.logger.log(entry)