### **Explication du code**

Ce code lit un fichier binaire contenant des données de mesure (courant, tensions des cellules, températures) et les affiche de manière lisible. Voici une explication détaillée des différentes parties :

---

### **1. Importations**
- **Modules importés** :
  - `LTC6811`, `Monitoring`, `read_temp`, `ADC` : Fournissent des constantes et fonctions pour traiter les données.
  - `datetime` : Utilisé pour convertir les timestamps en dates lisibles.
- **Fonction clé importée** :
  - `convert_current` : Convertit une valeur brute en courant (Ampères).

---

### **2. Fonction `print_data(n)`**
- **Objectif** : Affiche les données d'une ligne spécifique (index `n`) de manière lisible.
- **Structure des données affichées** :
  - **Date** : Timestamp converti en date.
  - **Courant** : Courant mesuré (en Ampères).
  - **Cellules** : Tensions des cellules (en Volts) pour chaque BMS.
  - **Températures** : Températures mesurées (en °C) pour chaque capteur.

---

### **3. Lecture du fichier binaire**
- **Chemin du fichier** : Défini par `filepath` (`/usr/share/AMS/data/data.bin`).
- **Taille d'un bloc de données** :
  - Calculée par `chunksize` : Dépend du nombre de cellules (`NB_CELLS`), de capteurs de température (`MAX_MUX_PIN`), et du nombre total de BMS (`TOTAL_IC`).
- **Lecture des blocs** :
  - Les blocs de données sont lus séquentiellement et ajoutés à `data_raw`.

---

### **4. Traitement des données brutes**
- **Structure des données** :
  - Chaque bloc brut est transformé en une liste `mes` contenant :
    1. **Timestamp** : Converti en date lisible.
    2. **Courant** : Converti en Ampères via `convert_current`.
    3. **Tensions des cellules** : Converties en Volts.
    4. **Températures** : Converties en °C via la fonction `temp`.

---

### **Résumé des étapes principales**
1. **Lecture du fichier binaire** :
   - Les données brutes sont lues et stockées dans `data_raw`.
2. **Traitement des données** :
   - Les données brutes sont converties en valeurs lisibles (date, courant, tensions, températures).
3. **Affichage** :
   - Les données traitées sont affichées ligne par ligne.

---

En résumé, ce code lit un fichier binaire contenant des mesures, les traite pour les rendre lisibles, et les affiche de manière structurée.