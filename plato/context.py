from dataclasses import dataclass


_seed = 0


@dataclass
class Context:
    seed: int

    def __init__(self):
        global _seed
        self.seed = _seed
        _seed += 1


def seed(value: int):
    global _seed
    _seed = value