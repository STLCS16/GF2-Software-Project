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

    def __init__(self, path, names):
        self.names = names
        with open(path, 'r') as f:
            self.file_lines = f.readlines()
        
        self.line_number = 0
        self.column_number = 0
        self.current_character = " " 
    
        self.symbol_type_list = [
            self.COMMA, self.SEMICOLON, self.EQUALS, self.COLON, self.DOT,
            self.OPEN_PAREN, self.CLOSE_PAREN, self.ARROW,
            self.KEYWORD, self.NUMBER, self.NAME, self.EOF
        ] = range(12)
    
        self.keywords_list = ["DEVICES", "CONNECTIONS", "SIGNALS", "END"]
        self.device_list = []
        self.keyword_ids = self.names.lookup(self.keywords_list)
    
        self.advance()

    def get_symbol(self):
        """Translate the next sequence of characters into a symbol."""
        symbol = Symbol()
        self.skip_spaces() # current character now not whitespace

        symbol.line = self.line_number
        symbol.column = self.column_number

        if self.current_character.isalpha(): # name
            name_string = self.get_name()
            if name_string in self.keywords_list:
                symbol.type = self.KEYWORD
            else:
                symbol.type = self.NAME
            [symbol.id] = self.names.lookup([name_string])
        elif self.current_character.isdigit(): # number
            symbol.id = self.get_number()
            symbol.type = self.NUMBER
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
            symbol.type = self.EQUALS
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
            
        elif self.current_character == "":
            symbol.type = self.EOF
        else:
        # Invalid character handling
            self.advance()
        
        return symbol

