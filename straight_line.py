import numpy as np

class Straight_Line:
    def __init__(self, t_data):
        self.maturity_map = t_data.maturity_map
        self.maturity_labels = t_data.maturity_labels
        self.maturity_floats = t_data.maturity_floats
        self.input_rates = t_data.input_rates

    def zero_rate(self, tgt_rt=None):

        # Retrieve Rates
        anchor_rts = self.input_rates

        # Interpolater
        rt_anchor_mat = np.searchsorted(self.maturity_floats, tgt_rt, side="right")
        interval = min(max(rt_anchor_mat, 1), len(self.maturity_floats) - 1) #clamp to final interval

        time_low, time_high = (
            self.maturity_floats[interval - 1],
            self.maturity_floats[interval],
        )
        rate_low, rate_high = anchor_rts[interval - 1], anchor_rts[interval]

        interval_width = time_high - time_low
        weight_low = (time_high - tgt_rt) / interval_width
        weight_high = (tgt_rt - time_low) / interval_width

        r_t = rate_low * weight_low + rate_high * weight_high

        return r_t
