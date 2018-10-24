#!/usr/bin/python

import os
import re
from collections import namedtuple
from termcolor import colored
import subprocess
import time

# define a file struct
FILE_STRUCT = namedtuple("file_t", "name path dependencies level mark info")
# get the current working directory
ORIGIN = os.getcwd()
NAME = "DEPSORT"
# Define the cmd to start a programme in a new console window
TERMINAL_CMD = "xterm -e"
# create a mark to color dictionary
COLOR_DICT = {
    'hidden': 'hidden',
    'normal': 'black',
    'analysed': 'green',
    'special': 'blue',
    'error': 'red'}


def get_files_in_dir(path):
    """
    Get all *.c, *.cpp, *.h or *.hpp in a directory
    """
    os.chdir(path)
    result = []
    entries = os.listdir(path)
    for e in entries:
        if os.path.isdir(e) == 0 and (e.endswith(".c") or e.endswith(
                ".cpp") or e.endswith(".h") or e.endswith(".hpp")):
            result.append(e)
    os.chdir(ORIGIN)
    return result


def get_dirs_in_dir(path):
    """
    Get all dirs within the dir at $path
    """
    os.chdir(path)
    result = []
    entries = os.listdir(path)
    for e in entries:
        if os.path.isdir(e):
            result.append(e)
    os.chdir(ORIGIN)
    return result


def get_mark(path):
    """
    Search for a mark with the form and return it as a string
    //[NAME]: [MARK]
    where [NAME] is the name specified at the top of this file
    and [MARK] is mark within this file
    """
    fd = open(path, "r")
    buf = fd.read()
    fd.close()
    index = buf.find("//" + NAME + ":")
    index2 = buf.find(";", index)
    if index == -1 or index2 == -1:
        return "0"
    return buf[index + len(NAME) + 3: index2]


def set_mark(name, mark):
    """
    Write the mark into a file named $name within the
    current working directory
    """
    f = find_by_name(files, name)
    if f is None:
        return
    path = f.path
    fd_in = open(path, "r")
    fd_out = open(path + ".tmp", "w")
    buf = fd_in.read()
    fd_in.close()
    index = buf.find("//" + NAME + ":")
    index2 = buf.find(";", index)
    if index == -1:
        """
        If the first index is -1 the file was never marked before,
        so the mark can be added at the very last of the file
        """
        fd_out.write(buf)
        fd_out.write("//" + NAME + ":" + mark + ";")
        fd_out.close()
    else:
        """
        Search for the mark and change it
        """
        if index2 == -1:
            """
            If index2 is -1 the mark is corrupted, the terminating
            semicolon is missing
            """
            print("Expecting semicolon in file: ",)
            print(path)
            fd_out.close()
            return
        """ Just change the mark """
        fd_out.write(buf[:index])
        fd_out.write("//" + NAME + ":" + mark + ";")
        fd_out.write(buf[index2 + 1:])
        fd_out.close()
    """ Overwrite old file and make the changes permanent """
    os.system("mv " + path + ".tmp " + path)


def get_info(path):
    """
    Read the info text saved within the file at $path
    """
    fd = open(path, "r")
    buf = fd.read()
    fd.close()
    index1 = buf.find("/*" + NAME + "_INFO:")
    index2 = buf.find("*/", index1)
    if index1 == -1 or index2 == -1:
        return ""
    return buf[index1 + len(NAME) + 8: index2]


def set_infos(name, infos):
    """
    Save an info text within the file named $name
    """
    f = find_by_name(files, name)
    if f is None:
        return
    path = f.path
    fd_in = open(path, "r")
    fd_out = open(path + ".tmp", "w")
    buf = fd_in.read()
    fd_in.close()
    index = buf.find("/*" + NAME + "_INFO:")
    index2 = buf.find("*/", index)
    if index == -1:
        """
        If index1 is -1 the file does not contain an info
        text yet. It can be added at the very last of the file
        """
        fd_out.write(buf)
        fd_out.write("/*" + NAME + "_INFO:")
        for i in infos:
            fd_out.write(i + " ")
        fd_out.write("*/")
        fd_out.close()
    else:
        if index2 == -1:
            """
            If index2 is -1 the terminating */ is missing
            """
            print("Expecting \"*/\" in file: ",)
            print(path)
            fd_out.close()
            return
        """
        Just add every element of infos as an info text within the file"
        """
        fd_out.write(buf[:index])
        fd_out.write("/*" + NAME + "_INFO:")
        for i in infos:
            fd_out.write(i + " ")
        fd_out.write("*/")
        fd_out.write(buf[index2 + 3:])
        fd_out.close()
    """ Overwrite old file and make the changes permanent """
    os.system("mv " + path + ".tmp " + path)


