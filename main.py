import tkinter as tk
from tkinter import ttk
import datetime as dt

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from ust_xml_pull import Treasury_Data
from straight_line import Straight_Line
from Cubic_Spline import Cubic_Spline
from Montone_Convex import Montone_Convex

METHODS = {
    "Straight Line":   Straight_Line,
    "Cubic Spline":    Cubic_Spline,
    "Monotone Convex": Montone_Convex,
}


class Curve_Builder:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Curve Builder')
        self.window.geometry('1200x900')

        self.build_controls()                   #data entry
        self.build_chart()                      #empty matplotlib chart

    def build_controls(self):
        controls = tk.Frame(self.window)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # date
        today = dt.date.today() - dt.timedelta(days=1)
        today = today.strftime('%m-%d-%Y')
        tk.Label(controls, text="Date (MM-DD-YYYY):").grid(row=0, column=0, padx=5)
        self.date_entry = tk.Entry(controls)
        self.date_entry.insert(0, today)
        self.date_entry.grid(row=0, column=1, padx=5)

        # method (values come straight from the dispatch table)
        tk.Label(controls, text="Method:").grid(row=0, column=2, padx=5)
        self.method_box = ttk.Combobox(controls, values=list(METHODS), state="readonly")
        self.method_box.set("Monotone Convex")
        self.method_box.grid(row=0, column=3, padx=5)

        tk.Label(controls, text='Lambda:').grid(row=0, column=4, padx=5)
        self.lambda_select = tk.Entry(controls)
        self.lambda_select.insert(0, 0.2)
        self.lambda_select.grid(row=0, column=5, padx=5)

        tk.Label(controls, text="Positivity:").grid(row=1, column=4, padx=5)
        self.positive_select = ttk.Combobox(controls, values=('True', 'False'), state="readonly")
        self.positive_select.insert(0, 'True')
        self.positive_select.grid(row=1, column=5, padx=5)

        # build button
        tk.Button(controls, text="Build Curve", command=self.build_curve).grid(row=1, column=0, padx=5)

        # status line (shows errors instead of crashing)
        self.status = tk.Label(controls, text="", fg="red")
        self.status.grid(row=1, column=0, columnspan=5, pady=5)

    # ---------- the chart that lives inside the window ----------
    def build_chart(self):
        self.figure = Figure(figsize=(9, 5))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


    def get_curve(self, data, method):
        mats = data.maturity_floats
        grid = np.linspace(mats[0], mats[-1], 200)

        builder = METHODS[method](data)  # instantiate the chosen class
        curve = [builder.zero_rate(t) for t in grid]
        return grid, curve

    def build_curve(self):
        date = self.date_entry.get().strip()
        method = self.method_box.get()
        self.status.config(text="")

        try:
            data = Treasury_Data(date=date)  # pulls from the treasury feed
            grid, curve = self.get_curve(data, method)
        except Exception as e:
            self.status.config(text=f"Error: {e}")
            return

        # redraw the chart
        self.ax.clear()
        self.ax.plot(grid, curve, color="#98002E", linewidth=1.5, label=f"{method} curve")
        self.ax.scatter(data.maturity_floats, data.input_rates,
                        color="#BC9B6A", zorder=3, label="Input rates")
        self.ax.set_xlabel("Maturity (years)")
        self.ax.set_ylabel("Rate (%)")
        self.ax.set_title(f"US Treasury Yield Curve  {method} ({date})")
        self.ax.legend()
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.canvas.draw()

    def run(self):
        self.window.mainloop()


def main():
    app = Curve_Builder()
    app.run()


if __name__ == "__main__":
    main()
