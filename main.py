import pygame
import copy
import tkinter as tk
import json
import tkinter.filedialog
import tkinter.messagebox
import genetic_algorithm
import time
from itertools import permutations
#boilerplate from https://github.com/tasdikrahman/pygame-boilerplate/blob/master/template.py

WIDTH = 500
HEIGHT = 700
FPS = 30

# Define Colors 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

## initialize pygame and create window
pygame.init()
pygame.mixer.init()  ## For sound
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Battleship Solitaire")
clock = pygame.time.Clock()     ## For syncing the FPS

# initial variables
size = 0
board = None
reset = None
disable_user_input = False
PADDING = 100
CELL_SIZE = 0
BUTTON_PADDING = 5  # padding for the text on the buttons
active = "w"  # active cell type
row_numbers = []
col_numbers = []
TYPES_OF_SHIPS = ("s", "ss", "ms", "us", "ds", "ls", "rs", "ps")
'''Types of ships:
    s: ship
    
    - None below can be replaced (hint pieces) -
    ss: single ship 
    ms: middle ship 
    us: upper ship
    ds: down ship
    ls: left ship
    rs: right ship
    ps: "permanent" ship (cannot be replaced but is not a middleship, is used for constraint propagation locking the board)'''
TYPES_OF_WATER = ("w", "sw")
'''Types of water:
    w: water
    sw: starting water (cannot be replaced)'''


def type_of_ship(board, row, col):
    indetermined_type = None
    temp_row = row - 1
    # check all up cells
    while temp_row >= 0 and board[temp_row][col] != "w" and board[temp_row][col] != "sw":
        if "s" in board[temp_row][col] and board[temp_row][col] != "sw":
            indetermined_type = "vertical"
        if board[temp_row][col] == "e":
            break
        temp_row -= 1
    # check all down cells
    temp_row = row + 1
    while temp_row < size and board[temp_row][col] != "w" and board[temp_row][col] != "sw":
        if "s" in board[temp_row][col] and board[temp_row][col] != "sw":
            indetermined_type = "vertical"
        if board[temp_row][col] == "e":
            break
        temp_row += 1
    # check all left cells
    temp_col = col - 1
    while temp_col >= 0 and board[row][temp_col] != "w" and board[row][temp_col] != "sw":
        if "s" in board[row][temp_col] and board[row][temp_col] != "sw":
            if indetermined_type == "vertical":
                return "invalid"
            indetermined_type = "horizontal"
        if board[row][temp_col] == "e":
            break
        temp_col -= 1
    # check all right cells
    temp_col = col + 1
    while temp_col < size and board[row][temp_col] != "w" and board[row][temp_col] != "sw":
        if "s" in board[row][temp_col] and board[row][temp_col] != "sw":
            if indetermined_type == "vertical":
                return "invalid"
            indetermined_type = "horizontal"
        if board[row][temp_col] == "e":
            break
        temp_col += 1
    return indetermined_type

checked_ships = {} #track ship segments already marked

def surrounded(board, row, col):
    if row > 0 and board[row-1][col] != "w" and board[row-1][col] != "sw":
        return False
    if row < size-1 and board[row+1][col] != "w" and board[row+1][col] != "sw":
        return False
    if col > 0 and board[row][col-1] != "w" and board[row][col-1] != "sw":
        return False
    if col < size-1 and board[row][col+1] != "w" and board[row][col+1] != "sw":
        return False
    return True

# returns (true, length of ship) if the ship is complete, otherwise returns false
def is_ship_complete(board, row, col, type):
    if type == "vertical":
        temp_row = row - 1
        while temp_row >= 0 and board[temp_row][col] != "w" and board[temp_row][col] != "sw":
            if board[temp_row][col] == "e" or type_of_ship(board, temp_row, col) == "invalid":
                return False
            if board[temp_row][col] == "us":
                temp_row -= 1
                break
            temp_row -= 1
        lowest = temp_row
        temp_row = row + 1
        while temp_row < size and board[temp_row][col] != "w" and board[temp_row][col] != "sw":
            if board[temp_row][col] == "e" or type_of_ship(board, temp_row, col) == "invalid":
                return False
            if board[temp_row][col] == "ds":
                temp_row += 1
                break
            temp_row += 1
        highest = temp_row
        for i in range(lowest+1, highest):
            if i != row:
                checked_ships[(i, col)] = highest - lowest - 1
        return True, highest - lowest - 1
    elif type == "horizontal":
        temp_col = col - 1
        while temp_col >= 0 and board[row][temp_col] != "w" and board[row][temp_col] != "sw":
            if board[row][temp_col] == "e" or type_of_ship(board, row, temp_col) == "invalid":
                return False
            if board[row][temp_col] == "ls":
                temp_col -= 1
                break
            temp_col -= 1
        lowest = temp_col
        temp_col = col + 1
        while temp_col < size and board[row][temp_col] != "w" and board[row][temp_col] != "sw":
            if board[row][temp_col] == "e" or type_of_ship(board, row, temp_col) == "invalid":
                return False
            if board[row][temp_col] == "rs":
                temp_col += 1
                break
            temp_col += 1
        highest = temp_col
        for i in range(lowest+1, highest):
            if i != col:
                checked_ships[(row, i)] = highest - lowest - 1
        return True, highest - lowest - 1

def mark_ship(length):
    try:
        for i in range(1, size):
            if not checkboxes[f"{length}-{i}"]["state"]:
                checkboxes[f"{length}-{i}"]["state"] = True
                break
    except KeyError:
        return
def prompt_file():
    """Create a Tk file dialog and cleanup when finished"""
    top = tk.Tk()
    top.withdraw()  # hide window
    file_name = tk.filedialog.askopenfilename(parent=top, filetypes=[("Battleship files", "*.bs*")])
    top.destroy()
    return file_name
def show_message(message):
    """ Display a message on the screen for 2 seconds"""
    font = pygame.font.SysFont(None, 48)
    text = font.render(message, True, (255, 255, 255))
    rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
    
    screen.fill((0, 0, 0))
    screen.blit(text, rect)
    pygame.display.flip()
    pygame.time.delay(2000)  # Show the message for 2 seconds
    

