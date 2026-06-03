import Montone_Convex from Montone_Convex
import Cubic_Spline from Cubic_Spline
import Straight_Line from straight_line
import matplotlib.pyplot as plt
import tkinter as tk
import numpy as np

class Curve_Builder:
    def __init__(self, method, date):
        self.method = method
        self.date = date


    def interface(self):
        mywindow = tk.Tk()
        mywindow.geometry('1200x1200')
        mywindow.title("Curve Builder")

        tk.Label(mywindow, text='Method').place(x=10, y=10)
        method_entry =

        #method select
        methods = ['Straight Line', 'Cubic Spline', 'Montone Convex']
        method_dropdown = tk.ttk.Combobox(values= methods)
        method_dropdown.set('SELECT METHOD')
        method_dropdown.pack(pady=5)



    def plot_curve(self):
        grid = np.linspace(self.maturity_floats[0], self.maturity_floats[-1], 100)
        zero_rates = [self.zero_rate(t) for t in grid]

        plt.figure(figsize=(12, 6))
        plt.plot(grid, zero_rates, label='Zero Curve', color='#98002E')
        plt.scatter(self.maturity_floats, self.input_rates, color='#BC9B6A', label='Input Rates')
        plt.xlabel('Maturity (Years)')
        plt.ylabel('Rate (%)')
        plt.title(f'{self.method} Curve')
        plt.legend()
        plt.grid(True)
        plt.show()




def main():



if __name__ == "__main__":
    main()
