from typing import List


class CV:
    """
    Cell Voltage data structure.
    """

    def __init__(self):
        self.c_codes: List[int] = [0] * 18  # Cell Voltage Codes
        self.pec_match: List[int] = [0] * 6
        # If a PEC error was detected during most recent read cmd


class AX:
    """
    AUX Reg Voltage Data structure.
    """

    def __init__(self):
        self.a_codes: List[int] = [0] * 9  # Aux Voltage Codes
        self.pec_match: List[int] = [0] * 4
        # If a PEC error was detected during most recent read cmd


class ST:
    """
    Status Reg data structure.
    """

    def __init__(self):
        self.stat_codes: List[int] = [0] * 4  # Status codes
        self.flags: List[int] = [0] * 3  # Byte array that contains the uv/ov flag data
        self.mux_fail: List[int] = [0] * 1  # Mux self test status flag
        self.thsd: List[int] = [0] * 1  # Thermal shutdown status
        self.pec_match: List[int] = [0] * 2
        # If a PEC error was detected during most recent read cmd


class ICRegister:
    """
    IC register structure.
    """

    def __init__(self):
        self.tx_data: List[int] = [0] * 6  # Stores data to be transmitted
        self.rx_data: List[int] = [0] * 8  # Stores received data
        self.rx_pec_match: int = 0
        # If a PEC error was detected during most recent read cmd


class PECCounter:
    """
    PEC error counter structure.
    """

    def __init__(self):
        self.pec_count: int = 0  # Overall PEC error count
        self.cfgr_pec: int = 0  # Configuration register data PEC error count
        self.cell_pec: List[int] = [0] * 6  # Cell voltage register data PEC error count
        self.aux_pec: List[int] = [0] * 4  # Aux register data PEC error count
        self.stat_pec: List[int] = [0] * 2  # Status register data PEC error count


class RegisterCfg:
    """
    Register configuration structure.
    """

    def __init__(self):
        self.cell_channels: int = 0  # Number of Cell channels
        self.stat_channels: int = 0  # Number of Stat channels
        self.aux_channels: int = 0  # Number of Aux channels
        self.num_cv_reg: int = 0  # Number of Cell voltage register
        self.num_gpio_reg: int = 0  # Number of Aux register
        self.num_stat_reg: int = 0  # Number of Status register


class CellASIC:
    """
    Cell variable structure.
    """

    def __init__(self):
        self.config = ICRegister()
        self.configb = ICRegister()
        self.cells = CV()
        self.aux = AX()
        self.stat = ST()
        self.com = ICRegister()
        self.pwm = ICRegister()
        self.pwmb = ICRegister()
        self.sctrl = ICRegister()
        self.sctrlb = ICRegister()
        self.sid: List[int] = [0] * 6
        self.isospi_reverse: bool = False
        self.crc_count = PECCounter()
        self.ic_reg = RegisterCfg()
        self.system_open_wire: int = 0
        self.temp = [0] * 18


def init(total_ic):
    """Initialise les configurations pour chaque BMS"""
    global BMS_IC
    BMS_IC = [CellASIC() for _ in range(total_ic)]