# function to draw the level selection menu
def draw_menu(screen: pygame.Surface):
    pygame.event.pump()
    # draw battleship solitaire title in center of screen
    font = pygame.font.Font(None, 36)
    text = font.render("Battleship Solitaire", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
    screen.blit(text, text_rect)
    # draw level selection button on screen near bottom
    rect = pygame.Rect(WIDTH//2-50, HEIGHT//2, 100, 50)
    pygame.draw.rect(screen, GREEN, rect)
    font = pygame.font.Font(None, 24)
    text = font.render("Select Level", True, BLACK)
    text_rect = text.get_rect(center=rect.center)
    screen.blit(text, text_rect)

ship_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

def reset_ship_count():
    global ship_count
    ship_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
# function to draw the grid
def draw_grid(board, screen):
    for row in range(size):
        for col in range(size):
            rect = pygame.Rect(PADDING/2 + col * CELL_SIZE, PADDING/2 + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if board[row][col] == "e":
                pygame.draw.rect(screen, BLACK, rect, 1)  # Draw empty cell with white border
            elif board[row][col] == "w" or board[row][col] == "sw":
                pygame.draw.rect(screen, BLUE, rect) # draw blue cell
            elif board[row][col] == "s" or board[row][col] == "ps":
                # get type of ship
                type = type_of_ship(board, row, col)
                if type == "invalid":
                    pygame.draw.rect(screen, BLACK, rect, 1)
                    inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                    inflated_rect.center = rect.center
                    pygame.draw.rect(screen, RED, inflated_rect)
                elif type == None:
                    if surrounded(board, row, col) and board[row][col] not in set(TYPES_OF_SHIPS) - {"ps", "s"}: # if boat is surrounded by water and not a starting boat
                        # draw ship as a circle if completely surrounded by water
                        pygame.draw.rect(screen, BLACK, rect, 1)
                        pygame.draw.circle(screen, BLACK, rect.center, CELL_SIZE//4)
                        ship_count[1] += 1
                        mark_ship(1)
                    else:
                        pygame.draw.rect(screen, BLACK, rect, 1)
                        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                        inflated_rect.center = rect.center
                        pygame.draw.rect(screen, BLACK, inflated_rect)
                elif type == "vertical":
                    # if water (or nothing) is above or below the ship, draw the ship with a rounded border facing the water
                    if (row > 0 and board[row-1][col] in TYPES_OF_WATER) or row == 0:
                        pygame.draw.rect(screen, BLACK, rect, 1)
                        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                        inflated_rect.center = rect.center
                        pygame.draw.rect(screen, BLACK, inflated_rect, border_top_left_radius=CELL_SIZE//4, border_top_right_radius=CELL_SIZE//4)
                    elif (row + 1 < size and board[row+1][col] in TYPES_OF_WATER) or row == size-1:
                        pygame.draw.rect(screen, BLACK, rect, 1)
                        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                        inflated_rect.center = rect.center
                        pygame.draw.rect(screen, BLACK, inflated_rect, border_bottom_left_radius=CELL_SIZE//4, border_bottom_right_radius=CELL_SIZE//4)
                    else: 
                        pygame.draw.rect(screen, BLACK, rect, 1)
                        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                        inflated_rect.center = rect.center
                        pygame.draw.rect(screen, BLACK, inflated_rect)
                elif type == "horizontal":
                    # if water (or nothing) is to the left or right of the ship, draw the ship with a rounded border facing the water
                    if col > 0 and board[row][col-1] in TYPES_OF_WATER or col == 0:
                        pygame.draw.rect(screen, BLACK, rect, 1)
                        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                        inflated_rect.center = rect.center
                        pygame.draw.rect(screen, BLACK, inflated_rect, border_top_left_radius=CELL_SIZE//4, border_bottom_left_radius=CELL_SIZE//4)
                    elif col+1 < size and board[row][col+1] in TYPES_OF_WATER or col == size-1:
                        pygame.draw.rect(screen, BLACK, rect, 1)
                        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                        inflated_rect.center = rect.center
                        pygame.draw.rect(screen, BLACK, inflated_rect, border_top_right_radius=CELL_SIZE//4, border_bottom_right_radius=CELL_SIZE//4)
                    else:
                        pygame.draw.rect(screen, BLACK, rect, 1)
                        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                        inflated_rect.center = rect.center
                        pygame.draw.rect(screen, BLACK, inflated_rect)
                    result = is_ship_complete(board, row, col, type)
                    if result:
                        if (row, col) not in checked_ships:
                            length = result[1]
                            checked_ships[((row, col))] = length
                            try:
                                ship_count[length] += 1
                            except KeyError:
                                ship_count[length] = 1000000 # if the ship is too long, set it to a large number to indicate that it is invalid
                            mark_ship(length)
            elif board[row][col] == "ms":
                pygame.draw.rect(screen, BLACK, rect, 1)
                inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                inflated_rect.center = rect.center
                pygame.draw.rect(screen, BLACK, inflated_rect)
            elif board[row][col] == "us":
                pygame.draw.rect(screen, BLACK, rect, 1)
                inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                inflated_rect.center = rect.center
                pygame.draw.rect(screen, BLACK, inflated_rect, border_top_left_radius=CELL_SIZE//4, border_top_right_radius=CELL_SIZE//4)
            elif board[row][col] == "ds":
                pygame.draw.rect(screen, BLACK, rect, 1)
                inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                inflated_rect.center = rect.center
                pygame.draw.rect(screen, BLACK, inflated_rect, border_bottom_left_radius=CELL_SIZE//4, border_bottom_right_radius=CELL_SIZE//4)
            elif board[row][col] == "ls":
                pygame.draw.rect(screen, BLACK, rect, 1)
                inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                inflated_rect.center = rect.center
                pygame.draw.rect(screen, BLACK, inflated_rect, border_top_left_radius=CELL_SIZE//4, border_bottom_left_radius=CELL_SIZE//4)
            elif board[row][col] == "rs":
                pygame.draw.rect(screen, BLACK, rect, 1)
                inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
                inflated_rect.center = rect.center
                pygame.draw.rect(screen, BLACK, inflated_rect, border_top_right_radius=CELL_SIZE//4, border_bottom_right_radius=CELL_SIZE//4)
            elif board[row][col] == "ss":
                pygame.draw.rect(screen, BLACK, rect, 1)
                pygame.draw.circle(screen, BLACK, rect.center, CELL_SIZE//4)
                mark_ship(1)
                ship_count[1] += 1
            if board[row][col] in TYPES_OF_SHIPS:
                type = type_of_ship(board, row, col)
                result = is_ship_complete(board, row, col, type)
                if result:
                    if (row, col) not in checked_ships:
                        length = result[1]
                        checked_ships[(row, col)] = length
                        try:
                            ship_count[length] += 1
                        except KeyError:
                            ship_count[length] = 1000000 # if the ship is too long, set it to a large number to indicate that it is invalid
                        mark_ship(length)
                
    # draw row and column numbers
    for i in range(size):
        font = pygame.font.Font(None, 36)
        # render number as red if number of ships in the row/column exceeds the row/column number
        if (len(list(cell for cell in board[i] if cell in TYPES_OF_SHIPS)) > row_numbers[i]) :
            text = font.render(str(row_numbers[i]), True, RED)
        else:
            text = font.render(str(row_numbers[i]), True, BLACK)
        text_rect = text.get_rect(center=(PADDING/4, PADDING/2 + i * CELL_SIZE + CELL_SIZE//2))
        screen.blit(text, text_rect)
        if (len(list(cell for cell in [board[j][i] for j in range(size)] if cell in TYPES_OF_SHIPS)) > col_numbers[i]) :
            text = font.render(str(col_numbers[i]), True, RED)
        else:
            text = font.render(str(col_numbers[i]), True, BLACK)
        text_rect = text.get_rect(center=(PADDING/2 + i * CELL_SIZE + CELL_SIZE//2, PADDING/4))
        screen.blit(text, text_rect)
        
checkboxes = {}

def clear_checkboxes():
    for key, value in checkboxes.items():
        value["state"] = False

def draw_ship_manifest(screen, size):
    if size == 6:
        ships = [
            (3, 1),  # 3-ship with 1 checkbox
            (2, 2),  # 2-ship with 2 checkboxes
            (1, 3),  # 1-ship with 3 checkboxes
        ]

        for i, (num_boxes, num_checkboxes) in enumerate(ships):
            # Draw the ship
            for j in range(num_boxes):
                rect = pygame.Rect(
                    CELL_SIZE + j * (CELL_SIZE // 2 + 10),
                    (size + 1) * CELL_SIZE + CELL_SIZE * (0.75 * i),
                    CELL_SIZE // 2,
                    CELL_SIZE // 2,
                )
                if j == 0 and num_boxes != 1:  # First box (rounded left corners)
                    pygame.draw.rect(
                        screen,
                        BLACK,
                        rect,
                        border_top_left_radius=CELL_SIZE // 4,
                        border_bottom_left_radius=CELL_SIZE // 4,
                    )
                elif j == num_boxes - 1 and num_boxes != 1:  # Last box (rounded right corners)
                    pygame.draw.rect(
                        screen,
                        BLACK,
                        rect,
                        border_top_right_radius=CELL_SIZE // 4,
                        border_bottom_right_radius=CELL_SIZE // 4,
                    )
                elif num_boxes == 1:  # Single box (circle)
                    pygame.draw.circle(screen, BLACK, rect.center, CELL_SIZE // 4)
                else:  # Middle boxes
                    pygame.draw.rect(screen, BLACK, rect)

            # Draw the checkboxes
            for k in range(num_checkboxes):
                rect = pygame.Rect(
                    CELL_SIZE + (num_boxes + k) * (CELL_SIZE // 2 + 10),
                    (size + 1) * CELL_SIZE + CELL_SIZE * (0.75 * i),
                    CELL_SIZE // 2,
                    CELL_SIZE // 2,
                )
                checkbox_key = f"{num_boxes}-{k + 1}"
                if checkbox_key not in checkboxes:
                    pygame.draw.rect(screen, BLACK, rect, 1)
                    checkboxes[checkbox_key] = {"rect": rect, "state": False}
                else:
                    if checkboxes[checkbox_key]["state"]:
                        pygame.draw.rect(screen, GREEN, rect)
                    else:
                        pygame.draw.rect(screen, BLACK, rect, 1)
    elif size == 8:
        ships = [
            (4, 1),  
            (3, 2),  
            (2, 3),  
            (1, 3),  
        ]

        for i, (num_boxes, num_checkboxes) in enumerate(ships):
            # Draw the ship
            for j in range(num_boxes):
                rect = pygame.Rect(
                    CELL_SIZE + j * (CELL_SIZE // 2 + 10),
                    CELL_SIZE // 2 + (size + 1) * CELL_SIZE + CELL_SIZE * (0.75 * i),
                    CELL_SIZE // 2,
                    CELL_SIZE // 2,
                )
                if j == 0 and num_boxes != 1:  # First box (rounded left corners)
                    pygame.draw.rect(
                        screen,
                        BLACK,
                        rect,
                        border_top_left_radius=CELL_SIZE // 4,
                        border_bottom_left_radius=CELL_SIZE // 4,
                    )
                elif j == num_boxes - 1 and num_boxes != 1:  # Last box (rounded right corners)
                    pygame.draw.rect(
                        screen,
                        BLACK,
                        rect,
                        border_top_right_radius=CELL_SIZE // 4,
                        border_bottom_right_radius=CELL_SIZE // 4,
                    )
                elif num_boxes == 1:  # Single box (circle)
                    pygame.draw.circle(screen, BLACK, rect.center, CELL_SIZE // 4)
                else:  # Middle boxes
                    pygame.draw.rect(screen, BLACK, rect)

            # Draw the checkboxes
            for k in range(num_checkboxes):
                rect = pygame.Rect(
                    CELL_SIZE + (num_boxes + k) * (CELL_SIZE // 2 + 10),
                    CELL_SIZE // 2 + (size + 1) * CELL_SIZE + CELL_SIZE * (0.75 * i),
                    CELL_SIZE // 2,
                    CELL_SIZE // 2,
                )
                checkbox_key = f"{num_boxes}-{k + 1}"
                if checkbox_key not in checkboxes:
                    pygame.draw.rect(screen, BLACK, rect, 1)
                    checkboxes[checkbox_key] = {"rect": rect, "state": False}
                else:
                    if checkboxes[checkbox_key]["state"]:
                        pygame.draw.rect(screen, GREEN, rect)
                    else:
                        pygame.draw.rect(screen, BLACK, rect, 1)
    elif size == 10:
        ships = [
            (4, 1),
            (3, 2),
            (2, 3),
            (1, 4)
        ]
        for i, (num_boxes, num_checkboxes) in enumerate(ships):
            # Draw the ship
            for j in range(num_boxes):
                rect = pygame.Rect(
                    CELL_SIZE + j * (CELL_SIZE // 2 + 10),
                    CELL_SIZE // 2 + (size + 1) * CELL_SIZE + CELL_SIZE * (0.75 * i),
                    CELL_SIZE // 2,
                    CELL_SIZE // 2,
                )
                if j == 0 and num_boxes != 1:  # First box (rounded left corners)
                    pygame.draw.rect(
                        screen,
                        BLACK,
                        rect,
                        border_top_left_radius=CELL_SIZE // 4,
                        border_bottom_left_radius=CELL_SIZE // 4,
                    )
                elif j == num_boxes - 1 and num_boxes != 1:  # Last box (rounded right corners)
                    pygame.draw.rect(
                        screen,
                        BLACK,
                        rect,
                        border_top_right_radius=CELL_SIZE // 4,
                        border_bottom_right_radius=CELL_SIZE // 4,
                    )
                elif num_boxes == 1:  # Single box (circle)
                    pygame.draw.circle(screen, BLACK, rect.center, CELL_SIZE // 4)
                else:  # Middle boxes
                    pygame.draw.rect(screen, BLACK, rect)

            # Draw the checkboxes
            for k in range(num_checkboxes):
                rect = pygame.Rect(
                    CELL_SIZE + (num_boxes + k) * (CELL_SIZE // 2 + 10),
                    CELL_SIZE // 2 + (size + 1) * CELL_SIZE + CELL_SIZE * (0.75 * i),
                    CELL_SIZE // 2,
                    CELL_SIZE // 2,
                )
                checkbox_key = f"{num_boxes}-{k + 1}"
                if checkbox_key not in checkboxes:
                    pygame.draw.rect(screen, BLACK, rect, 1)
                    checkboxes[checkbox_key] = {"rect": rect, "state": False}
                else:
                    if checkboxes[checkbox_key]["state"]:
                        pygame.draw.rect(screen, GREEN, rect)
                    else:
                        pygame.draw.rect(screen, BLACK, rect, 1)
    elif size == 15:
        ships = [
            (5, 1),
            (4, 2),
            (3, 3),
            (2, 4),
            (1, 5)
        ]
        for i, (num_boxes, num_checkboxes) in enumerate(ships):
            # Draw the ship
            for j in range(num_boxes):
                rect = pygame.Rect(
                    CELL_SIZE + j * (CELL_SIZE // 2 + 10),
                    2*CELL_SIZE + (size + 1) * CELL_SIZE + CELL_SIZE * (0.75 * i),
                    CELL_SIZE // 2,
                    CELL_SIZE // 2,
                )
                if j == 0 and num_boxes != 1:  # First box (rounded left corners)
                    pygame.draw.rect(
                        screen,
                        BLACK,
                        rect,
                        border_top_left_radius=CELL_SIZE // 4,
                        border_bottom_left_radius=CELL_SIZE // 4,
                    )
                elif j == num_boxes - 1 and num_boxes != 1:  # Last box (rounded right corners)
                    pygame.draw.rect(
                        screen,
                        BLACK,
                        rect,
                        border_top_right_radius=CELL_SIZE // 4,
                        border_bottom_right_radius=CELL_SIZE // 4,
                    )
                elif num_boxes == 1:  # Single box (circle)
                    pygame.draw.circle(screen, BLACK, rect.center, CELL_SIZE // 4)
                else:  # Middle boxes
                    pygame.draw.rect(screen, BLACK, rect)

            # Draw the checkboxes
            for k in range(num_checkboxes):
                rect = pygame.Rect(
                    CELL_SIZE + (num_boxes + k) * (CELL_SIZE // 2 + 10),
                    2*CELL_SIZE + (size + 1) * CELL_SIZE + CELL_SIZE * (0.75 * i),
                    CELL_SIZE // 2,
                    CELL_SIZE // 2,
                )
                checkbox_key = f"{num_boxes}-{k + 1}"
                if checkbox_key not in checkboxes:
                    pygame.draw.rect(screen, BLACK, rect, 1)
                    checkboxes[checkbox_key] = {"rect": rect, "state": False}
                else:
                    if checkboxes[checkbox_key]["state"]:
                        pygame.draw.rect(screen, GREEN, rect)
                    else:
                        pygame.draw.rect(screen, BLACK, rect, 1)
        

def draw_buttons(screen, active):
    # draw water button
    rect = pygame.Rect(PADDING/2, HEIGHT-(PADDING/2.75), PADDING/3, PADDING/3)
    if active == "w":
        pygame.draw.rect(screen, RED, rect, 3)
        pygame.draw.circle(screen, BLUE, rect.center, PADDING//10)
    else:
        pygame.draw.rect(screen, BLACK, rect, 1)
        pygame.draw.circle(screen, BLUE, rect.center, PADDING//10)
    
    # draw ship button
    rect = pygame.Rect(PADDING/2+2*PADDING/3, HEIGHT-(PADDING/2.75), PADDING/3, PADDING/3)
    if active == "s":
        pygame.draw.rect(screen, RED, rect, 3)
        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
        inflated_rect.center = rect.center  # Center the inflated rect within the original rect
        pygame.draw.rect(screen, BLACK, inflated_rect)
    else:
        pygame.draw.rect(screen, BLACK, rect, 1)
        inflated_rect = rect.inflate(-rect.width//2, -rect.height//2)
        inflated_rect.center = rect.center  # Center the inflated rect within the original rect
        pygame.draw.rect(screen, BLACK, inflated_rect)
        
    # draw backtracking algorithm selection button
    pygame.draw.rect(screen, GREEN, pygame.Rect((WIDTH/2)-(PADDING/2), HEIGHT-(PADDING/3)-(PADDING/2.5), PADDING, PADDING/3))
    font = pygame.font.Font(None, 24)
    text = font.render("Backtrack", True, BLACK)
    screen.blit(text, ((WIDTH/2)-(PADDING/2)+BUTTON_PADDING, HEIGHT-(PADDING/3)-(PADDING/2.5)+BUTTON_PADDING))
    
    # draw constraint prop. button
    pygame.draw.rect(screen, GREEN, pygame.Rect((WIDTH/2)-(PADDING/2), HEIGHT-(PADDING/2.5), PADDING, PADDING/3))
    font = pygame.font.Font(None, 24)
    text = font.render("Backtrack+", True, BLACK)
    screen.blit(text, ((WIDTH/2)-(PADDING/2)+BUTTON_PADDING, HEIGHT-(PADDING/2.5)+BUTTON_PADDING))
    
    # draw genetic algorithm button
    pygame.draw.rect(screen, GREEN, pygame.Rect((WIDTH/2)-(PADDING/2), HEIGHT-(PADDING/3)*2-(PADDING/2.5), PADDING, PADDING/3))
    font = pygame.font.Font(None, 24)
    text = font.render("GA", True, BLACK)
    screen.blit(text, ((WIDTH/2)-(PADDING/2)+BUTTON_PADDING, HEIGHT-(PADDING/3)*2-(PADDING/2.5)+BUTTON_PADDING, PADDING, PADDING/3))

    # draw reset button
    pygame.draw.rect(screen, RED, pygame.Rect((WIDTH)-(PADDING*1.5), HEIGHT-(PADDING/2.5), PADDING, PADDING/3))
    font = pygame.font.Font(None, 36)
    text = font.render("Reset", True, BLACK)
    screen.blit(text, ((WIDTH)-(PADDING*1.5)+BUTTON_PADDING*3.5, HEIGHT-(PADDING/2.5)+BUTTON_PADDING))

def is_solved(board, row_numbers, col_numbers):
    # # check if all ships are placed
    if not (all([x["state"] for x in checkboxes.values()])):
        return False
    # check if all row numbers are satisfied
    for row in range(size):
        row_number = row_numbers[row]
        count = 0
        for col in range(size):
            if board[row][col] in TYPES_OF_SHIPS:
                count += 1
        if count != row_number:
            return False
    # check if all column numbers are satisfied
    for col in range(size):
        col_number = col_numbers[col]
        count = 0
        for row in range(size):
            if board[row][col] in TYPES_OF_SHIPS:
                count += 1
        if count != col_number:
            return False
    return True

def invalid_ms_config(type, board, row, col):
    if type == "w":
        # check if there is a middle ship next to the given cell
        # if water is connected to it on the opposite plane return true
        # if another ship is connected to it on the opposite side return true
        # if the middle ship is on an edge of the board and the water is on the opposite plane as the edge return true
        # else return false
        if row > 0 and board[row-1][col] == "ms":
            if col > 0 and board[row-1][col-1] in TYPES_OF_WATER:
                return True
            elif col < size-1 and board[row-1][col+1] in TYPES_OF_WATER:
                return True
            if row > 1 and board[row-2][col] in TYPES_OF_SHIPS:
                return True
            if col == size-1 or col == 0:
                return True
        if row < size-1 and board[row+1][col] == "ms":
            if col > 0 and board[row+1][col-1] in TYPES_OF_WATER:
                return True
            elif col < size-1 and board[row+1][col+1] in TYPES_OF_WATER:
                return True
            if row < size-2 and board[row+2][col] in TYPES_OF_SHIPS:
                return True
            if col == size-1 or col == 0:
                return True
        if col > 0 and board[row][col-1] == "ms":
            if row > 0 and board[row-1][col-1] in TYPES_OF_WATER:
                return True
            elif row < size-1 and board[row+1][col-1] in TYPES_OF_WATER:
                return True
            if col > 1 and board[row][col-2] in TYPES_OF_SHIPS:
                return True
            if row == size-1 or row == 0:
                return True
        if col < size-1 and board[row][col+1] == "ms":
            if row > 0 and board[row-1][col+1] in TYPES_OF_WATER:
                return True
            elif row < size-1 and board[row+1][col+1] in TYPES_OF_WATER:
                return True
            if col < size-2 and board[row][col+2] in TYPES_OF_SHIPS:
                return True
            if row == size-1 or row == 0:
                return True
        return False
    else:
        # check if there is a middle ship next to the given cell
        # if ship is connected to it on the opposite plane return true
        # if water is connected to it on the opposite side return true
        # else return false
        if row > 0 and board[row-1][col] == "ms":
            if col > 0 and board[row-1][col-1] in TYPES_OF_SHIPS:
                return True
            elif col < size-1 and board[row-1][col+1] in TYPES_OF_SHIPS:
                return True
            if row > 1 and board[row-2][col] in TYPES_OF_WATER:
                return True
        if row < size-1 and board[row+1][col] == "ms":
            if col > 0 and board[row+1][col-1] in TYPES_OF_SHIPS:
                return True
            elif col < size-1 and board[row+1][col+1] in TYPES_OF_SHIPS:
                return True
            if row < size-2 and board[row+2][col] in TYPES_OF_WATER:
                return True
        if col > 0 and board[row][col-1] == "ms":
            if row > 0 and board[row-1][col-1] in TYPES_OF_SHIPS:
                return True
            elif row < size-1 and board[row+1][col-1] in TYPES_OF_SHIPS:
                return True
            if col > 1 and board[row][col-2] in TYPES_OF_WATER:
                return True
        if col < size-1 and board[row][col+1] == "ms":
            if row > 0 and board[row-1][col+1] in TYPES_OF_SHIPS:
                return True
            elif row < size-1 and board[row+1][col+1] in TYPES_OF_SHIPS:
                return True
            if col < size-2 and board[row][col+2] in TYPES_OF_WATER:
                return True
        return False

def is_valid_move(board, row, col, cell, row_numbers, col_numbers, last_placeable): 
    if cell == "s":
        if row_numbers[row] == 0 or col_numbers[col] == 0:
            return False
        if row > 0 and board[row-1][col] in TYPES_OF_SHIPS and (type_of_ship(board, row, col) != "vertical" or board[row-1][col] == "ss" or board[row-1][col] == "ds"):
            return False
        if col > 0 and board[row][col-1] in TYPES_OF_SHIPS and (type_of_ship(board, row, col) != "horizontal" or board[row][col-1] == "ss" or board[row][col-1] == "rs"):
            return False
        if row < size-1 and board[row+1][col] in TYPES_OF_SHIPS and (type_of_ship(board, row, col) != "vertical" or board[row+1][col] == "ss" or board[row+1][col] == "us"):
            return False
        if col < size-1 and board[row][col+1] in TYPES_OF_SHIPS and (type_of_ship(board, row, col) != "horizontal" or board[row][col+1] == "ss" or board[row][col+1] == "ls"):
            return False
        if row > 0 and col > 0 and board[row-1][col-1] in TYPES_OF_SHIPS:
            return False
        if row > 0 and col < size-1 and board[row-1][col+1] in TYPES_OF_SHIPS:
            return False
        if row < size-1 and col > 0 and board[row+1][col-1] in TYPES_OF_SHIPS:
            return False
        if row < size-1 and col < size-1 and board[row+1][col+1] in TYPES_OF_SHIPS:
            return False
        # if row has too many ships
        if sum([1 for cell in board[row] if cell in TYPES_OF_SHIPS]) >= row_numbers[row]:
            return False
        # if col has too many ships
        if sum([1 for row in board if row[col] in TYPES_OF_SHIPS]) >= col_numbers[col]:
            return False
        # if row doesn't have enough ships (or more than one away) and this is the last placeable cell in the row
        if col == last_placeable[row]:
            if sum([1 for cell in board[row] if cell in TYPES_OF_SHIPS]) < row_numbers[row]-1:
                return False
        # if ship is next to middle ship where adding it would make it invalid
        if invalid_ms_config("s", board, row, col):
            return False
        # if size is 15 and the board has an invalid number of ships or an invalid length, return false
        if size == 15:
            if ship_count[1] > 5 or ship_count[2] > 4 or ship_count[3] > 3 or ship_count[4] > 2 or ship_count[5] > 1 or 1000000 in ship_count.values():
                return False
        # if size is 10 and the board has an invalid number of ships or an invalid length, return false
        if size == 10:
            if ship_count[1] > 4 or ship_count[2] > 3 or ship_count[3] > 2 or ship_count[4] > 1 or 1000000 in ship_count.values():
                return False
        # if size is 8 and the board has an invalid number of ships or an invalid length, return false
        if size == 8:
            if ship_count[1] > 3 or ship_count[2] > 3 or ship_count[3] > 2 or ship_count[4] > 1 or 1000000 in ship_count.values():
                return False
        # if size is 6 and the board has an invalid number of ships or an invalid length, return false
        if size == 6:
            if ship_count[1] > 3 or ship_count[2] > 2 or ship_count[3] > 1 or 1000000 in ship_count.values():
                return False
        return True        
    if cell == "w":
        # is cell is the last placeable cell in the row and there are not enough ships in the row, return false
        if col == last_placeable[row]:
            if sum([1 for cell in board[row] if cell in TYPES_OF_SHIPS]) < row_numbers[row]:
                return False
        if row > 0 and board[row-1][col] == "us":
            return False
        if col > 0 and board[row][col-1] == "ls":
            return False
        if row < size-1 and board[row+1][col] == "ds":
            return False
        if col < size-1 and board[row][col+1] == "rs":
            return False
        # if water is next to middle ship where adding it would make it invalid (middleship has a ship connected on the other side)
        if invalid_ms_config("w", board, row, col):
            return False
        return True
    
def naive_backtracking(board, screen, row_numbers, col_numbers):
    def solve(board, screen, row_numbers, col_numbers, row, col, last_placeable):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        clear_checkboxes()
        reset_ship_count()
        checked_ships.clear()
        draw_grid(board, screen)
        draw_ship_manifest(screen, size)
        draw_buttons(screen, active)
        pygame.display.flip()
        pygame.event.pump()
        #pygame.time.delay(100)
        screen.fill(WHITE)
        if col == 0 and row == size:  # If we finished all rows, check the board
            if is_solved(board, row_numbers, col_numbers):
                print('Solved!')
                return True, board
            return False, None
        
        next_row = row + 1 if col == size - 1 else row
        next_col = 0 if col == size - 1 else col + 1
        if board[row][col] not in ("e", "w", "s"):
            return solve(board, screen, row_numbers, col_numbers, next_row, next_col, last_placeable)
        for cell in ("s", "w"):
            if is_valid_move(board, row, col, cell, row_numbers, col_numbers, last_placeable):
                board[row][col] = cell
                if solve(board, screen, row_numbers, col_numbers, next_row, next_col, last_placeable)[0]:
                    return True, board
                board[row][col] = "e"
        return False, None
    
    # precompute the last placeable cell for each row
    last_placeable = [0] * size
    for i, row in enumerate(board):
        for cell in range(size-1, 0, -1):
            if row[cell] == "e":
                last_placeable[i] = cell
                break       
    result = solve(board, screen, row_numbers, col_numbers, 0, 0, last_placeable)
    # returns True, board if solved, else returns False, None (this is so the board can be updated in the main loop)
    return result

def ship_filling(partial_solution):
    # for ls,rs,us,ds: we can add a ship segment and place water around the known parts of the ship
    for row in range(size):
        for col in range(size):
            if partial_solution[row][col] == "ls":
                if col > 0:
                    partial_solution[row][col-1] = "w"
                if col > 0 and row > 0:
                    partial_solution[row-1][col-1] = "w"
                if col > 0 and row < size-1:
                    partial_solution[row+1][col-1] = "w"
                if row > 0:
                    partial_solution[row-1][col] = "w"
                if row < size-1:
                    partial_solution[row+1][col] = "w"
                if col < size-1 and row > 0:
                    partial_solution[row-1][col+1] = "w"
                if col < size-1 and row < size-1:
                    partial_solution[row+1][col+1] = "w"
                if col < size-2 and row > 0:
                    partial_solution[row-1][col+2] = "w"
                if col < size-2 and row < size-1:
                    partial_solution[row+1][col+2] = "w"
                if col < size-1:
                    partial_solution[row][col+1] = "s"
            elif partial_solution[row][col] == "rs":
                if col < size-1:
                    partial_solution[row][col+1] = "w"
                if col < size-1 and row > 0:
                    partial_solution[row-1][col+1] = "w"
                if col < size-1 and row < size-1:
                    partial_solution[row+1][col+1] = "w"
                if col > 1 and row > 0:
                    partial_solution[row-1][col-2] = "w"
                if col > 1 and row < size-1:
                    partial_solution[row+1][col-2] = "w"
                if row > 0:
                    partial_solution[row-1][col] = "w"
                if row < size-1:
                    partial_solution[row+1][col] = "w"
                if col > 0 and row > 0:
                    partial_solution[row-1][col-1] = "w"
                if col > 0 and row < size-1:
                    partial_solution[row+1][col-1] = "w"
                if col > 0:
                    partial_solution[row][col-1] = "s"
            elif partial_solution[row][col] == "us":
                if row > 0:
                    partial_solution[row-1][col] = "w"
                if row > 0 and col > 0:
                    partial_solution[row-1][col-1] = "w"
                if row > 0 and col < size-1:
                    partial_solution[row-1][col+1] = "w"
                if col > 0:
                    partial_solution[row][col-1] = "w"
                if col < size-1:
                    partial_solution[row][col+1] = "w"
                if col > 0 and row < size-1:
                    partial_solution[row+1][col-1] = "w"
                if col < size-1 and row < size-1:
                    partial_solution[row+1][col+1] = "w"
                if col > 0 and row < size-2:
                    partial_solution[row+2][col-1] = "w"
                if col < size-1 and row < size-2:
                    partial_solution[row+2][col+1] = "w"
                if row < size-1:
                    partial_solution[row+1][col] = "s"
            elif partial_solution[row][col] == "ds":
                if row < size-1:
                    partial_solution[row+1][col] = "w"
                if row < size-1 and col > 0:
                    partial_solution[row+1][col-1] = "w"
                if row < size-1 and col < size-1:
                    partial_solution[row+1][col+1] = "w"
                if col > 0:
                    partial_solution[row][col-1] = "w"
                if col < size-1:
                    partial_solution[row][col+1] = "w"
                if col > 0 and row > 0:
                    partial_solution[row-1][col-1] = "w"
                if col < size-1 and row > 0:
                    partial_solution[row-1][col+1] = "w"
                if col > 0 and row > 0:
                    partial_solution[row-2][col-1] = "w"
                if col < size-1 and row > 0:
                    partial_solution[row-2][col+1] = "w"
                if row > 0:
                    partial_solution[row-1][col] = "s"
            elif partial_solution[row][col] == "ms":
                # add diagonal water to the middle ship
                if row > 0 and col > 0:
                    partial_solution[row-1][col-1] = "w"
                if row > 0 and col < size-1:
                    partial_solution[row-1][col+1] = "w"
                if row < size-1 and col > 0:
                    partial_solution[row+1][col-1] = "w"
                if row < size-1 and col < size-1:
                    partial_solution[row+1][col+1] = "w"
            elif partial_solution[row][col] == "ss":
                # add water around the single ship
                if row > 0:
                    partial_solution[row-1][col] = "w"
                if row < size-1:
                    partial_solution[row+1][col] = "w"
                if col > 0:
                    partial_solution[row][col-1] = "w"
                if col < size-1:
                    partial_solution[row][col+1] = "w"
                if row > 0 and col > 0:
                    partial_solution[row-1][col-1] = "w"
                if row > 0 and col < size-1:
                    partial_solution[row-1][col+1] = "w"
                if row < size-1 and col > 0:
                    partial_solution[row+1][col-1] = "w"
                if row < size-1 and col < size-1:
                    partial_solution[row+1][col+1] = "w"
def lock_cells(board, row_numbers, col_numbers):
    for row in range(size):
        for col in range(size):
            if board[row][col] == "w":
                board[row][col] = "sw"
            if board[row][col] == "s":
                type = type_of_ship(board, row, col)
                if type == None:
                    if surrounded(board, row, col):
                        board[row][col] = "ss"
                    else:
                        board[row][col] = "ps"
                elif type == "vertical":
                    if (row > 0 and board[row-1][col] in TYPES_OF_WATER) or row == 0:
                        board[row][col] = "us"
                    elif (row + 1 < size and board[row+1][col] in TYPES_OF_WATER) or row == size-1:
                        board[row][col] = "ds"
                    else: 
                        board[row][col] = "ps"
                elif type == "horizontal":
                    if col > 0 and board[row][col-1] in TYPES_OF_WATER or col == 0:
                        board[row][col] = "ls"
                    elif col+1 < size and board[row][col+1] in TYPES_OF_WATER or col == size-1:
                        board[row][col] = "rs"
                    else:
                        board[row][col] = "ps"
    return board
def constraint_propagation(board, screen, row_numbers, col_numbers):
    partial_solution = copy.deepcopy(board)
    # go cell by cell and look for a ship, fill in water around the ships
    ship_filling(partial_solution)
    # keep going through rows and columns until no more ships or water can be placed
    change_made = True
    while change_made:
        change_made = False
        for row in range(size):
            row_number = row_numbers[row]
            # if row is filled, skip over it
            if all([cell != "e" for cell in partial_solution[row]]):
                continue
            # check if the row has exactly the number of ships needed
            if sum([1 for cell in partial_solution[row] if cell in TYPES_OF_SHIPS]) == row_number:
                for col in range(size):
                    if partial_solution[row][col] not in TYPES_OF_SHIPS:
                        partial_solution[row][col] = "w"
                change_made = True
            # check if the row has the right amount of empty cells to place the ships
            if sum([1 for cell in partial_solution[row] if cell == "e"]) == row_number - sum([1 for cell in partial_solution[row] if cell in TYPES_OF_SHIPS]):
                for col in range(size):
                    if partial_solution[row][col] == "e":
                        partial_solution[row][col] = "s"
                change_made = True
        for col in range(size):
            col_number = col_numbers[col]
            # if column is filled, skip over it
            if all([partial_solution[row][col] != "e" for row in range(size)]):
                continue
            # check if the column has exactly the number of ships needed
            if sum([1 for row in range(size) if partial_solution[row][col] in TYPES_OF_SHIPS]) == col_number:
                for row in range(size):
                    if partial_solution[row][col] not in TYPES_OF_SHIPS:
                        partial_solution[row][col] = "w"
                change_made = True
            # check if the column has the right amount of empty cells to place the ships
            if sum([1 for row in range(size) if partial_solution[row][col] == "e"]) == col_number - sum([1 for row in range(size) if partial_solution[row][col] in TYPES_OF_SHIPS]):
                for row in range(size):
                    if partial_solution[row][col] == "e":
                        partial_solution[row][col] = "s"
                change_made = True
        # go through each middle ship and check for water next to it
        for row in range(size):
            for col in range(size):
                if partial_solution[row][col] == "ms":
                    # check if there is water next to the middle ship
                    if row > 0 and partial_solution[row-1][col] in TYPES_OF_WATER:
                        # check if change was already made in the last iteration
                        if row < size-1 and partial_solution[row+1][col] == "e":
                            partial_solution[row+1][col] = "w"
                            change_made = True
                        if col > 0 and partial_solution[row][col-1] == "e":
                            partial_solution[row][col-1] = "s"
                            change_made = True
                        if col < size-1 and partial_solution[row][col+1] == "e":
                            partial_solution[row][col+1] = "s"
                            change_made = True
                        
                    if row < size-1 and partial_solution[row+1][col] in TYPES_OF_WATER:
                        if row > 0 and partial_solution[row-1][col] == "e":
                            partial_solution[row-1][col] = "w"
                            change_made = True
                        if col > 0 and partial_solution[row][col-1] == "e":
                            partial_solution[row][col-1] = "s"
                            change_made = True
                        if col < size-1 and partial_solution[row][col+1] == "e":
                            partial_solution[row][col+1] = "s"
                            change_made = True
                    if col > 0 and partial_solution[row][col-1] in TYPES_OF_WATER:
                        if col < size-1 and partial_solution[row][col+1] == "e":
                            partial_solution[row][col+1] = "w"
                            change_made = True
                        if row < size-1 and partial_solution[row+1][col] == "e":
                            partial_solution[row+1][col] = "s"
                            change_made = True
                        if row > 0 and partial_solution[row-1][col] == "e":
                            partial_solution[row-1][col] = "s"
                            change_made = True
                    if col < size-1 and partial_solution[row][col+1] in TYPES_OF_WATER:
                        if col > 0 and partial_solution[row][col-1] == "e":
                            partial_solution[row][col-1] = "w"
                            change_made = True
                        if row < size-1 and partial_solution[row+1][col] == "e":
                            partial_solution[row+1][col] = "s"
                            change_made = True
                        if row > 0 and partial_solution[row-1][col] == "e":
                            partial_solution[row-1][col] = "s"
                            change_made = True

    # once we have a partial solution, lock the cells that are already filled in and continue with naive backtracking
    partial_solution = lock_cells(partial_solution, row_numbers, col_numbers)
    isSolved, solutionBoard = naive_backtracking(partial_solution, screen, row_numbers, col_numbers)
    if isSolved:
        # update the board in the main loop
        board = solutionBoard
        return True, board
    
# function to check if the mouse is over the solve button
def is_mouse_over_solve_button(mouse_pos):
    solve_button_rect = pygame.Rect((WIDTH/2)-(PADDING/2), HEIGHT-(PADDING/2.5), PADDING, PADDING/3)
    return solve_button_rect.collidepoint(mouse_pos)
def is_mouse_over_backtrack_button(mouse_pos):
    backtrack_button_rect = pygame.Rect((WIDTH/2)-(PADDING/2), HEIGHT-(PADDING/3)-(PADDING/2.5), PADDING, PADDING/3)
    return backtrack_button_rect.collidepoint(mouse_pos)
def is_mouse_over_ga_button(mouse_pos):
    ga_button_rect = pygame.Rect((WIDTH/2)-(PADDING/2), HEIGHT-(PADDING/3)*2-(PADDING/2.5), PADDING, PADDING/3)
    return ga_button_rect.collidepoint(mouse_pos)
# function to check if the mouse is over the water button
def is_mouse_over_water_button(mouse_pos):
    water_button_rect = pygame.Rect(PADDING/2, HEIGHT-(PADDING/2.75), PADDING/3, PADDING/3)
    return water_button_rect.collidepoint(mouse_pos)
# function to check if the mouse is over the ship button
def is_mouse_over_ship_button(mouse_pos):
    ship_button_rect = pygame.Rect(PADDING/2+2*PADDING/3, HEIGHT-(PADDING/2.75), PADDING/3, PADDING/3)
    return ship_button_rect.collidepoint(mouse_pos)
# function to check if the mouse is over the reset button
def is_mouse_over_reset_button(mouse_pos):
    reset_button_rect = pygame.Rect((WIDTH)-(PADDING*1.5), HEIGHT-(PADDING/2.5), PADDING, PADDING/3)
    return reset_button_rect.collidepoint(mouse_pos)
# function to check if the mouse is over the level selection button
def is_mouse_over_level_button(mouse_pos):
    level_button_rect = pygame.Rect(WIDTH//2-50, HEIGHT//2, 100, 50)
    if not level:
        return level_button_rect.collidepoint(mouse_pos)
## Game loop
level = None
running = True
while running:
    #1 Process input/events
    clock.tick(FPS)     ## will make the loop run at the same speed all the time
    clear_checkboxes()
    checked_ships.clear()
    
    for event in pygame.event.get():        # gets all the events which have occured till now and keeps tab of them.
        ## listening for the the X button at the top
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and not disable_user_input:
            if is_mouse_over_solve_button(pygame.mouse.get_pos()):
                if level:
                    start = time.time()
                    print("Solving with Constraint Propagation")
                    board = copy.deepcopy(reset)
                    disable_user_input = True
                    screen.fill(WHITE)
                    result = constraint_propagation(board, screen, row_numbers, col_numbers)
                    time_taken = time.time() - start
                    print("Time taken: " + str(time_taken) + " seconds")
                    file_name = "/".join(level.split("/")[:8] + ["times"] + level.split("/")[8:]) + "-results.txt"
                    with open(file_name, "a") as f:
                        f.write("Algorithm: Constraint Propagation\n")
                        f.write("Time taken: " + str(time_taken) + " seconds\n\n")
                    disable_user_input = False
                    if result:
                        board = result[1]
            if is_mouse_over_backtrack_button(pygame.mouse.get_pos()):
                if level:
                    start = time.time()
                    print("Solving with Backtracking")
                    board = copy.deepcopy(reset)
                    disable_user_input = True
                    screen.fill(WHITE)
                    result = naive_backtracking(board, screen, row_numbers, col_numbers)
                    time_taken = time.time() - start
                    print("Time taken: " + str(time_taken) + " seconds")
                    file_name = "/".join(level.split("/")[:8] + ["times"] + level.split("/")[8:]) + "-results.txt"
                    with open(file_name, "a") as f:
                        f.write("Algorithm: Backtracking\n")
                        f.write("Time taken: " + str(time_taken) + " seconds\n\n")
                    disable_user_input = False
                    if result:
                        board = result[1]
            if is_mouse_over_ga_button(pygame.mouse.get_pos()):
                if level:
                    print("Solving with Genetic Algorithm")
                    start = time.time()
                    # try ga 5 times and take the best result
                    results = []
                    disable_user_input = True
                    counter = 0
                    for i in range(5):
                        board = copy.deepcopy(reset)
                        screen.fill(WHITE)
                        result = genetic_algorithm.solve(board, screen, row_numbers, col_numbers, draw_grid, draw_ship_manifest)
                        results.append(result)
                        print("Fitness of best solution: " + str(result[2]))
                        board = result[1]
                        counter += 1
                        if result[2] == 0:
                            break
                    time_taken = time.time() - start
                    print("Time taken: " + str(time_taken) + " seconds")
                    file_name = "/".join(level.split("/")[:8] + ["times"] + level.split("/")[8:]) + "-results.txt"
                    with open(file_name, "a") as f:
                        f.write("Algorithm: GA\n")
                        f.write("Time taken: " + str(time_taken) + " seconds\n")
                        f.write("Number of attempts: " + str(counter) + "\n")
                        f.write("Fitness of best solution: " + str(min(results, key=lambda x: x[2])[2]) + "\n\n")
                        
                    disable_user_input = False
                    # take the best result
                    best_result = min(results, key=lambda x: x[2])
                    board = best_result[1]
            if is_mouse_over_water_button(pygame.mouse.get_pos()) and not disable_user_input:
                if level:
                    if active == "w":
                        active = "e"
                    else:
                        active = "w"
            if is_mouse_over_ship_button(pygame.mouse.get_pos()):
                if level:
                    if active == "s":
                        active = "e"
                    else:
                        active = "s"
            if is_mouse_over_reset_button(pygame.mouse.get_pos()):
                if level:
                    board = copy.deepcopy(reset)
                    checked_ships.clear()
                    checkboxes.clear()
            if is_mouse_over_level_button(pygame.mouse.get_pos()):
                level = prompt_file()
                if level:
                    print("Level selected: " + level)

    #2 Draw/render
    screen.fill(WHITE)
    
    # draw level selection menu
    if not level:
        level = draw_menu(screen)
        
    
    # draw puzzle board
    else:
        if not board:
            # set up the initial board
            with open(level, "r") as f:
                level_data = json.load(f)
            size = level_data["size"]
            board = [["e" for i in range(size)] for j in range(size)]
            PADDING = 100
            CELL_SIZE = (WIDTH-PADDING) // size
            BUTTON_PADDING = 5  # padding for the text on the buttons
            active = "w"  # active cell type
            last_toggled_cell = None
            # Populate board
            for key, value in level_data["board"].items():
                row, col = map(int, key.split(","))
                board[row][col] = value
            row_numbers = level_data["row_numbers"]
            col_numbers = level_data["col_numbers"]
            print(row_numbers)
            print(col_numbers)
            '''
                SW: Starting Water
                MS: Middle Ship
                US: Ship end facing up
                DS: Ship end facing down
                LS: Ship end facing left
                RS: Ship end facing right   
                SS: Single Ship (Circle)
                
                None of these pieces can be changed
            '''
            reset = copy.deepcopy(board)
        # check if the mouse button is held down for drawing on the grid
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] and not disable_user_input:  # Left mouse button is held down
            mouse_pos = pygame.mouse.get_pos()
            # check if the mouse is over the grid
            for row in range(size):
                for col in range(size):
                    #if the cell is not a ship that is given at the start
                    if not ("s" in board[row][col] and board[row][col] != "s"):
                        rect = pygame.Rect(PADDING/2 + col * CELL_SIZE, PADDING/2 + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        if rect.collidepoint(mouse_pos):
                            board[row][col] = active
            
        draw_grid(board, screen)
        
        draw_ship_manifest(screen, size)
    
        draw_buttons(screen, active)

    ## Done after drawing everything to the screen
    pygame.display.flip()       

pygame.quit()