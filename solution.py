assignments = []
# Valid for 9x9 grid; change rows and cols accordingly for other grids
rows = 'ABCDEFGHI'
cols = '123456789'


def assign_value(values, box, value):
    """
    Assigns a value to a given box. If it updates the board record it.

    Args:
        values : dict
            A values dictionary.
        box : string
            The box to edit in string form.
        value : string
            New value of the box.

    Returns:
        values : dict
            A dictionary with updated values.
    """
    # Don't waste memory appending when nothing has changed
    if values[box] == value:
        return values
    values[box] = value
    # Append tofinal assignments list if box is solved
    if len(value) == 1:
        assignments.append(values.copy())
    return values


def cross(A, B):
    """
    Cross product of elements in A and elements in B.

    Returns:
        A list containing the cross product of A and B
    """
    return [a+b for a in A for b in B]


boxes = cross(rows, cols)
row_units = [cross(r, cols) for r in rows]
column_units = [cross(rows, c) for c in cols]
square_units = [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for
                cs in ('123', '456', '789')]
diag = [[rs+cs for rs, cs in zip(rows, cols)]]
reverse_diag = [[rs+cs for rs, cs in zip(rows, cols[::-1])]]
unitlist = row_units + column_units + square_units + diag + reverse_diag
# Units that a particular box belongs to
units = dict((box, [unit for unit in unitlist if box in unit])
            for box in boxes)
# Peers of a box. Value of a box cannot appear in any peer
peers = dict((box, set(sum(units[box], [])) - set([box])) for box in boxes)


def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '123456789' for empties.

    Args:
        grid : string
            A grid in string form.
    Returns:
        grid : dict
            Keys are the boxes (e.g., 'A1').
            Values are the values in each box (e.g., '8').
            If the box has no value, then the value will be '123456789'.
    """
    # Change assertion for different-sized grids
    assert len(grid) == 81
    digits = '123456789'
    values = []
    for c in grid:
        if c == '.':
            values.append(digits)
        elif c in digits:
            values.append(c)
    # Sanity check that values is size it should be
    assert len(values) == 81
    return dict(zip(boxes, values))


def display(values):
    """
    Display the values as a 2-D grid.

    Args:
        values : dict
            The sudoku in dictionary form
    """
    width = 1+max(len(values[s]) for s in boxes)
    line = '+'.join(['-'*(width*3)]*3)
    for r in rows:
        print(''.join(values[r+c].center(width)+('|' if c in '36' else '')
                      for c in cols))
        if r in 'CF':
            print(line)
    return


def eliminate(values):
    """
    Go through all the boxes, and whenever there is a box with only one digit,
    eliminate this digit from the values of all its peers.

    Args:
        values : dict
            A sudoku in dictionary form.
    Returns:
        values : dict
            The resulting sudoku in dictionary form.
    """
    solved_values = [box for box in values.keys() if len(values[box]) == 1]
    for box in solved_values:
        digit = values[box]
        for peer in peers[box]:
            assign_value(values, peer, values[peer].replace(digit, ''))
    return values


def only_choice(values):
    """
    Finalize all values that are the only choice for a unit.
    Go through all the units, and whenever there is a unit with a value
    that only fits in one box (in that unit), assign the value to this box.

    Args:
        values : dict
            Sudoku in dictionary form.
    Returns:
        values : dict
            Resulting Sudoku in dictionary form after filling in only choices.
    """
    for unit in unitlist:
        for digit in '123456789':
            places = [box for box in unit if digit in values[box]]
            if len(places) == 1:
                assign_value(values, places[0], digit)
    return values


def naked_twins(values):
    """
    Two boxes in a unit are twins if they have two possible solutions, and they
    are both equal. E.g. Let's say A1: 45, G1: 45; A1 and G1 are naked twins
    for this column unit. Another box in this unit cannot have the values 4 or
    5. So we eliminate these two digits from all boxes in this unit.

    Args:
        values : dict
            Sudoku in dictionary form
    Returns:
        values : dict
            The values dictionary with the naked twins eliminated from peers.
    """
    for unit in unitlist:
        # Get all boxes with two possible solutions
        possible_twins = [box for box in unit if len(values[box]) == 2]
        # Iterate through the possible_twins list for all possible twin pairs
        for twin in possible_twins:
            for sec_twin in possible_twins:
                if (twin != sec_twin) and (values[twin] == values[sec_twin]):
                    # We have found a twin pair
                    twin_value = values[twin]
                    for box in unit:
                        # Remove these digits from all other boxes in the unit
                        if ((box !=twin) and (box !=sec_twin) and
                            (len(values[box]) >= 2)):
                            for digit in twin_value:
                                assign_value(values, box,
                                             values[box].replace(digit, ''))
    return values


def reduce_puzzle(values):
    """
    Iterate eliminate() and only_choice().
    If at some point, there is a box with no available values, return False.
    If the sudoku is solved, return the sudoku.
    If after an iteration of both functions, the sudoku remains the same,
    return the sudoku.

    Args:
        values : dict
            A sudoku in dictionary form.
    Returns:
        values : dict
            The resulting sudoku in dictionary form.
    """
    stalled = False
    while not stalled:
        # Check how many boxes have a determined value
        solved_values_before = len([box for box in values.keys()
                                    if len(values[box]) == 1])
        # Use the Eliminate Strategy
        values = eliminate(values)
        # Use the Only Choice Strategy
        values = only_choice(values)
        # Use the Naked Twins Strategy
        values = naked_twins(values)
        # Check how many boxes have a determined value, to compare
        solved_values_after = len([box for box in values.keys()
                                    if len(values[box]) == 1])
        # If no new values were added, stop the loop.
        stalled = solved_values_before == solved_values_after
        # Sanity check, return False if zero available values:
        if len([box for box in values.keys() if len(values[box]) == 0]):
            return False
    return values


def search(values):
    """
    Using depth-first search and propagation, try all possible values.

    Args:
        values : dict
            A sudoku in dictionary form.
    Returns:
        values : dict
            The resulting sudoku in dictionary form
    """
    # First, reduce the puzzle using the previous function
    values = reduce_puzzle(values)
    if values is False:
        return False  # Failed earlier
    if all(len(values[s]) == 1 for s in boxes):
        return values  # Solved!
    # Choose one of the unfilled squares with the fewest possibilities
    n, s = min((len(values[s]), s) for s in boxes if len(values[s]) > 1)
    # Now use recurrence to solve each one of the resulting sudokus, and
    for value in values[s]:
        new_sudoku = values.copy()
        new_sudoku[s] = value
        attempt = search(new_sudoku)
        if attempt:
            return attempt


def solve(grid):
    """
    Find the solution to a Sudoku grid.

    Args:
        grid : string
            A string representing a sudoku grid.
            Example: '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    Returns:
        grid : dict
            The dictionary representation of the final sudoku grid.
            False if no solution exists.
    """
    return search(grid_values(grid))


if __name__ == '__main__':
    diag_sudoku_grid = '2.............62....1....7...6..8...3...9...7...6..4...4....8....52.............3'
    display(solve(diag_sudoku_grid))
    #sudoku_grid = '4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......'
    #display(solve(sudoku_grid))
    try:
        from visualize import visualize_assignments
        visualize_assignments(assignments)

    except SystemExit:
        pass
    except:
        print('We could not visualize your board due to a pygame issue. Not a problem! It is not a requirement.')
