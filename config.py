from typing import List


class CV:
    """
    Structure des données de tension des cellules.
    
    Attributs :
    -----------
    c_codes : List[int]
        Liste des tensions mesurées sur les cellules (en code brut ADC).
        Longueur maximale : 18 cellules par circuit intégré (IC).
        Initialisation à 0 pour toutes les cellules.
        Ces valeurs seront mises à jour après lecture effective depuis les registres du LTC6811.

    pec_match : List[int]
        Liste d’indicateurs d’erreurs PEC (Packet Error Code) pour chaque registre de tension cellule lu.
        Chaque élément vaut :
            0 → OK : le code PEC reçu correspond au code recalculé (données valides)
            1 → ERREUR : le code PEC ne correspond pas (données potentiellement corrompues)
    """

    def __init__(self):
        self.c_codes: List[int] = [0] * 18  
        self.pec_match: List[int] = [0] * 6  


class AX:
    """
    Structure pour stocker les tensions des broches auxiliaires (GPIO).

    Attributs :
    -----------
    a_codes : List[int]
        Liste des tensions mesurées sur les broches auxiliaires (ex : GPIO1 à GPIO5, Vref2, etc.).
        Chaque valeur est un code brut ADC, initialisé à 0.
        Longueur maximale : 9 codes (selon la configuration de l’IC).

    pec_match : List[int]
        Liste d’indicateurs d’erreurs PEC (Packet Error Code) pour les lectures des registres auxiliaires.
        Chaque élément vaut :
            0 → OK : le code PEC reçu est correct (les données sont fiables)
            1 → ERREUR : le code PEC est incorrect (données potentiellement invalides)
    """

    def __init__(self):
        self.a_codes: List[int] = [0] * 9
        self.pec_match: List[int] = [0] * 4


class ST:
    """
    La classe ST (pour Status Register) représente les informations internes 
    du circuit intégré BMS qui ne sont pas directement liées aux cellules ou 
    aux GPIOs, mais à son propre état de fonctionnement.

    Attributs :
    -----------
    stat_codes : List[int]
        Liste contenant les valeurs mesurées dans les registres de statut internes
        Jusqu’à 4 codes peuvent être présents selon le nombre de registres activés (RDSTATA et RDSTATB).
        Chaque valeur correspond à une mesure brute (ADC), interprétée ailleurs si nécessaire.

    flags : List[int]
        Données brutes extraites du registre RDSTATB indiquant des conditions de défaut :
            - Détection de sous-tension (UV) ou surtension (OV),
            - Statuts divers liés aux cellules.
        Codées sur 3 octets.

    mux_fail : List[int]
        Le LTC6811 effectue un self-test interne pour vérifier si le multiplexeur fonctionne correctement
        S’il détecte une anomalie (ex : court-circuit, broche bloquée, canal non actif), il le signale en mettant un bit à 1.        

    thsd : List[int]  
        C’est un indicateur de sécurité fourni par le circuit intégré LTC6811, qui signale si la température interne du 
        composant a dépassé une limite critique, entraînant l’arrêt automatique de certaines fonctions pour éviter la surchauffe destructrice.
        Contient 1 bit indiquant si une condition de "thermal shutdown" a été détectée

    pec_match : List[int]
        Indicateurs d’erreurs PEC associés à la lecture des registres de statut.
        Chaque élément vaut :
            0 → OK : le code PEC reçu est correct (données fiables)
            1 → ERREUR : le code PEC est incorrect (données potentiellement corrompues)
    """

    def __init__(self):
        self.stat_codes: List[int] = [0] * 4       
        self.flags: List[int] = [0] * 3            
        self.mux_fail: List[int] = [0] * 1         
        self.thsd: List[int] = [0] * 1             
        self.pec_match: List[int] = [0] * 2        




