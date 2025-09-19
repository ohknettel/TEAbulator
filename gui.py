# im too lazy to add ReST comments to this, take it as it is

from typing import Any
from tabulator import validate_csv, tabulate
from tkinter import filedialog, messagebox, ttk
import os
import threading
import tkinter as tk
import classes

tea_info = {}

class FieldsetFrame(tk.Frame):
    def __init__(self, parent, label_text="INPUT", fixed_height=None, **kwargs):
        super().__init__(parent, bg=kwargs.get("bg", "#f0f0f0"))

        self.label_text = label_text

        if fixed_height:
            self.canvas = tk.Canvas(self, bg=self["bg"], highlightthickness=0, height=fixed_height)
        else:
            self.canvas = tk.Canvas(self, bg=self["bg"], highlightthickness=0)

        self.canvas.pack(fill="both", expand=True)

        self.label = ttk.Label(self, text=f" {label_text} ", font=("Arial", 10, "bold"))
        self.inner_frame = ttk.Frame(self.canvas, style="Custom.TFrame")
        self.inner_frame.columnconfigure(0, weight=1)
        self.inner_frame.rowconfigure(0, weight=1)
        self.inner_window = self.canvas.create_window(0, 0, window=self.inner_frame, anchor="nw")

        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        pad = 10
        x1, y1 = pad, 10
        x2, y2 = event.width - pad, event.height - pad
        self.canvas.delete("border")
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="gray", width=2, tags="border")
        self.canvas.create_window(x1 + 10, y1 - 10, window=self.label, anchor="nw", tags="border")
        self.canvas.coords(self.inner_window, x1 + 10, y1 + 10)
        self.canvas.itemconfig(self.inner_window, width=x2 - x1 - 20, height=y2 - y1 - 20)

    def add_widget(self, widget):
        widget.grid(in_=self.inner_frame, row=0, column=0, sticky="nsew")

def add_placeholder(entry, placeholder):
    def on_focus_in(_):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.configure(style="TEntry")

    def on_focus_out(_):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.configure(style="Custom.Placeholder.TEntry")

    entry.insert(0, placeholder)
    entry.config(style="Custom.Placeholder.TEntry")
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)

root = tk.Tk()
root.title("TEAbulator")
root.geometry("600x550")
root.configure(bg="#f0f0f0")
root.resizable(False, False)

ICON = tk.PhotoImage(file="assets/icon.png")
root.wm_iconphoto(False, ICON)

style = ttk.Style()
style.configure("Custom.TFrame", background="#f0f0f0")
style.configure("Custom.Placeholder.TEntry", foreground="gray")
style.configure("Custom.Treeview", rowheight=25, borderwidth=1, relief="solid", font=("Arial", 10, "bold"))

container = tk.Frame(root)
container.pack(fill="x", expand=False)

input_fs = FieldsetFrame(container, label_text="Input", fixed_height=82)

f1 = tk.Frame(container, bg="#f0f0f0")
f1.pack(side="right", anchor="n", padx=(0, 10), pady=(5, 0))

load_from_url = ttk.Button(f1, text="Load from URL", width=20)
load_from_file = ttk.Button(f1, text="Load from file", width=20)
load_from_url.pack(pady=5)
load_from_file.pack(pady=(5, 0))

input_fs.pack(side="top", fill="x", expand=False)

def begin_tabulation(file_or_url):
    try:
        file_or_url = validate_csv(file_or_url)
        tabulate_(file_or_url)
    except Exception as e:
        messagebox.showerror("Error", str(e))

def open_url():
    for widget in input_fs.inner_frame.winfo_children():
        widget.destroy()
    entry = ttk.Entry(input_fs.inner_frame)
    add_placeholder(entry, "  Enter a valid spreadsheet URL")
    input_fs.add_widget(entry)

    def on_enter(_):
        url = entry.get().strip()
        if url and url != "  Enter a valid spreadsheet URL":
            begin_tabulation(url)

    entry.bind("<Return>", on_enter)

def open_file():
    filename = filedialog.askopenfilename(title="Select a file", filetypes=[("CSV Files", "*.csv")], parent=root)
    if filename:
        dispname = os.path.basename(filename)
        for widget in input_fs.inner_frame.winfo_children():
            widget.destroy()
        input_fs.inner_frame.columnconfigure(0, weight=1)
        input_fs.inner_frame.rowconfigure(1, weight=1)
        btn = ttk.Button(input_fs.inner_frame, text=f"Open {dispname}", command=lambda: os.startfile(filename))
        btn.grid(row=1, column=0, sticky="nsew", pady=(2, 5))

        begin_tabulation(filename)

