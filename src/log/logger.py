import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class ExperimentLogger:
    def __init__(self, experiment_name):
        self.filename = f"{experiment_name}.xlsx"
        self.logs = []
        
        # 1. Define the STRICT column order
        self.columns_order = [
            "shape", "K", "k", "W", "K/(k*g)", "G", "lenCL",
            
            # Metrics
            "base_iadu_hpfr", "base_iadu_pss_sum", "base_iadu_psr_sum",
            "grid_sampling_hpfr", "grid_sampling_pss_sum", "grid_sampling_psr_sum",
            "biased_hpfr", "biased_pss_sum", "biased_psr_sum",
            
            # Prep Times
            "baseline_prep_time", "gridsampling_prep_time", "biasedsampling_prep_time",
            
            # Selection Times
            "baseline_sel_time", "gridsampling_sel_time", "biasedsampling_sel_time",
            
            # Total Times
            "baseline_x_time", "gridsampling_x_time", "biasedsampling_x_time"
        ]

        # 2. Map internal names to your preferred CSV headers
        self.rename_map = {
            "base_iadu_prep_time": "baseline_prep_time",
            "grid_sampling_prep_time": "gridsampling_prep_time",
            "biased_prep_time": "biasedsampling_prep_time",
            
            "base_iadu_sel_time": "baseline_sel_time",
            "grid_sampling_sel_time": "gridsampling_sel_time",
            "biased_sel_time": "biasedsampling_sel_time",
            
            "base_iadu_x_time": "baseline_x_time",
            "grid_sampling_x_time": "gridsampling_x_time",
            "biased_x_time": "biasedsampling_x_time"
        }

    def log(self, row_dict):
        processed = {k: self._smart_round(v) for k, v in row_dict.items()}
        self.logs.append(processed)

    def _smart_round(self, value):
        if isinstance(value, float):
            if value == 0: return 0
            if abs(value) >= 0.01: return round(value, 3)
            return float(f"{value:.5f}")
        return value

    def save(self):
        if not self.logs:
            print("No logs to save.")
            return

        df = pd.DataFrame(self.logs)
        
        # Rename and Filter
        df.rename(columns=self.rename_map, inplace=True)
        final_cols = [c for c in self.columns_order if c in df.columns]
        df = df[final_cols]

        # Save raw data first
        df.to_excel(self.filename, index=False)
        
        # Apply Styling
        self._apply_styling()
        print(f"✔ Results saved with COLORS to: {self.filename}")

    def _apply_styling(self):
        try:
            wb = load_workbook(self.filename)
            ws = wb.active
            
            # --- Definitions ---
            header_fill = PatternFill(start_color="A6A6A6", end_color="A6A6A6", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")
            thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                 top=Side(style='thin'), bottom=Side(style='thin'))
            
            # Color Groups
            colors = {
                "setup": PatternFill(start_color="D9E1F2", fill_type="solid"), # Blue
                "score": PatternFill(start_color="E2EFDA", fill_type="solid"), # Green
                "prep":  PatternFill(start_color="FFF2CC", fill_type="solid"), # Yellow
                "sel":   PatternFill(start_color="FCE4D6", fill_type="solid"), # Orange
                "total": PatternFill(start_color="EDEDED", fill_type="solid"), # Gray
            }

            # --- Apply Header Style ---
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

            # --- Apply Column Body Styles ---
            # We iterate columns and determine their group based on the header name
            for col in ws.columns:
                col_letter = get_column_letter(col[0].column)
                header_val = str(col[0].value)
                
                # Determine Fill Color based on header keywords
                fill_style = None
                
                if any(x in header_val for x in ["shape", "K", "k", "W", "G", "lenCL"]):
                    fill_style = colors["setup"]
                elif any(x in header_val for x in ["hpfr", "pss", "psr"]):
                    fill_style = colors["score"]
                elif "prep_time" in header_val:
                    fill_style = colors["prep"]
                elif "sel_time" in header_val:
                    fill_style = colors["sel"]
                elif "x_time" in header_val:
                    fill_style = colors["total"]

                # Apply to all cells in column (skipping header)
                if fill_style:
                    for i in range(1, len(col)):
                        cell = col[i]
                        cell.fill = fill_style
                        cell.border = thin_border

            # --- Auto-width ---
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    try:
                        if cell.value: max_len = max(max_len, len(str(cell.value)))
                    except: pass
                ws.column_dimensions[col_letter].width = max_len + 3
            
            wb.save(self.filename)

        except Exception as e:
            print(f"Warning: Styling step failed: {e}")