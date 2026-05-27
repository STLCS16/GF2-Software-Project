"""Parse the definition file and build the logic network.

Used in the Logic Simulator project to analyse the syntactic and semantic
correctness of the symbols received from the scanner and then builds the
logic network.

Classes
-------
Parser - parses the definition file and builds the logic network.
"""
import scanner
import sys

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
    
        self.get_next_symbol()
        if self.symbol.id == self.names.lookup(["DEVICES"])[0]:
            self.get_next_symbol()
        else:
            return self.error(False,"Expected 'DEVICES' header.")
        if self.symbol.type == self.scanner.COLON:
            self.get_next_symbol()
        else:
            return self.error(False, "Expected ':' at the end of line.")
        while self.symbol.id != self.names.lookup(["CONNECTIONS"])[0]:
            self.assignment()
        
        if self.symbol.id == self.names.lookup(["CONNECTIONS"])[0]:
            self.get_next_symbol()
        else:
            return self.error(False, "Expected 'CONNECTIONS' header.")
        if self.symbol.type == self.scanner.COLON:
            self.get_next_symbol()
        else:
            return self.error(False, "Expected ':' at the end of line.")
        while self.symbol.id != self.names.lookup(["SIGNALS"])[0]:
            self.connection()
        
        if self.symbol.id == self.names.lookup(["SIGNALS"])[0]:
            self.get_next_symbol()
        else:
            return self.error(False, "Expected 'SIGNALS' header.")
        if self.symbol.type == self.scanner.COLON:
            self.get_next_symbol()
        else:
            return self.error(False, "Expected ':' at the end of line.")
        self.signals()

        if self.symbol.type == self.scanner.END:
            self.get_next_symbol()
            if self.symbol.type == self.scanner.EOF:
                return True
            else:
                return self.error(False, "Expected no more text after 'END'. Expected end of file.")
        else:
            return self.error(False, "Expected 'END' header.")
    
    def identifier(self):
        if self.symbol.type == self.scanner.NAME:
            self.get_next_symbol()
        else:
            return self.error(False, "Invalid assignment. Expected a component name.")

    def device(self):
        if self.symbol.type == self.scanner.DEVICE:
            self.get_next_symbol()
        else:
            return self.error(False, "Invalid device name. Expected gate (NOT/AND/NAND/OR/NOR/XOR), switch, bistable or clock.")

    def assignment(self):
        self.identifier()

        if self.symbol.type != self.scanner.EQUAL:
            return self.error(False, "Invalid assignment. Expected '=' sign.")
        self.get_next_symbol()
        self.device()

        if self.symbol.type == self.scanner.OPEN_PAREN:
            self.get_next_symbol()

            if self.symbol.type != self.scanner.NUMBER:
                return self.error(False, "Invalid parameter. Expected a number.")
            self.get_next_symbol()

            if self.symbol.type != self.scanner.CLOSE_PAREN:
                return self.error(False, "Missing ')' in the assignment.")
            self.get_next_symbol()

        if self.symbol.type != self.scanner.SEMICOLON:
            return self.error(False, "Expected ';' at the end of line.")
        self.get_next_symbol()


    def terminal(self):
        self.identifier()

        if self.symbol.type == self.scanner.DOT:
            self.get_next_symbol()
            if self.symbol.type == self.scanner.IDENTIFIER:
                self.get_next_symbol()
            else:
                return self.error(False, "Invalid terminal. Expected a input/output name after the '.'.")


    def connection(self):
        self.terminal()
        if self.symbol.type == self.scanner.ARROW:
            self.get_next_symbol()
            self.terminal()
            if self.symbol.type == self.scanner.SEMICOLON:
                self.get_next_symbol()
            else:
                return self.error(False, "Expected ';' at the end of line.")
        else:
            return self.error(False, "Invalid connection. Expected '->' after the terminal.")

    def signals(self):
        while self.symbol.type != self.scanner.END:
            self.terminal()
            if self.symbol.type == self.scanner.SEMICOLON:
                self.get_next_symbol()
            else:
                return self.error(False, "Expected ';' at the end of line.")
    
    def get_next_symbol(self):
        self.symbol = self.scanner.get_symbol()
        if self.symbol.line != self.current_line:
            self.current_line = self.symbol.line
            self.current_column = self.symbol.column
            
    def error(self, error_type, message):
        #error type will be a boolean (False if syntax error and True if semantic error)
        #message will represent the error message
        error_message_list = ["Syntax error detected.","Semantic error detected."]
        print(error_message_list[error_type],"Line",self.current_line+1,":", self.scanner.file_lines[self.current_line])
        print(message)
        #sys.exit("Parse error")
        return False