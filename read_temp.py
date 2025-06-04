# importing the module
import csv
from scipy.interpolate import CubicSpline

# open the file in read mode
filename = open("/usr/share/AMS/data/RT_table.csv", "r")

# creating dictreader object
file = csv.DictReader(filename, delimiter=";")

# creating empty lists
temperature = []
resistance = []

# iterating over each row and append
# values to empty list
for col in file:
    temperature.append(col["temperature"])
    resistance.append(col["resistance"])

# printing lists
temperature = [int(x) for x in temperature]
resistance = [int(float(x) * 1000) for x in resistance]


Vref = 3  # V
R = 10000  # Ohm
V_error = 0.0305  # V
voltage_read = [x / (x + R) * Vref for x in resistance]

data = [[voltage_read[i], temperature[i]] for i in range(len(temperature))]
data.sort()
voltage_sorted = [x[0] for x in data]
temperature_sorted = [x[1] for x in data]

temp = CubicSpline(voltage_sorted, temperature_sorted)
volt = CubicSpline(temperature, voltage_read)
