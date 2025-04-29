import copy
import random
import pygame
class Ship:
    def __init__(self, length, orientation, start_row, start_col):
        self.length = length
        self.orientation = orientation  # 'horizontal' or 'vertical'
        self.start_row = start_row
        self.start_col = start_col

def place_ships(board, best_solution):
    """
    Draw the best solution on the screen.
    """
    for ship in best_solution:
        place_ship(board, ship)
    for row in range(len(board)):
        for col in range(len(board)):
            if board[row][col] == "e":
                board[row][col] = "sw"
def place_ship(board, ship):
    if ship.orientation == 'horizontal':
        for i in range(ship.length):
            board[ship.start_row][ship.start_col + i] = "ms"
        board[ship.start_row][ship.start_col] = "ls"
        board[ship.start_row][ship.start_col + ship.length - 1] = "rs"
    else:
        for i in range(ship.length):
            board[ship.start_row + i][ship.start_col] = "ms"
        board[ship.start_row][ship.start_col] = "us"
        board[ship.start_row + ship.length - 1][ship.start_col] = "ds"
    if ship.length == 1:
        board[ship.start_row][ship.start_col] = "ss"
         

def evaluate_individual(individual, board, hints, row_numbers, col_numbers):
    """
    Evaluate the fitness of an individual by checking how many ships are placed correctly.
    The fitness is a sum of penalties incurred for overlapping ships, touching ships, number of incorrect row and columns.
    Overlapping : 10 point per ship
    Touching : 100 point per ship
    Breaking a hint: 1000 points per hint broken
    Row or column doesn't match the number: 50 point per row/column
    """
    board = [["e" for _ in range(len(board))] for _ in range(len(board))]
    fitness = 0
    for ship in individual:
        # Check for overlapping ships
        if ship.orientation == 'horizontal':
            for i in range(ship.length):
                if board[ship.start_row][ship.start_col + i] != "e":
                    fitness += 10
        else:
            for i in range(ship.length):
                if board[ship.start_row + i][ship.start_col] != "e":
                    fitness += 10
        # Check for touching ships
        if ship.orientation == 'horizontal':
            # check above and below the ship
            for i in range(ship.length):
                if ship.start_row > 0 and board[ship.start_row - 1][ship.start_col + i] != "e":
                    fitness += 100
                if ship.start_row < len(board) - 1 and board[ship.start_row + 1][ship.start_col + i] != "e":
                    fitness += 100
            # check left and right of the ship
            if ship.start_col > 0 and board[ship.start_row][ship.start_col - 1] != "e":
                fitness += 100
            if ship.start_col + ship.length <= len(board) - 1 and board[ship.start_row][ship.start_col + ship.length] != "e":
                fitness += 100
            # check corners
            if ship.start_row > 0 and ship.start_col > 0 and board[ship.start_row - 1][ship.start_col - 1] != "e":
                fitness += 100
            if ship.start_row > 0 and ship.start_col + ship.length <= len(board) - 1 and board[ship.start_row - 1][ship.start_col + ship.length] != "e":
                fitness += 100
            if ship.start_row + 1 < len(board) - 1 and ship.start_col > 0 and board[ship.start_row + 1][ship.start_col - 1] != "e":
                fitness += 100
            if ship.start_row + 1 < len(board) and ship.start_col + ship.length <= len(board) - 1 and board[ship.start_row + 1][ship.start_col + ship.length] != "e":
                fitness += 100
        else:
            # check left and right of the ship
            for i in range(ship.length):
                if ship.start_col > 0 and board[ship.start_row + i][ship.start_col - 1] != "e":
                    fitness += 100
                if ship.start_col < len(board) - 1 and board[ship.start_row + i][ship.start_col + 1] != "e":
                    fitness += 100
            # check above and below the ship
            if ship.start_row > 0 and board[ship.start_row - 1][ship.start_col] != "e":
                fitness += 100
            if ship.start_row + ship.length <= len(board) - 1 and board[ship.start_row + ship.length][ship.start_col] != "e":
                fitness += 100
            # check corners
            if ship.start_row > 0 and ship.start_col > 0 and board[ship.start_row - 1][ship.start_col - 1] != "e":
                fitness += 100
            if ship.start_row > 0 and ship.start_col + 1 < len(board) - 1 and board[ship.start_row - 1][ship.start_col + 1] != "e":
                fitness += 100
            if ship.start_row + ship.length < len(board) - 1 and ship.start_col > 0 and board[ship.start_row + ship.length][ship.start_col - 1] != "e":
                fitness += 100
            if ship.start_row + ship.length <= len(board) - 1 and ship.start_col + 1 < len(board) and board[ship.start_row + ship.length][ship.start_col + 1] != "e":
                fitness += 100
        place_ship(board, ship)
    # Check for hint violations
    for row in range(len(board)):
        for col in range(len(board)):
            if board[row][col] == "e":
                board[row][col] = "sw"
    for hint_pos, hint_value in hints.items():
        row, col = hint_pos
        if board[row][col] != hint_value:
            fitness += 1000
    # Check for row and column violations
    for row in range(len(board)):
        row_count = 0
        for col in range(len(board)):
            if board[row][col] not in ("e", "sw"):
                row_count += 1
        if row_count != row_numbers[row]:
            fitness += 50
    for col in range(len(board)):
        col_count = 0
        for row in range(len(board)):
            if board[row][col] not in ("e", "sw"):
                col_count += 1
        if col_count != col_numbers[col]:
            fitness += 50
    # clear board
    for i in range(len(board)):
        for j in range(len(board)):
            board[i][j] = "e"
    return fitness
   
