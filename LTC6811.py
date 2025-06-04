"""
Librairie de communication avec le processeur LTC6811 du BMS.
"""
### Fichier principal permettant la communication avec le processeur LTC6811


from LTC681x import *
import config


def bin2hex(bin):
    n = bin2int(bin)
    return hex(n)


def hex2bin(hex):
    binst = bin(int(hex, 16))
    nb0 = 8 - len(binst) + 2
    res = [0] * nb0
    for x in binst[2:]:
        res.append(int(x))
    return res


##Paramètres
TOTAL_IC = 1  # nombre de BMS en daisy chain
NB_CELLS = 13  # nombre de cellules par BMS

ENABLED = 1
DISABLED = 0
DATALOG_ENABLED = 1
DATALOG_DISABLED = 0

###################################################################
# Setup Variables
# The following variables can be modified to configure the software.
###################################################################

# ADC Command Configurations. See LTC681x.h for options.
ADC_OPT = ADC_OPT_DISABLED  # ADC Mode option bit
ADC_CONVERSION_MODE = MD_7KHZ_3KHZ  # ADC Mode
ADC_DCP = DCP_ENABLED  # Discharge Permitted
CELL_CH_TO_CONVERT = CELL_CH_ALL  # Channel Selection for ADC conversion
AUX_CH_TO_CONVERT = AUX_CH_ALL  # Channel Selection for ADC conversion
STAT_CH_TO_CONVERT = STAT_CH_ALL  # Channel Selection for ADC conversion
SEL_ALL_REG = REG_ALL  # Register Selection
SEL_REG_A = REG_1  # Register Selection
SEL_REG_B = REG_2  # Register Selection

MEASUREMENT_LOOP_TIME = 500  # Loop Time in milliseconds (ms)

# Under Voltage and Over Voltage Thresholds
OV_THRESHOLD = 41000  # Over voltage threshold ADC Code. LSB = 0.0001 ---(4.1V)
UV_THRESHOLD = 30000  # Under voltage threshold ADC Code. LSB = 0.0001 ---(3V)

# Loop Measurement Setup. These Variables are ENABLED or DISABLED. Remember ALL CAPS
WRITE_CONFIG = DISABLED  # This is to ENABLE or DISABLE writing into to configuration registers in a continuous loop
READ_CONFIG = DISABLED  # This is to ENABLE or DISABLE reading the configuration registers in a continuous loop
MEASURE_CELL = ENABLED  # This is to ENABLE or DISABLE measuring the cell voltages in a continuous loop
MEASURE_AUX = DISABLED  # This is to ENABLE or DISABLE reading the auxiliary registers in a continuous loop
MEASURE_STAT = DISABLED  # This is to ENABLE or DISABLE reading the status registers in a continuous loop
PRINT_PEC = DISABLED  # This is to ENABLE or DISABLE printing the PEC Error Count in a continuous loop
#####################################
# END SETUP
#####################################

##Additional specific functions


def LTC6811_init_reg_limits(
    total_ic: int,  # The number of ICs in the system
) -> None:
    """
    Initialize the Register limits.

    Parameters:
        total_ic (int): The number of ICs in the system.
        ic (List[cell_asic]): A two dimensional array where data will be written.
    """
    for cic in range(total_ic):
        config.BMS_IC[cic].ic_reg.cell_channels = 12
        config.BMS_IC[cic].ic_reg.stat_channels = 4
        config.BMS_IC[cic].ic_reg.aux_channels = 6
        config.BMS_IC[cic].ic_reg.num_cv_reg = 4
        config.BMS_IC[cic].ic_reg.num_gpio_reg = 2
        config.BMS_IC[cic].ic_reg.num_stat_reg = 3


def LTC6811_set_discharge(Cell: int, total_ic: int) -> None:
    """
    Helper function to set discharge bit in CFG register.

    Args:
        Cell (int): The cell to be discharged.
        total_ic (int): Number of ICs in the system.
        ic (List[CellASIC]): A list of CellASIC objects storing the data.
    """
    for i in range(total_ic):
        if 0 < Cell < 9:
            config.BMS_IC[i].config.tx_data[4] |= 1 << (Cell - 1)
        elif 9 <= Cell < 13:
            config.BMS_IC[i].config.tx_data[5] |= 1 << (Cell - 9)
        else:
            break


