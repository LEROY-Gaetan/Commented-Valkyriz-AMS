"""
Lit le fichier de log binaire et affiche les données traitées de manière lisible.
"""

from LTC6811 import TOTAL_IC, NB_CELLS
from Monitoring import MAX_MUX_PIN
from read_temp import temp
from ADC import convert_current
import datetime


def print_data(n: int):
    """
    Affiche les données d'une ligne de données traitées au preaalable.
    """
    line = data[n]
    print("Date :", line[0])
    print("Courant (A) :", line[1])
    for i in range(TOTAL_IC):
        print("BMS " + str(i + 1))
        strcell = ""
        for k in range(12):
            strcell += "C" + str(k + 1) + ": " + str(line[k + 2]) + ", "
        print("Cellules (V) : " + strcell[:-2])
        strtemp = ""
        for k in range(MAX_MUX_PIN):
            strtemp += "T" + str(k + 1) + ": " + str(line[k + 12 + 2]) + ", "
        print("Températures (°C) : " + strtemp[:-2])
    print()


if __name__ == "__main__":
    filepath = "/usr/share/AMS/data/data.bin"       # Chemin vers le fichier de log

    file = open(filepath, "rb")     # Ouverture du fichier en mode binaire (lecture)

    chunksize = 8 + 2 + (12 + MAX_MUX_PIN) * 2 * TOTAL_IC   # Taille d'un bloc de données

    data_raw = []

    while True:
        chunk = file.read(chunksize)    # Lecture d'un bloc de données
        data_raw.append(chunk)          # Ajout du bloc de données à la liste
        if not chunk:                   # Si le bloc de données est vide, on a atteint la fin du fichier
            break

    data = []

    for raw in data_raw:
        mes = []
        mes.append(datetime.datetime.fromtimestamp(int.from_bytes(raw[0:8]) / 1e8))     # Conversion du timestamp en date
        mes.append(round(convert_current(int.from_bytes(raw[8:10])), 2))                # Conversion du courant en Ampères
        for current_bms in range(TOTAL_IC):   # Pour chaque BMS
            for cell in range(NB_CELLS):      # Pour chaque cellule du BMS k
                indic = (current_bms * (12 + MAX_MUX_PIN) + cell + 1) * 2 + 8           # Calcul de l'indice pour accéder à la cellule
                mes.append(round(int.from_bytes(raw[indic : indic + 2]) * 0.0001, 4))   # Conversion de la valeur de la cellule en Volts
            for temp_n in range(MAX_MUX_PIN):   # Pour chaque capteur de température du BMS k
                indic = (current_bms * (12 + MAX_MUX_PIN) + 12 + temp_n + 1) * 2 + 8    # Calcul de l'indice pour accéder à la température
                mes.append(
                    round(float(temp(int.from_bytes(raw[indic : indic + 2]) * 0.0001)), 4)    # Conversion de la valeur de la température en °C
                )
        data.append(mes)    # [timestamp, courant, Tensions, Températures] pour chaque BMS

    for i in range(len(data) - 1):  # Affiche les données de chaque ligne
        print_data(i)
