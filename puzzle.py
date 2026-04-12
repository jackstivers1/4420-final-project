from collections import deque

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


def copy_state(state):
    return [row[:] for row in state]


def get_capacity(state):
    max_len = 0
    for bottle in state:
        if len(bottle) > max_len:
            max_len = len(bottle)
    return max_len


def is_uniform(bottle):
    if len(bottle) == 0:
        return True
    first = bottle[0]
    for color in bottle:
        if color != first:
            return False
    return True


def is_goal(state_str):
    state = convert_to_2dlist(state_str)
    capacity = get_capacity(state)

    for bottle in state:
        if len(bottle) == 0:
            continue
        if len(bottle) != capacity:
            return False
        if not is_uniform(bottle):
            return False
    return True


def can_pour(state, source_num, target_num):
    capacity = get_capacity(state)
    source = state[source_num]
    target = state[target_num]

    if source_num == target_num:
        return False
    if len(source) == 0:
        return False
    if len(target) == capacity:
        return False
    if len(target) == 0:
        return True
    return source[-1] == target[-1]


def pour(state_str, source_num, target_num):
    state = convert_to_2dlist(state_str)

    if not can_pour(state, source_num, target_num):
        return None

    source = state[source_num]
    target = state[target_num]
    capacity = get_capacity(state)

    new_state = copy_state(state)

    source = new_state[source_num]
    target = new_state[target_num]

    moving_color = source[-1]

    while (
        len(source) > 0
        and source[-1] == moving_color
        and len(target) < capacity
        and (len(target) == 0 or target[-1] == moving_color)
    ):
        target.append(source.pop())

    return convert_to_string(new_state)


def possible_moves(state_str):
    state = convert_to_2dlist(state_str)
    moves = []

    for i in range(len(state)):
        for j in range(len(state)):
            if i == j:
                continue
            new_state = pour(state_str, i, j)
            if new_state is not None:
                moves.append((i, j, new_state))

    return moves


def build_graph(start_state, max_states=10000):
    graph = {}
    visited = set()
    queue = deque([start_state])

    while queue and len(visited) < max_states:
        current = queue.popleft()

        if current in visited:
            continue

        visited.add(current)
        graph[current] = []

        for source, target, next_state in possible_moves(current):
            graph[current].append((source, target, next_state))
            if next_state not in visited:
                queue.append(next_state)

    return graph


def reconstruct_path(parent, move_used, goal_state):
    path = []
    current = goal_state

    while parent[current] is not None:
        path.append((move_used[current], current))
        current = parent[current]

    path.reverse()
    return path


def bfs_solve(start_state):
    if is_goal(start_state):
        return []

    visited = set([start_state])
    parent = {start_state: None}
    move_used = {start_state: None}
    queue = deque([start_state])

    while queue:
        current = queue.popleft()

        for source, target, next_state in possible_moves(current):
            if next_state in visited:
                continue

            visited.add(next_state)
            parent[next_state] = current
            move_used[next_state] = (source, target)
            queue.append(next_state)

            if is_goal(next_state):
                return reconstruct_path(parent, move_used, next_state)

    return None


def print_solution(start_state, solution):
    print("Start:")
    print_buckets(start_state)

    if solution is None:
        print("No solution found.")
        return

    current = start_state

    for step, (move, next_state) in enumerate(solution, 1):
        s, t = move
        print(f"Step {step}: {s} → {t}")
        print_buckets(next_state)
        current = next_state

def print_buckets(state_str):
    state = convert_to_2dlist(state_str)
    capacity = get_capacity(state)

    print()

    for level in range(capacity - 1, -1, -1):
        for bottle in state:
            if level < len(bottle):
                block = COLOR_MAP.get(bottle[level], "??")
                print(f"|{block}|", end=" ")
            else:
                print("|  |", end=" ")
        print()

    print("---- " * len(state))
    print()

if __name__ == "__main__":
    start = input('Enter puzzle in format like "RBB-RBB--": ').strip()

    if not start:
        print("Error: empty puzzle string.")
    else:
        print("\nYou entered:")
        print(start)

        print("\nInitial state:")
        print_buckets(start)

        print("Solving...")
        solution = bfs_solve(start)
        print_solution(start, solution)
