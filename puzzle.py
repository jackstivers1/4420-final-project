from collections import deque
import heapq
import time

# =========================
# Color display
# =========================

COLOR_MAP = {
    # Bright colors
    'R': '\033[48;5;196m  \033[0m',   # bright red
    'G': '\033[48;5;46m  \033[0m',    # bright green
    'B': '\033[48;5;21m  \033[0m',    # bright blue
    'Y': '\033[48;5;226m  \033[0m',   # bright yellow
    'P': '\033[48;5;201m  \033[0m',   # pink / magenta
    'O': '\033[48;5;208m  \033[0m',   # orange
    'C': '\033[48;5;51m  \033[0m',    # cyan
    'W': '\033[48;5;15m  \033[0m',    # white
    'K': '\033[48;5;16m  \033[0m',    # black

    # Dark versions
    'r': '\033[48;5;88m  \033[0m',    # dark red
    'g': '\033[48;5;22m  \033[0m',    # dark green
    'b': '\033[48;5;18m  \033[0m',    # dark blue
    'y': '\033[48;5;136m  \033[0m',   # dark yellow
    'p': '\033[48;5;90m  \033[0m',    # dark purple
    'o': '\033[48;5;130m  \033[0m',   # dark orange
    'c': '\033[48;5;23m  \033[0m',    # dark cyan
    'k': '\033[48;5;232m  \033[0m',   # dark gray

    # Extra shades
    'M': '\033[48;5;200m  \033[0m',   # hot pink
    'A': '\033[48;5;244m  \033[0m',   # gray
    'D': '\033[48;5;238m  \033[0m',   # dark gray
    'L': '\033[48;5;153m  \033[0m',   # light blue
    'T': '\033[48;5;121m  \033[0m',   # teal

    # Empty
    ' ': '  '
}


def get_block(color):
    return COLOR_MAP.get(color, '\033[48;5;250m??\033[0m')


# =========================
# Conversion / state helpers
# =========================

def convert_to_2dlist(puzzle):
    main_list = []
    count = 0
    for _ in range(puzzle.count("-") + 1):
        sub_list = []
        while count < len(puzzle) and puzzle[count] != "-":
            sub_list.append(puzzle[count])
            count += 1
        main_list.append(sub_list)
        count += 1
    return main_list


def convert_to_string(list_state):
    main_str = ""
    for row in list_state:
        for column in row:
            main_str += str(column)
        main_str += "-"
    return main_str[:-1]


def to_state(state_str):
    return tuple(tuple(bottle) for bottle in convert_to_2dlist(state_str))


def from_state(state):
    return "-".join("".join(bottle) for bottle in state)


def bottle_capacity(state):
    return max(len(bottle) for bottle in state)


def top_run_length(bottle):
    if not bottle:
        return 0
    color = bottle[-1]
    count = 1
    i = len(bottle) - 2
    while i >= 0 and bottle[i] == color:
        count += 1
        i -= 1
    return count


def is_uniform(bottle):
    return len(bottle) == 0 or len(set(bottle)) == 1


def is_solved_bottle(bottle, capacity):
    return len(bottle) == 0 or (len(bottle) == capacity and is_uniform(bottle))


def is_goal_state(state):
    cap = bottle_capacity(state)
    for bottle in state:
        if len(bottle) == 0:
            continue
        if len(bottle) != cap:
            return False
        if not is_uniform(bottle):
            return False
    return True


# =========================
# Visualization
# =========================

def print_buckets(state):
    if isinstance(state, str):
        state = to_state(state)

    cap = bottle_capacity(state)

    print()
    for level in range(cap - 1, -1, -1):
        for bottle in state:
            if level < len(bottle):
                block = get_block(bottle[level])
                print(f"|{block}|", end=" ")
            else:
                print("|  |", end=" ")
        print()

    print("---- " * len(state))
    for i in range(len(state)):
        print(f" {i:<2} ", end=" ")
    print("\n")


# =========================
# Canonicalization
# =========================

def bottle_sort_key(bottle):
    return (len(bottle), bottle)


def canonicalize(state):
    return tuple(sorted(state, key=bottle_sort_key))


# =========================
# Move generation / pruning
# =========================

def legal_moves(state):
    cap = bottle_capacity(state)
    n = len(state)
    moves = []

    for i in range(n):
        source = state[i]
        if len(source) == 0:
            continue

        empty_target_seen = False

        # Do not pour out of an already solved full bottle
        if len(source) == cap and is_uniform(source):
            continue

        source_top = source[-1]
        source_run = top_run_length(source)

        for j in range(n):
            if i == j:
                continue

            target = state[j]

            if len(target) == cap:
                continue

            if len(target) == 0:
                if empty_target_seen:
                    continue
            else:
                if target[-1] != source_top:
                    continue

            # avoid pointless move: uniform source into empty
            if len(target) == 0 and is_uniform(source):
                continue

            amount = min(source_run, cap - len(target))
            if amount <= 0:
                continue

            if len(target) == 0:
                empty_target_seen = True

            moves.append((i, j, amount))

    return moves


