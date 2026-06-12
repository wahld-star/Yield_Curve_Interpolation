import tkinter as tk
from tkinter import ttk, filedialog, filedialog
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

PRIMARY_CURVE_COLOR = "#98002E"   # BC maroon
PRIMARY_DOT_COLOR   = "#BC9B6A"   # BC gold
COMPARE_COLOR       = "#C0C0C0"   # grey, for the overlay date


class Curve_Builder:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Curve Builder')
        self.window.geometry('1200x900')

        # date string -> Treasury_Data; one pull per date for the life of the app
        self._data_cache = {}

        self.build_controls()           # data entry
        self.build_chart()              # empty matplotlib chart

    # ------------------------------------------------------------------ #
    #  Treasury data  (pulled once per date, cached in a dict by date)
    # ------------------------------------------------------------------ #
    def get_treasury_data(self, date):
        """Return the Treasury_Data for a date, pulling only on a cache miss."""
        if date not in self._data_cache:
            self._data_cache[date] = Treasury_Data(date=date)
        return self._data_cache[date]

    def reset_data(self, date=None):
        """Drop one cached pull (or all of them) so the next access re-fetches."""
        if date is None:
            self._data_cache.clear()
        else:
            self._data_cache.pop(date, None)

    # ------------------------------------------------------------------ #
    #  Controls
    # ------------------------------------------------------------------ #
    def build_controls(self):
        controls = tk.Frame(self.window)
        controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # date
        default_date = (dt.date.today() - dt.timedelta(days=1)).strftime('%m-%d-%Y')
        tk.Label(controls, text="Date (MM-DD-YYYY):").grid(row=0, column=0, padx=5)
        self.date_entry = tk.Entry(controls)
        self.date_entry.insert(0, default_date)
        self.date_entry.grid(row=0, column=1, padx=5)

        # compare date (optional second curve on the same axes)
        tk.Label(controls, text="Compare Date (optional):").grid(row=1, column=0, padx=5)
        self.compare_entry = tk.Entry(controls)
        self.compare_entry.grid(row=1, column=1, padx=5)

        # method
        tk.Label(controls, text="Method:").grid(row=0, column=2, padx=5)
        self.method_box = ttk.Combobox(controls, values=list(METHODS), state="readonly")
        self.method_box.set("Monotone Convex")
        self.method_box.grid(row=0, column=3, padx=5)

        # target maturity
        tk.Label(controls, text="Target Maturity:").grid(row=1, column=2, padx=5)
        self.target_entry = tk.Entry(controls)
        self.target_entry.insert(0, "6")
        self.target_entry.grid(row=1, column=3, padx=5)

        # amelioration
        tk.Label(controls, text="Amelioration:").grid(row=0, column=4, padx=5)
        self.amel_select = ttk.Combobox(controls, values=('True', 'False'), state="readonly")
        self.amel_select.set('True')
        self.amel_select.grid(row=0, column=5, padx=5)

        # lambda
        tk.Label(controls, text='Lambda:').grid(row=1, column=4, padx=5)
        self.lambda_select = tk.Entry(controls)
        self.lambda_select.insert(0, "0.2")
        self.lambda_select.grid(row=1, column=5, padx=5)

        # positivity
        tk.Label(controls, text="Positivity:").grid(row=2, column=4, padx=5)
        self.positive_select = ttk.Combobox(controls, values=('True', 'False'), state="readonly")
        self.positive_select.set('True')
        self.positive_select.grid(row=2, column=5, padx=5)

        # build button
        tk.Button(controls, text="Build Curve", command=self.build_curve).grid(
            row=2, column=0, padx=5, pady=5)

        # export button
        tk.Button(controls, text="Export JPEG", command=self.export_chart).grid(
            row=2, column=1, padx=5, pady=5)

        # export button
        tk.Button(controls, text="Export JPEG", command=self.export_jpeg).grid(
            row=2, column=1, padx=5, pady=5)

        # status line on its own row so it doesn't sit under the button
        self.status = tk.Label(controls, text="", fg="red")
        self.status.grid(row=3, column=0, columnspan=8, pady=5)

    # ------------------------------------------------------------------ #
    #  Chart
    # ------------------------------------------------------------------ #
    def build_chart(self):
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Maturity (years)")
        self.ax.set_ylabel("Rate (%)")
        self.ax.set_title("US Treasury Yield Curve")
        self.ax.grid(True, linestyle="--", alpha=0.4)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                                         padx=10, pady=10)
        self.canvas.draw()

    # ------------------------------------------------------------------ #
    #  Export
    # ------------------------------------------------------------------ #
    def export_jpeg(self):
        """Save the current chart to a JPEG chosen via a save-file dialog."""
        default_name = f"yield_curve_{dt.date.today().strftime('%m-%d-%Y')}.jpg"
        path = filedialog.asksaveasfilename(
            title="Export chart as JPEG",
            defaultextension=".jpg",
            initialfile=default_name,
            filetypes=[("JPEG image", "*.jpg *.jpeg"), ("All files", "*.*")],
        )
        if not path:
            return   # user hit Cancel

        try:
            # JPEG has no alpha channel, so pin the background to white
            self.fig.savefig(path, format="jpg", dpi=200,
                             facecolor="white", bbox_inches="tight")
            self.status.config(text=f"Saved {path}", fg="green")
        except Exception as e:
            self.status.config(text=f"Export error: {e}", fg="red")

    # ------------------------------------------------------------------ #
    #  Curve evaluation
    # ------------------------------------------------------------------ #
    def make_interp(self, method, data):
        if method == "Straight Line":
            return Straight_Line(data)
        elif method == "Cubic Spline":
            return Cubic_Spline(data)
        elif method == "Monotone Convex":
            lam        = float(self.lambda_select.get())
            positivity = self.positive_select.get() == 'True'   # string -> real bool
            amel       = self.amel_select.get() == 'True'
            return Montone_Convex(data, amel=amel, lam=lam, positivity=positivity)
        raise ValueError(f"Unknown method: {method}")

    def get_curve(self, method, date):
        data = self.get_treasury_data(date)       # cached pull, no network on a repeat date
        mats = data.maturity_floats
        grid = np.linspace(mats[0], mats[-1], 200)

        interp = self.make_interp(method, data)
        curve = np.array([interp.zero_rate(t) for t in grid])
        return grid, curve, interp, data

    # ------------------------------------------------------------------ #
    #  Build + draw  (the button handler)
    # ------------------------------------------------------------------ #
    def build_curve(self):
        method = self.method_box.get()
        self.status.config(text="", fg="red")

        date         = self.date_entry.get().strip()
        compare_date = self.compare_entry.get().strip()

        # primary curve: if this fails there's nothing to draw
        try:
            grid, curve, interp, data = self.get_curve(method, date)
        except Exception as e:
            self.status.config(text=f"Error ({date}): {e}")
            return

        # redraw the chart
        self.ax.clear()
        self.ax.plot(grid, curve, color=PRIMARY_CURVE_COLOR, linewidth=1.5,
                     label=f"{method}  {date}")
        self.ax.scatter(data.maturity_floats, data.input_rates,
                        color=PRIMARY_DOT_COLOR, zorder=3,
                        label=f"Input rates  {date}")

        # optional overlay curve for a second date (same method/settings)
        compare_plotted = False
        if compare_date and compare_date == date:
            self.status.config(text="Compare date matches primary date — overlay skipped.")
        elif compare_date:
            try:
                grid2, curve2, _, data2 = self.get_curve(method, compare_date)
                self.ax.plot(grid2, curve2, color=COMPARE_COLOR, linewidth=1.5,
                             linestyle="--", label=f"{method}  {compare_date}")
                self.ax.scatter(data2.maturity_floats, data2.input_rates,
                                facecolors="none", edgecolors=COMPARE_COLOR, zorder=3,
                                label=f"Input rates  {compare_date}")
                compare_plotted = True
            except Exception as e:
                # a bad compare date shouldn't kill the primary plot
                self.status.config(text=f"Compare date error ({compare_date}): {e}")

        # optional: mark the requested target maturity (on the primary curve)
        try:
            tgt = float(self.target_entry.get())
            if grid[0] <= tgt <= grid[-1]:
                r_tgt = interp.zero_rate(tgt)
                self.ax.scatter([tgt], [r_tgt], color="black", zorder=4,
                                label=f"Target {tgt:g}y = {r_tgt:.3f}%")
        except Exception:
            pass   # bad target text shouldn't kill the plot

        title_dates = f"{date} vs {compare_date}" if compare_plotted else date
        self.ax.set_xlabel("Maturity (years)")
        self.ax.set_ylabel("Rate (%)")
        self.ax.set_title(f"US Treasury Yield Curve  —  {method} ({title_dates})")
        self.ax.legend()
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.canvas.draw()

    # ------------------------------------------------------------------ #
    #  Export  (saves whatever is currently drawn on the axes)
    # ------------------------------------------------------------------ #
    def export_chart(self):
        default_name = f"yield_curve_{dt.date.today().strftime('%m-%d-%Y')}.jpg"
        path = filedialog.asksaveasfilename(
            title="Export chart as JPEG",
            defaultextension=".jpg",
            initialfile=default_name,
            filetypes=[("JPEG image", "*.jpg *.jpeg"), ("PNG image", "*.png")],
        )
        if not path:
            return   # user hit cancel

        try:
            self.fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
            self.status.config(text=f"Saved: {path}", fg="green")
        except Exception as e:
            self.status.config(text=f"Export error: {e}", fg="red")

    def run(self):
        self.window.mainloop()


def main():
    app = Curve_Builder()
    app.run()


if __name__ == "__main__":
    main()