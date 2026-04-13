from collections import deque
import heapq
import time

BOARD_SIZE = 6
TARGET_CAR = 'X'
EXIT_ROW = 2  # third row


# =========================================
# Color display
# =========================================

COLOR_MAP = {
    'X': '\033[48;5;196m  \033[0m',  # red goal car
    'A': '\033[48;5;39m  \033[0m',
    'B': '\033[48;5;46m  \033[0m',
    'C': '\033[48;5;226m  \033[0m',
    'D': '\033[48;5;208m  \033[0m',
    'E': '\033[48;5;201m  \033[0m',
    'F': '\033[48;5;51m  \033[0m',
    'G': '\033[48;5;129m  \033[0m',
    'H': '\033[48;5;244m  \033[0m',
    'I': '\033[48;5;15m  \033[0m',
    'J': '\033[48;5;94m  \033[0m',
    'K': '\033[48;5;121m  \033[0m',
    'L': '\033[48;5;214m  \033[0m',
    'M': '\033[48;5;200m  \033[0m',
    'N': '\033[48;5;27m  \033[0m',
    'O': '\033[48;5;154m  \033[0m',
    'P': '\033[48;5;93m  \033[0m',
    'Q': '\033[48;5;172m  \033[0m',
    'R': '\033[48;5;33m  \033[0m',
    'S': '\033[48;5;70m  \033[0m',
    'T': '\033[48;5;141m  \033[0m',
    'U': '\033[48;5;160m  \033[0m',
    'V': '\033[48;5;28m  \033[0m',
    'W': '\033[48;5;220m  \033[0m',
    'Y': '\033[48;5;111m  \033[0m',
    'Z': '\033[48;5;240m  \033[0m',
    '.': '\033[48;5;255m  \033[0m',  # empty
    '#': '\033[48;5;240m  \033[0m',  # obstacle
    '@': '\033[48;5;16m  \033[0m',   # exit square drawn outside board
}

COLOR_NAME_MAP = {
    'X': 'red',
    'A': 'blue',
    'B': 'green',
    'C': 'yellow',
    'D': 'orange',
    'E': 'pink',
    'F': 'cyan',
    'G': 'purple',
    'H': 'gray',
    'I': 'white',
    'J': 'brown',
    'K': 'teal',
    'L': 'light orange',
    'M': 'hot pink',
    'N': 'dark blue',
    'O': 'lime',
    'P': 'violet',
    'Q': 'amber',
    'R': 'sky blue',
    'S': 'olive',
    'T': 'lavender',
    'U': 'dark red',
    'V': 'dark green',
    'W': 'gold',
    'Y': 'light teal',
    'Z': 'dark gray',
}

DIRECTION_MAP = {
    'L': 'left',
    'R': 'right',
    'U': 'up',
    'D': 'down'
}


def get_block(ch):
    return COLOR_MAP.get(ch, '\033[48;5;250m??\033[0m')


# =========================================
# Input / parsing
# =========================================

def read_board():
    print("Enter 6 rows of 6 characters each.")
    print('Use "." for empty cells.')
    print('Use "#" for an obstacle.')
    print('Use "X" for the red goal car.')
    print("Do NOT type the exit; it is fixed to the right of row 2.")
    print()
    print("Example:")
    print("AA.#.B")
    print("CDDD.B")
    print("CXX...")
    print("FFGE..")
    print("..GHHH")
    print("IIIJJ.")
    print()

    rows = []
    for i in range(BOARD_SIZE):
        row = input(f"Row {i}: ").strip()
        rows.append(row)
    return rows