class ICRegister:
    """
    Structure pour modéliser un registre de communication entre le microcontrôleur 
    (comme un Raspberry Pi) et un circuit intégré LTC6811.
    
    
    Attributs :
    -----------
    tx_data : List[int] (= transit data)
        Données à transmettre vers le registre via le bus SPI.
        Composées de 6 octets selon la spécification du LTC6811.
        Exemples d’usages : activer des broches GPIO, définir les seuils UV/OV, configurer le mode ADC, etc.

    rx_data : List[int] (= receive data)
        Données reçues depuis le registre après une commande de lecture.
        Composées de 8 octets :
            - 6 octets de données utiles,
            - 2 octets contenant le code PEC (Packet Error Code) pour vérifier l’intégrité de la transmission.

    rx_pec_match : int
        Indicateur d’erreur PEC à la réception :
            - 0 → OK : le code PEC reçu est conforme aux données, pas d’erreur détectée,
            - 1 → ERREUR : le code PEC ne correspond pas → données potentiellement corrompues.
        Utilisé pour compter les erreurs et fiabiliser les lectures critiques.
    """

    def __init__(self):
        self.tx_data: List[int] = [0] * 6  
        self.rx_data: List[int] = [0] * 8  
        self.rx_pec_match: int = 0  


class PECCounter:
    """
    Structure de suivi des erreurs de type PEC (Packet Error Code)  

    Attributs :
    -----------
    pec_count : int
        Compteur global de toutes les erreurs PEC détectées sur l'ensemble des registres.
        C’est une mesure globale de la fiabilité de la communication SPI.

    cfgr_pec : int
        Compteur d’erreurs PEC spécifiques aux registres de configuration (CFGA et CFGB).
        Ces erreurs peuvent entraîner une mauvaise configuration des paramètres critiques (seuils UV/OV, GPIO, etc.).

    cell_pec : List[int]
        Liste contenant les erreurs PEC associées à chaque registre de tension cellule (RDCVA à RDCVF).
        Taille 6 : un compteur par registre de mesure cellule.

    aux_pec : List[int]
        Liste contenant les erreurs PEC associées aux registres auxiliaires (RDAUXA à RDAUXD), utilisés notamment pour les GPIOs.
        Taille 4 : un compteur par registre auxiliaire.

    stat_pec : List[int]
        Liste contenant les erreurs PEC associées aux registres de statut (RDSTATA et RDSTATB).
        Taille 2 : un compteur par registre de statut.

    Utilité :
    ---------
    Ces compteurs sont utilisés pour :
        - Détecter les problèmes de communication persistants ou ponctuels,
        - Fiabiliser l'interprétation des données (ignorer les mesures corrompues),
        - Évaluer la qualité du câblage ou des conditions EMI (perturbations),
        - Déclencher des actions correctives si nécessaire (relecture, sécurité...).
    """

    def __init__(self):
        self.pec_count: int = 0           
        self.cfgr_pec: int = 0           
        self.cell_pec: List[int] = [0] * 6  
        self.aux_pec: List[int] = [0] * 4   
        self.stat_pec: List[int] = [0] * 2  


class RegisterCfg:
    """
    Structure de description des tailles de registres pour un circuit intégré LTC6811.

    Cette structure permet d'indiquer au logiciel combien de canaux (cellules, GPIO, statut)
    et combien de registres de données sont effectivement utilisés pour chaque puce BMS (CellASIC).
    Elle est essentielle pour dimensionner dynamiquement les boucles de lecture/écriture et
    garantir que seules les données utiles sont traitées.

    Attributs :
    -----------
    cell_channels : int
        Nombre total de cellules surveillées par l’IC (ex : 12 pour 12 cellules Li-ion).

    stat_channels : int
        Nombre de canaux de statut (ex : température interne, VREG, etc.).

    aux_channels : int
        Nombre de broches auxiliaires (GPIO) actives pour des mesures analogiques (ex : thermistances).

    num_cv_reg : int
        Nombre de registres de tension cellule utilisés (1 registre = 3 cellules).
        Exemple : pour 12 cellules → 4 registres.

    num_gpio_reg : int
        Nombre de registres de mesures auxiliaires utilisés (1 registre = 3 GPIO).
        Exemple : pour 6 GPIOs → 2 registres.

    num_stat_reg : int
        Nombre de registres de statut utilisés (souvent 2 : RDSTATA et RDSTATB).
        Contiennent des informations comme ITMP, VREG, et flags UV/OV.
    """

    def __init__(self):
        self.cell_channels: int = 0
        self.stat_channels: int = 0
        self.aux_channels: int = 0
        self.num_cv_reg: int = 0
        self.num_gpio_reg: int = 0
        self.num_stat_reg: int = 0



