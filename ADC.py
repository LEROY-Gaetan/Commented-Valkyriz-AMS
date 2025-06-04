"""
Code de contrôle de l'ADC ADS1115-Q1 via I2C
"""
### Code de controle de l'ADC
# Datasheet du ADS1115-Q1:
# https://www.ti.com/lit/ds/symlink/ads1115-q1.pdf?ts=1718378770402

import smbus2
from typing import List
from LTC681x import bin2int, int2bin


# I2C channel 0 is connected to the GPIO pins
I2C_CHANNEL = 1  # i2cdetect -y 1 to detect

ADR = [1, 0, 0, 1, 0, 0, 0]  # Adresse de l'ADC, avec le pin address mis au gnd
CONFIG_REG = [0, 0, 0, 0, 0, 0, 0, 1]
DATA_REG = [0, 0, 0, 0, 0, 0, 0, 0]
CHANNEL = {0: [1, 0, 0], 1: [1, 0, 1], 2: [1, 1, 0], 3: [1, 1, 1]}
FSR = 6.144  # V Full Scale rate (valeur maximale de tension)
RESISTOR = 47  # Ohm (Valeur de résistance en entrée de channel)
ENTRY = 3

# Initialize I2C (SMBus)
bus = smbus2.SMBus(I2C_CHANNEL)


def set_channel(entry: int):
    """
    Ecrit dans le registre de configuration de l'ADC pour sélectionner le canal d'entrée et configurer les paramètres de conversion.
    
    Parameters:
        entry (int): Numéro du canal d'entrée à sélectionner (0 à 3).
    """
    address = bin2int(ADR)  # R/W bit low to Write --> vraie addresse = 144
    reg = bin2int(CONFIG_REG)  # Registre de configuration --> reg = 1
    if not (0 <= entry <= 3):   
        print("N° d'entrée invalide")
        return
    bit1 = [1] + CHANNEL[entry] + [0, 0, 0] + [0]
    # Voir datasheet p27 Table 8-6
    #
    # Premier bit : statut opérationnel (OS=0b1)                --> 1 pour allumé (0 pour éteint)
    # 2-3-4 bit : sélection du channel d'entrée (MUX)           --> controle l'assignment des entrées analogiques AIN0-AIN3 et GND au canaux AIN_N et AIN_P
    # 5-6-7 bit : Gain d'amplification programmable (PGA=0b000) --> FSR = ±6.144 V (valeur maximale de tension) 
    # 8 bit : mode de conversion (MODE=0b0)                     --> mode continu (1 pour mode single shot)
    bit2 = [1,0,0,  0,  0,  0,  1,1]
    # 1-2-3 bit : Sélection du data rate (DR=0b100)             --> 128 SPS (Samples Per Second ~= Hz)
    # 4 bit : Mode de comparateur (COMP_MODE=0b0)               --> comparateur normal (1 pour mode de fenêtre glissante)
    # 5 bit : Polarité de comparateur (COMP_POL=0b0)            --> normalement ouvert (1 pour normalement fermé)
    # 6 bit : Mode de trigger du comparateur (COMP_LAT=0b0)     --> triger sur la clock (1 pour trigger sur lecture)
    # 7-8 bit : Activer le alert/ready (COMP_QUE=0b11)          --> ALERT/RDY désactivé (haute impédance)
    
    msg = smbus2.i2c_msg.write(address, [reg, bin2int(bit1), bin2int(bit2)])
    bus.i2c_rdwr(msg)   # Envoi du message sur le bus I2C par le pin 0b10010000 = 144


def enable_read():
    """
    Séléctionne le registre de données de l'ADC pour lire la valeur convertie.
    """
    address = bin2int(ADR)   # R/W bit low to write --> vraie addresse = 144
    reg = bin2int(DATA_REG)  # Registre de données --> reg = 0
    msg = smbus2.i2c_msg.write(address, [reg])  # Sélection du registre de données
    bus.i2c_rdwr(msg)        # Envoi du message sur le bus I2C par le pin 0b10010000 = 144


def read_value():
    """
    Lit la valeur convertie de l'ADC depuis le registre de données.
    """
    global VALUE
    enable_read()
    addr = bin2int(ADR)     # R/W bit high to read --> vraie addresse = 145
    msg = smbus2.i2c_msg.read(addr, 2)     # Lecture des 2 octets de données (16 bits)
    bus.i2c_rdwr(msg)   # Envoi du message sur le bus I2C par le pin 0b10010001 = 145
    resmsg = []
    for value in msg:
        resmsg += int2bin(value)    # Concaténation des valeurs lues dans un tableau binaire
    if resmsg[0] == 0:    # Si le premier bit est à 0, c'est un nombre positif (complément à 2)
        VALUE = bin2int(resmsg)
    else:  # Sinon, c'est un nombre négatif
        comp2 = [0] * 16
        for k in range(1, 16):
            if resmsg[k] == 0:  # on inverse les bits
                comp2[k] = 1
        VALUE = 1-bin2int(comp2) # on assigne la valeur négative (+1 car -n = /n + 1 dans le complément à 2)


def convert_current(value: int):
    """
    Convertit sur 16 bits la valeur lue de l'ADC en courant (en Ampères).
    """
    return value * FSR * 1000 / (2**15) / RESISTOR      # réindexation de la valeur lue brute et conversion en courant (en A) via loi d'Ohm


def init():
    """
    Initialise l'ADC en configurant le canal d'entrée et en lisant la valeur initiale.
    """
    global VALUE  # Valeur lue de l'ADC
    VALUE = 0   # Initialisation de la valeur lue
    set_channel(ENTRY)  # Sélection du canal d'entrée (0 à 3)
    enable_read()   # initialisation de la lecture
    read_value()    # Lecture de la valeur convertie
    print("Valeur de tension initiale :", VALUE, " V")
    print("Valeur en courant : ", convert_current(VALUE), " A")


if __name__ == "__main__":
    init()
