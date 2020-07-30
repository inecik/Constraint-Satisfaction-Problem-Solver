# Constraint-Satisfaction-Problem
The package solves and represents constraint satisfaction problem by backtracking search and checking arc consistency with AC-3 algorithm. 

The usage is shown on an example, generating crossword puzzles.
Given the structure of a crossword puzzle (i.e., which squares of the grid are meant to be filled in with a letter), and a list of words to use, the problem becomes one of choosing which words should go in each vertical or horizontal sequence of squares. 
I can model this sort of problem as a constraint satisfaction problem. 
Each sequence of squares is one variable, for which we need to decide on its value (which word in the domain of possible words will fill in that sequence). 
As with many constraint satisfaction problems, these variables have both unary and binary constraints. 
The unary constraint on a variable is given by its length. 
The binary constraints on a variable are given by its overlap with neighboring variables. 
For this problem, I added the additional constraint that all words must be different: the same word should not be repeated multiple times in the puzzle.

Run "python generate.py data/structure1.txt data/words1.txt demo_output.png"
