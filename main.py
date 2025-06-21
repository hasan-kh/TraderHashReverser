import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import threading

from utils import process_excel

class ExcelHashGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trader ID Finder from Hashes")

        font_big = ("Arial", 12)
        entry_width = 50

        # Excel File
        self.excel_path = tk.StringVar()
        tk.Label(root, text="Excel File:", font=font_big).grid(row=0, column=0, sticky="w")
        tk.Entry(root, textvariable=self.excel_path, width=entry_width, font=font_big).grid(row=0, column=1)
        tk.Button(root, text="Browse", command=self.load_excel, font=font_big).grid(row=0, column=2)

        # Sheet Name
        tk.Label(root, text="Sheet Name:", font=font_big).grid(row=1, column=0, sticky="w")
        self.sheet_dropdown = tk.StringVar()
        self.sheet_menu = tk.OptionMenu(root, self.sheet_dropdown, "")
        self.sheet_menu.config(font=font_big)
        self.sheet_menu.grid(row=1, column=1, sticky="ew")

        # Column Name
        tk.Label(root, text="Hash Column:", font=font_big).grid(row=2, column=0, sticky="w")
        self.column_dropdown = tk.StringVar()
        self.column_menu = tk.OptionMenu(root, self.column_dropdown, "")
        self.column_menu.config(font=font_big)
        self.column_menu.grid(row=2, column=1, sticky="ew")

        # Max User ID
        tk.Label(root, text="Max Trader ID:", font=font_big).grid(row=3, column=0, sticky="w")
        self.max_user_id = tk.IntVar(value=5_000_000)
        tk.Entry(root, textvariable=self.max_user_id, width=entry_width, font=font_big).grid(row=3, column=1)

        # Output file name
        tk.Label(root, text="Output File:", font=font_big).grid(row=4, column=0, sticky="w")
        self.output_file = tk.StringVar(value="trader_id_results.xlsx")
        tk.Entry(root, textvariable=self.output_file, width=entry_width, font=font_big).grid(row=4, column=1)

        # Run button
        self.run_button = tk.Button(root, text="Run", command=self.run_process, font=font_big)
        self.run_button.grid(row=5, column=1, pady=10)

    def load_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if not path:
            return
        self.excel_path.set(path)

        try:
            xl = pd.ExcelFile(path)
            sheets = xl.sheet_names
            self.sheet_dropdown.set(sheets[0])
            self._update_dropdown(self.sheet_menu, self.sheet_dropdown, sheets)

            df = xl.parse(sheets[0])
            columns = list(df.columns)
            self.column_dropdown.set(columns[0])
            self._update_dropdown(self.column_menu, self.column_dropdown, columns)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel: {e}")

    def _update_dropdown(self, menu_widget, variable, options):
        menu = menu_widget["menu"]
        menu.delete(0, "end")
        for opt in options:
            menu.add_command(label=opt, command=lambda val=opt: variable.set(val))

    def run_process(self):
        input_path = self.excel_path.get()
        sheet = self.sheet_dropdown.get()
        column = self.column_dropdown.get()
        output = self.output_file.get()
        max_id = self.max_user_id.get()

        if not input_path or not sheet or not column or not output:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return

        def task():
            try:
                # You pass max_id to your Trader_hash_to_id.exe function here
                process_excel(input_path, sheet, column, output, max_id)
                messagebox.showinfo("Done", f"Results written to {output}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        threading.Thread(target=task).start()


if __name__ == "__main__":
    root = tk.Tk()
    gui = ExcelHashGUI(root)
    root.mainloop()