def evaluate_population(population, board, hints, row_numbers, col_numbers):
    """
    Evaluate the fitness of each individual in the population using the evaluate_individual function.
    """
    fitness_scores = []
    for individual in population:
        fitness = evaluate_individual(individual, board, hints, row_numbers, col_numbers)
        fitness_scores.append(fitness)
    return fitness_scores

def get_best_solution(population, board, hints, row_numbers, col_numbers):
    """
    Get the best solution from the population.
    """
    best_solution = None
    best_fitness = float('inf')
    for individual in population:
        fitness = evaluate_individual(individual, board, hints, row_numbers, col_numbers)
        if fitness < best_fitness:
            best_fitness = fitness
            best_solution = individual
    return best_solution
            
def initialize_population(population_size, board):
    """
    Initialize the population with random individuals.
    Each individual is a list of ships
    """
    population = []
    for _ in range(population_size):
        size = len(board)
        if size == 6:
            ships = [
                (3, 1),
                (2, 2),
                (1, 3)
            ]
        elif size == 8:
            ships = [
                (4, 1),
                (3, 2),
                (2, 3),
                (1, 3)
            ]
        elif size == 10:
            ships = [
                (4, 1),
                (3, 2),
                (2, 3),
                (1, 4),
            ]
        else:
            ships = [
                (5, 1),
                (4, 2),
                (3, 3),
                (2, 4),
                (1, 5)
            ]
        individual = []
        for length, count in ships:
            for _ in range(count):
                while True:
                    for i in range(len(board)):
                        for j in range(len(board)):
                            board[i][j] = "e"
                    orientation = 'horizontal' if random.choice([True, False]) else 'vertical'
                    if length == 1:
                        orientation = 'horizontal'
                    start_row = random.randint(0, size - 1)
                    start_col = random.randint(0, size - 1)
                    ship = Ship(length, orientation, start_row, start_col)
                    # Check if the ship fits in the board
                    if orientation == 'horizontal':
                        if start_col + length > size:
                            continue
                    else:
                        if start_row + length > size:
                            continue
                    individual.append(ship)
                    break
        
        population.append(individual)
    return population

def select_individuals(population, fitness_scores):
    """
    Using 4-tournament selection, select individuals from the population based on their fitness scores.
    """
    selected_individuals = []
    for _ in range(len(population)):
        tournament = random.sample(list(zip(population, fitness_scores)), 4)
        tournament.sort(key=lambda x: x[1])
        selected_individuals.append(tournament[0][0])
    return selected_individuals

def crossover(parent1, parent2):
    """
    Perform one point crossover between two parents to create two children.
    """
    crossover_point = random.randint(1, min(len(parent1), len(parent2)) - 1)
    child1 = parent1[:crossover_point] + parent2[crossover_point:]
    child2 = parent2[:crossover_point] + parent1[crossover_point:]
    return child1, child2

def mutate(individual, size):
    """
    Mutate an individual by randomly changing the position of all ships.
    """
    new_individual = copy.deepcopy(individual)
    for i in range(len(new_individual)):
        ship = new_individual[i]
        orientation = 'horizontal' if random.choice([True, False]) else 'vertical'
        if ship.length == 1:
            orientation = 'horizontal'
        while True:
            start_row = random.randint(0, size - 1)
            start_col = random.randint(0, size - 1)
            new_ship = Ship(ship.length, orientation, start_row, start_col)
            # Check if the ship fits in the board
            if orientation == 'horizontal':
                if start_col + ship.length > size:
                    continue
            else:
                if start_row + ship.length > size:
                    continue
            break
        new_individual[i] = new_ship
    return new_individual

