#!/usr/bin/python2

import sys, os, re
from collections import namedtuple
from termcolor import colored

#define a file struct
FILE = namedtuple("file_t", "name path dependencies level mark")
#get the current working directory
ORIGIN = os.getcwd()
NAME = "DEPSORT"
#create a mark to color dictionary
COLOR_DICT =  {'0':'black', '1':'green', '2':'yellow', '3':'red'}

def get_files_in_dir(path):
    os.chdir(path)
    result = []
    entries = os.listdir(path)
    for e in entries:
        if os.path.isdir(e) == 0:
            result.append(e)
    os.chdir(ORIGIN)
    return result

def get_dirs_in_dir(path):
    os.chdir(path)
    result = []
    entries = os.listdir(path)
    for e in entries:
        if os.path.isdir(e):
            result.append(e)
    os.chdir(ORIGIN)
    return result

def get_mark(path):
    fd = open(path, "r")
    buf = fd.read()
    fd.close()
    index = buf.find("//" + NAME + ":")
    index2 = buf.find("\n", index)
    if index == -1 or index2 == -1: return "0"
    return buf[index + len(NAME) + 3 : index2]

def set_mark(name, mark):
    f = find_by_name(files, name)
    if f is None: return
    path = f.path
    fd_in = open(path, "r")
    fd_out = open(path+".tmp", "w")
    buf = fd_in.read()
    fd_in.close()
    index = buf.find("//" + NAME + ":")
    if index == -1:
        fd_out.write(buf)
        fd_out.write("//" + NAME + ":" + mark)
        fd_out.close()
    else:
        fd_out.write(buf[:index])
        fd_out.write("//" + NAME + ":" + mark)
        fd_out.write(buf[index + len(NAME) + 4:])
        fd_out.close()
    os.system("mv " + path + ".tmp " + path)

def analyze_file(path, stack):
    fd = open(path, "r")
    buf = fd.read()
    dependencies = re.findall(r"#include \".*\"", buf)
    level = len(dependencies)
    name = os.path.basename(path)
    stack.append("#include \"" + name + "\"")
    for d in dependencies:
        if d not in stack:
            level += analyze_file(os.path.dirname(path) + "/"  + d[10:-1], stack).level
    return FILE(name, path, dependencies, level, get_mark(path))

def analyze_dir(path):
    files_in_dir = get_files_in_dir(path)
    dirs_in_dir = get_dirs_in_dir(path)
    result = []
    for f in files_in_dir:
        result.append(analyze_file(path + "/" +  f, []))
    for d in dirs_in_dir:
        result += analyze_dir(path + "/" +d)
    return result

def print_colored(string, color):
    if color =="black" or None:
        print string
        return
    print colored(string, color)
    return

def find_by_name(files, name):
    for f in files:
        if f.name == name: return f
    return None

#MAIN
files= analyze_dir(ORIGIN)
files.sort(key=lambda x:x.level)
for i  in range(0, len(files)):
    print "(" + files[i].level.__str__() + "): ",
    print_colored(files[i].name, COLOR_DICT.get(files[i].mark))

while True:
    cmd = raw_input("Enter a command: ")
    cmd_list = cmd.split()

    if len(cmd_list) == 0: continue
    if len(cmd_list) >= 1:
        if cmd_list[0] == "help" or cmd_list[0] == "h":
            help()
            continue
        if cmd_list[0] == "refresh" or cmd_list[0] == "r":
            files= analyze_dir(ORIGIN)
            files.sort(key=lambda x:x.level)
            for i  in range(0, len(files)):
                print "(" + files[i].level.__str__() + "): ",
                print_colored(files[i].name, COLOR_DICT.get(files[i].mark))
                continue
        if cmd_list[0] == "quit" or cmd_list[0] == "q":
            exit()
    if len(cmd_list) >= 3:
        if cmd_list[0] == "show" or cmd_list[0] == "s":
            if cmd_list[1] == "dependencies" or cmd_list[1] == "d":
                print find_by_name(files, cmd_list[2]).dependencies
                continue
            if cmd_list[1] == "code" or cmd_list[1] == "c":
                os.system("vim " + cmd_list[2])
                continue
            if cmd_list[1] == "intern" or cmd_list[1] == "i":
                print find_by_name(files, cmd_list[2])
                continue
            print "show: Invalid option"
            continue
        if cmd_list[0] == "mark" or cmd_list[0] == "m":
            if int(cmd_list[2]) < 0 and int(cmd_list[2]) > 3:
                print "mark: invalid option"
                continue
            set_mark(cmd_list[1], cmd_list[2])
            continue
