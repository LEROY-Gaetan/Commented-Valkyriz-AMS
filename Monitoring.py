import LTC6811 as BMS
import ADC
import can
from read_temp import temp

import gpiozero
import time
import datetime

import os.path
import py7zr

PATH = "/usr/share/AMS/"
NO_PROBLEM_PIN = 5  # GPIO5

NO_PROBLEM_OUTPUT = gpiozero.LED(NO_PROBLEM_PIN)    # Selection du PIN pour la sortie du SCS

MAX_MUX_PIN = BMS.NB_CELLS  # Nombre de thermistors

READ_ENABLE = False  # Affichage dans la console

MODE = "DISCHARGE"   # DISCHARGE, CHARGE or STANDBY

# Déclaration des bornes de protection
OVERVOLTAGE = 7  # V
UNDERVOLTAGE = 2.55  # V

CHARGE_MAX_T = 47.5  # °C
DISCHARGE_MAX_T = 57.5  # °C

MAX_DISCHARGE_CURRENT = 95  # A


LOW_WRITE_TIME = 10  # Temps d'écriture entre chaque donnée (en s) pour le LOW WRITE

CANID = 0x17    # ID du message CAN (0x17 = 23)

n = 0   # Compteur pour le message CAN, pour éviter les doublons (modulo 200)

### Functions


def write_data():
    """
    Convertie les données en données binaires et les écrit dans les fichiers data.bin et actualdata.bin.
    """
    data_raw = int(TIME * 1e8).to_bytes(8) + ADC.VALUE.to_bytes(2)  # Timestamp + ADC value (voltage batterie)
    for k in range(BMS.TOTAL_IC):   # Pour chaque BMS en chaine
        for i in range(BMS.NB_CELLS):   # Pour chaque cellule du BMS k
            data_raw += BMS.config.BMS_IC[k].cells.c_codes[i].to_bytes(2)   # Lit les valeurs de tension des cellules de chaque BMS
        for j in range(MAX_MUX_PIN):
            data_raw += BMS.config.BMS_IC[k].temp[j].to_bytes(2)    # Lit les valeurs de température des capteurs de chaque BMS
    data_raw += BMS.bin2int(NO_PROBLEM).to_bytes(5)     # Lit le code d'erreur NO_PROBLEM
    # Structure de data_raw:
    # [timestamp (8 bytes), ADC value (2 bytes), cell voltages (26 bytes), temperatures (26 bytes), NO_PROBLEM (5 bytes)]
    with open(PATH + "data/data.bin", "ab") as fileab:
        # data=bytearray(data_row)
        fileab.write(data_raw)      # Ecrit les données dans le fichier data.bin (ajoute à la fin du fichier)
    with open(PATH + "data/actualdata.bin", "wb") as filewb:
        filewb.write(data_raw)      # Ecrit les données dans le fichier actualdata.bin (écrase le fichier précédent)


def store_temp(sensor: int):
    """
    Stocke les données de température dans la configuration du BMS.
    :param sensor: Index du capteur de température (0 à 12)
    """
    global BMS
    for k in range(BMS.TOTAL_IC):   # Pour chaque BMS en chaine
        BMS.config.BMS_IC[k].temp[sensor] = BMS.config.BMS_IC[k].aux.a_codes[0]
        # Les capteurs de temp sont sur le GPIO1 (a_codes[0])


def update_archive():
    """
    Comprime le fichier data.bin en un fichier 7z sans doublons pour libérer de l'espace disque.
    """
    with open(PATH + "data/data.bin", "rb") as f:
        datebin = f.read(8)
        date = datetime.datetime.fromtimestamp(int.from_bytes(datebin) / 1e8).date()    # Convertit le timestamp en date
        written = False
        k = 1
        while not written:
            if os.path.isfile("data/" + str(date) + "-" + str(k) + ".7z"):  # Si le fichier est déjà comprimé, ne pas l'écraser
                k += 1
            else:   # Sinon, on crée le fichier compressé
                with py7zr.SevenZipFile(
                    PATH + "data/" + str(date) + "-" + str(k) + ".7z", "w"
                ) as archive:
                    archive.writeall(PATH + "data/data.bin", "data.bin")
                os.remove(PATH + "data/data.bin")   # On supprime le fichier data.bin après compression
                written = True


