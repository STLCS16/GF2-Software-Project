import pytest
import sys
from unittest.mock import patch, mock_open, MagicMock

import logsim


@pytest.fixture
def mock_dependencies():
    with patch('logsim.Scanner') as mock_scanner, \
            patch('logsim.Parser') as mock_parser, \
            patch('logsim.UserInterface') as mock_userint, \
            patch('logsim.Gui') as mock_gui, \
            patch('logsim.wx') as mock_wx:

        instance_parser = mock_parser.return_value
        instance_parser.parse_network.return_value = True

        yield mock_scanner, mock_parser, mock_userint, mock_gui, mock_wx


def test_main_invalid_arguments():
    with patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            logsim.main(["-x", "invalid_flag"])
        mock_exit.assert_called_once()
        mock_print.assert_any_call("Error: invalid command line arguments\n")


def test_main_help_option():
    with patch('sys.exit') as mock_exit, patch('builtins.print') as mock_print:
        mock_exit.side_effect = SystemExit
        with pytest.raises(SystemExit):
            logsim.main(["-h"])
        mock_exit.assert_called_once()
        assert mock_print.call_count >= 1


def test_main_cli_mode_success(mock_dependencies):
    (mock_scanner, mock_parser, mock_userint,
     mock_gui, mock_wx) = mock_dependencies

    logsim.main(["-c", "test_circuit.txt"])

    mock_scanner.assert_called_once()
    assert mock_scanner.call_args[0][0] == "test_circuit.txt"
    mock_parser.assert_called_once()

    mock_userint.assert_called_once()
    instance_userint = mock_userint.return_value
    instance_userint.command_interface.assert_called_once()

    mock_gui.assert_not_called()


def test_main_cli_mode_parse_fails(mock_dependencies):
    (mock_scanner, mock_parser,
     mock_userint, mock_gui, mock_wx) = mock_dependencies

    instance_parser = mock_parser.return_value
    instance_parser.parse_network.return_value = False

    logsim.main(["-c", "test_circuit.txt"])

    mock_userint.assert_not_called()


def test_main_gui_mode_wrong_arg_count():
    with patch('sys.exit') as mock_exit, patch('builtins.print'):
        mock_exit.side_effect = SystemExit  # Force the mock to actually exit
        with pytest.raises(SystemExit):
            logsim.main(["file1.txt", "file2.txt"])
        mock_exit.assert_called_once()


def test_main_gui_mode_success_english(mock_dependencies):
    (mock_scanner, mock_parser, mock_userint,
     mock_gui, mock_wx) = mock_dependencies

    with patch('os.path.exists', return_value=False):
        logsim.main(["test_circuit.txt"])

    mock_wx.App.assert_called_once()
    mock_gui.assert_called_once()

    instance_gui = mock_gui.return_value
    instance_gui.Show.assert_called_once_with(True)

    mock_wx.Locale.assert_called_once_with(mock_wx.LANGUAGE_ENGLISH)


@pytest.mark.parametrize("lang_string, expected_wx_lang", [
    ("fr", "LANGUAGE_FRENCH"),
    ("zh_CN", "LANGUAGE_CHINESE_SIMPLIFIED"),
    ("es", "LANGUAGE_ENGLISH")
])
def test_main_gui_mode_localization(
        mock_dependencies,
        lang_string,
        expected_wx_lang):
    (mock_scanner, mock_parser, mock_userint,
     mock_gui, mock_wx) = mock_dependencies

    setattr(mock_wx, expected_wx_lang, f"MOCK_{expected_wx_lang}")

    with patch('os.path.exists', return_value=True), \
            patch('builtins.open', mock_open(read_data=lang_string)):

        logsim.main(["test_circuit.txt"])

    expected_constant = getattr(mock_wx, expected_wx_lang)
    mock_wx.Locale.assert_called_once_with(expected_constant)

    instance_app = mock_wx.App.return_value
    instance_app.locale.AddCatalogLookupPathPrefix.assert_called_once()
    instance_app.locale.AddCatalog.assert_called_once_with('logsim')

    instance_app.MainLoop.assert_called_once()