def validate_board(rows):
    if len(rows) != BOARD_SIZE:
        return False, "Board must have exactly 6 rows."

    positions = {}

    for row in rows:
        if len(row) != BOARD_SIZE:
            return False, "Each row must have exactly 6 characters."

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            ch = rows[r][c]

            if ch == '.':
                continue
            if ch == '#':
                continue

            positions.setdefault(ch, []).append((r, c))

    if TARGET_CAR not in positions:
        return False, 'Board must include the goal car "X".'

    for car, cells in positions.items():
        if len(cells) < 2 or len(cells) > 3:
            return False, f'Car {car} must have length 2 or 3.'

        same_row = all(r == cells[0][0] for r, c in cells)
        same_col = all(c == cells[0][1] for r, c in cells)

        if not (same_row or same_col):
            return False, f'Car {car} must be straight.'

        if same_row:
            cols = sorted(c for r, c in cells)
            for i in range(len(cols) - 1):
                if cols[i + 1] != cols[i] + 1:
                    return False, f'Car {car} must occupy consecutive cells.'
        else:
            rows_sorted = sorted(r for r, c in cells)
            for i in range(len(rows_sorted) - 1):
                if rows_sorted[i + 1] != rows_sorted[i] + 1:
                    return False, f'Car {car} must occupy consecutive cells.'

    x_cells = positions[TARGET_CAR]
    same_row = all(r == x_cells[0][0] for r, c in x_cells)
    if not same_row:
        return False, 'Goal car "X" must be horizontal.'

    if x_cells[0][0] != EXIT_ROW:
        return False, 'Goal car "X" must be on row 2 (third row).'

    return True, ""


def normalize_state(state):
    return tuple(sorted(state))


def parse_board(rows):
    car_defs = {}
    state = []
    blocked = set()

    positions = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            ch = rows[r][c]

            if ch == '#':
                blocked.add((r, c))
                continue

            if ch == '.':
                continue

            positions.setdefault(ch, []).append((r, c))

    for car, cells in positions.items():
        cells = sorted(cells)
        length = len(cells)

        same_row = all(r == cells[0][0] for r, c in cells)
        orient = 'H' if same_row else 'V'

        if orient == 'H':
            row = cells[0][0]
            col = min(c for r, c in cells)
        else:
            row = min(r for r, c in cells)
            col = cells[0][1]

        car_defs[car] = {'length': length, 'orient': orient}
        state.append((car, row, col))

    return normalize_state(tuple(state)), car_defs, blocked


# =========================================
# Board building / display
# =========================================

