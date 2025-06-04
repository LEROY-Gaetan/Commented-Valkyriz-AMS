L'ADC (Analog-to-Digital Converter) est un composant électronique qui convertit un signal analogique (continu) en un signal numérique (discret). Dans ce code, l'ADC utilisé est un ADS1115-Q1, qui communique via le protocole I2C. Voici un résumé de son fonctionnement dans ce contexte :

1. **Configuration de l'ADC** :
   - L'ADC est configuré via son registre de configuration (`CONFIG_REG`).
   - La fonction `set_channel(entry)` permet de sélectionner un canal d'entrée (parmi 4 possibles) et de configurer les paramètres de conversion (gain, mode, etc.) en écrivant dans ce registre.

2. **Lecture des données** :
   - La fonction `enable_read()` sélectionne le registre de données (`DATA_REG`) pour préparer la lecture.
   - La fonction `read_value()` lit les données converties depuis ce registre. Les données sont récupérées sur 16 bits et converties en un entier signé (complément à 2).

3. **Conversion en courant** :
   - La fonction `convert_current(value)` utilise la loi d'Ohm pour convertir la valeur numérique lue en courant (en Ampères), en tenant compte de la pleine échelle (FSR) et de la résistance d'entrée.

4. **Initialisation** :
   - La fonction `init()` configure l'ADC, sélectionne un canal d'entrée, et effectue une première lecture pour afficher la tension et le courant initiaux.

5. **Protocole I2C** :
   - Le protocole I2C est utilisé pour communiquer avec l'ADC. Les fonctions `smbus2.i2c_msg.write` et `smbus2.i2c_msg.read` permettent d'envoyer et de recevoir des données via le bus I2C.

En résumé, ce code configure l'ADC, lit les données analogiques converties en numérique, et les convertit en courant pour une application spécifique.

### **Structures de données**

| Nom            | Type                   | Description                                                                      |
|----------------|------------------------|----------------------------------------------------------------------------------|
| `ADR`          | `List[int]`            | Adresse binaire de l'ADC (7 bits) avec le pin d'adresse connecté au GND.         |
| `CONFIG_REG`   | `List[int]`            | Registre de configuration de l'ADC (8 bits).                                     |
| `DATA_REG`     | `List[int]`            | Registre de données de l'ADC (8 bits).                                           |
| `CHANNEL`      | `Dict[int, List[int]]` | Dictionnaire associant chaque canal (0 à 3) à sa configuration binaire (3 bits). |
| `FSR`          | `float`                | Tension maximale en pleine échelle (±6.144 V).                                   |
| `RESISTOR`     | `int`                  | Résistance d'entrée en Ohms (47 Ω).                                              |
| `ENTRY`        | `int`                  | Canal d'entrée sélectionné par défaut (3).                                       |

---

### **Paramètres des registres**

[Fiche technique officielle de l'ADS1115-Q1](https://www.ti.com/lit/ds/symlink/ads1115-q1.pdf#%5B%7B%22num%22%3A181%2C%22gen%22%3A0%7D%2C%7B%22name%22%3A%22XYZ%22%7D%2Cnull%2C717%2Cnull%5D)

| Bit Position | Nom du champ | Description                                                                      |
|--------------|--------------|----------------------------------------------------------------------------------|
| 0            | OS           | Statut opérationnel (1 = actif, 0 = inactif).                                    |
| 1-3          | MUX          | Sélection du canal d'entrée (0-3).                                               |
| 4-6          | PGA          | Gain programmable (0 = ±6.144 V, 1 = ±4.096 V, 2 = ±2.048 V, ..., 5 = ±0.256 V). |
| 7            | MODE         | Mode de conversion (0 = continu, 1 = unique).                                    |
| 8-10         | DR           | Taux de conversion (0 = 8 SPS, 1 = 16 SPS, 2 = 32 SPS, ..., 7 = 860 SPS).        |
| 11           | COMP_MODE    | Mode de comparaison (0 = comparateur, 1 = alerte).                               |
| 12           | COMP_POL     | Polarité de l'alerte (0 = active haut, 1 = active bas).                          |
| 13           | COMP_LAT     | Latence de l'alerte (0 = non-latent, 1 = latent).                                |
| 14-15        | COMP_QUE     | Nombre d'erreurs avant alerte (0 = 1 err, 1 = 2 err, 2 = 4 err, 3 = désactivé)   |