class CellASIC:
    """
    Structure principale représentant un circuit intégré (IC) de gestion de batterie (BMS).

    Cette classe regroupe toutes les informations associées à un IC du système de gestion BMS,
    incluant ses configurations, ses mesures, son état interne et ses erreurs de communication.
    Elle centralise les objets de bas niveau (registre, mesure, statut) pour faciliter l'accès
    aux données et commandes relatives à un LTC6811.

    Attributs :
    -----------
    config : ICRegister
        Registre de configuration CFGA (paramètres ADC, GPIO, REFON...).

    configb : ICRegister
        Registre de configuration CFGB (paramètres complémentaires, ex : seuils UV/OV).

    cells : CV
        Structure contenant les codes de tension mesurés sur les cellules de la batterie.

    aux : AX
        Structure contenant les codes de tension mesurés sur les broches auxiliaires (GPIOs).

    stat : ST
        Structure contenant les données internes de l’IC (température, VREG, flags UV/OV, etc.).

    com : ICRegister
        Registre de communication pour le transfert de données via les GPIOs (I2C via SPI par ex.).

    pwm : ICRegister
        Registre de contrôle PWM (Pulse Width Modulation) pour pilotage externe (ex : équilibrage actif).

    pwmb : ICRegister
        Variante du registre PWM si configuration secondaire.

    sctrl : ICRegister
        Registre de contrôle secondaire (SCTRL), utilisé pour diverses fonctions avancées.

    sctrlb : ICRegister
        Variante du registre SCTRL B (optionnel selon configuration matérielle).

    sid : List[int]
        Identifiant de série du composant (souvent inutilisé ou non lu).

    isospi_reverse : bool
        Indique si le sens de la chaîne SPI est inversé (utile en cascade ou daisy chain inversée).

    crc_count : PECCounter
        Structure contenant les compteurs d’erreurs PEC (Packet Error Code), par type de registre.

    ic_reg : RegisterCfg
        Décrit le nombre de canaux et de registres utilisés pour les cellules, GPIOs et statuts.

    system_open_wire : int
        Indicateur utilisé pour détecter des fils ouverts (open wire) dans les connexions de cellules.

    temp : List[int]
        Températures calculées à partir des tensions lues sur les GPIOs (via interpolation NTC).
        Longueur 18 → pour couvrir toutes les entrées potentielles même si partiellement utilisées.
    """

    def __init__(self):
        self.config = ICRegister()     # Registre de configuration A (CFGA)
        self.configb = ICRegister()    # Registre de configuration B (CFGB)
        self.cells = CV()              # Mesures de tension cellule
        self.aux = AX()                # Mesures GPIO / auxiliaires
        self.stat = ST()               # Données internes (temp, VREG, flags)
        self.com = ICRegister()        # Registre de communication
        self.pwm = ICRegister()        # Registre PWM A
        self.pwmb = ICRegister()       # Registre PWM B
        self.sctrl = ICRegister()      # Registre de contrôle secondaire A
        self.sctrlb = ICRegister()     # Registre de contrôle secondaire B
        self.sid: List[int] = [0] * 6  # Identifiant série (optionnel)
        self.isospi_reverse: bool = False  # Chaînage SPI inversé ?
        self.crc_count = PECCounter()  # Compteur d'erreurs PEC
        self.ic_reg = RegisterCfg()    # Configuration logique des tailles de registre
        self.system_open_wire: int = 0  # Fil ouvert détecté
        self.temp = [0] * 18           # Températures interpolées (1 par GPIO possible)


def init(total_ic):
    """
    Initialise les configurations pour chaque IC BMS.
    """
    global BMS_IC
    BMS_IC = [CellASIC() for _ in range(total_ic)]