def apply_move(state, source_index, target_index, amount):
    bottles = [list(bottle) for bottle in state]

    moved = bottles[source_index][-amount:]
    bottles[source_index] = bottles[source_index][:-amount]
    bottles[target_index].extend(moved)

    return tuple(tuple(bottle) for bottle in bottles)


# =========================
# Heuristic
# =========================

def bottle_transitions(bottle):
    count = 0
    for i in range(len(bottle) - 1):
        if bottle[i] != bottle[i + 1]:
            count += 1
    return count


def color_group_penalty(state):
    total = 0
    for bottle in state:
        if len(bottle) == 0:
            continue
        seen_groups = 1
        for i in range(1, len(bottle)):
            if bottle[i] != bottle[i - 1]:
                seen_groups += 1
        total += seen_groups - 1
    return total


def unfinished_bottle_count(state):
    cap = bottle_capacity(state)
    count = 0
    for bottle in state:
        if len(bottle) > 0 and not (len(bottle) == cap and is_uniform(bottle)):
            count += 1
    return count


def heuristic(state):
    transitions = sum(bottle_transitions(bottle) for bottle in state)
    return transitions


# =========================
# Path reconstruction
# =========================

def reconstruct_path(parent, end_state):
    path = []
    current = end_state

    while parent[current][0] is not None:
        prev_state, move = parent[current]
        path.append((move, current))
        current = prev_state

    path.reverse()
    return path

def bfs_solve(start_str):
    start_state = to_state(start_str)

    if is_goal_state(start_state):
        return [], start_state, 0

    visited = {start_state}
    parent = {start_state: (None, None)}
    queue = deque([start_state])
    expanded = 0

    while queue:
        state = queue.popleft()
        expanded += 1

        for move in legal_moves(state):
            next_state = apply_move(state, *move)

            if next_state in visited:
                continue

            visited.add(next_state)
            parent[next_state] = (state, move)

            if is_goal_state(next_state):
                return reconstruct_path(parent, next_state), next_state, expanded

            queue.append(next_state)

    return None, None, expanded

# =========================
# A* Search
# =========================

def astar_solve(start_str):
    start_state = to_state(start_str)
    start_key = canonicalize(start_state)

    pq = []
    start_h = heuristic(start_state)
    heapq.heappush(pq, (start_h, 0, start_state))

    g_score = {start_key: 0}
    parent = {start_state: (None, None)}

    expanded = 0

    while pq:
        f_score, current_g, state = heapq.heappop(pq)
        state_key = canonicalize(state)

        if current_g != g_score.get(state_key, float('inf')):
            continue

        expanded += 1

        if is_goal_state(state):
            return reconstruct_path(parent, state), state, expanded

        for move in legal_moves(state):
            source_index, target_index, amount = move
            next_state = apply_move(state, source_index, target_index, amount)
            next_key = canonicalize(next_state)

            new_g = current_g + 1

            if new_g < g_score.get(next_key, float('inf')):
                g_score[next_key] = new_g
                parent[next_state] = (state, move)
                new_f = new_g + heuristic(next_state)
                heapq.heappush(pq, (new_f, new_g, next_state))

    return None, None, expanded

# =========================
# Output
# =========================

def print_solution(start_str, path, final_state, expanded):
    start_state = to_state(start_str)

    print("\nInitial state:")
    print_buckets(start_state)

    print(f"States expanded: {expanded}")

    if path is None:
        print("No solution found.")
        return

    if len(path) == 0:
        print("Already solved.")
        return

    for step, (move, next_state) in enumerate(path, 1):
        source_index, target_index, amount = move
        print(f"Step {step}: pour bottle {source_index} into bottle {target_index}")
        print_buckets(next_state)

    print("Solved in", len(path), "moves.")

# =========================
# Basic validation
# =========================

def validate_input(puzzle):
    if not puzzle:
        return False, "Puzzle string is empty."

    bottles = puzzle.split("-")
    if len(bottles) < 3:
        return False, "Need at least 3 bottles."

    lengths = [len(b) for b in bottles]
    cap = max(lengths)

    if cap == 0:
        return False, "All bottles are empty."

    for bottle in bottles:
        if len(bottle) > cap:
            return False, "Invalid bottle length."

    return True, ""


# =========================
# Main
# =========================

if __name__ == "__main__":
    puzzle = input('Enter puzzle in format like "RBB-RBB--": ').strip()

    valid, message = validate_input(puzzle)
    if not valid:
        print("Error:", message)
    else:
        print("1. Solve with BFS")
        print("2. Solve with A*")
        choice = input("Choose solver (1 or 2): ").strip()

        start_time = time.time()

        if choice == "1":
            path, final_state, expanded = bfs_solve(puzzle)
            print("\nUsing BFS")
            print_solution(puzzle, path, final_state, expanded)
        elif choice == "2":
            path, final_state, expanded = astar_solve(puzzle)
            print("\nUsing A*")
            print_solution(puzzle, path, final_state, expanded)
        else:
            print("Invalid choice.")

        end_time = time.time()
        runtime = end_time - start_time

        if choice == "1":
            print(f"\nUsing BFS")
        if choice == "2":
            print(f"\nUsing A*")
        print(f"Runtime: {runtime:.4f} seconds")
