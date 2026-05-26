"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""
import scanner

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

    def parse_network(self):
        """Parse the circuit definition file."""
        # For now just return True, so that userint and gui can run in the
        # skeleton code. When complete, should return False when there are
        # errors in the circuit definition file.
        #return True
    
        self.symbol = self.scanner.get_symbol()
        if self.symbol.id == self.names.lookup(["DEVICES"]):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error()
        if self.symbol.type == self.scanner.COLON:
                self.symbol = self.scanner.get_symbol()
        else:
            self.error()
        while self.symbol.type != self.scanner.KEYWORD:
            self.assignment()
        
        if self.symbol.id == self.names.lookup(["CONNECTIONS"]):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error()
        if self.symbol.type == self.scanner.COLON:
                self.symbol = self.scanner.get_symbol()
        else:
            self.error()
        while self.symbol.type != self.scanner.KEYWORD:
            self.connection()
        
        if self.symbol.id == self.names.lookup(["SIGNALS"]):
            self.symbol = self.scanner.get_symbol()
        else:
            self.error()
        if self.symbol.type == self.scanner.COLON:
                self.symbol = self.scanner.get_symbol()
        else:
            self.error()
        self.signals()

        if self.symbol.id == self.names.lookup(["END"]):
            self.symbol = self.scanner.get_symbol()
            if self.symbol.type == self.scanner.EOF:
                return True
            else:
                self.error()
        else:
            self.error()

    def device(self):
        if self.symbol.type == self.scanner.NAME:
            if self.symbol.id in self.devices.gate_types:
                self.symbol = self.scanner.get_symbol()
            elif self.symbol.id in self.devices.device_types:
                self.symbol = self.scanner.get_symbol()
            else:
                self.error()
        else:
            self.error()

    def assignment(self):
        self.identifier()

        if self.symbol.type != self.scanner.EQUALS:
            self.error()
        self.symbol = self.scanner.get_symbol()
        self.device()

        if self.symbol.type == self.scanner.OPEN_PAREN:
            self.symbol = self.scanner.get_symbol()

            if self.symbol.type != self.scanner.NUMBER:
                self.error()
            self.symbol = self.scanner.get_symbol()

            if self.symbol.type != self.scanner.CLOSE_PAREN:
                self.error()
            self.symbol = self.scanner.get_symbol()

        if self.symbol.type != self.scanner.SEMICOLON:
            self.error()
        self.symbol = self.scanner.get_symbol()


    def terminal(self):
        self.identifier()

        if self.symbol.type == self.scanner.DOT:
            self.symbol = self.scanner.get_symbol()
            if self.symbol.type == self.scanner.INPUT:
                self.symbol = self.scanner.get_symbol()
            elif self.symbol.id in self.devices.dtype_input_ids:
                self.symbol = self.scanner.get_symbol()
            if self.symbol.id in self.devices.dtype_outputs:
                self.symbol = self.scanner.get_symbol()
            else:
                self.error()


    def connection(self):
        self.terminal()
        if self.symbol.type == self.scanner.ARROW:
            self.symbol = self.scanner.get_symbol()
            self.terminal()
            if self.symbol.type == self.scanner.SEMICOLON:
                self.symbol = self.scanner.get_symbol()
            else:
                self.error()
        else:
            self.error()

    def signals(self):
        while self.symbol.type == self.scanner.TERMINAL:
            self.terminal()
            if self.symbol.type == self.scanner.SEMICOLON:
                self.symbol = self.scanner.get_symbol()
            else:
                self.error()
            
    def error(self, error_type):
        pass