from ust_xml_pull import Treasury_Data
import numpy as np
import matplotlib.pyplot as plt

class Interpolation:
    def __init__(self, t_data):
        self.maturity_map = t_data.maturity_map
        self.maturity_labels = t_data.maturity_labels
        self.maturity_floats = t_data.maturity_floats
        self.raw_rate_pull = t_data.anchor_ratess

    def straight_line_interp(self, tgt_rt: float, date: str):
        """
        #param date: %M-%d-YYYY
        #param T: target maturity in years
        """

        if tgt_rt < self.maturity_floats[0] or tgt_rt > self.maturity_floats[-1]:
            raise ValueError(f"Target {tgt_rt} outside range [{self.maturity_floats[0]}, {self.maturity_floats[-1]}]")

        #Retrieve Rates
        _, curve = next(iter(self.raw_rate_pull.items()))
        float_curve = dict(zip(self.maturity_floats, curve.values()))
        anchor_rts = np.array(list(float_curve.values()))

        #Interpolater
        rt_anchor_mat = np.searchsorted(self.maturity_floats, tgt_rt, side='right')
        interval = max(rt_anchor_mat, 1)

        time_low, time_high = self.maturity_floats[interval - 1], self.maturity_floats[interval]
        rate_low, rate_high = anchor_rts[interval - 1], anchor_rts[interval]

        interval_width = time_high - time_low
        weight_low = (time_high - tgt_rt) / interval_width
        weight_high = (tgt_rt - time_low) / interval_width

        interp_rt = rate_low * weight_low + rate_high * weight_high

        #DEBUG
        print("maturity_floats:", self.maturity_floats.shape, self.maturity_floats)
        print("anchor_rts:    ", anchor_rts.shape, anchor_rts)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(self.maturity_floats, anchor_rts, color='#98002E', linewidth=1.5, label='Yield Curve (linear interp)')
        ax.scatter(self.maturity_floats, anchor_rts, color='#98002E', zorder=3, label='Known tenors')
        ax.scatter(tgt_rt, interp_rt, color='#BC9B6A', zorder=5, s=80, label=f'Interpolated ({tgt_rt:.4f}Y → {interp_rt:.4f}%)')
        ax.set_xlabel('Maturity (years)')
        ax.set_ylabel('Yield (%)')
        ax.set_title(f'US Treasury Yield Curve — Straight Line Interpolation ({date})')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.show()

        return interp_rt

def main():
    #date = input("Enter date (%M-%d-YYYY): ")
    #target = float(input('Select maturity period in years: '))
    date = '04-01-2020'
    target = 6
    data = Treasury_Data(date = date)
    interp = Interpolation(t_data=data)
    interp.straight_line_interp(tgt_rt=target, date=date)

if __name__ == '__main__':
    main()