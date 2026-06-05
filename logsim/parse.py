"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""

from scanner import Symbol


class ParseSyntaxError(Exception):
    """Custom exception raised when a syntax rule is broken."""

    pass


class ParseSemanticError(Exception):
    """Custom exception raised when a semantic rule is broken."""

    pass


class Parser:
    """Parse the definition file and build the logic network.

    The parser deals with error handling. It analyses the syntactic and
    semantic correctness of the symbols it receives from the scanner, and
    then builds the logic network. If there are errors in the definition file,
    the parser detects this and tries to recover from it, giving helpful
    error messages.

    Parameters
    ----------
    names: instance of the names.Names() class.
    devices: instance of the devices.Devices() class.
    network: instance of the network.Network() class.
    monitors: instance of the monitors.Monitors() class.
    scanner: instance of the scanner.Scanner() class.

    Public methods
    --------------
    parse_network(self): Parses the circuit definition file.
    """

    def __init__(self, names, devices, network, monitors, scanner):
        """Initialise constants."""
        self.names = names
        self.scanner = scanner
        self.devices = devices
        self.network = network
        self.monitors = monitors
        self.symbol = Symbol()
        self.error_count = 0

        self.current_line = 0
        self.current_column = 0

        self.assignment_dict = {
            "identifier": None,
            "device": None,
            "parameter": None,
        }
        self.connection_dict = {}
        self.signals_dict = {}

        self.previous_line = 0
        self.previous_column = 0
        self.previous_symbol_length = 0
        self.DEVICES_ID = self.names.lookup(["DEVICES"])[0]
        self.CONNECTIONS_ID = self.names.lookup(["CONNECTIONS"])[0]
        self.SIGNALS_ID = self.names.lookup(["SIGNALS"])[0]
        self.AND_ID = self.names.lookup(["AND"])[0]
        self.OR_ID = self.names.lookup(["OR"])[0]
        self.NAND_ID = self.names.lookup(["NAND"])[0]
        self.NOR_ID = self.names.lookup(["NOR"])[0]
        self.XOR_ID = self.names.lookup(["XOR"])[0]
        self.NOT_ID = self.names.lookup(["NOT"])[0]
        self.SWITCH_ID = self.names.lookup(["SWITCH"])[0]
        self.CLOCK_ID = self.names.lookup(["CLOCK"])[0]
        self.DTYPE_ID = self.names.lookup(["DTYPE"])[0]
        self.RC_ID = self.names.lookup(["RC"])[0]

    def parse_network(self):
        """Parse the circuit definition file."""
        try:
            self.get_next_symbol()
            # device
            if self.symbol.id != self.DEVICES_ID:
                self.error(False, "Expected 'DEVICES' header.", False)
                raise ParseSyntaxError()
            self.get_next_symbol()

            if self.symbol.type != self.scanner.COLON:
                self.error(False, "Expected ':' at the end of line.", True)
                raise ParseSyntaxError()
            self.get_next_symbol()

            while self.symbol.id != self.CONNECTIONS_ID:
                if self.symbol.type == self.scanner.EOF:
                    self.error(
                        False,
                        "Unexpected end of file while looking for"
                        " 'CONNECTIONS'.",
                        False,
                    )
                    return False
                try:
                    self.assignment()
                except (ParseSyntaxError, ParseSemanticError):
                    pass
                    # self.synchronise()
            self.get_next_symbol()
            # connections
            if self.symbol.type != self.scanner.COLON:
                self.error(False, "Expected ':' at the end of line.", True)
                raise ParseSyntaxError()
            self.get_next_symbol()

            while self.symbol.id != self.SIGNALS_ID:
                if self.symbol.type == self.scanner.EOF:
                    self.error(
                        False,
                        "Unexpected end of file while looking for 'SIGNALS'.",
                        False,
                    )
                    return False
                try:
                    self.connection()
                except (ParseSyntaxError, ParseSemanticError):
                    pass
                    # self.synchronise()
            # signals
            self.get_next_symbol()

            if self.symbol.type != self.scanner.COLON:
                self.error(False, "Expected ':' at the end of line.", True)
                raise ParseSyntaxError()
            self.get_next_symbol()

            try:
                self.signals()
            except (ParseSyntaxError, ParseSemanticError):
                pass
            # ending
            if self.symbol.type != self.scanner.END:
                self.error(False, "Expected 'END' header.", False)
                return False
            self.get_next_symbol()

            if self.symbol.type != self.scanner.EOF:
                self.error(
                    False,
                    "Expected no more text after 'END'. Expected end of file.",
                    False,
                )
                return False
            return self.error_count == 0
        except (ParseSyntaxError, ParseSemanticError):
            print(
                "Parser execution halted prematurely due to"
                " catastrophic structural flaws."
            )
            return False

    def name(self):
        """Check that a symbol is a name."""
        if self.symbol.type == self.scanner.NAME:
            name_id = self.symbol.id
            self.get_next_symbol()
            return name_id
        else:
            self.error(False, "Invalid assignment."
                       "Expected a component name.", False)
            raise ParseSyntaxError()

    def device(self):
        """Check that a symbol is a device."""
        valid_device_ids = [
            self.AND_ID,
            self.OR_ID,
            self.NAND_ID,
            self.NOR_ID,
            self.XOR_ID,
            self.NOT_ID,
            self.SWITCH_ID,
            self.CLOCK_ID,
            self.DTYPE_ID,
            self.RC_ID
        ]
        if self.symbol.id in valid_device_ids:
            device_id = self.symbol.id
            self.get_next_symbol()
            return device_id
        else:
            self.error(
                False,
                "Invalid device name. "
                "Expected gate (NOT/AND/NAND/OR/NOR/XOR),"
                " switch, bistable or clock.",
                False,
            )
            raise ParseSyntaxError()

    def assignment(self):
        """Check assignements definitions."""
        # syntax
        name_id = self.name()
        self.assignment_dict["identifier"] = self.previous_column

        if self.symbol.type != self.scanner.EQUAL:
            self.error(False, "Invalid assignment. Expected '=' sign.", False)
            raise ParseSyntaxError()
        self.get_next_symbol()

        device_id = self.device()
        self.assignment_dict["device"] = self.previous_column

        parameter = None
        if self.symbol.type == self.scanner.OPEN_PAREN:
            self.get_next_symbol()

            if self.symbol.type != self.scanner.NUMBER:

                self.error(
                    False, "Invalid parameter. Expected a number.", False
                )
                raise ParseSyntaxError()

            self.assignment_dict["parameter"] = self.current_column
            parameter = int(self.symbol.id)
            self.get_next_symbol()

            if self.symbol.type != self.scanner.CLOSE_PAREN:
                self.error(False, "Missing ')' in the assignment.", False)
                raise ParseSyntaxError()
            self.get_next_symbol()

        if self.symbol.type != self.scanner.SEMICOLON:
            self.error(False, "Expected ';' at the end of line.", True)
            raise ParseSyntaxError()

        # semantic
        if device_id in [self.AND_ID, self.OR_ID, self.NAND_ID, self.NOR_ID]:
            if parameter is None:
                self.error(
                    True,
                    "Number of Input is required",
                    False,
                    self.assignment_dict["parameter"],
                )
                raise ParseSemanticError()
            if not (2 <= parameter <= 16):
                self.error(
                    True,
                    "Number of Input is not valid",
                    False,
                    self.assignment_dict["parameter"],
                )
                raise ParseSemanticError()
        elif device_id == self.SWITCH_ID:
            if parameter is None:
                self.error(
                    True,
                    "Initial setting for SWITCH is required",
                    False,
                    self.assignment_dict["parameter"],
                )
                raise ParseSemanticError()
            if parameter not in [0, 1]:
                self.error(
                    True,
                    "Initial setting for SWITCH is not valid",
                    False,
                    self.assignment_dict["parameter"],
                )
                raise ParseSemanticError()
        elif device_id == self.RC_ID:
            if parameter is None:
                self.error(
                    True,
                    "Number of symulation cycles is required.",
                    False,
                    self.assignment_dict["parameter"]
                )
                raise ParseSemanticError
            if parameter <= 0:
                self.error(
                    True,
                    "Number of symulation cycles for RC is not valid",
                    False,
                    self.assignment_dict["parameter"],
                )
                raise ParseSemanticError
        elif device_id == self.CLOCK_ID:
            if parameter is None:
                self.error(
                    True,
                    "Initial setting for CLOCK is required",
                    False,
                    self.assignment_dict["parameter"],
                )
                raise ParseSemanticError()
            if parameter <= 0:
                self.error(
                    True,
                    "Initial setting for CLOCK is not valid",
                    False,
                    self.assignment_dict["parameter"],
                )
                raise ParseSemanticError()
        elif device_id in [self.NOT_ID, self.XOR_ID, self.DTYPE_ID]:
            if parameter is not None:
                self.error(
                    True,
                    "Number of Input is not allowed to change for this device",
                    False,
                    self.assignment_dict["parameter"],
                )
                raise ParseSemanticError()
            if device_id == self.XOR_ID:
                parameter = None
            if device_id == self.NOT_ID:
                parameter = None
        error_code = self.devices.make_device(name_id, device_id, parameter)
        if error_code != self.devices.NO_ERROR:
            if error_code == self.devices.DEVICE_PRESENT:
                self.error(
                    True,
                    "Change name. This name is already in use.",
                    False,
                    self.assignment_dict["identifier"],
                )
            elif error_code == self.devices.BAD_DEVICE:
                self.error(
                    True,
                    "The backend does not support this"
                    " device type definition.",
                    False,
                    self.assignment_dict["device"],
                )
            elif error_code == self.devices.INVALID_QUALIFIER:
                self.error(
                    True,
                    "The specified initialization parameter is invalid.",
                    False,
                    self.assignment_dict["parameter"],
                )
            elif error_code == self.devices.QUALIFIER_PRESENT:
                self.error(
                    True,
                    "No qualifier expected for this device.",
                    False,
                    self.assignment_dict["parameter"],
                )
            else:
                self.error(
                    True,
                    f"Unhandled device creation error code: {error_code}",
                    False,
                )
            raise ParseSemanticError()
        self.get_next_symbol()

    def terminal(self):
        """Check that a terminal definition is valid."""
        name_id = self.name()
        name_col = self.previous_column
        ident_col = None
        identifier_id = None

        if self.symbol.type == self.scanner.DOT:
            self.get_next_symbol()
            if self.symbol.type == self.scanner.IDENTIFIER:
                identifier_id = self.symbol.id
                ident_col = self.current_column
                self.get_next_symbol()
            else:
                self.error(
                    False,
                    "Invalid terminal."
                    " Expected a input/output name after the '.'.",
                    False,
                )
                raise ParseSyntaxError()

        return name_id, identifier_id, name_col, ident_col

    def connection(self):
        """Check that a connection definition is valid."""
        # syntax
        name_id_1, identifier_id_1, name_col1, ident_col1 = self.terminal()
        self.connection_dict["LHS_identifier"] = name_col1
        self.connection_dict["LHS_output"] = ident_col1
        if self.symbol.type != self.scanner.ARROW:
            self.error(
                False,
                "Invalid connection. Expected '->' after the terminal.",
                False,
            )
            raise ParseSyntaxError()
        self.get_next_symbol()
        name_id_2, identifier_id_2, name_col2, ident_col2 = self.terminal()
        self.connection_dict["RHS_identifier"] = name_col2
        self.connection_dict["RHS_input"] = ident_col2

        if self.symbol.type != self.scanner.SEMICOLON:
            self.error(False, "Expected ';' at the end of line.", True)
            raise ParseSyntaxError()

        # semantic
        if name_id_1 == name_id_2 and identifier_id_1 == identifier_id_2:
            self.error(
                True,
                "A terminal must not be connected to itself.",
                False,
                self.connection_dict["RHS_identifier"],
            )
            raise ParseSemanticError()
        error_code, error_device = self.network.make_connection(
            name_id_1, identifier_id_1, name_id_2, identifier_id_2
        )
        if error_code != self.network.NO_ERROR:
            error_col = self.connection_dict[
                list(self.connection_dict.keys())[error_device]
            ]
            if error_code == self.network.DEVICE_ABSENT:
                self.error(
                    True,
                    "Terminal names must already be "
                    "specified in the DEVICES block.",
                    False,
                    error_col,
                )
            elif error_code == self.network.PORT_ABSENT:
                self.error(
                    True,
                    "The specified identifier is "
                    "invalid for this device configuration.",
                    False,
                    error_col,
                )
            elif error_code == self.network.INPUT_CONNECTED:
                self.error(
                    True,
                    "Multi-driven input error. "
                    "This input pin is already connected to an output.",
                    False,
                    error_col,
                )
            elif error_code == self.network.INPUT_TO_INPUT:
                self.error(
                    True,
                    "Invalid connection direction. "
                    "You cannot source a wire from an input pin.",
                    False,
                    error_col,
                )
            elif error_code == self.network.OUTPUT_TO_OUTPUT:
                self.error(
                    True,
                    "Invalid connection direction. "
                    "You cannot route a wire into an output pin.",
                    False,
                    error_col,
                )
            raise ParseSemanticError()
        self.get_next_symbol()

    def signals(self):
        """Check that signals to be monitored are valid."""
        # syntax
        signal_counter = 1
        while self.symbol.type != self.scanner.END:
            name_id, identifier_id, name_col, ident_col = self.terminal()
            self.signals_dict["name" + str(signal_counter)] = name_col
            self.signals_dict["identifier" + str(signal_counter)] = ident_col
            signal_counter += 1
            if self.symbol.type != self.scanner.SEMICOLON:
                self.error(False, "Expected ';' at the end of line.", True)
                raise ParseSyntaxError()
            # semantic
            error_code = self.monitors.make_monitor(name_id, identifier_id)
            if error_code != self.monitors.NO_ERROR:
                if error_code == self.monitors.network.DEVICE_ABSENT:
                    self.error(
                        True,
                        "Cannot monitor a device that has not been defined.",
                        False,
                        name_col,
                    )
                if error_code == self.monitors.NOT_OUTPUT:
                    self.error(
                        True,
                        "Only explicit device output pins (e.g., Q, QBAR)"
                        " or simple gates can be monitored.",
                        False,
                        ident_col,
                    )
                elif error_code == self.monitors.MONITOR_PRESENT:
                    self.error(
                        True,
                        "This exact device signal target is already"
                        " tracked under active monitors.",
                        False,
                        ident_col,
                    )
                continue
            self.get_next_symbol()

    def get_next_symbol(self):
        """Return the next symbol in the definition file."""
        old_symbol = self.symbol
        self.symbol = self.scanner.get_symbol()
        if old_symbol is not None:
            self.previous_line = old_symbol.line
            self.previous_column = old_symbol.column
            self.previous_symbol_length = old_symbol.length
        if self.symbol is not None:
            self.current_line = self.symbol.line
            self.current_column = self.symbol.column

    def error(self, error_type, message, end, semantic_column=None):
        """Report the error detected (syntax or semantic)."""
        self.error_count += 1
        if semantic_column is not None:
            error_line = self.current_line
            error_column = semantic_column
        else:
            if end:
                error_line = self.previous_line
                error_column = (
                    self.previous_column + self.previous_symbol_length
                )
            else:
                error_line = self.current_line
                error_column = self.current_column
        error_message_list = [
            "Syntax error detected.",
            "Semantic error detected.",
        ]
        print(error_message_list[error_type])
        self.scanner.print_error_line(error_line, error_column)
        print(f"Details:{message}\n")
        if not end:
            self.synchronise()
        return False

    def synchronise(self):
        """Resume parsing after an error has occured."""
        while self.symbol.type != self.scanner.EOF:
            if self.symbol.id in [
                self.DEVICES_ID,
                self.CONNECTIONS_ID,
                self.SIGNALS_ID,
            ]:
                return

            if self.symbol.type == self.scanner.SEMICOLON:
                self.get_next_symbol()
                return

            self.get_next_symbol()