def build_board(state, car_defs, blocked):
    board = [['.' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    for r, c in blocked:
        board[r][c] = '#'

    for car_id, row, col in state:
        length = car_defs[car_id]['length']
        orient = car_defs[car_id]['orient']

        if orient == 'H':
            for k in range(length):
                board[row][col + k] = car_id
        else:
            for k in range(length):
                board[row + k][col] = car_id

    return board


def print_board(state, car_defs, blocked):
    board = build_board(state, car_defs, blocked)

    print()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            print(get_block(board[r][c]), end=" ")
        if r == EXIT_ROW:
            print(get_block('@'), end="")
        print()
    print()


# =========================================
# Goal test
# =========================================

def is_goal(state, car_defs):
    for car_id, row, col in state:
        if car_id == TARGET_CAR:
            length = car_defs[car_id]['length']
            return row == EXIT_ROW and (col + length - 1) == BOARD_SIZE - 1
    return False


# =========================================
# Legal moves
# =========================================

def legal_moves(state, car_defs, blocked):
    board = build_board(state, car_defs, blocked)
    moves = []

    for car_id, row, col in state:
        length = car_defs[car_id]['length']
        orient = car_defs[car_id]['orient']

        if orient == 'H':
            step = 1
            while col - step >= 0 and board[row][col - step] == '.':
                moves.append((car_id, 'L', step))
                step += 1

            step = 1
            while col + length - 1 + step < BOARD_SIZE and board[row][col + length - 1 + step] == '.':
                moves.append((car_id, 'R', step))
                step += 1

        else:
            step = 1
            while row - step >= 0 and board[row - step][col] == '.':
                moves.append((car_id, 'U', step))
                step += 1

            step = 1
            while row + length - 1 + step < BOARD_SIZE and board[row + length - 1 + step][col] == '.':
                moves.append((car_id, 'D', step))
                step += 1

    return moves


def apply_move(state, move):
    car_to_move, direction, steps = move
    new_state = []

    for car_id, row, col in state:
        if car_id == car_to_move:
            if direction == 'L':
                col -= steps
            elif direction == 'R':
                col += steps
            elif direction == 'U':
                row -= steps
            elif direction == 'D':
                row += steps
        new_state.append((car_id, row, col))

    return normalize_state(tuple(new_state))


# =========================================
# Heuristic
# =========================================

def blocking_heuristic(state, car_defs, blocked):
    board = build_board(state, car_defs, blocked)

    x_row = None
    x_col = None
    x_length = None

    for car_id, row, col in state:
        if car_id == TARGET_CAR:
            x_row = row
            x_col = col
            x_length = car_defs[car_id]['length']
            break

    if x_row is None:
        return 0

    blockers = set()

    for c in range(x_col + x_length, BOARD_SIZE):
        if board[x_row][c] != '.':
            blockers.add(board[x_row][c])

    distance_to_edge = (BOARD_SIZE - 1) - (x_col + x_length - 1)
    car_blockers = len([b for b in blockers if b != '#'])

    return distance_to_edge + car_blockers


# =========================================
# Path reconstruction
# =========================================

def reconstruct_path(parent, goal_state):
    path = []
    current = goal_state

    while parent[current][0] is not None:
        prev_state, move = parent[current]
        path.append((move, current))
        current = prev_state

    path.reverse()
    return path


# =========================================
# BFS
# =========================================

def bfs_solve(start_state, car_defs, blocked):
    if is_goal(start_state, car_defs):
        return [], start_state, 0

    visited = {start_state}
    parent = {start_state: (None, None)}
    queue = deque([start_state])
    expanded = 0

    while queue:
        state = queue.popleft()
        expanded += 1

        for move in legal_moves(state, car_defs, blocked):
            next_state = apply_move(state, move)

            if next_state in visited:
                continue

            visited.add(next_state)
            parent[next_state] = (state, move)

            if is_goal(next_state, car_defs):
                return reconstruct_path(parent, next_state), next_state, expanded

            queue.append(next_state)

    return None, None, expanded


# =========================================
# A*
# =========================================

def astar_solve(start_state, car_defs, blocked):
    pq = []
    heapq.heappush(
        pq,
        (blocking_heuristic(start_state, car_defs, blocked), 0, start_state)
    )

    g_score = {start_state: 0}
    parent = {start_state: (None, None)}
    expanded = 0

    while pq:
        f_score, current_g, state = heapq.heappop(pq)

        if current_g != g_score.get(state, float('inf')):
            continue

        expanded += 1

        if is_goal(state, car_defs):
            return reconstruct_path(parent, state), state, expanded

        for move in legal_moves(state, car_defs, blocked):
            next_state = apply_move(state, move)
            new_g = current_g + 1

            if new_g < g_score.get(next_state, float('inf')):
                g_score[next_state] = new_g
                parent[next_state] = (state, move)
                new_f = new_g + blocking_heuristic(next_state, car_defs, blocked)
                heapq.heappush(pq, (new_f, new_g, next_state))

    return None, None, expanded


# =========================================
# Output
# =========================================

def print_solution(start_state, path, final_state, expanded, car_defs, blocked):
    print("Initial state:")
    print_board(start_state, car_defs, blocked)

    print(f"States expanded: {expanded}")

    if path is None:
        print("No solution found.")
        return

    if len(path) == 0:
        print("Already solved.")
        return

    for step_num, (move, next_state) in enumerate(path, 1):
        car_id, direction, steps = move
        color_name = COLOR_NAME_MAP.get(car_id, car_id)

        direction_word = DIRECTION_MAP.get(direction, direction)
        print(f"Step {step_num}: move {color_name} {direction_word} by {steps}")
        print_board(next_state, car_defs, blocked)

    print(f"Solved in {len(path)} moves.")


# =========================================
# Main
# =========================================

if __name__ == "__main__":
    rows = read_board()
    valid, message = validate_board(rows)

    if not valid:
        print("Error:", message)
    else:
        start_state, car_defs, blocked = parse_board(rows)

        print("1. Solve with BFS")
        print("2. Solve with A*")
        choice = input("Choose solver (1 or 2): ").strip()

        start_time = time.time()

        if choice == "1":
            path, final_state, expanded = bfs_solve(start_state, car_defs, blocked)
            print_solution(start_state, path, final_state, expanded, car_defs, blocked)
        elif choice == "2":
            path, final_state, expanded = astar_solve(start_state, car_defs, blocked)
            print_solution(start_state, path, final_state, expanded, car_defs, blocked)
        else:
            print("Invalid choice.")

        end_time = time.time()
        runtime = end_time - start_time

        print(f"\nUsing {choice}")
        print(f"Runtime: {runtime:.4f} seconds")
        print_solution(start_state, path, final_state, expanded, car_defs, blocked)
