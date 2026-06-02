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
        self.length = 0

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
        
        #self.symbol = Symbol() #initialise the symbol object
        
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
        self.device_list_ni = ["DTYPE", "NOT"]#ni means no need to specify number of input
        self.device_list_i = ["AND", "XOR","OR", "NAND", "NOR","CLOCK", "SWITCH"] # i means need to specify number of input
        self.names.lookup(self.device_list_ni + self.device_list_i)
        #identifier
        self.identifier_list = [f'I{i}' for i in range(1, 17)] + ['DATA', 'CLK', 'SET','CLEAR', 'Q','QBAR'] 
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
        self.skip_spaces_and_comments() # current character now not whitespace

        self.symbol = Symbol()

        self.symbol.line = self.line_number
        self.symbol.column = self.column_number

        if self.current_character == "":
            self.symbol.type = self.EOF
            self.symbol.length = 0
            return self.symbol

        if self.current_character.isalpha(): 
            name_list = self.get_name()
            name_string = name_list
            self.symbol.id = self.names.lookup([name_string])[0]
            self.symbol.length = len(name_list)
            if name_string.islower():
                return None
            if name_string in self.heading_set:
                self.symbol.type = self.HEADINGS
            elif name_string in self.end_list:
                self.symbol.type = self.END
            elif name_string in self.device_set:
                    self.symbol.type = self.DEVICE
            elif name_string in self.identifier_list:
                    self.symbol.type = self.IDENTIFIER
            else:
                self.symbol.type = self.NAME
            return self.symbol
                
        if self.current_character.isdigit(): 
            self.symbol.id = self.get_number()
            self.symbol.type = self.NUMBER
            self.symbol.length = len(self.symbol.id)
            return self.symbol
        
        #punctuation
        elif self.current_character == ";":
            self.symbol.type = self.SEMICOLON
            self.symbol.length = 1
            self.advance()
        elif self.current_character == ":":
            self.symbol.type = self.COLON
            self.symbol.length = 1
            self.advance()
        elif self.current_character == ".":
            self.symbol.type = self.DOT
            self.symbol.length = 1
            self.advance()
        elif self.current_character == "(":
            self.symbol.type = self.OPEN_PAREN
            self.symbol.length = 1
            self.advance()
        elif self.current_character == ")":
            self.symbol.type = self.CLOSE_PAREN
            self.symbol.length = 1
            self.advance()
        elif self.current_character == "=":
            self.symbol.type = self.EQUAL
            self.symbol.length = 1
            self.advance()
        elif self.current_character == ",":
            self.symbol.type = self.COMMA
            self.symbol.length = 1
            self.advance()
        elif self.current_character == "-":
            self.advance()
            if self.current_character == ">":
                self.symbol.type = self.ARROW
                self.symbol.length = 2
                self.advance()
            else:
                self.symbol.type = self.EOF # Or handle as invalid character
                self.symbol.length = 0
            
        else:
            self.advance()
            return None
        
        return self.symbol

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

    def skip_spaces_and_comments(self):
        """Skip both space and comments, comments is anything within quotes"""
        while self.current_character.isspace() or self.current_character =='"':
            if self.current_character.isspace():
                self.advance()
            elif self.current_character =='"':
                self.advance()
                while self.current_character != '"' and self.current_character != "":
                    self.advance()
                if self.current_character =='"':
                    self.advance()

    def advance(self):
        self.char_index += 1
        if self.char_index < len(self.source_string):
            self.current_character = self.source_string[self.char_index]
            if self.current_character == '\n':
                self.line_number += 1
                self.column_number = 0
            else:
                self.column_number += 1
        else:
            self.current_character = ""  # EOF reached
        return self.current_character

    def print_error_line(self, error_line_number, error_column_number):
        """Prints the line of code and a caret pointing to the error location."""
        if error_line_number >= len(self.file_lines):
            print("Error occurred at the end of the file (unexpected EOF).")
            return
        code_line = self.file_lines[error_line_number]
        pointer_string = (" " * ((error_column_number - 1)+len(str(error_line_number+1))+8)) + "^"
        print("Line",error_line_number + 1, ":",code_line)
        #print(code_line)
        print(pointer_string)