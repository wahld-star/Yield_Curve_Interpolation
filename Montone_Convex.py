from ust_xml_pull import Treasury_Data
import numpy as np
import matplotlib.pyplot as plt


class Montone_Convex:
    def __init__(self, t_data):
        self.maturity_map = t_data.maturity_map
        self.maturity_labels = t_data.maturity_labels #replacing maturities
        self.maturity_floats = t_data.maturity_floats #replacing maturity_numerical
        self.anchor_rts = t_data.anchor_rates #Anchoor Rates

    #Create discrete fwd arb-free rates
    def discrete_fwd(self):
        disc_fwd = {}
        anchor_rts = self.anchor_rts
        period = self.maturity_floats
        for n, rate in enumerate(anchor_rts[:-1]):
            disc_fwd[period[n]] = (anchor_rts[n + 1] * period[n+1] - anchor_rts[n] * period[n]) / (period[n + 1] - period[n])
        return disc_fwd

    #make cc fwd rates equation 30 (Hagan West)
    def continuous_fwd(self):
        cc_fwds = {}
        anchor_fwds = list(self.discrete_fwd().values())
        period = self.maturity_floats
        for n in range (1, len(period) - 1):
            tau_prev = period[n-1]
            tau_curr = period[n]
            tau_next = period[n+1]

            #set fwd bounds
            left_bound = anchor_fwds[n-1]
            right_bound = anchor_fwds[n]

            #set interval weights
            wt_left = (tau_curr - tau_prev) / (tau_next - tau_prev)
            wt_right = (tau_next - tau_curr) / (tau_next - tau_prev)

            cc_fwds[tau_curr] = wt_left * right_bound + wt_right * left_bound
        return cc_fwds

def main():
    # date = input("Enter date (%M-%d-YYYY): ")
    # target = float(input('Select maturity period in years: '))
    date = "04-01-2026"
    target = 6
    data = Treasury_Data(date=date)
    test = Montone_Convex(data)
    test.discrete_fwd()
    test.continuous_fwd()



if __name__ == "__main__":
    main()
