from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
import re
import numpy as np
import itertools
import random

@dataclass
class Config:
    target: int
    mode: str                 # "verbose" or "compact"
    restarts: Optional[int]   # hill-climbing random restarts (if present)
    def __str__(self):
        return f"Target: {self.target}, Mode: {self.mode}, Restarts: {self.restarts}"

@dataclass
class Task:
    name: str
    value: int
    length: int
    due: int
    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return (
            self.name == other.name and
            self.value == other.value and
            self.length == other.length and
            self.due == other.due
        )
    def __str__(self):
        return f"Name: {self.name}, Value: {self.value}, Length: {self.length}, Due: {self.due}"


def parse_file(lines: List[str]) -> Tuple[Config, List[Task]]:
    if not lines:
        raise ValueError("input.txt is empty or only comments.")
    header = re.split(r" +", lines[0].strip())
    if len(header) < 2:
        raise ValueError("First line must contain at least: <target> <V|C> [restarts].")

    try:
        target = int(header[0])
        if target <= 0:
            raise ValueError
    except ValueError:
        raise ValueError("Target must be a positive integer on line 1.")

    flag = header[1].upper()
    if flag not in ("V", "C"):
        raise ValueError('Flag must be "V" (verbose) or "C" (compact) on line 1.')
    mode = "verbose" if flag == "V" else "compact"

    # optional restarts
    restarts: Optional[int] = None
    if len(header) >= 3:
        try:
            restarts = int(header[2])
            if restarts < 0:
                raise ValueError
        except ValueError:
            raise ValueError("If provided, restarts must be a non-negative integer on line 1.")

    config = Config(target=target, mode=mode, restarts=restarts)

    tasks: List[Task] = []
    for i, raw in enumerate(lines[1:], start=2):  # human line numbers start at 1
        parts = re.split(r' +', raw.strip())
        if len(parts) != 4:
            raise ValueError(f"Line {i}: expected 4 fields: <Name> <Value> <Length> <Due>.")

        name, v_str, l_str, d_str = parts

        if not (len(name) == 1 and name.isalpha()):
            raise ValueError(f"Line {i}: Name must be a single alphabetic character.")

        try:
            value = int(v_str)
            length = int(l_str)
            due = int(d_str)
            if value <= 0 or length <= 0 or due <= 0:
                raise ValueError
        except ValueError:
            raise ValueError(f"Line {i}: Value, Length, and Due must be positive integers.")

        tasks.append(Task(name=name, value=value, length=length, due=due))

    return config, tasks


def main():
    with open("input.txt", "r") as f:
        content = f.read()
        lines = content.split("\n")
        config, tasks = parse_file(lines)
        hill_climbing(config, tasks)

def can_add_task(tasks: List[Task], task: Task) -> bool:
    end_time = 0
    for t in tasks:
        end_time += t.length
        if end_time > t.due:
            return False

    if end_time + task.length <= task.due:
        return True
    return False

def select_random_start_state(tasks: List[Task]) -> List[Task]:
    # pick a random length between 1 and len(tasks)
    # length = random.randint(1, len(tasks))
    # # randomly permute and take only the first `length` elements
    # return list(np.random.permutation(tasks)[:length])
    return [tasks[3], tasks[4]] # make this the random permutation for testing

def get_value(tasks: List[Task]) -> int:
    return sum(task.value for task in tasks)

def get_error(state: List[Task], config: Config) -> int:
    value = get_value(state)
    time = 0
    overrun = 0
    for task in state:
        if time + task.length > task.due:
            overrun +=  time + task.length - task.due
        time += task.length
    if value < config.target:
        return abs(config.target - value) + overrun
    else:
        return overrun

def print_task_pattern(tasks: List[Task], config: Config):
    value = get_value(tasks)
    error = get_error(tasks, config)
    names = " ".join([task.name for task in tasks])
    print(f"{names} Value={value}. Error={error}")

# def get_neighbors(state: List[Task], all_tasks: List[Task]) -> List[List[Task]]:
#     permutations = []
#     if len(state) - 1 > 0:
#         for perm in itertools.permutations(state, len(state) - 1):
#             permutations.append(list(perm))
#     for perm in itertools.permutations(state, len(state)):
#         if list(perm) != state:
#             permutations.append(list(perm))
#     for task in all_tasks:
#         if task not in state:
#             new_state = state + [task]
#             permutations.append(new_state)
#     return permutations

def get_neighbors(state: List[Task], all_tasks: List[Task]) -> List[List[Task]]:
    neighbors: List[List[Task]] = []
    seen = set()  # dedupe by task names (assumes names uniquely identify tasks)

    def add(candidate: List[Task]):
        if candidate == state:
            return
        key = tuple(t.name for t in candidate)
        if key not in seen:
            seen.add(key)
            neighbors.append(candidate)

    n = len(state)

    # A) Delete a task from S
    for i in range(n):
        add(state[:i] + state[i+1:])

    # B) Switch two consecutive tasks in S
    for i in range(n - 1):
        cand = state[:]
        cand[i], cand[i+1] = cand[i+1], cand[i]
        add(cand)

    # C) Add a task not in S to the end of S
    for t in all_tasks:
        if t not in state:
            add(state + [t])

    return neighbors
def names_of(ts: List[Task]) -> str:
    return " ".join(t.name for t in ts) if ts else "{}"
def hill_climbing(config: Config, tasks: List[Task]):
    if config.restarts is None:
        raise ValueError("Random restarts must be provided to hill climbing")
    restarts = 0
    while restarts < config.restarts:
        state: List[Task] = select_random_start_state(tasks)
        names = " ".join([task.name for task in state])
        value = get_value(state)
        error = get_error(state, config)
        if config.mode == "verbose":
            print(f"\nRandomly chosen start state: {names} Value={value}. Error={error}")
        while True:
            neighbors = get_neighbors(state, tasks)
            if not neighbors:
                if config.mode == "verbose":
                    print("Search failed")
                break
            if config.mode == "verbose":
                for neighbor in neighbors:
                    print_task_pattern(neighbor, config)
            min_neighbor = min(
                neighbors,
                key=lambda n: (get_error(n, config))
            )
            if get_error(min_neighbor, config) == 0:
                names = " ".join([task.name for task in min_neighbor])
                value = get_value(min_neighbor)
                state = min_neighbor
                print(f"\nFound solution {names} Value={value}")
                break
            elif get_error(min_neighbor, config) >= get_error(state, config):
                if config.mode == "verbose":
                    print("Search failed")
                break
            else:
                state = min_neighbor
                if config.mode == "verbose":
                    names = " ".join([task.name for task in state])
                    value = get_value(state)
                    error = get_error(state, config)
                    print(f"\nMove to {names} Value={value}. Error={error}")
        if get_error(state, config) == 0:
            break
        restarts += 1
        if restarts >= config.restarts:
            print("No solution found")
    




if __name__ == "__main__":
    main()
