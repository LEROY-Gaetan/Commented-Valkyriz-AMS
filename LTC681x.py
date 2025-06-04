import time
import spidev

from typing import List
import config

spi = spidev.SpiDev()

###Variables

# Macros for ADC conversion modes
MD_422HZ_1KHZ = 0
MD_27KHZ_14KHZ = 1
MD_7KHZ_3KHZ = 2
MD_26HZ_2KHZ = 3

# Macros for ADC options
ADC_OPT_ENABLED = 1
ADC_OPT_DISABLED = 0

# Macros for cell channel configurations for ADC conversion
CELL_CH_ALL = 0
CELL_CH_1and7 = 1
CELL_CH_2and8 = 2
CELL_CH_3and9 = 3
CELL_CH_4and10 = 4
CELL_CH_5and11 = 5
CELL_CH_6and12 = 6

# Macros for self-test options
SELFTEST_1 = 1
SELFTEST_2 = 2

# Macros for auxiliary channel configurations for ADC conversion
AUX_CH_ALL = 0
AUX_CH_GPIO1 = 1
AUX_CH_GPIO2 = 2
AUX_CH_GPIO3 = 3
AUX_CH_GPIO4 = 4
AUX_CH_GPIO5 = 5
AUX_CH_VREF2 = 6

# Macros for status channel configurations for ADC conversion
STAT_CH_ALL = 0
STAT_CH_SOC = 1
STAT_CH_ITEMP = 2
STAT_CH_VREGA = 3
STAT_CH_VREGD = 4

# Macros for register configurations
REG_ALL = 0
REG_1 = 1
REG_2 = 2
REG_3 = 3
REG_4 = 4
REG_5 = 5
REG_6 = 6

# Macros for enabling or disabling permitted discharge
DCP_DISABLED = 0
DCP_ENABLED = 1

# Macros for pull-up/down current options
PULL_UP_CURRENT = 1
PULL_DOWN_CURRENT = 0

# Number of received bytes
NUM_RX_BYT = 8

# Register types
CELL = 1
AUX = 2
STAT = 3
CFGR = 0
CFGRB = 4

MAX_SPEED_HZ = int(1e6)