load_from_url["command"] = open_url
load_from_file["command"] = open_file
open_url()

labels = []

info_container = tk.Frame(root, bg="#f0f0f0")
info_container.pack(fill="x", padx=10, pady=(2, 7))

long_row = tk.Frame(info_container, height=35, bg="white", highlightbackground="gray", highlightthickness=2)
long_label = tk.Label(long_row, text="Threshold", bg=long_row["bg"], font=("Arial", 14, "bold"))
long_label.place(relx=0.5, rely=0.5, anchor="center")
labels.append(long_label)
long_row.pack(fill="x")

short_row = tk.Frame(info_container, bg="#f0f0f0")
short_row.pack(fill="x")

for i, text in enumerate(["Quota", "Seats"]):
    frame = tk.Frame(short_row, height=35, bg="white", highlightbackground="gray", highlightthickness=2)
    label = tk.Label(frame, text=text, bg=frame["bg"], font=("Arial", 14, "bold"))
    label.place(relx=0.5, rely=0.5, anchor="center")
    labels.append(label)
    frame.pack(side="left", expand=True, fill="both", pady=(2, 0), padx=(0, 1) if i == 0 else (1, 0))

def set_info(threshold="", quota="", seats=""):
    texts = [
        f"Threshold = {threshold} | Round 0" if threshold else "Threshold | Round",
        f"Quota = {quota:.6f}" if quota else "Quota",
        f"Seats = {seats}" if seats else "Seats"
    ]
    for i, text in enumerate(texts):
        labels[i].config(text=text)

set_info()

data_fs = FieldsetFrame(root, label_text="Data")
data_fs.pack(side="top", fill="x", expand=False)

row_ids = {}

tree = ttk.Treeview(data_fs.inner_frame, columns=("Candidate", "Weight", "Status"), style="Custom.Treeview", show="headings")
tree.grid(row=0, column=0)

sb = ttk.Scrollbar(data_fs.inner_frame, orient="vertical", command=tree.yview)
sb.grid(row=0, column=1, sticky="ns")
tree.config(yscrollcommand=sb.set)

tree.heading("Candidate", text="Candidate", anchor="center")
tree.heading("Weight", text="Weight", anchor="center")
tree.heading("Status", text="Status", anchor="center")

tree.column("Candidate", anchor="center", width=240, stretch=False)
tree.column("Weight", anchor="center", width=100, stretch=False)
tree.column("Status", anchor="center", width=215, stretch=False)

tag_options: dict[str, Any] = {
    "unelected": {"background": "white"},
    "elected": {"background": "#ccffcc"},
    "reweighing": {"background": "#fff6cc"},
    "disqualified": {"background": "#ffd6d6"}
}

for name, options in tag_options.items():
    tree.tag_configure(name, **options)

def enlarge_table():
    popup = tk.Toplevel(root)
    popup.title("Data")
    popup.geometry("700x400")
    popup.wm_iconphoto(False, ICON)
    popup.grab_set()

    enlarged_tree = ttk.Treeview(popup, columns=("Candidate", "Weight", "Status"), style="Custom.Treeview", show="headings")
    enlarged_tree.pack(fill="both", expand=True)

    for col in ("Candidate", "Weight", "Status"):
        enlarged_tree.heading(col, text=col, anchor="center")
        enlarged_tree.column(col, anchor="center", stretch=True)

    for item_id in tree.get_children():
        values = tree.item(item_id)["values"]
        tags = tree.item(item_id)["tags"]
        enlarged_tree.insert("", "end", values=values or (), tags=tags)

    for name, options in tag_options.items():
        enlarged_tree.tag_configure(name, **options)

menu = tk.Menu(root, tearoff=0)
menu.add_command(label="Full View", command=enlarge_table)

def show_popup(event):
    menu.tk_popup(event.x_root, event.y_root)

def block_resize(event):
    if tree.identify_region(event.x, event.y) == "separator":
        return "break"

tree.bind("<Button-1>", block_resize)
tree.bind("<Motion>", block_resize)
tree.bind("<Button-3>", show_popup)

def reset():
    for item in tree.get_children():
        tree.delete(item)

    row_ids.clear()

    slider.state(["!disabled"])
    next_round.state(["disabled"])
    auto_round.state(["disabled"])

def schedule_check(t):
    root.after(1000, check_if_done, t)

