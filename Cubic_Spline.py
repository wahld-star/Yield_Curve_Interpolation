import scipy.interpolate as csp

class Cubic_Spline:
    def __init__(self, t_data):
        self.maturity_map = t_data.maturity_map                     #UST Mapping (vestigial variable)
        self.maturity_labels = t_data.maturity_labels               #Maturity Labels (1M, 1.5M, 3M, 1Y, etc)
        self.maturity_floats = t_data.maturity_floats               #Maturity in float form (0.08333, .25, 1, 5, etc)
        self.input_rates = t_data.input_rates                       #Imported UST rates

        self.cubic_spline = csp.CubicSpline(self.maturity_floats, self.input_rates)


    def zero_rate(self, target):
        return float(self.cubic_spline(target))