import sys

from crossword import *
from operator import itemgetter

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable in self.domains:
            to_modify = []
            for word in self.domains[variable]:
                if variable.length == len(word):
                    to_modify.append(word)
            self.domains[variable] = to_modify

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        x_neigbours = self.crossword.neighbors(x)
        if y in x_neigbours:
            return False
        else:
            flag = False
            overlapping_character = self.crossword.overlaps[(x, y)]
            for y_value in self.domains[y]:
                for x_value in self.domains[x]:
                    if x_value[overlapping_character[0]] == y_value[overlapping_character[1]]:
                        self.domains[x].remove(x_value)
                        flag = True
                        break
            return flag

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if arcs is None:
            arcs = list()
            for i in self.crossword.variables:
                for j in self.crossword.variables:
                    try:
                        if self.crossword.overlaps[(i, j)]:
                            arcs.append((i, j))
                    except KeyError:
                        pass
        while len(arcs) > 0:
            x, y = arcs[0]
            arcs = arcs[1:]
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x) - y:
                    arcs.append((z, x))
        return True



    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.crossword.variables:
            try:
                if len(assignment[var]) < 1:
                    return False
            except KeyError:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for variable in assignment:
            if variable.length != len(assignment[variable]):
                return False
            for neighbouring in self.crossword.neighbors(variable):
                try:
                    overlap = self.crossword.overlaps[(variable, neighbouring)]
                    if assignment[variable][overlap[0]] != assignment[neighbouring][overlap[1]]:
                        return False
                except KeyError:
                    pass
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        var_words = self.domains[var]
        power = [0] * len(var_words)
        to_check = self.crossword.neighbors(var) - set(assignment.keys())
        for neighbouring in to_check:
            try:
                overlap = self.crossword.overlaps[(var, neighbouring)]
                for ind, var_word in enumerate(var_words):
                    for neig_word in self.domains[neighbouring]:
                        if var_word[overlap[0]] == neig_word[overlap[1]]:
                            power[ind] += 1
            except KeyError:
                pass
        return [x for _, x in sorted(zip(power, var_words), reverse=True)]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        unassigned = list(self.crossword.variables - set(assignment.keys()))
        remaining_values_in_its_domain = [len(self.domains[i]) for i in unassigned]  # minimum remaining value heuristic
        has_the_most_neighbors = [len(self.crossword.neighbors(i)) for i in unassigned]  # degree heuristic.
        to_sort = [[unassigned[i], remaining_values_in_its_domain[i], has_the_most_neighbors[i]] for i in range(len(unassigned))]
        s = sorted(to_sort, key=lambda e: (-e[1], e[2]), reverse=True) # '-' becuase we want minimum number of remaining values
        return s[0][0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        else:
            var = self.select_unassigned_variable(assignment)
            for value in self.order_domain_values(var, assignment):
                assignment[var] = value
                if self.consistent(assignment):
                    result = self.backtrack(assignment)
                    if result:
                        return result
                del assignment[var]
            return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
