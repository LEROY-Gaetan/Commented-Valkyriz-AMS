import csv
from scipy.interpolate import CubicSpline

"""
permet d'estimer la température en fonction d'une tension mesurée sur un 
thermistor (capteur de température à résistance variable) 
via une interpolation en spline cubique
"""

# Utilisation du chemin Windows pour le fichier CSV
filename = open("/usr/share/AMS/data/RT_table.csv", "r")
file = csv.DictReader(filename, delimiter=";")

# Création des listes
temperature = []
resistance = []

for col in file:
    temperature.append(col["temperature"])
    resistance.append(col["resistance"])

# Conversion en entiers
temperature = [int(x) for x in temperature]
resistance = [int(float(x) * 1000) for x in resistance]


# Calcul des tensions correspondant aux résistances
Vref = 3  # V
R = 10000  # Ohm
V_error = 0.0305  # V
voltage_read = [x / (x + R) * Vref for x in resistance]

# Tri des données pour l'interpolation
data = [[voltage_read[i], temperature[i]] for i in range(len(temperature))]
data.sort()
voltage_sorted = [x[0] for x in data]
temperature_sorted = [x[1] for x in data]

# Fonctions d'interpolation

# convertir une tension mesurée (venant d’un thermistor) en température
temp = CubicSpline(voltage_sorted, temperature_sorted)

# convertir une température en tension équivalente 
# (moins utilisée, utile pour tests, calibrations ou visualisations)
volt = CubicSpline(temperature, voltage_read)
