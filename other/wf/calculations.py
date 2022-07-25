from abc import ABC, abstractmethod
from math import sqrt

def to_decimal(percantage: str) -> int:
    return float(percantage.split("%")[0]) / 100


def human_format(num):
    num = float("{:.3g}".format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return "{}{}".format(
        "{:f}".format(num).rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude]
    )


def calc_ehp(
    health: int,
    armor: int = 0,
    damage_reduction_percentage: str = "0%",
    damage_modifier_percentage: str = "0%",
):

    dr = to_decimal(damage_reduction_percentage)
    dm = to_decimal(damage_modifier_percentage)

    num = health * (armor + 300)
    den = 300 * (1 - dr) * (1 + dm)

    return human_format(int(num / den))


class BaseScaling(ABC):
    def __init__(self, base_level: int, current_level: int):
        self.base = base_level
        self.current = current_level

    @abstractmethod
    def f1(self):
        pass

    @abstractmethod
    def f2(self):
        pass

    def T(self, x):
        return (x - self.base - 70) / 10

    def S(self, x):
        diff = x - self.base
        if diff < 70: return 0
        elif diff > 80: return 1
        else: return 3 * (self.T(x))**2 - 2 * (self.T(x))**3



class EnemyHP(BaseScaling):
    def __init__(self, base_level: int, current_level: int, base_health: int = 1):
        self.base = base_level
        self.current = current_level
        self.hp = base_health
        super().__init__(base_level, current_level)

    def f1(self, x):
        return 1 + 0.015 * (x - self.base)**2
    
    def f2(self, x):
        return 1 + ((24 * sqrt(5)) / 5) * (x - self.base)**0.5

    def get_multi(self):
        return (self.f1(self.current) * (1 - self.S(self.current))) + (self.f2(self.current) * self.S(self.current))

    def calc(self):
        return self.hp * self.get_multi()