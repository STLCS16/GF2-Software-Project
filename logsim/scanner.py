"""Read the circuit definition file and translate the characters into symbols.

Used in the Logic Simulator project to read the characters in the definition
file and translate them into symbols that are usable by the parser.

Classes
-------
Scanner - reads definition file and translates characters into symbols.
Symbol - encapsulates a symbol and stores its properties.
"""
import sys

class Symbol:

    """Encapsulate a symbol and store its properties.

    Parameters
    ----------
    No parameters.

    Public methods
    --------------
    No public methods.
    """

    def __init__(self):
        """Initialise symbol properties."""
        self.type = None 
        self.id = None
        self.line = None 
        self.column = None 

class Scanner:

    """Read circuit definition file and translate the characters into symbols.

    Once supplied with the path to a valid definition file, the scanner
    translates the sequence of characters in the definition file into symbols
    that the parser can use. It also skips over comments and irrelevant
    formatting characters, such as spaces and line breaks.

    Parameters
    ----------
    path: path to the circuit definition file.
    names: instance of the names.Names() class.

    Public methods
    -------------
    get_symbol(self): Translates the next sequence of characters into a symbol
                      and returns the symbol.
    """

    # type ID
    #(HEADINGS, END, DEVICE, IDENTIFIER, NAME, COMMA, SEMICOLON, EQUAL, COLON, DOT, OPEN_PAREN, CLOSE_PAREN, ARROW, NUMBER,EOF ) = range(15)
    (HEADINGS, END, DEVICE, IDENTIFIER, NAME,
        COMMA, SEMICOLON, EQUAL, COLON, DOT,
        OPEN_PAREN, CLOSE_PAREN, ARROW, NUMBER, EOF) = (
    "HEADINGS", "END", "DEVICE", "IDENTIFIER", "NAME",
    "COMMA", "SEMICOLON", "EQUAL", "COLON", "DOT",
    "OPEN_PAREN", "CLOSE_PAREN", "ARROW", "NUMBER", "EOF"
    )

    def __init__(self, path, names):
        self.names = names
        with open(path, 'r') as f:
            self.file_lines = [line.rstrip('\n') for line in f] # for error reporting
            f.seek(0)
            self.source_string = f.read()
        
        self.char_index = 0
        self.line_number = 0 #was 1 before?
        self.column_number = 1
        self.current_character = self.source_string[0] if self.source_string else ""
        # heading
        self.heading_list = ["DEVICES", "CONNECTIONS", "SIGNALS"]
        self.names.lookup(self.heading_list) # pre-regist
        #end
        self.end_list = ["END"]
        self.names.lookup(self.end_list)
        #device
        self.device_list_ni = ["DTYPE", "XOR","NOT"]#ni means no need to specify number of input
        self.device_list_i = ["AND", "OR", "NAND", "NOR","CLOCK", "SWITCH"] # i means need to specify number of input
        self.names.lookup(self.device_list_ni + self.device_list_i)
        #identifier
        self.identifier_list = [f'I{i}' for i in range(1, 17)] + ['D', 'CLK', 'SET','CLEAR', 'Q','QBAR'] #changed DATA to D
        self.names.lookup(self.identifier_list) # avoid user name the device as I1 or other confusing term
        #punctuation
        self.comma = ','
        self.semicolon =';'
        self.equal ='='
        self.colon = ':'
        self.dot ='.'
        self.open_paren ='('
        self.close_paren = ')'
        self.minus = '-'
        self.greater = '>'
        self.newline = '\n'

        #fast search
        self.heading_set = set(self.heading_list)
        self.device_set = set(self.device_list_ni + self.device_list_i)
        self.identifier_set = set(self.identifier_list)

    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""
        symbol = Symbol()
        self.skip_spaces() # current character now not whitespace

        symbol.line = self.line_number
        symbol.column = self.column_number

        if self.current_character == "":
            symbol.type = self.EOF
            return symbol

        if self.current_character.isalpha(): #isalnum?
            name_list = self.get_name()
            #name_string = name_list[0]
            name_string = name_list
            symbol.id = self.names.lookup([name_string])[0]
            if name_string.islower():
                return None
            if name_string in self.heading_set:
                symbol.type = self.HEADINGS
            elif name_string in self.end_list:
                symbol.type = self.END
            elif name_string in self.device_set:
                    symbol.type = self.DEVICE
            elif name_string in self.identifier_list:
                    symbol.type = self.IDENTIFIER
            else:
                symbol.type = self.NAME
            return symbol
                
        if self.current_character.isdigit(): 
            symbol.id = self.get_number()
            symbol.type = self.NUMBER
            return symbol
        
        #punctuation
        elif self.current_character == ";":
            symbol.type = self.SEMICOLON
            self.advance()
        elif self.current_character == ":":
            symbol.type = self.COLON
            self.advance()
        elif self.current_character == ".":
            symbol.type = self.DOT
            self.advance()
        elif self.current_character == "(":
            symbol.type = self.OPEN_PAREN
            self.advance()
        elif self.current_character == ")":
            symbol.type = self.CLOSE_PAREN
            self.advance()
        elif self.current_character == "=":
            symbol.type = self.EQUAL
            self.advance()
        elif self.current_character == ",":
            symbol.type = self.COMMA
            self.advance()
        elif self.current_character == "-":
            self.advance()
            if self.current_character == ">":
                symbol.type = self.ARROW
                self.advance()
            else:
                symbol.type = self.EOF # Or handle as invalid character
            
        else:
            self.advance()
            return None
        
        return symbol

    def get_name(self):
        """Builds a string of alphanumeric characters."""
        name_chars = []
        while self.current_character.isalnum():
            name_chars.append(self.current_character)
            self.advance()
        return "".join(name_chars)

    def get_number(self):
        """Builds a string of continuous digits."""
        num_chars = []
        while self.current_character.isdigit():
            num_chars.append(self.current_character)
            self.advance()
        return "".join(num_chars)

    def skip_spaces(self):
        while self.current_character.isspace():
            self.advance()

    def advance(self):
        self.char_index += 1
        if self.char_index < len(self.source_string):
            self.current_character = self.source_string[self.char_index]
            if self.current_character == '\n':
                self.line_number += 1
                self.column_number = 1
            else:
                self.column_number += 1
        else:
            self.current_character = ""  # EOF reached
        return self.current_character