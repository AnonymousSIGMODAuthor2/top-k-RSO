import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class ExperimentLogger:
    def __init__(self, experiment_name):
        self.filename = f"{experiment_name}.xlsx"
        self.logs = []
        
        # Define column groups for styling
        self.cols_setup = ["K", "k", "W", "K'", "W'", "K/(k*g)", "G", "shape"]
        self.cols_score = ["algorithm", "hpfr", "hpfr_diff_%", "pss_sum", "pss_error_%", "psr_sum"]
        self.cols_prep = ["prep_time"]
        self.cols_select = ["select_time"]
        self.cols_total = ["total_time"]

    def log(self, row_dict):
        """
        Add a single result row. Smart rounds floats automatically.
        """
        processed_row = {k: self._smart_round(v) for k, v in row_dict.items()}
        self.logs.append(processed_row)

    def _smart_round(self, value):
        if isinstance(value, float):
            if value == 0: return 0.0
            if abs(value) >= 0.01: return round(value, 3)
            return float(f"{value:.5f}")
        return value

    def save(self):
        if not self.logs:
            print("No logs to save.")
            return

        # 1. Create DataFrame and Order Columns
        df = pd.DataFrame(self.logs)
        
        # Ensure all expected columns exist
        all_defined_cols = self.cols_setup + self.cols_score + self.cols_prep + self.cols_select + self.cols_total
        final_cols = [c for c in all_defined_cols if c in df.columns]
        
        # Add any extra columns found in data but not in definitions
        extra_cols = [c for c in df.columns if c not in final_cols]
        df = df[final_cols + extra_cols]

        # 2. Save raw data
        df.to_excel(self.filename, index=False)

        # 3. Apply Mandatory Formatting
        self._apply_styling(df)
        print(f"✔ Results saved with formatting to: {self.filename}")

    def _apply_styling(self, df):
        wb = load_workbook(self.filename)
        ws = wb.active

        # Styles
        header_fill = PatternFill(start_color="A6A6A6", end_color="A6A6A6", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                             top=Side(style='thin'), bottom=Side(style='thin'))
        thick_right = Border(right=Side(style='thick'), top=Side(style='thin'), bottom=Side(style='thin'))

        # Group Colors
        fills = {
            "setup": PatternFill(start_color="D9E1F2", fill_type="solid"), # Blue
            "score": PatternFill(start_color="E2EFDA", fill_type="solid"), # Green
            "prep":  PatternFill(start_color="FFF2CC", fill_type="solid"), # Yellow
            "select": PatternFill(start_color="FCE4D6", fill_type="solid"),# Orange
            "total": PatternFill(start_color="EDEDED", fill_type="solid"), # Gray
        }

        # 1. Format Header
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        # 2. Format Data Columns by Group
        col_map = {name: i+1 for i, name in enumerate(df.columns)}

        def style_group(group_cols, fill_style, thick_border=True):
            group_indices = [col_map[c] for c in group_cols if c in col_map]
            if not group_indices: return
            
            last_idx = max(group_indices)
            
            for col_idx in group_indices:
                col_letter = get_column_letter(col_idx)
                # Apply to all rows in this column
                for row in range(2, ws.max_row + 1):
                    cell = ws[f"{col_letter}{row}"]
                    cell.fill = fill_style
                    
                    # Border logic
                    if thick_border and col_idx == last_idx:
                        cell.border = thick_right
                    else:
                        cell.border = thin_border

        style_group(self.cols_setup, fills["setup"])
        style_group(self.cols_score, fills["score"])
        style_group(self.cols_prep, fills["prep"])
        style_group(self.cols_select, fills["select"])
        style_group(self.cols_total, fills["total"], thick_border=False)

        # 3. Auto-size columns
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max_len + 3

        wb.save(self.filename)