CMD = {
    "STCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1],
    "RDCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0],
    "WRCOMM": [1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1],
    "WRCGFA": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    "WRCFGB": [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
    "RDCFGA": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    "RDCFGB": [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0],
    "RDCVA": [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    "RDCVB": [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
    "RDCVC": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    "RDCVD": [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],
    "RDCVE": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    "RDCVF": [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1],
    "RDAUXA": [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
    "RDAUXB": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
    "RDAUXC": [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1],
    "RDAUXD": [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
    "RDSTATA": [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    "RDSTATB": [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
    "WRSCTRL": [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
    "WRPWM": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    "WRPSB": [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0],
    "RDSCTRL": [0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0],
    "RDPWM": [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    "RDPSB": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],
    "STSCTRL": [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1],
    "CLRSCTRL": [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
    "CLRCELL": [1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    "CLRAUX": [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    "CLRSTAT": [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1],
    "PLADC": [1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0],
    "DIAGN": [1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1],
}

###Utilitaires divers


def bin2int(binval: List[bool]) -> int:
    """
    Convertit une liste de bits en entier.
    """
    st = ""
    for x in binval:
        st += str(x)
    return int(st, 2)


def int2bin(nb: int) -> List[bool]:
    """
    Convertit un entier en liste de bits.
    """
    if nb < 0:
        nb = -nb
    binst = bin(nb)
    nb0 = 8 * ((len(binst[2:]) - 1) // 8 + 1) - len(binst) + 2
    res = [0] * nb0
    for x in binst[2:]:
        res.append(int(x))
    return res


def create_bin_for_pec(data):
    res = []
    for x in data:
        res += int2bin(x)
    return res


def pec15_calc(nb_byte: int, data: List[bool]):
    bindata = create_bin_for_pec(data[:nb_byte])
    pecbin = calcul_PEC(bindata)
    return bin2int(pecbin[:8]), bin2int(pecbin[8:])


def XOR(a, b):
    """Simple fonction XOR"""
    if a != b:
        return 1
    else:
        return 0


def calcul_PEC(Din: list):
    """Calcul du PEC pour le mot binaire Din"""
    PEC = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0][::-1]
    for bit in Din:
        IN0 = XOR(bit, PEC[14])
        IN3 = XOR(IN0, PEC[2])
        IN4 = XOR(IN0, PEC[3])
        IN7 = XOR(IN0, PEC[6])
        IN8 = XOR(IN0, PEC[7])
        IN10 = XOR(IN0, PEC[9])
        IN14 = XOR(IN0, PEC[13])

        PEC[14] = IN14
        PEC[13] = PEC[12]
        PEC[12] = PEC[11]
        PEC[11] = PEC[10]
        PEC[10] = IN10
        PEC[9] = PEC[8]
        PEC[8] = IN8
        PEC[7] = IN7
        PEC[6] = PEC[5]
        PEC[5] = PEC[4]
        PEC[4] = IN4
        PEC[3] = IN3
        PEC[2] = PEC[1]
        PEC[1] = PEC[0]
        PEC[0] = IN0
    res = [0] + PEC
    return res[::-1]


def spi_write_read(tx_data: List[int], rx_len: int) -> None:
    """
    Writes and reads a set number of bytes using the SPI port.

    Args:
        tx_data (List[int]): Array of data to be written on SPI port.
        rx_len (int): Length of the expected rx data array.

    Returns:
        List[int]: Array of readed value
    """
    data = spi.xfer3(tx_data + [255] * rx_len)
    return data[len(tx_data) :]


###Fonctions de la LTC
def wakeup_idle(total_ic: int):
    """Wake isoSPI up from IDlE state and enters the READY state"""
    for _ in range(total_ic):
        spi.xfer3([0xFF])


def wakeup_sleep(total_ic: int, f_hz=MAX_SPEED_HZ):
    """Generic wakeup command to wake the LTC681x from sleep state"""
    # LTC681x_rdcfg(total_ic)
    for _ in range(total_ic):

        spi.xfer3([255] * int(300 * 1e-6 * f_hz))
        time.sleep(10 * 1e-6)


def cmd_68(cmd: List[bool]):
    """Generic function to write 68xx commands.\n
    Function calculates PEC for cmd data."""
    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [
        bin2int(cmdbit[:8]),
        bin2int(cmdbit[8:]),
        bin2int(pec[:8]),
        bin2int(pec[8:]),
    ]
    spi.xfer3(word)


def write_68(
    total_ic: int,
    cmd: List[bool],
    data: List[int],
):
    """Generic function to write 68xx commands and write payload data. \n
    Function calculates PEC for cmd data and the data to be transmitted."""
    BYTES_IN_REG = 6

    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [0] * (4 + 8 * total_ic)
    word[0] = bin2int(cmdbit[:8])
    word[1] = bin2int(cmdbit[8:])
    word[2] = bin2int(pec[:8])
    word[3] = bin2int(pec[8:])

    cmd_index = 4
    for current_ic in range(1, total_ic + 1)[::-1]:
        # Executes for each LTC681x, this loops starts with the last IC on the stack.
        for current_byte in range(BYTES_IN_REG):
            # The first configuration written is received by the last IC in the daisy chain
            word[cmd_index] = data[((current_ic - 1) * 6) + current_byte]
            cmd_index += 1
        data_pec = pec15_calc(BYTES_IN_REG, data[((current_ic - 1) * 6) :])
        word[cmd_index] = data_pec[0]
        word[cmd_index + 1] = data_pec[1]

        cmd_index += 2

    spi.xfer3(word)


def read_68(total_ic: int, cmd: List[bool]):
    """Generic function to write 68xx commands and read data. \n
    Function calculated PEC for cmd data"""

    BYTES_IN_REG = 8
    pec_error = 0

    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [0] * 4
    word[0] = bin2int(cmdbit[:8])
    word[1] = bin2int(cmdbit[8:])
    word[2] = bin2int(pec[:8])
    word[3] = bin2int(pec[8:])

    data = spi_write_read(word, (BYTES_IN_REG) * total_ic)
    res = [0] * len(data)

    for current_ic in range(total_ic):
        for current_byte in range(BYTES_IN_REG):
            res[(current_ic * 8) + current_byte] = data[
                current_byte + (current_ic * BYTES_IN_REG)
            ]

    received_pec = (res[(current_ic * 8) + 6], res[(current_ic * 8) + 7])
    data_pec = pec15_calc(6, data[((current_ic) * 6) :])
    if received_pec != data_pec:
        pec_error = -1

    return res, pec_error


def LTC681x_wrcfg(total_ic: int):
    """
    Write the LTC681x CFGRA.

    :param total_ic: The number of ICs being written to.
    :param ic: A list of CellASIC objects that contain the configuration data to be written.
    """
    cmd = CMD["WRCGFA"]
    write_buffer = [0 for _ in range(6 * (total_ic))]
    write_count = 0

    for current_ic in range(total_ic):
        if not config.BMS_IC[current_ic].isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for data in range(6):
            write_buffer[write_count] = config.BMS_IC[c_ic].config.tx_data[data]
            write_count += 1
    write_68(total_ic, cmd, write_buffer)


def LTC681x_wrcfgb(total_ic: int):
    """
    Write the LTC681x CFGRB.

    :param total_ic: The number of ICs being written to.
    :param ic: A list of CellASIC objects that contain the configuration data to be written.
    """
    cmd = CMD["WRCGFB"]
    write_buffer = [0] * 256
    write_count = 0

    for current_ic in range(total_ic):
        if not config.BMS_IC[current_ic].isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for data in range(6):
            write_buffer[write_count] = config.BMS_IC[c_ic].configb.tx_data[data]
            write_count += 1

    write_68(total_ic, cmd, write_buffer)


def LTC681x_rdcfg(total_ic: int) -> int:
    """
    Read the LTC681x CFGA.

    :param total_ic: Number of ICs in the system.
    :param ic: A list of CellASIC objects where the function stores the read configuration data.
    :return: PEC error status.
    """
    cmd = CMD["RDCFGA"]
    pec_error = 0

    read_buffer, pec_error = read_68(total_ic, cmd)

    for current_ic in range(total_ic):
        if not config.BMS_IC[current_ic].isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for byte in range(8):
            config.BMS_IC[c_ic].config.rx_data[byte] = read_buffer[
                byte + (8 * current_ic)
            ]

        calc_pec = pec15_calc(6, read_buffer[8 * current_ic :])
        data_pec = (
            read_buffer[6 + (8 * current_ic)],
            read_buffer[7 + (8 * current_ic)],
        )
        if calc_pec != data_pec:
            config.BMS_IC[c_ic].config.rx_pec_match = 1
        else:
            config.BMS_IC[c_ic].config.rx_pec_match = 0

    LTC681x_check_pec(total_ic, CFGR)

    return pec_error


def LTC681x_rdcfgb(total_ic: int) -> int:
    """
    Read the LTC681x CFGB.

    :param total_ic: Number of ICs in the system.
    :param ic: A list of CellASIC objects where the function stores the read configuration data.
    :return: PEC error status.
    """
    cmd = CMD["RDCFGB"]
    read_buffer = [0] * 256
    pec_error = 0

    read_buffer, pec_error = read_68(total_ic, cmd)

    for current_ic in range(total_ic):
        if not config.BMS_IC[current_ic].isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for byte in range(8):
            config.BMS_IC[c_ic].configb.rx_data[byte] = read_buffer[
                byte + (8 * current_ic)
            ]

        calc_pec = pec15_calc(6, read_buffer[8 * current_ic :])
        data_pec = (
            read_buffer[6 + (8 * current_ic)],
            read_buffer[7 + (8 * current_ic)],
        )
        if calc_pec != data_pec:
            config.BMS_IC[c_ic].configb.rx_pec_match = 1
        else:
            config.BMS_IC[c_ic].configb.rx_pec_match = 0

    LTC681x_check_pec(total_ic, CFGRB)

    return pec_error


def LTC681x_check_pec(total_ic: int, reg: int):
    """
    Helper function that increments PEC counters.

    :param total_ic: Number of ICs in the system.
    :param reg: Type of Register.
    :param ic: A list of CellASIC objects that store the data.
    """
    if reg == CFGR:
        for current_ic in range(total_ic):
            config.BMS_IC[current_ic].crc_count.pec_count += config.BMS_IC[
                current_ic
            ].config.rx_pec_match
            config.BMS_IC[current_ic].crc_count.cfgr_pec += config.BMS_IC[
                current_ic
            ].config.rx_pec_match
    elif reg == CFGRB:
        for current_ic in range(total_ic):
            config.BMS_IC[current_ic].crc_count.pec_count += config.BMS_IC[
                current_ic
            ].configb.rx_pec_match
            config.BMS_IC[current_ic].crc_count.cfgr_pec += config.BMS_IC[
                current_ic
            ].configb.rx_pec_match
    elif reg == CELL:
        for current_ic in range(total_ic):
            for i in range(config.BMS_IC[0].ic_reg.num_cv_reg):
                config.BMS_IC[current_ic].crc_count.pec_count += config.BMS_IC[
                    current_ic
                ].cells.pec_match[i]
                config.BMS_IC[current_ic].crc_count.cell_pec[i] += config.BMS_IC[
                    current_ic
                ].cells.pec_match[i]
    elif reg == AUX:
        for current_ic in range(total_ic):
            for i in range(config.BMS_IC[0].ic_reg.num_gpio_reg):
                config.BMS_IC[current_ic].crc_count.pec_count += config.BMS_IC[
                    current_ic
                ].aux.pec_match[i]
                config.BMS_IC[current_ic].crc_count.aux_pec[i] += config.BMS_IC[
                    current_ic
                ].aux.pec_match[i]
    elif reg == STAT:
        for current_ic in range(total_ic):
            for i in range(config.BMS_IC[0].ic_reg.num_stat_reg - 1):
                config.BMS_IC[current_ic].crc_count.pec_count += config.BMS_IC[
                    current_ic
                ].stat.pec_match[i]
                config.BMS_IC[current_ic].crc_count.stat_pec[i] += config.BMS_IC[
                    current_ic
                ].stat.pec_match[i]


def LTC681x_adcv(MD: int, DCP: int, CH: int):
    """
    Starts ADC conversion for cell voltage.

    :param MD: ADC Mode.
    :param DCP: Discharge Permit.
    :param CH: Cell Channels to be measured.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits + 0x02
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits + 0x60 + (DCP << 4) + CH
    cmdbits = int2bin(cmd[0]) + int2bin(cmd[1])

    cmd_68(cmdbits[5:])


def LTC681x_adax(MD: int, CHG: int):
    """
    Start ADC Conversion for GPIO and Vref2.

    :param MD: ADC Mode.
    :param CHG: GPIO Channels to be measured.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits + 0x04
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits + 0x60 + CHG
    cmdbits = int2bin(cmd[0]) + int2bin(cmd[1])

    cmd_68(cmdbits[5:])


def LTC681x_adstat(MD: int, CHST: int):
    """
    Start ADC Conversion for Status.

    :param MD: ADC Mode.
    :param CHST: Stat Channels to be measured.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits + 0x04
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits + 0x68 + CHST
    cmdbits = int2bin(cmd[0]) + int2bin(cmd[1])

    cmd_68(cmdbits[5:])


def LTC681x_adcvsc(MD: int, DCP: int):
    """
    Starts cell voltage and SOC conversion.

    :param MD: ADC Mode.
    :param DCP: Discharge Permit.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits | 0x04
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits | 0x60 | (DCP << 4) | 0x07
    cmdbits = int2bin(cmd[0]) + int2bin(cmd[1])

    cmd_68(cmdbits[5:])


def LTC681x_adcvax(MD: int, DCP: int):
    """
    Starts cell voltage and GPIO 1&2 conversion.

    :param MD: ADC Mode.
    :param DCP: Discharge Permit.
    """
    cmd = [0, 0]
    md_bits = (MD & 0x02) >> 1
    cmd[0] = md_bits | 0x04
    md_bits = (MD & 0x01) << 7
    cmd[1] = md_bits | ((DCP & 0x01) << 4) + 0x6F
    cmdbits = int2bin(cmd[0]) + int2bin(cmd[1])

    cmd_68(cmdbits[5:])


def LTC681x_rdcv(reg: int, total_ic: int) -> int:
    """
    Reads and parses the LTC681x cell voltage registers.
    The function is used to read the parsed Cell voltages codes of the LTC681x.
    This function will send the requested read commands, parse the data,
    and store the cell voltages in c_codes variable.

    :param reg: Controls which cell voltage register is read back.
    :param total_ic: The number of ICs in the system.
    :param ic: Array of the parsed cell codes.
    :return: PEC error count.
    """
    pec_error = 0
    c_ic = 0

    if reg == 0:
        for cell_reg in range(1, config.BMS_IC[0].ic_reg.num_cv_reg + 1):
            cell_data = LTC681x_rdcv_reg(cell_reg, total_ic)
            for current_ic in range(total_ic):
                if not config.BMS_IC[current_ic].isospi_reverse:
                    c_ic = current_ic
                else:
                    c_ic = total_ic - current_ic - 1

                pec_error += parse_cells(
                    current_ic,
                    cell_reg,
                    cell_data,
                    config.BMS_IC[c_ic].cells.c_codes,
                    config.BMS_IC[c_ic].cells.pec_match,
                )
    else:
        cell_data = LTC681x_rdcv_reg(reg, total_ic)
        for current_ic in range(total_ic):
            if not config.BMS_IC[current_ic].isospi_reverse:
                c_ic = current_ic
            else:
                c_ic = total_ic - current_ic - 1

            pec_error += parse_cells(
                current_ic,
                reg,
                cell_data[8 * c_ic :],
                config.BMS_IC[c_ic].cells.c_codes,
                config.BMS_IC[c_ic].cells.pec_match,
            )

    LTC681x_check_pec(total_ic, CELL)

    return pec_error


def LTC681x_rdaux(reg: int, total_ic: int) -> int:
    """
    The function is used to read the parsed GPIO codes of the LTC681x.
    This function will send the requested read commands, parse the data,
    and store the gpio voltages in a_codes variable.

    :param reg: Determines which GPIO voltage register is read back.
    :param total_ic: The number of ICs in the system.
    :param ic: A two dimensional array of the gpio voltage codes.
    :return: PEC error count.
    """
    pec_error = 0
    c_ic = 0

    if reg == 0:
        for gpio_reg in range(1, config.BMS_IC[0].ic_reg.num_gpio_reg + 1):
            data = LTC681x_rdaux_reg(gpio_reg, total_ic)
            for current_ic in range(total_ic):
                if not config.BMS_IC[current_ic].isospi_reverse:
                    c_ic = current_ic
                else:
                    c_ic = total_ic - current_ic - 1

                pec_error += parse_cells(
                    current_ic,
                    gpio_reg,
                    data,
                    config.BMS_IC[c_ic].aux.a_codes,
                    config.BMS_IC[c_ic].aux.pec_match,
                )
    else:
        data = LTC681x_rdaux_reg(reg, total_ic)
        for current_ic in range(total_ic):
            if not config.BMS_IC[current_ic].isospi_reverse:
                c_ic = current_ic
            else:
                c_ic = total_ic - current_ic - 1

            pec_error += parse_cells(
                current_ic,
                reg,
                data,
                config.BMS_IC[c_ic].aux.a_codes,
                config.BMS_IC[c_ic].aux.pec_match,
            )

    LTC681x_check_pec(total_ic, AUX)

    return pec_error


def LTC681x_rdaux_reg(reg: int, total_ic: int):
    """
    The function reads a single GPIO voltage register and stores the read data
    in the *data point as a byte array. This function is rarely used outside of
    the LTC681x_rdaux() command.

    :param reg: Determines which GPIO voltage register is read back.
    :param total_ic: The number of ICs in the system.
    """
    REG_LEN = 8  # Number of bytes in the register + 2 bytes for the PEC

    if reg == 1:  # Read back auxiliary group A
        cmd = CMD["RDAUXA"]
    elif reg == 2:  # Read back auxiliary group B
        cmd = CMD["RDAUXB"]
    elif reg == 3:  # Read back auxiliary group C
        cmd = CMD["RDAUXC"]
    elif reg == 4:  # Read back auxiliary group D
        cmd = CMD["RDAUXD"]
    else:  # Read back auxiliary group A
        cmd = CMD["RDAUXA"]

    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [
        bin2int(cmdbit[:8]),
        bin2int(cmdbit[8:]),
        bin2int(pec[:8]),
        bin2int(pec[8:]),
    ]
    data = spi_write_read(word, REG_LEN * total_ic)
    return data


def LTC681x_rdcv_reg(reg: int, total_ic: int):
    """
    Writes the command and reads the raw cell voltage register data.

    :param reg: Determines which cell voltage register is read back.
    :param total_ic: The number of ICs in the system.
    """
    REG_LEN = 8  # Number of bytes in each ICs register + 2 bytes for the PEC

    if reg == 1:  # 1: RDCVA
        cmd = CMD["RDCVA"]
    elif reg == 2:  # 2: RDCVB
        cmd = CMD["RDCVB"]
    elif reg == 3:  # 3: RDCVC
        cmd = CMD["RDCVC"]
    elif reg == 4:  # 4: RDCVD
        cmd = CMD["RDCVD"]
    elif reg == 5:  # 5: RDCVE
        cmd = CMD["RDCVE"]
    elif reg == 6:  # 6: RDCVF
        cmd = CMD["RDCVF"]
    else:
        cmd = CMD["RDCVA"]

    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [
        bin2int(cmdbit[:8]),
        bin2int(cmdbit[8:]),
        bin2int(pec[:8]),
        bin2int(pec[8:]),
    ]
    data = spi_write_read(word, REG_LEN * total_ic)
    return data


def parse_cells(
    current_ic: int,  # Current IC
    cell_reg: int,  # Type of register
    cell_data: List[int],  # Unparsed data
    cell_codes: List[int],  # Parsed data
    ic_pec: List[int],  # PEC error
) -> int:
    """
    Helper function that parses voltage measurement registers.

    :param current_ic: Current IC
    :param cell_reg: Type of register
    :param cell_data: Unparsed data
    :param cell_codes: Parsed data
    :param ic_pec: PEC error
    :return: PEC error flag (0 if no error, 1 if error)
    """
    BYT_IN_REG = 6
    CELL_IN_REG = 3
    pec_error = 0
    data_counter = current_ic * NUM_RX_BYT  # data counter

    for current_cell in range(CELL_IN_REG):
        # This loop parses the read back data into the register codes
        # Each code is received as two bytes and is combined to create the parsed code
        parsed_cell = cell_data[data_counter] + (cell_data[data_counter + 1] << 8)
        cell_codes[current_cell + ((cell_reg - 1) * CELL_IN_REG)] = parsed_cell

        data_counter += 2  # Increment by two for each parsed code

    # The received PEC for the current_ic is transmitted as the 7th and 8th bytes
    received_pec = (cell_data[data_counter], cell_data[data_counter + 1])
    data_pec = pec15_calc(
        BYT_IN_REG, cell_data[current_ic * NUM_RX_BYT : (current_ic + 1) * NUM_RX_BYT]
    )

    if received_pec != data_pec:
        pec_error = 1  # Set pec_error to 1 if any PEC errors
        ic_pec[cell_reg - 1] = 1
    else:
        ic_pec[cell_reg - 1] = 0

    return pec_error


def LTC681x_rdstat(
    reg: int,  # Determines which Stat register is read back.
    total_ic: int,  # The number of ICs in the system.
) -> int:
    """
    Reads and parses the LTC681x stat registers.

    The function is used to read the parsed Stat codes of the LTC681x.
    This function will send the requested read commands, parse the data
    and store the gpio voltages in the stat_codes variable.

    :param reg: Determines which Stat register is read back.
    :param total_ic: The number of ICs in the system.
    :param ic: A two dimensional array of the stat codes.
    :return: PEC error flag (0 if no error, -1 if error)
    """
    BYT_IN_REG = 6
    STAT_IN_REG = 3
    data = [0] * (12 * total_ic)
    data_counter = 0
    pec_error = 0
    c_ic = 0

    if reg == 0:
        for stat_reg in range(
            1, 3
        ):  # Executes once for each of the LTC681x stat voltage registers
            data_counter = 0
            data = LTC681x_rdstat_reg(stat_reg, total_ic)
            # Reads the raw status register data into the data[] array

            for current_ic in range(total_ic):
                # Executes for every LTC681x in the daisy chain
                if not config.BMS_IC[0].isospi_reverse:
                    c_ic = current_ic
                else:
                    c_ic = total_ic - current_ic - 1

                if stat_reg == 1:
                    for current_stat in range(STAT_IN_REG):
                        # This loop parses the read back data into Status registers
                        parsed_stat = data[data_counter] + (data[data_counter + 1] << 8)
                        config.BMS_IC[c_ic].stat.stat_codes[current_stat] = parsed_stat
                        data_counter += 2
                elif stat_reg == 2:
                    parsed_stat = data[data_counter] + (data[data_counter + 1] << 8)
                    data_counter += 2
                    config.BMS_IC[c_ic].stat.stat_codes[3] = parsed_stat
                    config.BMS_IC[c_ic].stat.flags[0] = data[data_counter]
                    data_counter += 1
                    config.BMS_IC[c_ic].stat.flags[1] = data[data_counter]
                    data_counter += 1
                    config.BMS_IC[c_ic].stat.flags[2] = data[data_counter]
                    data_counter += 1
                    config.BMS_IC[c_ic].stat.mux_fail[0] = (
                        data[data_counter] & 0x02
                    ) >> 1
                    config.BMS_IC[c_ic].stat.thsd[0] = data[data_counter] & 0x01
                    data_counter += 1

                received_pec = (data[data_counter], data[data_counter + 1])
                data_pec = pec15_calc(
                    BYT_IN_REG,
                    data[current_ic * NUM_RX_BYT : (current_ic + 1) * NUM_RX_BYT],
                )

                if received_pec != data_pec:
                    pec_error = (
                        -1
                    )  # The pec_error variable is simply set negative if any PEC errors are detected
                    config.BMS_IC[c_ic].stat.pec_match[stat_reg - 1] = 1
                else:
                    config.BMS_IC[c_ic].stat.pec_match[stat_reg - 1] = 0

                data_counter += 2  # Because the transmitted PEC code is 2 bytes long, increment the data_counter by 2 bytes
    else:
        data = LTC681x_rdstat_reg(reg, total_ic)
        for current_ic in range(total_ic):
            # Executes for every LTC681x in the daisy chain
            if not config.BMS_IC[0].isospi_reverse:
                c_ic = current_ic
            else:
                c_ic = total_ic - current_ic - 1

            if reg == 1:
                for current_stat in range(STAT_IN_REG):
                    # This loop parses the read back data into Status voltages
                    parsed_stat = data[data_counter] + (data[data_counter + 1] << 8)
                    config.BMS_IC[c_ic].stat.stat_codes[current_stat] = parsed_stat
                    data_counter += 2
            elif reg == 2:
                parsed_stat = data[data_counter] + (data[data_counter + 1] << 8)
                data_counter += 2
                config.BMS_IC[c_ic].stat.stat_codes[3] = parsed_stat
                config.BMS_IC[c_ic].stat.flags[0] = data[data_counter]
                data_counter += 1
                config.BMS_IC[c_ic].stat.flags[1] = data[data_counter]
                data_counter += 1
                config.BMS_IC[c_ic].stat.flags[2] = data[data_counter]
                data_counter += 1
                config.BMS_IC[c_ic].stat.mux_fail[0] = (data[data_counter] & 0x02) >> 1
                config.BMS_IC[c_ic].stat.thsd[0] = data[data_counter] & 0x01
                data_counter += 1

            received_pec = (data[data_counter], data[data_counter + 1])
            data_pec = pec15_calc(
                BYT_IN_REG,
                data[current_ic * NUM_RX_BYT : (current_ic + 1) * NUM_RX_BYT],
            )
            if received_pec != data_pec:
                pec_error = -1
                # The pec_error variable is simply set negative if any PEC errors are detected
                config.BMS_IC[c_ic].stat.pec_match[reg - 1] = 1
            else:
                config.BMS_IC[c_ic].stat.pec_match[reg - 1] = 0

            data_counter += 2

    LTC681x_check_pec(total_ic, STAT)

    return pec_error


def LTC681x_rdstat_reg(
    reg: int,  # Determines which stat register is read back
    total_ic: int,  # The number of ICs in the system
) -> None:
    """
    The function reads a single stat register and stores the read data
    in the *data point as a byte array. This function is rarely used outside of
    the LTC681x_rdstat() command.

    :param reg: Determines which stat register is read back
    :param total_ic: The number of ICs in the system
    :param data: Array of the unparsed stat codes
    """
    REG_LEN = 8  # number of bytes in the register + 2 bytes for the PEC

    if reg == 1:  # Read back status group A
        cmd = CMD["RDSTATA"]
    elif reg == 2:  # Read back status group B
        cmd = CMD["RDSTATB"]
    else:  # Read back status group A
        cmd = CMD["RDSTATA"]

    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [
        bin2int(cmdbit[:8]),
        bin2int(cmdbit[8:]),
        bin2int(pec[:8]),
        bin2int(pec[8:]),
    ]
    data = spi_write_read(word, REG_LEN * total_ic)
    return data


def LTC681x_init_cfg(
    total_ic: int,  # Number of ICs in the system
) -> None:
    """
    Helper function to initialize CFG variables

    :param total_ic: Number of ICs in the system
    :param ic: A list of dictionaries that stores the data
    """
    for current_ic in range(total_ic):
        for j in range(6):
            config.BMS_IC[current_ic].config.tx_data[j] = 0


def LTC681x_set_cfgr(
    nIC: int,  # Current IC
    refon: bool,  # The REFON bit
    adcopt: bool,  # The ADCOPT bit
    gpio: list,  # The GPIO bits
    dcc: list,  # The DCC bits
    dcto: list,  # The Dcto bits
    uv: int,  # The UV value
    ov: int,  # The OV value
) -> None:
    """
    Helper function to set CFGR variable

    :param nIC: Current IC
    :param ic: A list of dictionaries that stores the data
    :param refon: The REFON bit
    :param adcopt: The ADCOPT bit
    :param gpio: The GPIO bits
    :param dcc: The DCC bits
    :param dcto: The Dcto bits
    :param uv: The UV value
    :param ov: The OV value
    """
    LTC681x_set_cfgr_refon(nIC, refon)
    LTC681x_set_cfgr_adcopt(nIC, adcopt)
    LTC681x_set_cfgr_gpio(nIC, gpio)
    LTC681x_set_cfgr_dis(nIC, dcc)
    LTC681x_set_cfgr_dcto(nIC, dcto)
    LTC681x_set_cfgr_uv(nIC, uv)
    LTC681x_set_cfgr_ov(nIC, ov)


def LTC681x_set_cfgr_refon(nIC, refon):
    """
    Helper function to set the REFON bit
    """
    if refon:
        config.BMS_IC[nIC].config.tx_data[0] |= 0x04
    else:
        config.BMS_IC[nIC].config.tx_data[0] &= 0xFB


def LTC681x_set_cfgr_adcopt(nIC, adcopt):
    """
    Helper function to set the ADCOPT bit
    """
    if adcopt:
        config.BMS_IC[nIC].config.tx_data[0] |= 0x01
    else:
        config.BMS_IC[nIC].config.tx_data[0] &= 0xFE


def LTC681x_set_cfgr_gpio(nIC, gpio):
    """
    Helper function to set GPIO bits
    """
    for i in range(5):
        if gpio[i]:
            config.BMS_IC[nIC].config.tx_data[0] |= 0x01 << (i + 3)
        else:
            config.BMS_IC[nIC].config.tx_data[0] &= ~(0x01 << (i + 3))


def LTC681x_set_cfgr_dis(nIC, dcc):
    """
    Helper function to control discharge
    """
    for i in range(8):
        if dcc[i]:
            config.BMS_IC[nIC].config.tx_data[4] |= 0x01 << i
        else:
            config.BMS_IC[nIC].config.tx_data[4] &= ~(0x01 << i)
    for i in range(4):
        if dcc[i + 8]:
            config.BMS_IC[nIC].config.tx_data[5] |= 0x01 << i
        else:
            config.BMS_IC[nIC].config.tx_data[5] &= ~(0x01 << i)


def LTC681x_set_cfgr_dcto(nIC, dcto):
    """
    Helper function to control discharge time value
    """
    for i in range(4):
        if dcto[i]:
            config.BMS_IC[nIC].config.tx_data[5] |= 0x01 << (i + 4)
        else:
            config.BMS_IC[nIC].config.tx_data[5] &= ~(0x01 << (i + 4))


def LTC681x_set_cfgr_uv(nIC, uv):
    """
    Helper function to set UV value in CFG register
    """
    tmp = (uv // 16) - 1
    config.BMS_IC[nIC].config.tx_data[1] = 0x00FF & tmp
    config.BMS_IC[nIC].config.tx_data[2] &= 0xF0
    config.BMS_IC[nIC].config.tx_data[2] |= (0x0F00 & tmp) >> 8


def LTC681x_set_cfgr_ov(nIC, ov):
    """
    Helper function to set OV value in CFG register
    """
    tmp = ov // 16
    config.BMS_IC[nIC].config.tx_data[3] = 0x00FF & (tmp >> 4)
    config.BMS_IC[nIC].config.tx_data[2] &= 0x0F
    config.BMS_IC[nIC].config.tx_data[2] |= (0x000F & tmp) << 4


def LTC681x_reset_crc_count(total_ic: int):
    """
    Helper Function to reset PEC counters.

    Parameters:
    - total_ic (int): Number of ICs in the system.
    - ic (List[CellASIC]): A two-dimensional list that stores the data.

    Returns:
    None
    """
    for current_ic in range(total_ic):
        config.BMS_IC[current_ic].crc_count.pec_count = 0
        config.BMS_IC[current_ic].crc_count.cfgr_pec = 0
        for i in range(6):
            config.BMS_IC[current_ic].crc_count.cell_pec[i] = 0

        for i in range(4):
            config.BMS_IC[current_ic].crc_count.aux_pec[i] = 0

        for i in range(2):
            config.BMS_IC[current_ic].crc_count.stat_pec[i] = 0


def LTC681x_pollAdc() -> int:
    """
    This function will block operation until the ADC has finished its conversion.

    Returns:
        int: The counter value.
    """
    counter = 0
    cmd = CMD["PLADC"]
    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [
        bin2int(cmdbit[:8]),
        bin2int(cmdbit[8:]),
        bin2int(pec[:8]),
        bin2int(pec[8:]),
    ]
    data = spi_write_read(word, 20000)
    while counter < 20000 and (not (data[counter] > 0)):
        counter += 1
    return counter * 10


def LTC681x_clear_discharge(total_ic: int) -> None:
    """
    Clears all of the DCC bits in the configuration registers.

    Args:
        total_ic (int): Number of ICs in the daisy chain.
        ic (List[cell_asic]): A list of cell_asic objects that will store the data.
    """
    for i in range(total_ic):
        config.BMS_IC[i].config.tx_data[4] = 0
        config.BMS_IC[i].config.tx_data[5] &= 0xF0
        config.BMS_IC[i].configb.tx_data[0] &= 0x0F
        config.BMS_IC[i].configb.tx_data[1] &= 0xF0


def LTC681x_wrcomm(total_ic: int):
    """
    Writes the comm register.

    Args:
        total_ic (int): The number of ICs being written to.
    """
    cmd = CMD["WRCOMM"]
    write_buffer = []
    write_count = 0

    for current_ic in range(total_ic):
        if not config.BMS_IC[0].isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for data in range(6):
            write_buffer.append(config.BMS_IC[c_ic].com.tx_data[data])
            write_count += 1

    write_68(total_ic, cmd, write_buffer)


def LTC681x_rdcomm(total_ic: int) -> int:
    """
    Reads COMM registers of a LTC681x daisy chain.

    Args:
        total_ic (int): Number of ICs in the system.
    Returns:
        int: PEC error status.
    """
    cmd = CMD["RDCOMM"]
    read_buffer = [0] * 256
    pec_error = 0

    read_buffer, pec_error = read_68(total_ic, cmd)

    for current_ic in range(total_ic):
        if not config.BMS_IC[0].isospi_reverse:
            c_ic = current_ic
        else:
            c_ic = total_ic - current_ic - 1

        for byte in range(8):
            config.BMS_IC[c_ic].com.rx_data[byte] = read_buffer[byte + (8 * current_ic)]

        calc_pec = pec15_calc(6, read_buffer[8 * current_ic :])
        data_pec = (
            read_buffer[6 + (8 * current_ic)],
            read_buffer[7 + (8 * current_ic)],
        )

        if calc_pec != data_pec:
            config.BMS_IC[c_ic].com.rx_pec_match = 1
        else:
            config.BMS_IC[c_ic].com.rx_pec_match = 0

    return pec_error


def LTC681x_stcomm(tx_len: int):
    """
    Shifts data in COMM register out over LTC681x SPI/I2C port.

    Args:
        tx_len (int): Length of data to be transmitted.
    """
    cmd = CMD["STCOMM"]
    cmdbit = [0, 0, 0, 0, 0] + cmd[:3] + cmd[3:]
    pec = calcul_PEC(cmdbit)
    word = [
        bin2int(cmdbit[:8]),
        bin2int(cmdbit[8:]),
        bin2int(pec[:8]),
        bin2int(pec[8:]),
    ]
    spi.xfer3(word + [0] * tx_len * 3)
