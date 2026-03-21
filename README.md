# Processor Design Task 2

This project implements Task 2 of the CSC 4210/6210 Computer Architecture processor design project.

## Overview

The program accepts a truth table for a Boolean function, generates the canonical Boolean expression, simplifies it, and validates the simplified result against the original truth table.

## File

- `Processor(2).py`: Task 2 implementation

## Features

- Accepts the number of input variables from the command line
- Accepts a truth table from interactive input or a file
- Validates the truth table
- Generates canonical `SOP` or `POS`
- Lists minterms or maxterms
- Displays a Karnaugh Map for 2 to 4 variables
- Shows grouping used for simplification
- Prints the simplified Boolean expression
- Validates the simplified result with `PASS` or `FAIL`

## Requirements

- Python 3

## Run With Interactive Input

```bash
python3 'Processor(2).py' 3 --form SOP
```

Enter each row in this format:

```text
<bits> <output>
```

Example:

```text
000 0
001 1
010 1
011 0
100 1
101 0
110 1
111 1
```

## Run With File Input

```bash
python3 'Processor(2).py' 3 --form POS --file truth_table.txt
```

Example `truth_table.txt`:

```text
000 0
001 1
010 1
011 0
100 1
101 0
110 1
111 1
```

You can also provide separated bits:

```text
0 0 0 0
0 0 1 1
0 1 0 1
0 1 1 0
1 0 0 1
1 0 1 0
1 1 0 1
1 1 1 1
```

## Program Output

The program prints:

1. Truth table
2. Canonical equation
3. Minterm or maxterm list
4. K-Map
5. K-Map grouping
6. Simplified Boolean expression
7. Validation result
