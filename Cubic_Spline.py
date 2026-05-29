from functools import cached_property

from matplotlib import pyplot as plt

from ust_xml_pull import Treasury_Data
import numpy as np
import scipy.interpolate as csp

class Cubic_Spline:
    def __init__(self, t_data):
        self.maturity_map = t_data.maturity_map                     #UST Mapping (vestigial variable)
        self.maturity_labels = t_data.maturity_labels               #Maturity Labels (1M, 1.5M, 3M, 1Y, etc)
        self.maturity_floats = t_data.maturity_floats               #Maturity in float form (0.08333, .25, 1, 5, etc)
        self.input_rates = t_data.input_rates                       #Imported UST rates


    def cubic_spline(self, target):
        curve_points = self.input_rates
        maturites = self.maturity_floats
        #fit using sci_py cubic_spline function
        cs_fit = csp.CubicSpline(maturites, curve_points)

        x_smooth = np.linspace(self.maturity_floats[0], self.maturity_floats[-1],300)
        y_smooth = cs_fit(x_smooth)



        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(
            x_smooth,
            y_smooth,
            color="#98002E",
            linewidth=1.5,
            label="Yield Curve (cubic spline)",
        )
        ax.scatter(
            self.maturity_floats,
            curve_points,
            color="#98002E",
            zorder=3,
            label="Known tenors",
        )
        if target > 0:
            target_yield = cs_fit(target)
            ax.scatter(
                target,
                target_yield,
                color="#BC9B6A",
                zorder=5,
                s=80,
                label=f"Interpolated ({target:.4f}Y → {target_yield:.4f}%)",
            )
        ax.set_xlabel("Maturity (years)")
        ax.set_ylabel("Yield (%)")
        ax.set_title("US Treasury Yield Curve — Cubic Spline Interpolation")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.show()


def main():
    # date = input("Enter date (%M-%d-YYYY): ")
    # target = float(input('Select maturity period in years: '))
    date = "04-01-2026"
    target = 6
    data = Treasury_Data(date=date)
    test = Cubic_Spline(data)
    test.cubic_spline(target)
    # Trigger the computations

if __name__ == "__main__":
    main()