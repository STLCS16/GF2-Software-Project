import pytest
from unittest.mock import MagicMock, patch
from scanner import Scanner, Symbol  # Assumes your file is named scanner.py


# --- Mock Classes for Dependency Injection ---

class DummyNames:
    """A minimal fake Names class to handle initialization lookups."""
    def lookup(self, name_list):
        # Maps names to a deterministic dummy ID index list
        return [i for i, _ in enumerate(name_list)]


@pytest.fixture
def mock_file(tmp_path):
    """Fixture to create a temporary file so open() doesn't fail on init."""
    file_path = tmp_path / "dummy_circuit.txt"
    file_path.write_text("DEVICES:\n")
    return str(file_path)


@pytest.fixture
def scanner_instance(mock_file):
    """Fixture supplying a Scanner instance initialized with a fake Names registry."""
    names_mock = DummyNames()
    return Scanner(mock_file, names_mock)


# --- Tests for Symbol Class ---

def test_symbol_initialization():
    """Verify that a new Symbol instantiates with clean, empty properties."""
    sym = Symbol()
    assert sym.type is None
    assert sym.id is None
    assert sym.line is None
    assert sym.column is None


# --- Unit Tests for Scanner.get_symbol() ---

def test_get_symbol_keyword(scanner_instance):
    """Verify that keywords match and pull correct IDs from the Names module."""
    scanner_instance.skip_spaces = MagicMock()
    scanner_instance.get_name = MagicMock(return_value="DEVICES")
    scanner_instance.names.lookup = MagicMock(return_value=[42])
    
    # Simulate stopping at an alphabetical character character
    scanner_instance.current_character = "D"
    scanner_instance.line_number = 1
    scanner_instance.column_number = 0
    
    symbol = scanner_instance.get_symbol()
    
    assert symbol.type == scanner_instance.KEYWORD
    assert symbol.id == 42
    assert symbol.line == 1
    assert symbol.column == 0
    scanner_instance.get_name.assert_called_once()


def test_get_symbol_name(scanner_instance):
    """Verify user-defined names are tagged correctly and registered via lookup."""
    scanner_instance.skip_spaces = MagicMock()
    scanner_instance.get_name = MagicMock(return_value="G1")
    scanner_instance.names.lookup = MagicMock(return_value=[101])
    
    scanner_instance.current_character = "G"
    
    symbol = scanner_instance.get_symbol()
    
    assert symbol.type == scanner_instance.NAME
    assert symbol.id == 101
    scanner_instance.names.lookup.assert_called_with(["G1"])


def test_get_symbol_number(scanner_instance):
    """Verify string digits trigger the number block and return accurate IDs."""
    scanner_instance.skip_spaces = MagicMock()
    scanner_instance.get_number = MagicMock(return_value=16)
    
    scanner_instance.current_character = "1"
    
    symbol = scanner_instance.get_symbol()
    
    assert symbol.type == scanner_instance.NUMBER
    assert symbol.id == 16


@pytest.mark.parametrize("char, expected_type", [
    (";", 1),  # SEMICOLON
    (":", 3),  # COLON
    (".", 4),  # DOT
    ("(", 5),  # OPEN_PAREN
    (")", 6),  # CLOSE_PAREN
    ("=", 2),  # EQUALS
    (",", 0),  # COMMA
])
def test_get_symbol_single_punctuation(scanner_instance, char, expected_type):
    """Test that individual punctuation marks map to the exact integer types defined."""
    scanner_instance.skip_spaces = MagicMock()
    scanner_instance.advance = MagicMock()
    
    scanner_instance.current_character = char
    symbol = scanner_instance.get_symbol()
    
    assert symbol.type == expected_type
    scanner_instance.advance.assert_called_once()


def test_get_symbol_arrow_success(scanner_instance):
    """Verify that a dash followed by a '>' symbol returns an ARROW token."""
    scanner_instance.skip_spaces = MagicMock()
    
    # Mock advance to alter state midway through execution
    def side_effect():
        scanner_instance.current_character = ">"
    scanner_instance.advance = MagicMock(side_effect=side_effect)
    
    scanner_instance.current_character = "-"
    symbol = scanner_instance.get_symbol()
    
    assert symbol.type == scanner_instance.ARROW
    assert scanner_instance.advance.call_count == 2


def test_get_symbol_arrow_incomplete(scanner_instance):
    """Verify that an isolated dash fails gracefully, defaulting type safely."""
    scanner_instance.skip_spaces = MagicMock()
    
    def side_effect():
        scanner_instance.current_character = " "  # Not a '>'
    scanner_instance.advance = MagicMock(side_effect=side_effect)
    
    scanner_instance.current_character = "-"
    symbol = scanner_instance.get_symbol()
    
    assert symbol.type == scanner_instance.EOF
    assert scanner_instance.advance.call_count == 1


def test_get_symbol_eof(scanner_instance):
    """Verify that hitting the end of file sequence stops processing safely."""
    scanner_instance.skip_spaces = MagicMock()
    scanner_instance.current_character = ""
    
    symbol = scanner_instance.get_symbol()
    assert symbol.type == scanner_instance.EOF


def test_get_symbol_invalid_character(scanner_instance):
    """Ensure unexpected punctuation character safely advances without crashing."""
    scanner_instance.skip_spaces = MagicMock()
    scanner_instance.advance = MagicMock()
    scanner_instance.current_character = "$"  # Invalid grammar character
    
    symbol = scanner_instance.get_symbol()
    assert symbol.type is None
    scanner_instance.advance.assert_called_once()