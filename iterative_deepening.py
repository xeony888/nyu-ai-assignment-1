from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
import re

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
    def __str__(self):
        return f"Name: {self.name}, Value: {self.value}, Length: {self.length}, Due: {self.due}"

def main():
    with open("input.txt", "r") as f:
        # Read the entire content
        content = f.read()
        lines = content.split("\n")
        config, tasks = parse_file(lines)
        iterative_deepening(config, tasks)

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
def contains(tasks: List[Task], task: Task) -> bool:
    return any(t.name == task.name for t in tasks)
def can_add_task(tasks: List[Task], task: Task) -> bool:
    end_time = 0
    for t in tasks:
        end_time += t.length
        if end_time > t.due:
            return False

    if end_time + task.length <= task.due:
        return True
    return False
def get_value(tasks: List[Task]) -> int:
    return sum(task.value for task in tasks)
def print_task_pattern(tasks: List[Task]):
    value = get_value(tasks)
    names = " ".join([task.name for task in tasks])
    print(f"{names} Value={value}")
def step_expand(all_task_patterns: List[List[Task]], tasks: List[Task], val: int) -> List[List[Task]]:
    new_patterns: list[list[Task]] = []
    for base in all_task_patterns:
        new_patterns.append(base)  # keep the base pattern
        if len(base) != val:
            continue
        # compute all valid 1-step extensions of this base
        extensions = [
            base + [t]
            for t in tasks
            if not contains(base, t) and can_add_task(base, t)
        ]
        # insert them right after the base, preserving order
        new_patterns.extend(extensions)
    return new_patterns
def iterative_deepening(config: Config, tasks: List[Task]) -> Optional[List[Task]]:
    all_task_patterns: List[List[Task]] = [[task] for task in tasks if task.length <= task.due]
    if config.mode == "verbose":
        print("Depth=1")
        string ="\n".join([f"{task[0].name} Value={task[0].value}" for task in all_task_patterns])
        print(string)
    val = 1
    while True:
        if config.mode == "verbose":
            print(f"\nDepth={val+1}")
        prev_length = len(all_task_patterns)
        all_task_patterns = step_expand(all_task_patterns, tasks, val)
        if prev_length == len(all_task_patterns):
            if config.mode == "verbose":
                print("No solution found")
            break
        found = any(get_value(task_pattern) >= config.target for task_pattern in all_task_patterns)
        for task_pattern in all_task_patterns:
            if get_value(task_pattern) >= config.target:
                if config.mode == "verbose":
                    print_task_pattern(task_pattern)
                    print("\n")
                value = get_value(task_pattern)
                names = " ".join([task.name for task in task_pattern])
                print(f"Found solution {names}. Value={value}")
                break
            else:
                if config.mode == "verbose":
                    print_task_pattern(task_pattern)
        val += 1
        if found:
            break

        



if __name__ == "__main__":
    main()