def calc_temp():  # Calcul sur les données de températures
    """
    Renvoie divers paramètres sur les températures des capteurs.
    Températures en °C
    :return: Tmoy, Tmax, i_max, Tmin, i_min
    """
    sum = 0
    min = 100
    max = -100
    indicmin = [1, 1]
    indicmax = [1, 1]
    for k in range(BMS.TOTAL_IC):       # Pour chaque BMS en chaine
        for i in range(MAX_MUX_PIN):    # Pour chaque capteur de température
            tempe = temp(BMS.config.BMS_IC[k].temp[i])   # Lit la valeur du capteur de température (en V) du capteur i du BMS k et la convertit en °C via la courbe 'temp'
            sum += tempe
            if -50 < tempe <= min:          # On ne prend pas en compte les valeurs trop basses (en dessous de -50°C) car probablement erronées
                indicmin = [k + 1, i + 1]   # mise à jour de l'indice du capteur de température le plus bas
                min = tempe                 # mise à jour de la valeur minimale
            if 500 >= tempe >= max:         # On ne prend pas en compte les valeurs trop hautes (au dessus de 500°C) car probablement erronées
                indicmax = [k + 1, i + 1]   # mise à jour de l'indice du capteur de température le plus haut
                max = tempe                 # mise à jour de la valeur maximale
    return (sum / (BMS.TOTAL_IC * MAX_MUX_PIN), max, indicmax, min, indicmin)


def calc_voltage():
    """
    Renvoie divers paramètres sur les tensions des cellules.
    Tensions en V
    :return: Ttot, Tmoy, Tmax, i_max, Tmin, i_min
    """
    sum = 0
    min = 100
    max = -100
    indicmin = [1, 1]
    indicmax = [1, 1]
    for k in range(BMS.TOTAL_IC):   # Pour chaque BMS en chaine
        for i in range(BMS.NB_CELLS):         # Pour chaque cellule du BMS k
            volt = BMS.config.BMS_IC[k].cells.c_codes[i] * 0.0001   # Lit la valeur de tension de la cellule i du BMS k et la convertit en V
            sum += volt
            if volt <= min:
                indicmin = [k + 1, i + 1]
                min = volt
            if volt >= max:     
                indicmax = [k + 1, i + 1]
                max = volt
    return (sum, sum / (BMS.TOTAL_IC * 13), max, indicmax, min, indicmin)


def send_data_CAN():
    """
    Envoie les données de tension et de température sur le bus CAN.'e
    """
    global n
    tempe = calc_temp()     # Calcul des températures moyennes, maximales et minimales
    volt = calc_voltage()   # Calcul des tensions moyennes, maximales et minimales
    tension = volt[0]       # Tension totale de la batterie en V
    tensionbin = BMS.int2bin(int(tension * 100))    # Conversion de la tension totale en binaire avec 2 décimales fixes
    tempmax = tempe[1]      # Température maximale des capteurs de température en °C
    tempmaxbin = BMS.int2bin(int(tempmax * 100))    # Conversion de la température maximale en binaire avec 2 décimales fixes
    if len(tensionbin) <= 8:    # Si la longueur du tableau binaire de tension est inférieure ou égale à 8, on ajoute des zéros au début passer à 16 bits
        tensionbin = [0] * 8 + tensionbin
    if len(tempmaxbin) <= 8:    # Si la longueur du tableau binaire de température maximale est inférieure ou égale à 8, on ajoute des zéros au début passer à 16 bits
        tempmaxbin = [0] * 8 + tempmaxbin
    n += 1     # Incrémentation du compteur de messages CAN
    n = n%201  # On remet le compteur à 0 après 200 messages pour éviter les doublons
    with can.Bus(channel="can0", interface="socketcan") as bus:
        msg = can.Message(
            arbitration_id=CANID,
            data=[
                BMS.bin2int(tensionbin[:8]),    # 1er octet de la tension totale
                BMS.bin2int(tensionbin[8:]),    # 2ème octet de la tension totale
                BMS.bin2int(tempmaxbin[:8]),    # 1er octet de la température maximale
                BMS.bin2int(tempmaxbin[8:]),    # 2ème octet de la température maximale
                n,  # for test purpose only
            ],
        )       # Création du message CAN avec l'ID et les données
        try:
            bus.send(msg)   # Envoi du message CAN
        except Exception as err:    # Si une erreur est levée lors de l'envoi du message CAN
            print("Message CAN non envoyé :")
            print(f"{type(err).__name__} was raised: {err}")


