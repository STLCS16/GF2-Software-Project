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
        self.current_line = 0
        self.current_column = 0

    def parse_network(self):
        """Parse the circuit definition file."""
        # For now just return True, so that userint and gui can run in the
        # skeleton code. When complete, should return False when there are
        # errors in the circuit definition file.
        #return True
    
        self.symbol = self.get_next_symbol()
        if self.symbol.id == self.names.lookup(["DEVICES"]):
            self.symbol = self.get_next_symbol()
        else:
            self.error(False,"Expected 'DEVICES' header.")
        if self.symbol.type == self.scanner.COLON:
                self.symbol = self.get_next_symbol()
        else:
            self.error(False, "Expected ':' at the end of line.")
        while self.symbol.type != self.scanner.KEYWORD:
            self.assignment()
        
        if self.symbol.id == self.names.lookup(["CONNECTIONS"]):
            self.symbol = self.get_next_symbol()
        else:
            self.error(False, "Expected 'CONNECTIONS' header.")
        if self.symbol.type == self.scanner.COLON:
                self.symbol = self.get_next_symbol()
        else:
            self.error(False, "Expected ':' at the end of line.")
        while self.symbol.type != self.scanner.KEYWORD:
            self.connection()
        
        if self.symbol.id == self.names.lookup(["SIGNALS"]):
            self.symbol = self.get_next_symbol()
        else:
            self.error(False, "Expected 'SIGNALS' header.")
        if self.symbol.type == self.scanner.COLON:
                self.symbol = self.get_next_symbol()
        else:
            self.error(False, "Expected ':' at the end of line.")
        self.signals()

        if self.symbol.id == self.names.lookup(["END"]):
            self.symbol = self.get_next_symbol()
            if self.symbol.type == self.scanner.EOF:
                return True
            else:
                self.error(False, "Expected no more text after 'END'. Expected end of file.")
        else:
            self.error(False, "Expected 'END' header.")

    def device(self):
        if self.symbol.type == self.scanner.NAME:
            if self.symbol.id in self.devices.gate_types:
                self.symbol = self.get_next_symbol()
            elif self.symbol.id in self.devices.device_types:
                self.symbol = self.get_next_symbol()
            else:
                self.error(False, "Invalid device name. Expected gate (NOT/AND/NAND/OR/NOR/XOR), switch, bistable or clock.")
        else:
            self.error(False, "Invalid name. Expected a device name.")

    def assignment(self):
        self.identifier()

        if self.symbol.type != self.scanner.EQUALS:
            self.error(False, "Invalid assignment. Expected '=' sign.")
        self.symbol = self.get_next_symbol()
        self.device()

        if self.symbol.type == self.scanner.OPEN_PAREN:
            self.symbol = self.get_next_symbol()

            if self.symbol.type != self.scanner.NUMBER:
                self.error(False, "Invalid parameter. Expected a number.")
            self.symbol = self.get_next_symbol()

            if self.symbol.type != self.scanner.CLOSE_PAREN:
                self.error(False, "Missing ')' in the assignment.")
            self.symbol = self.get_next_symbol()

        if self.symbol.type != self.scanner.SEMICOLON:
            self.error(False, "Expected ';' at the end of line.")
        self.symbol = self.get_next_symbol()


    def terminal(self):
        self.identifier()

        if self.symbol.type == self.scanner.DOT:
            self.symbol = self.get_next_symbol()
            if self.symbol.type == self.scanner.INPUT:
                self.symbol = self.get_next_symbol()
            elif self.symbol.id in self.devices.dtype_input_ids:
                self.symbol = self.get_next_symbol()
            if self.symbol.id in self.devices.dtype_outputs:
                self.symbol = self.get_next_symbol()
            else:
                self.error(False, "Invalid terminal. Expected a input/output name after the '.'.")


    def connection(self):
        self.terminal()
        if self.symbol.type == self.scanner.ARROW:
            self.symbol = self.get_next_symbol()
            self.terminal()
            if self.symbol.type == self.scanner.SEMICOLON:
                self.symbol = self.get_next_symbol()
            else:
                self.error(False, "Expected ';' at the end of line.")
        else:
            self.error(False, "Invalid connection. Expected '->' after the terminal.")

    def signals(self):
        while self.symbol.type == self.scanner.TERMINAL:
            self.terminal()
            if self.symbol.type == self.scanner.SEMICOLON:
                self.symbol = self.get_next_symbol()
            else:
                self.error(False, "Expected ';' at the end of line.")
    
    def get_next_symbol(self):
        self.symbol = self.get_next_symbol()
        if self.symbol.line != self.current_line:
            self.current_line = self.symbol.line
            self.current_column = self.symbol.column
            
    def error(self, error_type, message):
        #error type will be a boolean (False if syntax error and True if semantic error)
        #message will represent the error message
        error_message_list = ["Syntax error detected.","Semantic error detected."]
        print(error_message_list[error_type],"Line",self.current_line,":", self.scanner.file_lines[self.current_line - 1])
        print(message)