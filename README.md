# battleship-solitaire
Project made for my Advanced Algorithms class. Features 20+ puzzles, manual solving, and three different solving algorithms.

- Backtracking
- Backtracking with Forward Hint Checking
- Genetic Algorithms

Run main.py to start and select a .bs file inside 6x6, 8x8, 10x10, 15x15. You can read the bs files to see the format for creating your own puzzles (they're just JSON)

To try the program, run main.py. Do not run genetic_algorithm.py as that is a module used by main.py. Click ”Select
Level” and select a valid ”.bs” file (short for battleship). These are just JSON text files with board size, hint locations
and row/column numbers.

Once loaded in you can solve the puzzle manually or click one of the green buttons to select a solver method. The red
outlined button on the bottom left is the active selection, you can click on the active button to enter erase mode which
will not allow you to erase hint pieces. **The checkboxes above these buttons has no clicking functionality**, it is
only meant to automatically check off ships once completed on the board. Numbers will outline in red if the row/column
has too many ships but NOT if there isn’t enough ships. This was done on purpose to not make manually solving it too
annoying.

During automatic solving, **user input will be disabled** but there is a bug where if you accidentally click reset during
execution the board will instantly reset as soon as solving is finished. During genetic algorithms, the genetic algorithms.py
script will execute 5 times and lock input the whole time. The only way to know if the next attempt has started inside
the GUI is that the checkboxes will briefly disappear. Apologies for my game being a little rough around the edges but I
prioritized the implementation of algorithms over usability of the tool.
During execution of GAs, you can also look at the console to see the generation count and average fitness of the current
generation.
