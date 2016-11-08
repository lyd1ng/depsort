# depsort
The idea behind this programme was it to make analysing c/c++ source code more easily.
The depsort programme builds a environment which allows it to edit the source code (using vim),
mark files and safe info texts for analysed files.
Furthermore it analyses the c/c++ files for locale include statements to simplify the decision
which file to analyse first. It does so by recursively scanning the current working directory
and all embedded c/cpp/h/hpp files.
If you mark a file or safe a additional info text the information will be safed within the file.
The changes are special c-style comments so that the workability should not be effected.
The marks "hidden", "normal", "analysed", "special" and "error" are valid marks and mapped to colours:

hidden   : not displayed

normal   : black

analysed : green

special  : blue

error    : red


The depsort programme provides following commands:
(Every command except "intern" can be abbreviated by using its first letter only)

show [code, dependencies, intern, info] file_name : Most should be selfe-explanatory.
                                                    "intern" shows the file as a tuple

mark file_name [hidden, normal, analysed, special, error] : Marks a file as specified

info file_name info_text : Safes info_text within the file specified by file_name

Incoming:
Using a vim server for editing multiple source code files.