def breed_population(selected_individuals, size, mutation_rate=0.01, crossover_rate=0.8):
    """
    Breed the selected individuals to create the next generation.
    """
    next_generation = []
    for i in range(len(selected_individuals) // 2):
        parent1 = selected_individuals[i]
        parent2 = selected_individuals[len(selected_individuals) - i - 1]
        #crossover
        if random.random() < crossover_rate:
            child1, child2 = crossover(parent1, parent2)
        else:
            child1, child2 = parent1, parent2
        # mutation
        if random.random() < mutation_rate:
            child1 = mutate(child1, size)
        if random.random() < mutation_rate:
            child2 = mutate(child2, size)
        next_generation.append(child1)
        next_generation.append(child2)
    return next_generation


def solve(board, screen, row_numbers, col_numbers, draw_func, draw_manifest_func, max_generations=1000, mutation_rate=0.05, crossover_rate=1, population_size=2500):
    """
    Solve the given board using a genetic algorithm.
    """
    original_board = copy.deepcopy(board)
    hints = {}
    # Wipe board but remember the hint pieces
    for i in range(len(board)):
        for j in range(len(board)):
            if board[i][j] != "e":
                hints[(i, j)] = board[i][j]
            board[i][j] = "e"
    # Initialize the population
    population = initialize_population(population_size, board)

    # Set the number of generations
    generations = max_generations

    fitness_scores = evaluate_population(population, board, hints, row_numbers, col_numbers)
    
    stagnant_generations = 0
    max_stagnant_generations = 10  # Number of generations to wait before declaring convergence
    previous_best_fitness = float('inf')
    # Evolve the population
    for generation in range(generations):
        # Calculate the average fitness of the population
        average_fitness = sum(fitness_scores) / len(fitness_scores)
        print(f"Generation {generation}: Average Fitness = {average_fitness:.2f}")
    
        # Evaluate the fitness of each individual
        fitness_scores = evaluate_population(population, board, hints, row_numbers, col_numbers)

        # Get the 5% best individuals
        best_individuals = sorted(zip(population, fitness_scores), key=lambda x: x[1])[:int(len(population) * 0.05)]
        # Select the best individuals to breed
        selected_individuals = select_individuals(population, fitness_scores)
        
        best_so_far = get_best_solution(population, board, hints, row_numbers, col_numbers)
        place_ships(board, best_so_far)
        draw_func(board, screen)
        draw_manifest_func(screen, len(board))
        pygame.display.flip()
        pygame.event.pump()
        screen.fill((255, 255, 255))
        
        best_fitness = evaluate_individual(best_so_far, board, hints, row_numbers, col_numbers)
        if best_fitness == 0:
            print(f"Solution found in generation {generation}!")
            break
        if best_fitness < previous_best_fitness:
            previous_best_fitness = best_fitness
            stagnant_generations = 0  # Reset the counter
        else:
            stagnant_generations += 1
            
        # Check for convergence
        if stagnant_generations >= max_stagnant_generations:
            print(f"GA has converged after {generation} generations.")
            break

        # Create the next generation
        next_generation = breed_population(selected_individuals, len(board), mutation_rate, crossover_rate)

        # Clear the board for the next generation
        for i in range(len(board)):
            for j in range(len(board)):
                board[i][j] = "e"
                
        # Replace the old population with the new one
        population = next_generation
        # Replace the first 5% of the population with the best individuals
        for i in range(int(len(population) * 0.05)):
            population[i] = best_individuals[i][0]

    # Return the best solution found
    best_solution = get_best_solution(population, board, hints, row_numbers, col_numbers)
    fitness = evaluate_individual(best_solution, board, hints, row_numbers, col_numbers)
    place_ships(board, best_solution)
    draw_func(board, screen)
    pygame.display.flip()
    # make best solution editable
    for row in range(len(original_board)):
        for col in range(len(original_board)):
            if original_board[row][col] == "e":
                if board[row][col] == "sw":
                    original_board[row][col] = "w"
                if board[row][col] in ("ms", "us", "ds", "ss", "ls", "rs"):
                    original_board[row][col] = "s"
    best_solution = original_board
    if fitness == 0:
        print("Solution found!")
    else:
        print("No solution found.")
        return False, best_solution, fitness
    return True, best_solution, fitness