Le processus d'acquisition et de gestion des données dans ce script se déroule en plusieurs étapes principales, exécutées en boucle dans la section `while ACTIVE`. Voici une explication détaillée avec des précisions supplémentaires :

---

### **1. Initialisation**
   - Avant d'entrer dans la boucle principale, le script initialise les modules et variables nécessaires :
     - **Initialisation des modules** :
       - `BMS.init()` : Initialise les variables et la configuration du système de gestion des batteries (Battery Management System).
       - `ADC.init()` : Configure l'ADC pour la lecture des tensions globales.
     - **Configuration du BMS** :
       - `BMS.write_read_cfg(READ_ENABLE)` : Écrit la configuration actuelle dans le BMS et active/désactive l'affichage des données dans la console selon `READ_ENABLE`.
     - **Préparation des variables** :
       - `NO_PROBLEM` : Tableau binaire initialisé à 0, utilisé pour signaler les erreurs (surtension, sous-tension, surchauffe, etc.).
       - `NO_PROBLEM_OUTPUT` : LED GPIO utilisée pour indiquer l'absence de problème (allumée par défaut).
       - `MUX_PIN` : Index du capteur de température actif (commence à 0).
       - `TIMER` : Stocke le temps de la dernière écriture dans le fichier pour le mode `STANDBY`.

---

### **2. Lecture des données**
   - À chaque itération de la boucle :
     - **Temps actuel** :
       - `TIME = time.time()` : Récupère le timestamp actuel pour synchroniser les opérations.
     - **Mesures des cellules** :
       - `BMS.start_cell_mes(READ_ENABLE)` : Démarre la mesure des tensions des cellules.
       - `BMS.read_cell_v(READ_ENABLE)` : Lit les tensions des cellules et les stocke dans la configuration du BMS (`BMS_IC.cells.c_codes`).
     - **Mesures des températures** :
       - `BMS.start_GPIO_mes(READ_ENABLE)` : Démarre la mesure des températures via les GPIO.
       - `BMS.read_GPIO_v(READ_ENABLE)` : Lit les valeurs des GPIO et les stocke dans la configuration du BMS (`BMS_IC.aux.a_codes`).
       - `store_temp(MUX_PIN - 1)` : Stocke la température du capteur actif dans la configuration du BMS (`BMS_IC.temp`).
       - **Gestion des capteurs** :
         - `MUX_PIN` est incrémenté pour passer au capteur suivant. Une fois tous les capteurs lus, il revient à 1.

---

### **3. Lecture de la tension globale**
   - `ADC.read_value()` : Lit la tension globale de la batterie via l'ADC et la stocke dans `ADC.VALUE`.

---

### **4. Traitement selon le mode**
   - Le comportement varie en fonction de la valeur de `MODE` :
     - **DISCHARGE** :
       - Les données sont écrites dans les fichiers avec `write_data()`.
       - Les courants et tensions des cellules sont vérifiés pour détecter des problèmes :
         - **Surtension** : Si une cellule dépasse `OVERVOLTAGE`.
         - **Sous-tension** : Si une cellule est en dessous de `UNDERVOLTAGE`.
         - **Surchauffe** : Si un capteur dépasse `DISCHARGE_MAX_T`.
     - **CHARGE** :
       - Similaire à `DISCHARGE`, mais avec des seuils spécifiques pour la charge (ex. `CHARGE_MAX_T` pour la température).
     - **STANDBY** :
       - Les données sont écrites à intervalles réguliers définis par `LOW_WRITE_TIME`.

---

### **5. Envoi des données sur le bus CAN**
   - Les données de tension et de température sont calculées via :
     - `calc_temp()` : Renvoie la température moyenne, maximale, minimale, et leurs indices.
     - `calc_voltage()` : Renvoie la tension totale, moyenne, maximale, minimale, et leurs indices.
   - Ces données sont envoyées sur le bus CAN avec `send_data_CAN()` :
     - Les valeurs sont converties en binaire (16 bits) et envoyées sous forme de message CAN.

---

### **6. Écriture des données**
   - Les données collectées (tensions, températures, etc.) sont converties en format binaire et écrites dans deux fichiers :
     - `data.bin` : Ajout des nouvelles données à la fin du fichier.
     - `actualdata.bin` : Remplacement du contenu précédent par les nouvelles données.

---

### **7. Archivage des données**
   - Si le fichier `data.bin` existe au démarrage, il est compressé en un fichier `.7z` pour libérer de l'espace disque via `update_archive()` :
     - Le fichier est renommé avec une date et un index pour éviter les doublons.
     - Une fois compressé, le fichier original est supprimé.

---

### **8. Gestion des erreurs**
   - Si des problèmes sont détectés (surtension, sous-tension, surchauffe), le tableau `NO_PROBLEM` est mis à jour pour signaler les erreurs :
     - Les indices correspondants dans `NO_PROBLEM` sont mis à 1.
     - La LED GPIO (`NO_PROBLEM_OUTPUT`) est éteinte pour indiquer un problème.
   - Les erreurs sont également gérées dans la boucle principale avec un bloc `try/except` (commenté dans le code).

---

### **Structures de données importantes**

| Nom                | Type       | Description                                                                 |
|--------------------|------------|-----------------------------------------------------------------------------|
| `NO_PROBLEM`       | `List[int]`| Tableau binaire signalant les erreurs (0 = pas de problème, 1 = problème). |
| `BMS_IC.cells.c_codes` | `List[int]`| Tensions des cellules pour chaque BMS (en unités brutes).                  |
| `BMS_IC.temp`      | `List[float]`| Températures des capteurs pour chaque BMS (en °C).                         |
| `ADC.VALUE`        | `int`      | Tension globale mesurée par l'ADC (en unités brutes).                      |

---

### **Résumé des étapes principales**
1. **Initialisation** : Configuration des modules et variables.
2. **Lecture des données** : Mesures des tensions et températures.
3. **Traitement** : Vérification des seuils et gestion des erreurs.
4. **Envoi CAN** : Transmission des données sur le bus CAN.
5. **Écriture** : Stockage des données dans des fichiers binaires.
6. **Archivage** : Compression des fichiers pour libérer de l'espace.
7. **Gestion des erreurs** : Mise à jour des indicateurs et signalisation des problèmes.

Ce processus est répété en boucle tant que `ACTIVE` est `True`, permettant un suivi en temps réel des paramètres critiques du système.