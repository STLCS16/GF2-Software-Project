import pytest
from logsim import names
from names import Names # Assumes your class is in names.py


@pytest.fixture
def names_instance():
    """Fixture to provide a fresh instance of Names for each test."""
    return Names()


def test_unique_error_codes_generation(names_instance):
    first_batch = names_instance.unique_error_codes(3)
    assert list(first_batch) == [0, 1, 2]
    
    second_batch = names_instance.unique_error_codes(2)
    assert list(second_batch) == [3, 4]


def test_unique_error_codes_invalid_type(names_instance):
    with pytest.raises(TypeError):
        names_instance.unique_error_codes("three")

def test_lookup_adds_new_names(names_instance):
    ids = names_instance.lookup(["gate", "switch", "clock"])
    assert ids == [0, 1, 2]


def test_lookup_handles_existing_names(names_instance):
    names_instance.lookup(["gate", "switch"])
    ids = names_instance.lookup(["switch", "clock"])
    assert ids == [1, 2]


def test_lookup_empty_list(names_instance):
    assert names_instance.lookup([]) == []

def test_query_existing_name(names_instance):
    names_instance.lookup(["gate", "switch"])
    assert names_instance.query("switch") == 1


def test_query_non_existent_name(names_instance):
    names_instance.lookup(["gate"])
    assert names_instance.query("clock") is None


def test_get_name_string_valid_id(names_instance):
    names_instance.lookup(["gate", "switch"])
    assert names_instance.get_name_string(0) == "gate"
    assert names_instance.get_name_string(1) == "switch"


def test_get_name_string_out_of_bounds(names_instance):
    names_instance.lookup(["gate"])
    assert names_instance.get_name_string(99) is None


def test_get_name_string_invalid_types(names_instance):
    with pytest.raises(TypeError):
        names_instance.get_name_string("zero")
        
    with pytest.raises(ValueError):
        names_instance.get_name_string(-1)