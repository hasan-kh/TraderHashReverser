import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import threading
import logging
from io import StringIO

from utils import match_hashes_parallel, process_excel

# Logger setup
log_stream = StringIO()
handler = logging.StreamHandler(log_stream)
handler.setLevel(logging.INFO)
logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s - %(message)s')


class ExcelHashGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TraderHash Reverser v1.0")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        self.init_single_tab()
        self.init_bulk_tab()
        self.init_logs_tab()

    def init_single_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔍 Single Hash")

        font_big = ("Arial", 12)

        tk.Label(frame, text="Trader Hash (SHA-256):", font=font_big).pack(pady=5)
        self.single_hash_input = tk.StringVar()
        tk.Entry(frame, textvariable=self.single_hash_input, width=60, font=font_big).pack(pady=5)

        self.single_result_label = tk.Label(frame, text="Trader ID: ", font=font_big, fg="blue")
        self.single_result_label.pack(pady=10)

        self.loading_label = tk.Label(frame, text="", font=("Arial", 10), fg="gray")
        self.loading_label.pack()

        self.single_max_id = tk.IntVar(value=5_000_000)
        tk.Label(frame, text="Max Trader ID to search:", font=font_big).pack()
        tk.Entry(frame, textvariable=self.single_max_id, font=font_big).pack()

        tk.Button(frame, text="Find Trader ID", font=font_big,
                  command=self.run_single_lookup).pack(pady=10)

    def run_single_lookup(self):
        hash_input = self.single_hash_input.get().strip()
        if not hash_input or len(hash_input) != 64:
            messagebox.showwarning("Invalid Input", "Please enter a valid SHA-256 hash.")
            return

        def task():
            try:
                self.loading_label.config(text="Searching...")
                self.single_result_label.config(text="Trader ID: ...")
                result = match_hashes_parallel([hash_input], self.single_max_id.get())
                trader_id = result.get(hash_input, "Not found")
                self.single_result_label.config(text=f"Trader ID: {trader_id}")
                logging.info(f"Searched for hash: {hash_input} → Trader ID: {trader_id}")
            except Exception as e:
                self.single_result_label.config(text="Trader ID: ERROR")
                logging.error(f"Single hash error: {str(e)}")
                messagebox.showerror("Error", str(e))
            finally:
                self.loading_label.config(text="")

        threading.Thread(target=task).start()

    def init_bulk_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📄 Bulk Excel")

        font_big = ("Arial", 12)
        entry_width = 50

        self.excel_path = tk.StringVar()
        tk.Label(frame, text="Excel File:", font=font_big).grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.excel_path, width=entry_width, font=font_big).grid(row=0, column=1)
        tk.Button(frame, text="Browse", command=self.load_excel, font=font_big).grid(row=0, column=2)

        tk.Label(frame, text="Sheet Name:", font=font_big).grid(row=1, column=0, sticky="w")
        self.sheet_dropdown = tk.StringVar()
        self.sheet_menu = tk.OptionMenu(frame, self.sheet_dropdown, "")
        self.sheet_menu.config(font=font_big)
        self.sheet_menu.grid(row=1, column=1, sticky="ew")

        tk.Label(frame, text="Hash Column:", font=font_big).grid(row=2, column=0, sticky="w")
        self.column_dropdown = tk.StringVar()
        self.column_menu = tk.OptionMenu(frame, self.column_dropdown, "")
        self.column_menu.config(font=font_big)
        self.column_menu.grid(row=2, column=1, sticky="ew")

        tk.Label(frame, text="Max Trader ID:", font=font_big).grid(row=3, column=0, sticky="w")
        self.max_user_id = tk.IntVar(value=5_000_000)
        tk.Entry(frame, textvariable=self.max_user_id, width=entry_width, font=font_big).grid(row=3, column=1)

        tk.Label(frame, text="Output File:", font=font_big).grid(row=4, column=0, sticky="w")
        self.output_file = tk.StringVar(value="trader_id_results.xlsx")
        tk.Entry(frame, textvariable=self.output_file, width=entry_width, font=font_big).grid(row=4, column=1)

        self.run_button = tk.Button(frame, text="Run", command=self.run_process, font=font_big)
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
            logging.error(f"Excel load error: {str(e)}")
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
                self.run_button.config(text="Processing...", state="disabled")
                process_excel(input_path, sheet, column, output, max_id)
                messagebox.showinfo("Done", f"Results written to {output}")
                logging.info(f"Excel processed: {output}")
            except Exception as e:
                logging.error(f"Excel processing error: {str(e)}")
                messagebox.showerror("Error", str(e))
            finally:
                self.run_button.config(text="Run", state="normal")

        threading.Thread(target=task).start()

    def init_logs_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🩵 Logs")

        self.log_text = tk.Text(frame, wrap='word', state='disabled', bg='black', fg='lime', font=("Courier", 10))
        self.log_text.pack(expand=True, fill='both', padx=5, pady=5)

        def update_logs():
            self.log_text.config(state='normal')
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, log_stream.getvalue())
            self.log_text.config(state='disabled')
            self.root.after(1000, update_logs)

        update_logs()


if __name__ == "__main__":
    root = tk.Tk()
    gui = ExcelHashGUI(root)
    root.mainloop()