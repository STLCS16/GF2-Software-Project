#!/usr/bin/env python3
"""Preliminary exercises for Part IIA Project GF2."""
import sys


def open_file(path):
    try:
        file = open(path, 'r') 
        return file
    except FileNotFoundError:
        print(f"Error! The file '{sys.path}' could not be found.")
        sys.exit()


def get_next_character(input_file):
    """Read and return the next character in input_file."""
    return input_file.read(1)

def get_next_non_whitespace_character(input_file):
    """Seek and return the next non-whitespace character in input_file."""
    while True:
        cha = input_file.read(1)
        if cha == "" or not cha.isspace():
            return cha

def get_next_number(input_file):
    """Seek the next number in input_file.
    Return the number (or None) and the next non-numeric character.
    """
    cha = input_file.read(1)
    while cha != "" and not cha.isdigit():
        cha = input_file.read(1)
    if cha == "":
        return (None, "")
    number_string = ""
    while cha != "" and cha.isdigit():
        number_string += cha         
        cha = input_file.read(1)  

    return (number_string, cha)


def get_next_name(input_file):
    """Seek the next name string in input_file.

    Return the name string (or None) and the next non-alphanumeric character.
    """
    cha = input_file.read(1)
    while cha != "" and not cha.isalpha():
        cha = input_file.read(1)
    if cha =="":
        return (None, "")
    name_string =""
    while cha != "" and cha.isalnum():
        name_string += cha
        cha = input_file.read(1)
    return (name_string, cha)

def main():
    """Preliminary exercises for Part IIA Project GF2."""
    arguments = sys.argv[1:] #ignore the first argument (the script itself) but take the rest of terms
    if len(arguments) != 1:
        print("Error! One command line argument is required.")
        sys.exit()

    else:
        print("\nNow opening file...")
        path = arguments[0]
        print(f"Path provided: {path}")
        input_file = open_file(path)

        print("\nNow reading file...")
        # Print out all the characters in the file, until the end of file
        while True:
            cha = get_next_character(input_file)
            if cha == "":
                break
            print(cha, end="")

        print("\nNow skipping spaces...")
        # Print out all the characters in the file, without spaces
        input_file.seek(0) #move pointer back to the beginning of the file
        while True:
            cha = get_next_non_whitespace_character(input_file)
            if cha == "":
                break
            print(cha, end="")

        print("\nNow reading numbers...")
        # Print out all the numbers in the file
        input_file.seek(0)
        while True:
            num, next_char = get_next_number(input_file)
            if num is None:
                break
            print(num, end=" ")

        print("\nNow reading names...")
        # Print out all the names in the file
        input_file.seek(0)
        while True:
            name,next_cha = get_next_name(input_file)
            if name is None:
                break
            print(name, end=" ")


        print("\nNow censoring bad names...")
        # Print out only the good names in the file
        # name = MyNames()
        # bad_name_ids = [name.lookup("Terrible"), name.lookup("Horrid"),
        #                 name.lookup("Ghastly"), name.lookup("Awful")]

if __name__ == "__main__":
    main()