def init():
    ########################################################
    # Global Battery Variables received from 681x commands.
    # These variables store the results from the LTC6811
    # register reads and the array lengths must be based
    # on the number of ICs on the stack
    ########################################################
    config.init(TOTAL_IC)

    ####################################################
    # Set the configuration bits.
    # Refer to the Configuration Register Group from data sheet.
    ####################################################
    global REFON
    REFON = True  # Reference Powered Up Bit
    global ADCOPT
    ADCOPT = False  # ADC Mode option bit
    global GPIOBITS_A
    GPIOBITS_A = [False, False, False, True, True]  # GPIO Pin Control // Gpio 1,2,3,4,5
    global UV
    UV = UV_THRESHOLD  # Under-voltage Comparison Voltage
    global OV
    OV = OV_THRESHOLD  # Over-voltage Comparison Voltage
    global DCCBITS_A
    DCCBITS_A = [False] * 12  # Discharge cell switch // Dcc 1,2,3,4,5,6,7,8,9,10,11,12
    global DCTOBITS
    DCTOBITS = [
        False,
        False,
        False,
        False,
    ]  # Discharge time value // Dcto 0,1,2,3 // Programmed for 4 min
    # Ensure that Dcto bits are set according to the required discharge time. Refer to the data sheet
    global MAX_SPEED_HZ
    MAX_SPEED_HZ = 1000000  # Fréquence max et par défaut du bus SPI

    # We only have SPI bus 0 available to us on the Pi
    bus = 0

    # Device is the chip select pin. Set to 0 or 1, depending on the connections
    device = 0

    # Open a connection to a specific bus and device (chip select pin)
    spi.open(bus, device)

    # Set SPI speed and mode
    spi.max_speed_hz = MAX_SPEED_HZ
    spi.mode = 3

    ##Initialisation

    LTC681x_init_cfg(TOTAL_IC)
    for current_ic in range(TOTAL_IC):
        LTC681x_set_cfgr(
            current_ic, REFON, ADCOPT, GPIOBITS_A, DCCBITS_A, DCTOBITS, UV, OV
        )
    LTC681x_reset_crc_count(TOTAL_IC)
    LTC6811_init_reg_limits(TOTAL_IC)


### Fonctions utiles :


def write_read_cfg(enable_read=True):
    """Write and Read Configuration Register"""
    wakeup_sleep(TOTAL_IC)
    LTC681x_wrcfg(TOTAL_IC)  # Write into Configuration Register
    if enable_read:
        print_wrconfig()
    wakeup_idle(TOTAL_IC)

    error = LTC681x_rdcfg(TOTAL_IC)  # Read Configuration Register
    check_error(error)
    if enable_read:
        print_rxconfig()


def read_cfg(enable_read=True):
    """Read Configuration Register"""
    wakeup_sleep(TOTAL_IC)
    error = LTC681x_rdcfg(TOTAL_IC)
    check_error(error)
    if enable_read:
        print_rxconfig()


def start_cell_mes(enable_read=True):
    """Start Cell ADC Measurement"""
    wakeup_sleep(TOTAL_IC)
    LTC681x_adcv(ADC_CONVERSION_MODE, ADC_DCP, CELL_CH_TO_CONVERT)
    conv_time = LTC681x_pollAdc()
    if enable_read:
        print_conv_time(conv_time)


def read_cell_v(enable_read=True):
    """Read Cell Voltage Registers"""
    wakeup_sleep(TOTAL_IC)
    error = LTC681x_rdcv(SEL_ALL_REG, TOTAL_IC)
    # Set to read back all cell voltage registers
    check_error(error)
    if enable_read:
        print_cells(DATALOG_DISABLED)


def start_GPIO_mes(enable_read=True):
    """Start GPIO ADC Measurement"""
    wakeup_sleep(TOTAL_IC)

    LTC681x_adax(ADC_CONVERSION_MODE, AUX_CH_TO_CONVERT)
    conv_time = LTC681x_pollAdc()
    if enable_read:
        print_conv_time(conv_time)


def read_GPIO_v(enable_read=True):
    """Read Auxiliary Voltage registers"""
    wakeup_sleep(TOTAL_IC)
    error = LTC681x_rdaux(SEL_ALL_REG, TOTAL_IC)  # Set to read back all aux registers
    check_error(error)
    if enable_read:
        print_aux(DATALOG_DISABLED)


def enable_DSC(pin: int, enable_read=True):
    """Enable a discharge transistor
    cell : the cell to discharge"""
    wakeup_sleep(TOTAL_IC)
    LTC6811_set_discharge(pin, TOTAL_IC)
    LTC681x_wrcfg(TOTAL_IC)
    if enable_read:
        print_wrconfig()
    wakeup_idle(TOTAL_IC)
    error = LTC681x_rdcfg(TOTAL_IC)
    check_error(error)
    if enable_read:
        print_rxconfig()


def clear_all_DSC(enable_read=True):
    """Clear all discharge transistors"""
    wakeup_sleep(TOTAL_IC)
    LTC681x_clear_discharge(TOTAL_IC)
    LTC681x_wrcfg(TOTAL_IC)
    if enable_read:
        print_wrconfig()
    wakeup_idle(TOTAL_IC)
    error = LTC681x_rdcfg(TOTAL_IC)
    check_error(error)
    if enable_read:
        print_rxconfig()


