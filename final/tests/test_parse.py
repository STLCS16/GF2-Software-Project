import pytest
from unittest.mock import MagicMock
from parse import Parser, ParseSyntaxError, ParseSemanticError


class MockSymbol:
    def __init__(self, type_=None, id_=None, line=1, column=1, length=1):
        self.type = type_
        self.id = id_
        self.line = line
        self.column = column
        self.length = length


@pytest.fixture
def mock_dependencies():
    names = MagicMock()
    names.lookup.side_effect = lambda name_list: [hash(name_list[0])]

    devices = MagicMock()
    devices.NO_ERROR = 0
    devices.make_device.return_value = devices.NO_ERROR

    network = MagicMock()
    network.NO_ERROR = 0
    network.make_connection.return_value = network.NO_ERROR

    monitors = MagicMock()
    monitors.NO_ERROR = 0
    monitors.make_monitor.return_value = monitors.NO_ERROR
    monitors.network = network

    scanner = MagicMock()
    scanner.EOF = "EOF"
    scanner.NAME = "NAME"
    scanner.NUMBER = "NUMBER"
    scanner.COLON = "COLON"
    scanner.SEMICOLON = "SEMICOLON"
    scanner.EQUAL = "EQUAL"
    scanner.OPEN_PAREN = "OPEN_PAREN"
    scanner.CLOSE_PAREN = "CLOSE_PAREN"
    scanner.DOT = "DOT"
    scanner.ARROW = "ARROW"
    scanner.END = "END"

    return names, devices, network, monitors, scanner


@pytest.fixture
def parser(mock_dependencies):
    names, devices, network, monitors, scanner = mock_dependencies
    return Parser(names, devices, network, monitors, scanner)


# --- FIXED TESTS ---

def test_name_invalid_raises_syntax_error(parser, mock_dependencies):
    _, _, _, _, scanner = mock_dependencies
    parser.symbol = MockSymbol(type_=scanner.NUMBER)

    # FIX: Provide an EOF symbol so synchronise() can break out of its loop
    scanner.get_symbol.return_value = MockSymbol(type_=scanner.EOF)

    with pytest.raises(ParseSyntaxError):
        parser.name()


def test_device_invalid_raises_syntax_error(parser, mock_dependencies):
    _, _, _, _, scanner = mock_dependencies
    parser.symbol = MockSymbol(id_=-999)

    # FIX: Provide an EOF symbol so synchronise() can break out of its loop
    scanner.get_symbol.return_value = MockSymbol(type_=scanner.EOF)

    with pytest.raises(ParseSyntaxError):
        parser.device()


def test_assignment_valid(parser, mock_dependencies):
    _, devices, _, _, scanner = mock_dependencies

    name_id = 100
    symbols = [
        MockSymbol(type_=scanner.NAME, id_=name_id),
        MockSymbol(type_=scanner.EQUAL),
        MockSymbol(type_=scanner.NAME, id_=parser.SWITCH_ID),
        MockSymbol(type_=scanner.OPEN_PAREN),
        MockSymbol(type_=scanner.NUMBER, id_=1),
        MockSymbol(type_=scanner.CLOSE_PAREN),
        MockSymbol(type_=scanner.SEMICOLON),
        MockSymbol(type_=scanner.EOF)
    ]

    parser.symbol = symbols[0]
    scanner.get_symbol.side_effect = symbols[1:]

    parser.assignment()
    devices.make_device.assert_called_once_with(name_id, parser.SWITCH_ID, 1)


def test_assignment_semantic_error_invalid_gate(parser, mock_dependencies):
    _, _, _, _, scanner = mock_dependencies

    symbols = [
        MockSymbol(type_=scanner.NAME, id_=100),
        MockSymbol(type_=scanner.EQUAL),
        MockSymbol(type_=scanner.NAME, id_=parser.AND_ID),
        MockSymbol(type_=scanner.OPEN_PAREN),
        MockSymbol(type_=scanner.NUMBER, id_=1),
        MockSymbol(type_=scanner.CLOSE_PAREN),
        MockSymbol(type_=scanner.SEMICOLON),
        MockSymbol(type_=scanner.EOF)
    ]

    parser.symbol = symbols[0]
    scanner.get_symbol.side_effect = symbols[1:]

    with pytest.raises(ParseSemanticError):
        parser.assignment()
