from ust_xml_pull import Treasury_Data
import numpy as np
import matplotlib.pyplot as plt
from functools import cached_property


class Montone_Convex:
    def __init__(self, t_data):
        self.maturity_map = t_data.maturity_map
        self.maturity_labels = t_data.maturity_labels #replacing maturities
        self.maturity_floats = t_data.maturity_floats #replacing maturity_numerical
        self.anchor_rts = t_data.anchor_rates #Anchor Rates

    #Create discrete fwd arb-free rates
    @cached_property
    def discrete_fwd(self):
        disc_fwd = {}
        anchor_rts = self.anchor_rts
        period = self.maturity_floats
        for n, rate in enumerate(anchor_rts[:-1]):
            disc_fwd[period[n]] = (anchor_rts[n + 1] * period[n+1] - anchor_rts[n] * period[n]) / (period[n + 1] - period[n])
        return disc_fwd

    #make cc fwd rates equation 30 (Hagan West)
    @cached_property
    def continuous_fwd_midpoints(self):
        fwd_midpoints = {}
        anchor_fwds = list(self.discrete_fwd.values())
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

            fwd_midpoints[tau_curr] = wt_left * right_bound + wt_right * left_bound
        self.fwd_midpoints = fwd_midpoints
        return fwd_midpoints

    @cached_property
    def boundary_conditions(self):
        disc_fwd = list(self.discrete_fwd.values())
        fwd_midpoints = list(self.continuous_fwd_midpoints.values())

        #boundry for entire interpolation range not interval
        #Left boundry (start) f0 = f^d_1 - .5(f1-f^d_1) equation 31 (Hagan West) - if overnight rate is known, use instead of 31 b
        f0 = disc_fwd[0] - .5*(fwd_midpoints[0]-disc_fwd[0])
        #right boundry (end) fn = f^d_n - .5(f^d_n-1 - f^d_n) equation 32 (Hagan West)
        fn = disc_fwd[-1] - .5*(fwd_midpoints[-1]-disc_fwd[-1])

        #Check f'(0) = 0 = f'(tau_n)
        self.boundary_conditions = [f0, fn]
        return (f0, fn)

    #Find the midpoint for a given boundry
    @cached_property
    def f_midpoint(self):
        period = self.maturity_floats
        f0, fn = self.boundary_conditions
        #pairs the start value and end values into one dict and unpacks the mid-points in between (AI designed)
        return {period[0]: f0,
                **self.continuous_fwd_midpoints,
                period[-1]: fn}

    def interpolate(self, tgt = None):
    #Define our quadratic as K + Lx(tau) _ Mx(tau)^2
    #interpolate at a single point (tau)

        period = self.maturity_floats
        f0, fn = self.boundary_conditions
        # Find the period in which tau falls in
        i = np.searchsorted(period, tgt , side='right')
        i = min(max(i, 1), len(period) - 1)

        tau_prev, tau_curr = period[i-1], period[i]

        f_disc = self.discrete_fwd[tau_prev]            #f^d on t_i-1, t_i
        f_mid_left = self.discrete_fwd[tau_prev]        #f_i-1
        f_mid_right = self.discrete_fwd[tau_curr]       #f_i


        x_tau = (tgt - tau_prev) / (tau_curr - tau_prev)   #Normalized position in the curve
        # Hagan West equation 35
        interpolated = f_mid_left * (1 -4 * x_tau + 3 * x_tau ** 2) + f_mid_right * (-2 * x_tau + 3*x_tau**2) + f_disc(6*x_tau - 6 * x_tau ** 2)
        f_tau = interpolated

        #define g_tau for monotinicity calculations
        g_tau = f_tau - f_disc                      #deviation of the continuous fwd curve from the discrete curve
        g_left = f_mid_left - f_disc
        g_right = f_mid_right - f_disc
        g_vars = [g_tau, g_left, g_right]

        return f_tau, x_tau, g_vars

    def monotonicity(self):

        #Unpack vars
        f_tau, x_tau, g_vars = self.interpolate()
        g_tau = g_vars[0]
        g_left = g_vars[1]
        g_right = g_vars[2]



        #Define our regions
        #Region I) g_i-1 > 0, -.5g_i-1 >= >= gi >= -2g_i-1 and g_i-1 < 0, .5g_i-1 <= g_i <= -2g-1
        if (g_left > 0 and .5 * g_left >= g_tau >= -2*g_left) or (g_left < 0 and .5 * g_left <= g_tau <= -2*g_left):
            pass
        #Region II) g_i-1 < 0, -2g_i-1 and g_i-1 > 0, g_i < -2g_i-1
        elif (g_left < 0 and g_tau > -2 * g_left) or (g_left > 0 and g_tau < -2*g_left):
            eta = (g_tau + 2*g_left)/(g_tau - g_left)                                       #Hagan West eq 50
            if 0 <= x_tau <= eta:
                g_tau = g_left                                                              #Hagan West eq 49
            elif eta < x_tau <= 1:
                g_tau = g_left + (g_tau - g_left) * ((x_tau - eta) / (1 - eta)) ** 2
        #Region III) g_i-1 > 0, 0 > g_i > .5g_i-1 and g_i-1 < 0, 0 < g_i < .5g_i-1
        elif (g_left > 0 and 0 > g_tau > .5 * g_left) or (g_left < 0 and 0 < g_tau < .5 * g_left):
            eta = 3 * (g_tau / (g_tau - g_left))                                            #Hagan West eq 52
            if 0 < x_tau < eta:
                g_tau = g_tau + (g_left - g_tau) * ((eta - x_tau) / eta) ** 2
            if eta <= x_tau < 1
                g_tau = g_tau
        #Region IV) g_i-1 >= 0, g_i >= 0 and g_i-1 <= 0, g_i <= 0
        elif (g_left >= 0 and g_tau >= 0) and (g_left <= 0 and g_tau <= 0):
            eta = g_tau / (g_tau + g_left)                                                  #Hagan West eq 55
            A = (g_left * g_tau)/(g_left + g_tau)                                           #Hagan West eq 56
            if 0 < x_tau < eta:
                g_tau = A + (g_left - A) * ((eta - x_tau) / eta) ** 2                       #Hagan West eq 53
            elif x_tau == eta:
                g_tau = A
            elif eta < x_tau < 1:
                g_tau = A + (g_left - A) * ((x_tau - eta) / (1-eta)) ** 2

def main():
    # date = input("Enter date (%M-%d-YYYY): ")
    # target = float(input('Select maturity period in years: '))
    date = "04-01-2026"
    target = 6
    data = Treasury_Data(date=date)
    test = Montone_Convex(data)
    # Trigger the computations
    test.discrete_fwd
    test.continuous_fwd_midpoints
    test.boundary_conditions

    import pprint
    pprint.pprint(vars(test))



if __name__ == "__main__":
    main()