def count_pec():
    print_pec_error_count()


def reset_pec_counter(enable_read=True):
    LTC681x_reset_crc_count(TOTAL_IC)
    if enable_read:
        print_pec_error_count()


def write_byte_i2c_communication(data: List[int], enable_read=True):
    """
    Writes a byte via I2C communication on the GPIO Ports (using I2C eeprom 24LC025).
    Ensure to set the GPIO bits to 1 in the CFG register group.

    Args
    data : The 6 bytes array of data to send
    """
    for current_ic in range(TOTAL_IC):
        for k in range(len(data) // 2):
            config.BMS_IC[current_ic].com.tx_data[2 * k] = data[2 * k]
            config.BMS_IC[current_ic].com.tx_data[2 * k + 1] = data[2 * k + 1]

    wakeup_sleep(TOTAL_IC)
    LTC681x_wrcomm(TOTAL_IC)  # Write to comm register
    if enable_read:
        print_wrcomm()  # Print transmitted data from the comm register

    wakeup_idle(TOTAL_IC)
    LTC681x_stcomm(len(data) // 2)
    # data length=3 // initiates communication between master and the I2C slave

    wakeup_idle(TOTAL_IC)
    error = LTC681x_rdcomm(TOTAL_IC)  # Read from comm register
    check_error(error)
    if enable_read:
        print_rxcomm()  # Print received data into the comm register


def reset_mux(enable_read=True):
    """Set Mux to no output/input
    ***HOMEMADE***
    """
    START = [0, 1, 1, 0]
    STOP = [0, 0, 0, 1]
    BLANK = [0, 0, 0, 0]
    ACK = [0, 0, 0, 0]
    NACK = [1, 0, 0, 0]
    NACKSTOP = [1, 0, 0, 1]
    ADG728 = [1, 0, 0, 1, 1]  # Adress of Mux ADG728 (see datasheet)
    PINBIN = [0] * 8
    RW = [0]

    ADR = [[0, 0], [0, 1]]
    for adrbits in ADR:
        data = []
        data.append(bin2int(START + ADG728[:4]))
        data.append(bin2int(ADG728[4:] + adrbits + RW + ACK))
        data.append(bin2int(BLANK + PINBIN[:4]))
        data.append(bin2int(PINBIN[4:] + ACK))
        data.append(bin2int(STOP + BLANK))
        data.append(bin2int(BLANK + ACK))
        write_byte_i2c_communication(data, enable_read)


def select_mux_pin(pin: int, enable_read=True):
    """Select the pin that will be readed among all the 18 pin of the two mux connected to the BMS
    Args
    pin : The number of the pin that will be readed
    ***HOMEMADE***
    """
    reset_mux()
    data = []
    START = [0, 1, 1, 0]
    STOP = [0, 0, 0, 1]
    BLANK = [0, 0, 0, 0]
    ACK = [0, 0, 0, 0]
    NACK = [1, 0, 0, 0]
    NACKSTOP = [1, 0, 0, 1]
    ADG728 = [1, 0, 0, 1, 1]  # Adress of Mux ADG728 (see datasheet)
    RW = [0]  # Read Write bit is low for writing
    PINBIN = [0, 0, 0, 0, 0, 0, 0, 0]
    if 0 < pin <= 8:  # Select the first or the second mux
        ADR = [0, 0]
        PINBIN[7 - pin + 1] = 1
    elif 8 < pin <= 16:
        ADR = [0, 1]
        PINBIN[7 - (pin - 8) + 1] = 1
    else:
        print("N° de pin invalide")
        return
    data.append(bin2int(START + ADG728[:4]))
    data.append(bin2int(ADG728[4:] + ADR + RW + ACK))
    data.append(bin2int(BLANK + PINBIN[:4]))
    data.append(bin2int(PINBIN[4:] + ACK))
    data.append(bin2int(STOP + BLANK))
    data.append(bin2int(BLANK + ACK))

    write_byte_i2c_communication(data, enable_read)


def set_GPIO_PIN(enable_read=True):
    wakeup_sleep(TOTAL_IC)
    for current_ic in range(TOTAL_IC):
        LTC681x_set_cfgr(
            current_ic, REFON, ADCOPT, GPIOBITS_A, DCCBITS_A, DCTOBITS, UV, OV
        )
    wakeup_idle(TOTAL_IC)
    LTC681x_wrcfg(TOTAL_IC)
    if enable_read:
        print_wrconfig()


### Fonctions d'affichage :
def print_conv_time(conv_time: int) -> None:
    """
    Function to print the Conversion Time.

    Args:
        conv_time (int): The conversion time to be printed.
    """
    m_factor = 1000  # to print in ms

    print("Conversion completed in:", "{:.1f}".format(conv_time / m_factor), "ms\n")


def check_error(error: int) -> None:
    """
    Function to check error flag and print PEC error message.

    Args:
        error (int): The error flag to be checked.
    """
    if error == -1:
        print("A PEC error was detected in the received data")


def print_wrconfig():
    print()
    print("Written Configuration: ")
    for current_ic in range(TOTAL_IC):
        string = "CFGA IC " + str(current_ic + 1) + " : "
        string += "[" + str(config.BMS_IC[current_ic].config.tx_data[0])
        for i in range(1, 6):
            string += ", " + str(config.BMS_IC[current_ic].config.tx_data[i])
        print(string + "]")
        pec = pec15_calc(6, config.BMS_IC[current_ic].config.tx_data)
        print("Calculated PEC: ({},{})".format(pec[0], pec[1]))
    print()


def print_rxconfig():
    print()
    print("Received Configuration ")
    for current_ic in range(TOTAL_IC):
        string = "CFGA IC " + str(current_ic + 1) + " : "
        string += "[" + str(config.BMS_IC[current_ic].config.rx_data[0])
        for i in range(1, 6):
            string += ", " + str(config.BMS_IC[current_ic].config.rx_data[i])
        print(string + "]")
        print(
            "Calculated PEC: ({},{})".format(
                config.BMS_IC[current_ic].config.rx_data[6],
                config.BMS_IC[current_ic].config.rx_data[7],
            )
        )
    print()


def print_cells(datalog_en: int) -> None:
    """
    Prints cell voltage to the console.

    Args:
        datalog_en (int): Data logging enable flag.
    """
    print()
    for current_ic in range(TOTAL_IC):
        if datalog_en == 0:
            print(f" IC {current_ic + 1} : ", end="")
            print(
                f" C1: {config.BMS_IC[current_ic].cells.c_codes[0] * 0.0001:.4f}",
                end="",
            )
            for i in range(1, config.BMS_IC[0].ic_reg.cell_channels):
                print(
                    f", C{i + 1}: {config.BMS_IC[current_ic].cells.c_codes[i] * 0.0001:.4f}",
                    end="",
                )
            print()
        else:
            print(" Cells :", end="")
            print(f"{config.BMS_IC[current_ic].cells.c_codes[0] * 0.0001:.4f},", end="")
            for i in range(1, config.BMS_IC[0].ic_reg.cell_channels):
                print(
                    f"{config.BMS_IC[current_ic].cells.c_codes[i] * 0.0001:.4f},",
                    end="",
                )
    print()


def print_pec_error_count() -> None:
    """
    Prints the PEC errors detected to the console.
    """
    for current_ic in range(TOTAL_IC):
        print(
            f"\n{config.BMS_IC[current_ic].crc_count.pec_count} : PEC Errors Detected on IC {current_ic + 1}"
        )
    print("\n")


def print_wrcomm():
    """
    Prints comm register data to the serial port.
    """
    print("Written Data in COMM Register:")
    for current_ic in range(TOTAL_IC):
        print(f" IC{current_ic + 1}", end="")
        for i in range(6):
            print(f", {config.BMS_IC[current_ic].com.tx_data[i]}", end="")
        comm_pec = pec15_calc(6, config.BMS_IC[current_ic].com.tx_data)
        print(f", Calculated PEC: ({comm_pec[0]}, {comm_pec[1]})")
        print("\n")


def print_rxcomm():
    """
    Prints comm register data that was read back from the LTC6811 to the serial port.
    """
    print("Received Data in COMM register:")
    for current_ic in range(TOTAL_IC):
        print(f" IC{current_ic + 1}", end="")
        for i in range(6):
            print(f", {config.BMS_IC[current_ic].com.rx_data[i]}", end="")
        print(
            f", Received PEC: ({config.BMS_IC[current_ic].com.rx_data[6]}, {config.BMS_IC[current_ic].com.rx_data[7]})"
        )
        print("\n")


def print_aux(datalog_en: int) -> None:
    """
    Prints GPIO voltage codes and Vref2 voltage code onto the serial port.

    Args:
        datalog_en (int): Flag to enable or disable data logging.
                          If 0, prints formatted data. If non-zero, prints raw data.
    """
    for current_ic in range(TOTAL_IC):
        if datalog_en == 0:
            print(f" IC {current_ic + 1}: ", end="")

            for i in range(5):
                print(
                    f" GPIO-{i + 1}:{config.BMS_IC[current_ic].aux.a_codes[i] * 0.0001:.4f},",
                    end="",
                )

            print(f" Vref2:{config.BMS_IC[current_ic].aux.a_codes[5] * 0.0001:.4f}")
        else:
            print(f"AUX IC {current_ic + 1}: ", end="")

            for i in range(6):
                print(
                    f"{config.BMS_IC[current_ic].aux.a_codes[i] * 0.0001:.4f},", end=""
                )

        print()


if __name__ == "__main__":
    init()
