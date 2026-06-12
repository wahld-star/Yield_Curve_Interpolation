from bisect import bisect_right
from functools import cached_property
import matplotlib.pyplot as plt
import numpy as np


class Montone_Convex:
    def __init__(self, t_data, amel=False, lam=0.20, positivity=True):
        self.maturity_map = t_data.maturity_map
        self.maturity_labels = t_data.maturity_labels  # replacing maturities
        self.maturity_floats = t_data.maturity_floats  # replacing maturity_numerical
        self.input_rates = t_data.input_rates  # Anchor Rates
        self.amel = amel  # amelioration of the curve?
        self.lam = lam
        self.positive = positivity

    # Create discrete fwd arb-free rates
    @cached_property
    def discrete_fwd(self):
        disc_fwd = {}
        anchor_rts = self.input_rates
        period = self.maturity_floats
        # add first interval f_d1 = r_1
        disc_fwd[period[0]] = anchor_rts[0]
        for n in range(1, len(anchor_rts)):
            disc_fwd[period[n]] = (
                anchor_rts[n] * period[n] - anchor_rts[n - 1] * period[n - 1]
            ) / (period[n] - period[n - 1])
        return disc_fwd

    # make cc fwd rates equation 30 (Hagan West)
    @cached_property
    def continuous_fwd_midpoints(self):
        fwd_midpoints = {}
        anchor_fwds = self.discrete_fwd
        period = [0.0] + list(self.maturity_floats)

        for n in range(1, len(period) - 1):
            t_prev, t_curr, t_next = period[n - 1], period[n], period[n + 1]
            fd_left = anchor_fwds[t_curr]
            fd_right = anchor_fwds[t_next]
            wt_on_right = (t_curr - t_prev) / (t_next - t_prev)
            wt_on_left = (t_next - t_curr) / (t_next - t_prev)
            fwd_midpoints[t_curr] = wt_on_right * fd_right + wt_on_left * fd_left

        self.fwd_midpoints = fwd_midpoints
        fwd_midpoints = list(fwd_midpoints.values())
        return fwd_midpoints

    @cached_property
    def boundary_conditions(self):
        disc_fwd = list(self.discrete_fwd.values())
        fwd_midpoints = self.continuous_fwd_midpoints

        # boundry for entire interpolation range not interval
        # Left boundry (start) f0 = f^d_1 - .5(f1-f^d_1) equation 31 (Hagan West) - if overnight rate is known, use instead of 31 b
        f0 = disc_fwd[0] - 0.5 * (fwd_midpoints[0] - disc_fwd[0])
        # right boundry (end) fn = f^d_n - .5(f^d_n-1 - f^d_n) equation 32 (Hagan West)
        fn = disc_fwd[-1] - 0.5 * (fwd_midpoints[-1] - disc_fwd[-1])

        # Check f'(0) = 0 = f'(tau_n)
        self.boundary_conditions = [f0, fn]
        return f0, fn

    # Add boundry conditions to continuous_fwd_points
    @cached_property
    def f_midpoint(self):
        f0, fn = self.boundary_conditions
        anchor_midpoints = list(self.continuous_fwd_midpoints)
        anchor_midpoints.insert(0, f0)
        anchor_midpoints.append(fn)
        return anchor_midpoints

    @cached_property
    def amelioration(self):
        # smoothness at the expense of locality
        lam = self.lam
        period = [0.0] + list(
            self.maturity_floats
        )  # add an extra input for calculating our first actual point aka 1 month
        fd = list(self.discrete_fwd.values())  # f_d1 - f_dn
        n = len(fd)  # why python start at 0  >:(

        # a) create new false intervals at each end
        new_start = period[0] - (period[1] - period[0])  # Equation 72 in Hagan West
        fd_0 = fd[0] - ((period[1] - period[0]) / (period[2] - period[0])) * (
            fd[1] - fd[0]
        )
        new_end = period[-1] + (period[-1] - period[-2])  # Equation 73 in Hagan West
        fd_n1 = fd[-1] + ((period[-1] - period[-2]) / (period[-1] - period[-3])) * (
            fd[-1] - fd[-2]
        )
        # Add new intervals to our list
        tau_new = [new_start] + period + [new_end]
        fd_new = [fd_0] + fd + [fd_n1]

        # b) select midpoint forwards
        f = [0.0] * (n + 1)  # create empty f list
        for i in range(1, n + 1):
            # Equation 74
            f[i] = (tau_new[i + 1] - tau_new[i]) / (
                tau_new[i + 2] - tau_new[i]
            ) * fd_new[i + 1] + (tau_new[i + 2] - tau_new[i + 1]) / (
                tau_new[i + 2] - tau_new[i]
            ) * fd_new[i]

        # c) clamp interior knots to bounded amelioration adjustment range
        for i in range(1, n):
            # equation 68
            theta_minus = (
                (tau_new[i + 1] - tau_new[i])
                / (tau_new[i + 1] - tau_new[i - 1])
                * (fd_new[i] - fd_new[i - 1])
            )
            # equation 67, previous interval
            if fd_new[i - 1] < fd_new[i] <= fd_new[i + 1]:
                f_min1 = min(fd_new[i] + 0.5 * theta_minus, fd_new[i + 1])
                f_max1 = min(fd_new[i] + 2 * theta_minus, fd_new[i + 1])

            elif fd_new[i - 1] < fd_new[i] and fd_new[i] > fd_new[i + 1]:
                f_min1 = max(fd_new[i] - 0.5 * lam * theta_minus, fd_new[i + 1])
                f_max1 = fd_new[i]

            elif fd_new[i - 1] >= fd_new[i] and fd_new[i] <= fd_new[i + 1]:
                f_min1 = fd_new[i]
                f_max1 = min(fd_new[i] - 0.5 * lam * theta_minus, fd_new[i + 1])

            elif fd_new[i - 1] >= fd_new[i] > fd_new[i + 1]:
                f_min1 = max(fd_new[i] + 2 * theta_minus, fd_new[i + 1])
                f_max1 = max(fd_new[i] + 0.5 * theta_minus, fd_new[i + 1])

            # equation 71
            theta_plus = (
                (tau_new[i + 2] - tau_new[i + 1]) / (tau_new[i + 3] - tau_new[i + 1])
            ) * (fd_new[i + 2] - fd_new[i + 1])
            # equation 70, next interval
            if fd_new[i] < fd_new[i + 1] <= fd_new[i + 2]:
                f_min2 = max(fd_new[i + 1] - 2 * theta_plus, fd_new[i])
                f_max2 = max(fd_new[i + 1] - 0.5 * theta_plus, fd_new[i])
            elif fd_new[i] < fd_new[i + 1] and fd_new[i + 1] > fd_new[i + 2]:
                f_min2 = max(fd_new[i + 1] + 0.5 * lam * theta_plus, fd_new[i])
                f_max2 = fd_new[i + 1]
            elif fd_new[i] >= fd_new[i + 1] and fd_new[i + 1] < fd_new[i + 2]:
                f_min2 = fd_new[i + 1]
                f_max2 = min(fd_new[i + 1] + 0.5 * lam * theta_plus, fd_new[i])
            elif fd_new[i] >= fd_new[i + 1] >= fd_new[i + 2]:
                f_min2 = min(fd_new[i + 1] - 0.5 * theta_plus, fd_new[i])
                f_max2 = min(fd_new[i + 1] - 2 * theta_plus, fd_new[i])

            # setting f
            # target ranges overlap
            common_lo = max(f_min1, f_min2)
            common_hi = min(f_max1, f_max2)

            if common_lo <= common_hi:
                f[i] = min(max(f[i], common_lo), common_hi)  # Hagan West eq 76
            else:
                gap_lo = min(f_max1, f_max2)
                gap_hi = max(f_min1, f_min2)
                if f[i] < gap_lo:
                    f[i] = gap_lo  # Eq 78
                elif f[i] > gap_hi:
                    f[i] = gap_hi

        # d/e conditional boundry replacement, f0 fn
        if abs(f[0] - fd_new[0]) > 0.5 * abs(f[1] - fd_new[0]):
            f[0] = fd_new[1] - 0.5 * (f[1] - fd_new[0])  # Eq 79
        if abs(f[n] - fd_new[n]) > 0.5 * abs(f[n - 1] - fd_new[n]):
            f[n] = fd_new[n] + 0.5 * (fd_new[n] - f[n - 1])  # Eq 80

        return f

    @cached_property
    def positivity_bound(self, amel=0):
        if self.amel == 1:
            f = self.amelioration
        else:
            f = list(self.f_midpoint)
        fd = list(self.discrete_fwd.values())
        n = len(fd)

        # cap f0 by interval 1's average
        f[0] = min(max(0.0, f[0]), 2 * fd[0])  # Hagan West eq 60

        # interior f_i is bounded by the stricter of the two adjacent intervals
        for i in range(1, n):
            cap = 2 * min(fd[i - 1], fd[i])
            f[i] = min(max(0.0, f[i]), cap)  # Hagan West eq 61

        # cap fn by last intervals average
        f[n] = min(max(0.0, f[n]), 2 * fd[-1])
        anchor_midpoints_bounded = f
        return anchor_midpoints_bounded

    def instantaneous_fwd(self, tgt=None):
        # Define our quadratic as K + Lx(tau) _ Mx(tau)^2
        # interpolate at a single point (tau)
        if self.positive == 1:
            anchor_points = self.positivity_bound
        else:
            anchor_points = self.f_midpoint
        period = self.maturity_floats

        # Find the interval in which tau falls in
        i = bisect_right(period, tgt)
        if i == len(period):
            i = len(period) - 1

        tau_prev = 0.0 if i == 0 else period[i - 1]  # start of interval
        tau_next = period[i]  # end of interval

        f_disc = list(self.discrete_fwd.values())[i]  # f^d on t_i-1, t_i

        f_mid_left = anchor_points[i]  # f_i-1
        f_mid_right = anchor_points[i + 1]  # f_i

        x_tau = (tgt - tau_prev) / (
            tau_next - tau_prev
        )  # Normalized position in the curve

        # Hagan West equation 35
        interpolated = (
            f_mid_left * (1 - 4 * x_tau + 3 * x_tau**2)
            + f_mid_right * (-2 * x_tau + 3 * x_tau**2)
            + f_disc * (6 * x_tau - 6 * x_tau**2)
        )
        f_tau = interpolated

        # define g_tau for monotinicity calculations
        g_tau = (
            f_tau - f_disc
        )  # deviation of the continuous fwd curve from the discrete curve
        g_left = f_mid_left - f_disc
        g_right = f_mid_right - f_disc
        g_vars = [g_tau, g_left, g_right]
        intervals = [tau_prev, tau_next]

        return f_tau, x_tau, g_vars, intervals

    def monotonicity(self, tgt=None):
        # Unpack vars
        f_tau, x_tau, g_vars, intervals = self.instantaneous_fwd(tgt)
        g_tau = g_vars[0]
        g_left = g_vars[1]
        g_right = g_vars[2]

        # Define our regions
        # Region I) g_i-1 > 0, -.5g_i-1 >= >= gi >= -2g_i-1 and g_i-1 < 0, .5g_i-1 <= g_i <= -2g-1
        if (g_left > 0 and -0.5 * g_left >= g_right >= -2 * g_left) or (
            g_left < 0 and -0.5 * g_left <= g_right <= -2 * g_left
        ):
            region = "I"
            pass  # no change needed
        # Region II) g_i-1 < 0, -2g_i-1 and g_i-1 > 0, g_i < -2g_i-1
        elif (g_left < 0 and g_right > -2 * g_left) or (
            g_left > 0 and g_right < -2 * g_left
        ):
            region = "II"
            eta = (g_right + 2 * g_left) / (g_right - g_left)  # Hagan West eq 50
            if 0 <= x_tau <= eta:
                g_tau = g_left  # Hagan West eq 49
            elif eta < x_tau <= 1:
                g_tau = g_left + (g_right - g_left) * ((x_tau - eta) / (1 - eta)) ** 2
        # Region III) g_i-1 > 0, 0 > g_i > .5g_i-1 and g_i-1 < 0, 0 < g_i < .5g_i-1
        elif (g_left > 0 and 0 > g_right > -0.5 * g_left) or (
            g_left < 0 and 0 < g_right < -0.5 * g_left
        ):
            region = "III"
            eta = 3 * (g_right / (g_right - g_left))  # Hagan West eq 52
            if 0 < x_tau < eta:
                g_tau = g_right + (g_left - g_right) * ((eta - x_tau) / eta) ** 2
            if eta <= x_tau < 1:
                g_tau = g_right
        # Region IV) g_i-1 >= 0, g_i >= 0 and g_i-1 <= 0, g_i <= 0
        elif (g_left >= 0 and g_right >= 0) or (g_left <= 0 and g_right <= 0):
            region = "IV"

            eta = g_right / (g_right + g_left)  # Hagan West eq 55
            A = -((g_left * g_right) / (g_left + g_right))  # Hagan West eq 56
            if 0 < x_tau < eta:
                g_tau = (
                    A + (g_left - A) * ((eta - x_tau) / eta) ** 2
                )  # Hagan West eq 53
            elif x_tau == eta:
                g_tau = A
            elif eta < x_tau < 1:
                g_tau = A + (g_right - A) * ((x_tau - eta) / (1 - eta)) ** 2
        return region, g_tau, intervals, g_left, g_right

    def recover_zero_rate(self, tgt=None):
        # Unpack variables passed from mono
        region, g_tau, intervals, g_left, g_right = self.monotonicity(tgt=tgt)
        tau_left, tau_right = intervals[0], intervals[1]
        x_tau = (tgt - tau_left) / (tau_right - tau_left)

        # Using our regions from before we will integrate back to the zero rates
        if region == "I":
            interval_width = tau_right - tau_left
            I_t = interval_width * (
                (g_left * (x_tau - 2 * x_tau**2 + x_tau**3))
                + g_right * (-(x_tau**2) + x_tau**3)
            )
        elif region == "II":
            interval_width = tau_right - tau_left
            eta = (g_right + 2 * g_left) / (g_right - g_left)
            if 0 <= x_tau <= eta:  # Case 1
                I_t = interval_width * (g_left * x_tau)
            elif eta < x_tau <= 1:  # Case 2
                I_t = interval_width * (
                    g_left * x_tau
                    + (((g_right - g_left) * (x_tau - eta) ** 3) / (3 * (1 - eta) ** 2))
                )
        elif region == "III":
            eta = 3 * (g_right / (g_right - g_left))
            interval_width = tau_right - tau_left
            if 0 <= x_tau <= eta:
                I_t = interval_width * (
                    g_right * x_tau
                    + (g_left - g_right)
                    * ((eta**3 - (eta - x_tau) ** 3) / (3 * eta**2))
                )
            elif eta < x_tau <= 1:
                I_t = interval_width * (g_right * x_tau + (g_left - g_right) * eta / 3)
        elif region == "IV":
            # introduce bounds?????? look at old notes *****

            interval_width = tau_right - tau_left
            eta = g_right / (g_right + g_left)
            A = -((g_left * g_right) / (g_left + g_right))
            if 0 <= x_tau <= eta:
                I_t = interval_width * (
                    A * x_tau
                    + ((g_left - A) * ((eta**3 - (eta - x_tau) ** 3) / (3 * eta**2)))
                )
            elif eta < x_tau <= 1:
                I_t = interval_width * (
                    A * x_tau
                    + ((g_left - A) * eta) / 3
                    + (g_right - A) * ((x_tau - eta) ** 3 / (3 * (1 - eta) ** 2))
                )
        else:
            print(f"Error, unknown region {region}")

        return I_t

    def zero_rate(self, tgt=None):
        I_t = self.recover_zero_rate(tgt=tgt)  # I_t
        period = self.maturity_floats
        i = bisect_right(period, tgt)
        if i == len(period):
            i = len(period) - 1
        tau_prev = 0.0 if i == 0 else period[i - 1]  # t_i-1
        f_disc = list(self.discrete_fwd.values())[i]  # fd_i connecting t_i-1 and t_i

        r_prev_tau_prev = 0.0 if i == 0 else self.input_rates[i - 1] * tau_prev

        r_t = (1 / tgt) * (r_prev_tau_prev + f_disc * (tgt - tau_prev) + I_t)

        return r_t