def check_if_done(t):
    if not t.is_alive():
        next_round.state(["!disabled"])
        auto_round.state(["!disabled"])
    else:
        schedule_check(t)

def tabulation_worker(source):
    global i, tea_info

    tea_info.clear()
    tea_info = tabulate(source)

    if (rounds := tea_info.get("rounds")):
        i = 0
        zero_round = rounds[0]

        reset()
        for candidate in zero_round.unelected:
            row_ids[candidate.name] = tree.insert("", tk.END, values=(candidate.name, zero_round.weights[candidate.name], "Unelected"))

        rounds.pop(0)

    if (quota := tea_info.get("quota")) and (seats := tea_info.get("seats")):
        set_info("5", quota, seats)

def tabulate_(source):
    t = threading.Thread(target=tabulation_worker, args=(source,))
    t.start()
    schedule_check(t)

control_fs = FieldsetFrame(root, label_text="Controls")
control_fs.pack(fill="x", expand=False)

layout = ttk.Frame(control_fs.inner_frame)
layout.grid(row=0, column=0, sticky="nsew")
layout.columnconfigure(0, weight=1)
layout.columnconfigure(1, weight=0)

def disable_inputs():
    load_from_file.state(["disabled"])
    load_from_url.state(["disabled"])

def enable_inputs():
    load_from_file.state(["!disabled"])
    load_from_url.state(["!disabled"])

i = 0
def advance_to_next_round():
    global i

    rounds = tea_info.get("rounds")

    if not rounds:
        return

    _round: classes.TabulationRound = rounds[i]
    round_number = i + 1

    for candidate in _round.unelected:
        rid = row_ids[candidate.name]
        tree.item(rid, tags=("unelected",), values=(candidate.name, f"{_round.weights[candidate.name]:.4f}", "Unelected"))

    if _round.elected:
        rid = row_ids[_round.elected.name]
        tree.item(rid, tags=("elected",), values=(_round.elected.name, f"{_round.weights[_round.elected.name]:.4f}", f"Elected (threshold = {_round.threshold})"))
        tree.move(rid, "", 0)
        tree.focus(rid)
    elif _round.reweighing:
        for candidate in _round.reweighing:
            rid = row_ids[candidate.name]
            tree.item(rid, tags=("reweighing",), values=(candidate.name, f"{_round.weights[candidate.name]:.4f}", "Reweighting"))

    tree.update_idletasks()
    labels[0].config(text=f"Threshold = {_round.threshold} | Round {round_number}")
    i += 1

    if i == len(rounds):
        next_round.state(["disabled"])
        auto_round.state(["disabled"])
        eliminate_remaining()
        return False
    return True

def eliminate_remaining():
    for item in tree.get_children():
        values = tree.item(item)["values"]
        if values[2] == "Unelected":
            tree.item(item, tags=("disqualified",), values=(values[0], values[1], "Disqualified"))

def disable_then_auto_update():
    next_round.state(["disabled"])
    auto_round.state(["disabled"])
    slider.state(["disabled"])
    auto_update()

def auto_update():
    check = advance_to_next_round()
    if check:
        update_progress(1 if progress["maximum"] > 1 else 0)
    else:
        progress["value"] = 0
        enable_inputs()

def update_progress(step):
    if step > progress["maximum"]:
        root.after(0, auto_update)
        return
    progress["value"] = step
    root.after(1000, lambda: update_progress(step + 1))

next_round = ttk.Button(layout, text="Next Round", state="disabled", command=advance_to_next_round)
next_round.grid(row=0, column=1, sticky="e", padx=5, pady=(5, 2))

auto_round = ttk.Button(layout, text="Auto Round", state="disabled", command=disable_then_auto_update)
auto_round.grid(row=1, column=1, sticky="e", padx=5, pady=(2, 5))

progress = ttk.Progressbar(layout, maximum=1, length=100, mode="determinate")
progress.grid(row=0, column=0, sticky="e", padx=5)

slider_var = tk.IntVar()
def on_slider_move(value):
    rounded = round(float(value))
    slider_var.set(rounded)
    progress.config(maximum=rounded)

slider = ttk.Scale(layout, from_=1, to=5, orient="horizontal", variable=slider_var, command=on_slider_move)
slider.grid(row=1, column=0, sticky="e", padx=(5, 10), pady=(2, 5))

ttk.Label(layout, text="1").place(in_=slider, relx=0.0, rely=1.0, anchor="nw")
ttk.Label(layout, text="5").place(in_=slider, relx=1.0, rely=1.0, anchor="ne")

if __name__ == "__main__":
    root.mainloop()