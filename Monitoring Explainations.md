Le processus d'acquisition des données dans ce script se déroule en plusieurs étapes principales, qui sont exécutées en boucle dans la section `while ACTIVE`. Voici une explication détaillée :

### 1. **Initialisation**
   - Avant d'entrer dans la boucle principale, le script initialise les modules nécessaires :
     - Initialisation des variables du BMS (`BMS.init()`).
     - Initialisation de l'ADC (`ADC.init()`).
     - Configuration du BMS avec `BMS.write_read_cfg(READ_ENABLE)`.

### 2. **Lecture des données**
   - À chaque itération de la boucle :
     - Le temps actuel est récupéré avec `TIME = time.time()`.
     - Les mesures des cellules (tensions) sont démarrées avec `BMS.start_cell_mes(READ_ENABLE)`.
     - Les mesures des GPIO (températures) sont démarrées avec `BMS.start_GPIO_mes(READ_ENABLE)`.
     - Les tensions des cellules sont lues et stockées dans la configuration du BMS avec `BMS.read_cell_v(READ_ENABLE)`.
     - Les valeurs des GPIO (températures) sont lues et stockées avec `BMS.read_GPIO_v(READ_ENABLE)`.

### 3. **Stockage des températures**
   - Les températures des capteurs sont stockées dans la configuration du BMS via la fonction `store_temp(MUX_PIN - 1)`. Cela permet de traiter un capteur à la fois, en incrémentant `MUX_PIN` à chaque itération.

### 4. **Lecture de la tension globale**
   - La tension globale de la batterie est mesurée avec `ADC.read_value()` et stockée dans `ADC.VALUE`.

### 5. **Traitement selon le mode**
   - Le comportement varie en fonction du mode (`MODE`), qui peut être `DISCHARGE`, `CHARGE`, ou `STANDBY` :
     - **DISCHARGE** :
       - Les données sont écrites dans le fichier avec `write_data()`.
       - Les courants et tensions des cellules sont vérifiés pour détecter des problèmes (surtension, sous-tension, surchauffe).
     - **CHARGE** :
       - Similaire à `DISCHARGE`, mais avec des seuils spécifiques pour la charge.
     - **STANDBY** :
       - Les données sont écrites à intervalles réguliers définis par `LOW_WRITE_TIME`.

### 6. **Envoi des données sur le bus CAN**
   - Les données de tension et de température sont calculées via les fonctions `calc_temp()` et `calc_voltage()`.
   - Ces données sont envoyées sur le bus CAN avec la fonction `send_data_CAN()`.

### 7. **Écriture des données**
   - Les données collectées (tensions, températures, etc.) sont converties en format binaire et écrites dans deux fichiers :
     - `data.bin` (ajout à la fin du fichier).
     - `actualdata.bin` (remplacement du contenu précédent).

### 8. **Archivage des données**
   - Si le fichier `data.bin` existe au démarrage, il est compressé en un fichier `.7z` pour libérer de l'espace disque via la fonction `update_archive()`.

### 9. **Gestion des erreurs**
   - Si des problèmes sont détectés (surtension, sous-tension, surchauffe), le code d'erreur `NO_PROBLEM` est mis à jour, et la LED associée (`NO_PROBLEM_OUTPUT`) est éteinte pour signaler un problème.

Ce processus est répété en boucle tant que `ACTIVE` est `True`.