if __name__ == "__main__":
    if os.path.isfile(PATH + "data/data.bin"):
        update_archive()    # Si le fichier data.bin existe, on le compresse pour libérer de l'espace disque avant de lancer le monitoring

    BMS.init()  # On initialise les variables du BMS
    ADC.init()  # On initialise les variables de l'ADC

    BMS.write_read_cfg(READ_ENABLE)  # On écrit la config actuelle dans le BMS

    ACTIVE = True  # On active la boucle
    MUX_PIN = 0    # On commence par traiter le capteur de température au PIN 0
    NO_PROBLEM = [0] * (32 * BMS.TOTAL_IC)
    # Création d'un code d'erreur en cas d'interruption
    NO_PROBLEM_OUTPUT.on()  # On allume la LED du SDC (pour indiquer qu'il n'y a pas de problème)

    TIMER = time.time()     # On initialise le timer

    while ACTIVE:
        # try:  # On utilise un try/except pour éviter les erreurs de lecture/écriture
        TIME = time.time()      # On récupère le temps actuel à chaque itération
        send_data_CAN()         # Envoi des données de tension et de température sur le bus CAN
        BMS.start_cell_mes(READ_ENABLE)     # On démarre la mesure des cellules (tensions)
        BMS.start_GPIO_mes(READ_ENABLE)     # On démarre la mesure des GPIO (températures)
        BMS.read_cell_v(READ_ENABLE)        # récupère les tensions des cellules dans le registre de conversion de l'ADC et les stocke dans la configuration du BMS (BMS_IC.cells.c_codes)
        if MUX_PIN <= MAX_MUX_PIN:          # l'ADC ne peut lire qu'une seule valeur de capteur de température à l ---> /!\ ATTENTION /!\ peut être une erreur ! fois, donc on lit les capteurs un par un
            MUX_PIN += 1        # On change de capteur de température à chaque itération
        else:
            MUX_PIN = 1         # On revient au capteur 1 après avoir lu tous les capteurs car on lit le cellules de
        BMS.read_GPIO_v(READ_ENABLE)        # récupère les valeurs des GPIO dans le registre de conversion de l'ADC et les stocke dans la configuration du BMS (BMS_IC.aux.a_codes)
        store_temp(MUX_PIN - 1)             # On stocke la valeur du capteur de température dans la configuration du BMS (BMS_IC.temp)
        ADC.read_value()        # On lit la valeur de l'ADC et la stocke dans ADC.VALUE (tension de la batterie)
        if MODE == "DISCHARGE":
            write_data()        # On écrit les données dans le fichier data.bin
            if ADC.convert_current(ADC.VALUE) >= MAX_DISCHARGE_CURRENT:     # Si le courant de décharge est supérieur au maximum autorisé
                NO_PROBLEM[1] = 1          # On met le code d'erreur à 1 pour indiquer qu'il y a un problème
                NO_PROBLEM_OUTPUT.off()    # On éteint la LED du SDC (pour indiquer qu'il y a un problème)
            for current_ic in range(BMS.TOTAL_IC):  # Pour chaque BMS en chaine
                for cell in range(12):     # Pour chaque cellule du BMS k
                    # On teste pour voir s'il y a des problemes d'over/undervoltage et on modifie le code d'erreur en conséquence
                    if (
                        BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001      # Lit la valeur de tension de la cellule i du BMS k et la convertit en V
                        >= OVERVOLTAGE      # Surtension
                    ):
                        NO_PROBLEM[current_ic * 32 + cell + 2] = 1      # On met le code d'erreur à 1 pour indiquer qu'il y a un problème
                        NO_PROBLEM_OUTPUT.off()     # On éteint la LED du SDC (pour indiquer qu'il y a un problème)
                    elif (
                        BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001      # Lit la valeur de tension de la cellule i du BMS k et la convertit en V
                        <= UNDERVOLTAGE     # Sous-tension
                    ):
                        NO_PROBLEM[current_ic * 32 + cell + 2] = 1      # On met le code d'erreur à 1 pour indiquer qu'il y a un problème
                        NO_PROBLEM_OUTPUT.off()     # On éteint la LED du SDC (pour indiquer qu'il y a un problème)
                for temp_v in range(MAX_MUX_PIN):   # idem mais pour les températures
                    if (
                        temp(BMS.config.BMS_IC[current_ic].temp[temp_v])    # Lit la valeur du capteur de température i du BMS k
                        >= DISCHARGE_MAX_T  # Surchauffe
                    ):
                        NO_PROBLEM[current_ic * 32 + 16 + 2 + temp_v] = 1   # On met le code d'erreur à 1 pour indiquer qu'il y a un problème
                        NO_PROBLEM_OUTPUT.off()     # On éteint la LED du SDC (pour indiquer qu'il y a un problème)
        elif MODE == "CHARGE":
            write_data()        # On écrit les données dans le fichier data.bin
            if ADC.convert_current(ADC.VALUE) >= MAX_DISCHARGE_CURRENT:     # Si le courant de charge est supérieur au maximum autorisé
                NO_PROBLEM[1] = 1           # On met le code d'erreur à 1 pour indiquer qu'il y a un problème
                NO_PROBLEM_OUTPUT.off()     # On éteint la LED du SDC (pour indiquer qu'il y a un problème)
            for current_ic in range(BMS.TOTAL_IC):      # Pour chaque BMS en chaine
                for cell in range(12):      # Pour chaque cellule du BMS k
                    if (
                        BMS.config.BMS_IC[current_ic].cells.c_codes[cell] * 0.0001      # Lit la valeur de tension de la cellule i du BMS k et la convertit en V
                        >= OVERVOLTAGE      # Surtension
                    ):
                        NO_PROBLEM[current_ic * 32 + cell + 2] = 1      # On met le code d'erreur à 1 pour indiquer qu'il y a un problème
                        NO_PROBLEM_OUTPUT.off()     # On éteint la LED du SDC (pour indiquer qu'il y a un problème)
                for temp_v in range(MAX_MUX_PIN):   # idem mais pour les températures
                    if temp(BMS.config.BMS_IC[current_ic].temp[temp_v]) >= CHARGE_MAX_T:    # Surchauffe
                        NO_PROBLEM[current_ic * 32 + 16 + temp_v + 2] = 1       # On met le code d'erreur à 1 pour indiquer qu'il y a un problème
                        NO_PROBLEM_OUTPUT.off()     # On éteint la LED du SDC (pour indiquer qu'il y a un problème)
        else:       # MODE == "STANDBY" Dans le cas ou on veut juste monitorer les valeurs, sur de longues durées
            if TIME - TIMER > LOW_WRITE_TIME:   # Si le temps écoulé depuis la dernière écriture est supérieur au temps d'écriture
                write_data()    # On écrit les données dans le fichier data.bin
                TIMER = TIME    # Mise à jour du timer
        # except:       # On utilise un try/except pour éviter les erreurs de lecture/écriture
        #     ACTIVE = False    # On arrête la boucle en cas d'erreur
        #     NO_PROBLEM[0] = 1         # On met le code d'erreur à 1 pour indiquer qu'il y a un problème
        #     NO_PROBLEM_OUTPUT.off()   # On éteint la LED du SDC (pour indiquer qu'il y a un problème)
