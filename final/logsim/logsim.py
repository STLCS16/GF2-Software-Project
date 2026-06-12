#!/usr/bin/env python3
"""Parse command line options and arguments for the Logic Simulator.

This script parses options and arguments specified on the command line, and
runs either the command line user interface or the graphical user interface.

Usage
-----
Show help: logsim.py -h
Command line user interface: logsim.py -c <file path>
Graphical user interface: logsim.py <file path>
"""
import getopt
import sys

import wx
import os

from logsim.names import Names
from logsim.devices import Devices
from logsim.network import Network
from logsim.monitors import Monitors
from logsim.scanner import Scanner
from logsim.parse import Parser
from logsim.userint import UserInterface
from logsim.gui import Gui


_ = wx.GetTranslation


def main(arg_list):
    """Parse the command line options and arguments specified in arg_list.

    Run either the command line user interface, the graphical user interface,
    or display the usage message.
    """
    usage_message = (_("Usage:\n"
                     "Show help: logsim.py -h\n"
                     "Command line user interface: logsim.py -c <file path>\n"
                     "Graphical user interface: logsim.py <file path>"))
    try:
        options, arguments = getopt.getopt(arg_list, "hc:")
    except getopt.GetoptError:
        print(_("Error: invalid command line arguments\n"))
        print(usage_message)
        sys.exit()

    # Initialise instances of the four inner simulator classes
    names = Names()
    devices = Devices(names)
    network = Network(names, devices)
    monitors = Monitors(names, devices, network)

    # names = None
    # devices = None
    # network = None
    # monitors = None

    for option, path in options:
        if option == "-h":  # print the usage message
            print(usage_message)
            sys.exit()
        elif option == "-c":  # use the command line user interface
            scanner = Scanner(path, names)
            parser = Parser(names, devices, network, monitors, scanner)
            if parser.parse_network():
                print("passed parser")
                # Initialise an instance of the userint.UserInterface() class
                userint = UserInterface(names, devices, network, monitors)
                userint.command_interface()

    if not options:  # no option given, use the graphical user interface

        if len(arguments) != 1:  # wrong number of arguments
            print("Error: one file path required\n")
            print(usage_message)
            sys.exit()

        [path] = arguments
        scanner = Scanner(path, names)
        parser = Parser(names, devices, network, monitors, scanner)
        if parser.parse_network():
            app = wx.App()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            base_dir = os.path.dirname(current_dir)

            lang_file_path = os.path.join(base_dir, "lang_pref.txt")

            lang_pref = "en"
            if os.path.exists(lang_file_path):
                with open(lang_file_path, "r") as f:
                    lang_pref = f.read().strip()

            if lang_pref == "fr":
                wx_lang = wx.LANGUAGE_FRENCH
            elif lang_pref == "zh_CN":
                wx_lang = wx.LANGUAGE_CHINESE_SIMPLIFIED
            else:
                wx_lang = wx.LANGUAGE_ENGLISH
            app.locale = wx.Locale(wx_lang)

            # Points to final/locale
            locale_dir = os.path.join(base_dir, 'locale')
            app.locale.AddCatalogLookupPathPrefix(locale_dir)
            app.locale.AddCatalog('logsim')
            
            gui = Gui("Logic Simulator", path, names, devices, network,
                      monitors)
            gui.Show(True)
            app.MainLoop()


if __name__ == "__main__":
    main(sys.argv[1:])
