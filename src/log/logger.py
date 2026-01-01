import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class ExperimentLogger:
    def __init__(self, experiment_name):
        self.filename = f"{experiment_name}.xlsx"
        self.logs = []
        
        # 1. Define the STRICT column order
        # Added 'diff' columns next to their respective method's HPFR
        self.columns_order = [
            "shape", "K", "k", "W", "K/(k*g)", "G", "lenCL",
            
            # Base (Reference)
            "base_iadu_hpfr", "base_iadu_pss_sum", "base_iadu_psr_sum",
            
            # Standard Grid
            "grid_standard_hpfr", "grid_standard_hpfr_diff%", "grid_standard_pss_sum", "grid_standard_psr_sum",
            
            # Weighted Grid
            "grid_weighted_hpfr", "grid_weighted_hpfr_diff%", "grid_weighted_pss_sum", "grid_weighted_psr_sum",

            # Quadtree
            "quadtree_sampling_hpfr", "quadtree_sampling_hpfr_diff%", "quadtree_sampling_pss_sum", "quadtree_sampling_psr_sum",
            
            # Prep Times
            "base_iadu_prep_time", "grid_standard_prep_time", "grid_weighted_prep_time", "quadtree_sampling_prep_time",
            
            # Selection Times
            "base_iadu_sel_time", "grid_standard_sel_time", "grid_weighted_sel_time", "quadtree_sampling_sel_time",
            
            # Total Times
            "base_iadu_x_time", "grid_standard_x_time", "grid_weighted_x_time", "quadtree_sampling_x_time"
        ]

    def log(self, row_dict):
        self.logs.append(row_dict)

    def save(self):
        if not self.logs:
            print("No logs to save.")
            return

        df = pd.DataFrame(self.logs)
        
        # --- NEW: Calculate Diff% Columns ---
        # Formula: (Method - Base) / Base
        base_col = "base_iadu_hpfr"
        targets = [
            ("grid_standard_hpfr", "grid_standard_hpfr_diff%"),
            ("grid_weighted_hpfr", "grid_weighted_hpfr_diff%"),
            ("quadtree_sampling_hpfr", "quadtree_sampling_hpfr_diff%")
        ]
        
        if base_col in df.columns:
            for score_col, diff_col in targets:
                if score_col in df.columns:
                    # Calculate percentage difference (e.g. 0.05 for 5%)
                    df[diff_col] = (df[score_col] - df[base_col]) / df[base_col]
        
        # Reorder columns: Keep strict order, append any new/unknown columns at the end
        existing_cols = [c for c in self.columns_order if c in df.columns]
        remaining_cols = [c for c in df.columns if c not in existing_cols]
        final_cols = existing_cols + remaining_cols
        
        df = df[final_cols]
        
        df.to_excel(self.filename, index=False)
        self._apply_pro_styling(df)
        print(f"✔ Results saved with DIFF% Columns to: {self.filename}")

    def _apply_pro_styling(self, df):
        try:
            wb = load_workbook(self.filename)
            ws = wb.active
            
            # 1. Define Styles
            header_fill = PatternFill(start_color="404040", end_color="404040", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            thin_border = Border(left=Side(style='thin', color="D9D9D9"), 
                                 right=Side(style='thin', color="D9D9D9"),
                                 top=Side(style='thin', color="D9D9D9"), 
                                 bottom=Side(style='thin', color="D9D9D9"))
            
            colors = {
                "setup": "E7E6E6", 
                "score": "E2EFDA", 
                "diff":  "D0CECE", # Darker Grey for diffs to make them stand out
                "prep":  "FFF2CC", 
                "sel":   "FCE4D6", 
                "total": "DDEBF7", 
            }
            
            integer_columns = ["K", "k", "W", "G", "lenCL"]

            # 2. Format Header Row
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            ws.freeze_panes = "B2"

            # 3. Iterate Columns
            for i, col_cells in enumerate(ws.columns, start=1):
                col_letter = get_column_letter(i)
                header_val = str(col_cells[0].value)
                
                # --- A. FIXED WIDTH CALCULATION ---
                max_length = 0
                for cell in col_cells:
                    try:
                        val_str = str(cell.value)
                        # If it's a percentage, the raw value is 0.05, but we see 5.00%. 
                        # We need to account for that visual length.
                        if "diff%" in header_val and isinstance(cell.value, float):
                             # Estimate length of "-10.00%"
                            val_len = len(f"{cell.value:.2%}")
                        else:
                            val_len = len(val_str)
                            
                        if val_len > max_length:
                            max_length = val_len
                    except:
                        pass
                
                adjusted_width = max_length + 3
                adjusted_width = max(adjusted_width, 10) 
                adjusted_width = min(adjusted_width, 60)
                ws.column_dimensions[col_letter].width = adjusted_width

                # --- B. COLOR LOGIC ---
                fill_color = None
                if "diff%" in header_val:
                    fill_color = colors["diff"]
                elif any(x in header_val for x in ["shape", "K", "k", "W", "G", "lenCL"]):
                    fill_color = colors["setup"]
                elif any(x in header_val for x in ["hpfr", "pss", "psr"]):
                    fill_color = colors["score"]
                elif "prep_time" in header_val:
                    fill_color = colors["prep"]
                elif "sel_time" in header_val:
                    fill_color = colors["sel"]
                elif "x_time" in header_val:
                    fill_color = colors["total"]

                # --- C. APPLY STYLING & FORMATTING ---
                if fill_color:
                    fill_obj = PatternFill(start_color=fill_color, fill_type="solid")
                    for cell in col_cells[1:]:
                        cell.fill = fill_obj
                        cell.border = thin_border
                        
                        if isinstance(cell.value, (int, float)):
                            # CASE 0: Percentage Differences
                            if "diff%" in header_val:
                                cell.number_format = '0.00%' # Displays 0.052 as 5.20%
                            
                            # CASE 1: Forced Integers 
                            elif header_val in integer_columns:
                                cell.number_format = '0'
                            
                            # CASE 2: True Zero or Integer-like floats
                            elif cell.value == 0 or (isinstance(cell.value, float) and cell.value.is_integer()):
                                cell.number_format = '0'
                            
                            # CASE 3: Tiny Numbers (Show raw digits)
                            elif abs(cell.value) < 0.01:
                                cell.number_format = 'General'
                                
                            # CASE 4: Normal Scores
                            else:
                                cell.number_format = '0.000'

            wb.save(self.filename)
        except Exception as e:
            print(f"Warning: Styling step failed: {e}")