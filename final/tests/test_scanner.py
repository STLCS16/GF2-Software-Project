import pytest
from unittest.mock import MagicMock
from logsim.scanner import Scanner, Symbol


class DummyNames:
    def lookup(self, name_list):
        return [i for i, _ in enumerate(name_list)]


@pytest.fixture
def scanner_instance(tmp_path):
    file_path = tmp_path / "dummy.txt"
    file_path.write_text("DEVICES:\n")
    return Scanner(str(file_path), DummyNames())


def test_symbol_initialization():
    sym = Symbol()
    assert sym.type is None
    assert sym.id is None
    assert sym.line is None
    assert sym.column is None
    assert sym.length == 0


def test_get_symbol_name(scanner_instance):
    scanner_instance.skip_spaces_and_comments = MagicMock()
    scanner_instance.get_name = MagicMock(return_value="G1")
    scanner_instance.names.lookup = MagicMock(return_value=[101])

    scanner_instance.current_character = "G"

    symbol = scanner_instance.get_symbol()

    assert symbol.type == Scanner.NAME
    assert symbol.id == 101
    scanner_instance.names.lookup.assert_called_with(["G1"])


def test_get_symbol_number(scanner_instance):
    scanner_instance.skip_spaces_and_comments = MagicMock()
    scanner_instance.get_number = MagicMock(return_value="16")

    scanner_instance.current_character = "1"

    symbol = scanner_instance.get_symbol()

    assert symbol.type == Scanner.NUMBER
    assert symbol.id == "16"


@pytest.mark.parametrize("char, expected_type", [
    (";", Scanner.SEMICOLON),
    (":", Scanner.COLON),
    (".", Scanner.DOT),
    ("(", Scanner.OPEN_PAREN),
    (")", Scanner.CLOSE_PAREN),
    ("=", Scanner.EQUAL),
    (",", Scanner.COMMA),
])
def test_get_symbol_single_punctuation(scanner_instance, char, expected_type):
    scanner_instance.skip_spaces_and_comments = MagicMock()
    scanner_instance.advance = MagicMock()

    scanner_instance.current_character = char
    symbol = scanner_instance.get_symbol()

    assert symbol.type == expected_type
    assert symbol.length == 1
    scanner_instance.advance.assert_called_once()


def test_get_symbol_arrow_success(scanner_instance):
    scanner_instance.skip_spaces_and_comments = MagicMock()

    def advance_side_effect():
        scanner_instance.current_character = ">"
    scanner_instance.advance = MagicMock(side_effect=advance_side_effect)

    scanner_instance.current_character = "-"

    symbol = scanner_instance.get_symbol()

    assert symbol.type == Scanner.ARROW
    assert symbol.length == 2
    assert scanner_instance.advance.call_count == 2


def test_get_symbol_arrow_incomplete(scanner_instance):
    scanner_instance.skip_spaces_and_comments = MagicMock()

    def advance_side_effect():
        scanner_instance.current_character = "x"
    scanner_instance.advance = MagicMock(side_effect=advance_side_effect)

    scanner_instance.current_character = "-"

    symbol = scanner_instance.get_symbol()

    assert symbol.type == scanner_instance.INVALID
    assert symbol.length == 0
    assert scanner_instance.advance.call_count == 1


def test_get_symbol_eof(scanner_instance):
    scanner_instance.skip_spaces_and_comments = MagicMock()
    scanner_instance.current_character = ""

    symbol = scanner_instance.get_symbol()

    assert symbol.type == Scanner.EOF


def test_get_symbol_invalid_character(scanner_instance):
    scanner_instance.skip_spaces_and_comments = MagicMock()
    scanner_instance.advance = MagicMock()

    scanner_instance.current_character = "$"

    symbol = scanner_instance.get_symbol()

    assert symbol.type == scanner_instance.INVALID
    scanner_instance.advance.assert_called_once()
