import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class ExperimentLogger:
    def __init__(self, experiment_name):
        self.filename = f"{experiment_name}.xlsx"
        self.logs = []
        
        # 1. Define the PREFERRED order for known columns.
        # Any column not in this list will be added automatically at the end.
        self.columns_order = [
            "shape", "K", "k", "W", "K/(k*g)", "G", "lenCL",
            
            # Base
            "base_iadu_hpfr", "base_iadu_pss_sum", "base_iadu_psr_sum",
            
            # Known Methods (order matters here, but names must match what is in runner.py)
            "grid_iadu_hpfr", 
            "grid_weighted_hpfr", 
            "quadtree_sampling_hpfr",
            "biased_sampling_hpfr",
            
            # Times
            "base_iadu_prep_time", "grid_iadu_prep_time", "grid_weighted_prep_time", "quadtree_sampling_prep_time",
            "base_iadu_sel_time", "grid_iadu_sel_time", "grid_weighted_sel_time", "quadtree_sampling_sel_time",
            "base_iadu_x_time", "grid_iadu_x_time", "grid_weighted_x_time", "quadtree_sampling_x_time"
        ]

    def log(self, row_dict):
        self.logs.append(row_dict)

    def _calculate_metrics(self, df):
        """Calculates Diff% and Speedup for ALL methods found in the dataframe."""
        base_col = "base_iadu_hpfr"
        base_time_col = "base_iadu_x_time"
        
        # 1. Find all score columns (ending in _hpfr)
        hpfr_cols = [c for c in df.columns if c.endswith("_hpfr") and c != base_col]
        
        for score_col in hpfr_cols:
            # Calculate Diff%
            diff_col = score_col + "_diff%"
            if base_col in df.columns:
                df[diff_col] = df.apply(
                    lambda row: (row[score_col] - row[base_col]) / row[base_col] if row[base_col] != 0 else 0,
                    axis=1
                )

        # 2. Find all total time columns (ending in _x_time)
        time_cols = [c for c in df.columns if c.endswith("_x_time") and c != base_time_col]
        
        for time_col in time_cols:
            # Calculate Speedup
            speedup_col = time_col.replace("_x_time", "_speedup")
            if base_time_col in df.columns:
                df[speedup_col] = df.apply(
                    lambda row: row[base_time_col] / row[time_col] if row[time_col] != 0 else 0,
                    axis=1
                )
        return df

    def _reorder_columns(self, df):
        """Smartly orders columns: Fixed Order -> Derived (Diff/Speedup) -> Remaining."""
        final_cols = []
        added_cols = set()

        def add_col_group(col_name):
            """Helper to add a column AND its associated metric (diff/speedup) immediately."""
            if col_name in df.columns and col_name not in added_cols:
                final_cols.append(col_name)
                added_cols.add(col_name)
                
                # Check for associated Diff% (for scores)
                diff_name = col_name + "_diff%"
                if diff_name in df.columns and diff_name not in added_cols:
                    final_cols.append(diff_name)
                    added_cols.add(diff_name)

                # Check for associated Speedup (for times)
                # Assuming time format: {method}_x_time -> {method}_speedup
                if col_name.endswith("_x_time"):
                    method_prefix = col_name.replace("_x_time", "")
                    speedup_name = f"{method_prefix}_speedup"
                    if speedup_name in df.columns and speedup_name not in added_cols:
                        final_cols.append(speedup_name)
                        added_cols.add(speedup_name)

        # 1. Process the User-Defined Order first
        for col in self.columns_order:
            add_col_group(col)

        # 2. Process all remaining columns (dynamically discovered methods)
        # We sort them to keep "method_A_..." columns grouped together
        remaining = sorted([c for c in df.columns if c not in added_cols])
        
        for col in remaining:
            # Skip diff/speedup columns here; they are added when their 'parent' is processed
            if col.endswith("_diff%") or col.endswith("_speedup"):
                continue
            add_col_group(col)

        # 3. Catch-all: If any diff/speedup columns were orphaned (parent missing), add them now
        for col in df.columns:
            if col not in added_cols:
                final_cols.append(col)
                added_cols.add(col)

        return df[final_cols]

    def save(self):
        if not self.logs:
            print("No logs to save.")
            return

        # 1. Create DataFrames
        df_detailed = pd.DataFrame(self.logs)
        
        # Calculate metrics for everything found in the logs
        df_detailed = self._calculate_metrics(df_detailed)
        
        # Reorder cleanly
        df_detailed = self._reorder_columns(df_detailed)

        # 2. Create Summary (Group by Settings)
        group_keys = [k for k in ["K", "k", "W", "K/(k*g)", "G"] if k in df_detailed.columns]
        
        if group_keys:
            df_summary = df_detailed.groupby(group_keys).mean(numeric_only=True).reset_index()
            # Re-calculate metrics on the averages to be mathematically correct
            df_summary = self._calculate_metrics(df_summary)
            df_summary = self._reorder_columns(df_summary)
            
            # Clean up nonsense columns in summary
            drop_cols = [c for c in ["shape", "lenCL"] if c in df_summary.columns]
            df_summary = df_summary.drop(columns=drop_cols)
        else:
            df_summary = pd.DataFrame()

        # 3. Save to Excel
        with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name='Settings Summary', index=False)
            df_detailed.to_excel(writer, sheet_name='Detailed Results', index=False)
        
        self._apply_pro_styling()
        print(f"✔ Results saved correctly to: {self.filename}")

    def _apply_pro_styling(self):
        try:
            wb = load_workbook(self.filename)
            
            for ws in wb.worksheets:
                # Styles
                header_fill = PatternFill(start_color="404040", end_color="404040", fill_type="solid")
                header_font = Font(bold=True, color="FFFFFF", size=11)
                
                colors = {
                    "setup": "E7E6E6", "score": "E2EFDA", "diff": "D0CECE", 
                    "prep": "FFF2CC", "sel": "FCE4D6", "time": "DDEBF7", "speedup": "E2EFDA"
                }

                # Format Headers
                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                
                ws.freeze_panes = "B2"

                # Format Columns
                for i, col_cells in enumerate(ws.columns, start=1):
                    header_val = str(col_cells[0].value)
                    col_letter = get_column_letter(i)
                    
                    # Width
                    max_len = max([len(str(c.value)) if c.value is not None else 0 for c in col_cells[:10]])
                    ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 50)

                    # Colors
                    fill_color = None
                    if "diff%" in header_val: fill_color = colors["diff"]
                    elif "speedup" in header_val: fill_color = colors["speedup"]
                    elif any(x in header_val for x in ["shape", "K", "k", "W", "G"]): fill_color = colors["setup"]
                    elif "hpfr" in header_val: fill_color = colors["score"]
                    elif "prep_time" in header_val: fill_color = colors["prep"]
                    elif "sel_time" in header_val: fill_color = colors["sel"]
                    elif "x_time" in header_val: fill_color = colors["time"]

                    if fill_color:
                        fill_obj = PatternFill(start_color=fill_color, fill_type="solid")
                        for cell in col_cells[1:]:
                            cell.fill = fill_obj
                            
                            # Number Formatting
                            if "diff%" in header_val: cell.number_format = '0.00%'
                            elif "speedup" in header_val: cell.number_format = '0.00"x"'
                            elif isinstance(cell.value, float):
                                cell.number_format = '0.000' if abs(cell.value) > 0.01 else '0.00E+00'
            
            wb.save(self.filename)
        except Exception as e:
            print(f"Warning: Styling step failed: {e}")