def analyze_file(path, stack):
    """
    Count the includes in the file at $path and add them to the stack.
    Then run analyze_file recursively for every included file.
    This way the real number of included files is computated.
    """
    fd = open(path, "r")
    buf = fd.read()
    """ Just checking for includes using "" instead of <> """
    dependencies = re.findall(r"#include \".*\"", buf)
    level = len(dependencies)
    name = os.path.basename(path)
    stack.append("#include \"" + name + "\"")
    for d in dependencies:
        if d not in stack:
            level += analyze_file(os.path.dirname(path) + "/" + d[10:-1], stack).level
    return FILE_STRUCT(
        name,
        path,
        dependencies,
        level,
        get_mark(path),
        get_info(path))


def analyze_dir(path):
    """
    Invoke analyze_file for every related code file within this
    directory and invoke analyze_dir recursivly for every sub-directory
    """
    files_in_dir = get_files_in_dir(path)
    dirs_in_dir = get_dirs_in_dir(path)
    result = []
    for f in files_in_dir:
        result.append(analyze_file(path + "/" + f, []))
    for d in dirs_in_dir:
        result += analyze_dir(path + "/" + d)
    return result


def print_files(files):
    """
    Print all files colored by their mark and their number of dependencies
    If the files is marked as "hidden" the file wont be printed at all
    """
    for i in range(0, len(files)):
        color = COLOR_DICT.get(files[i].mark)
        if color == "hidden":
            continue
        if color == "black" or None:
            print("(" + files[i].level.__str__() + "): " + files[i].name, color)
            continue
        print("(" + files[i].level.__str__() + "): " + colored(files[i].name, color))


def find_by_name(files, name):
    """
    Return a file by its name
    """
    for f in files:
        if f.name == name:
            return f
    return None


def check_vim_server():
    """
    Check for a running vim server with the name $NAME,
    where $NAME is defined gloabally
    """
    servers = subprocess.Popen(
        ["vim", "--serverlist"], stdout=subprocess.PIPE).communicate()[0].split("\n")
    return NAME in servers


# MAIN
files = analyze_dir(ORIGIN)
files.sort(key=lambda x: x.level)
print_files(files)

while True:
    cmd = input("Enter a command: ")
    cmd_list = cmd.split()

    if len(cmd_list) == 0:
        """
        If the user just hit enter
        """
        continue
    if len(cmd_list) >= 1:
        if cmd_list[0] == "refresh" or cmd_list[0] == "r":
            """
            The refresh command is used to make the changes made visible
            """
            files = analyze_dir(ORIGIN)
            files.sort(key=lambda x: x.level)
            print_files(files)
            continue
        if cmd_list[0] == "quit" or cmd_list[0] == "q":
            """
            Close the vim server and leave this programme
            """
            os.system(
                "vim --servername " + NAME + " --remote-send \":qa<CR>\"")
            exit()
    if len(cmd_list) >= 3:
        if cmd_list[0] == "show" or cmd_list[0] == "s":
            """
            Display the type of information specified by the next argument
            """
            if cmd_list[1] == "dependencies" or cmd_list[1] == "d":
                """
                Lists all dependencies
                """
                print(find_by_name(files, cmd_list[2]).dependencies)
                continue
            if cmd_list[1] == "code" or cmd_list[1] == "c":
                """
                Opens the code in the vim server instance
                """
                if not check_vim_server():
                    os.system(TERMINAL_CMD + " vim --servername " + NAME + "&")
                    time.sleep(0.25)
                os.system(
                    "vim --servername " + NAME + " --remote-tab " + cmd_list[2])
                continue
            if cmd_list[1] == "intern":
                """
                Displays the intern representation of a file
                """
                print(find_by_name(files, cmd_list[2]))
                continue
            if cmd_list[1] == "info" or cmd_list[1] == "i":
                """
                Displays the informations strings saved within this file
                """
                print(find_by_name(files, cmd_list[2]).info)
                continue
            print("show: Invalid option")
            continue
        if cmd_list[0] == "mark" or cmd_list[0] == "m":
            """
            Set the mark of a file
            """
            if cmd_list[2] not in COLOR_DICT.keys():
                """
                Only marks specified in the COLOR_DICT are valid
                """
                print("mark: invalid option")
                continue
            set_mark(cmd_list[1], cmd_list[2])
            continue
        if cmd_list[0] == "info" or cmd_list[0] == "i":
            """
            Saves all following parameters as info texts
            """
            set_infos(cmd_list[1], cmd_list[2:])
