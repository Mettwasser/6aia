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

    def T1(self, x):
        return (x - self.base - 70) / 10

    def T2(self, x):
        return (x - self.base - 45) / 5

    def S1(self, x):
        diff = x - self.base
        if diff < 70: return 0
        elif diff > 80: return 1
        else: return 3 * (self.T1(x))**2 - 2 * (self.T1(x))**3

    def S2(self, x):
        diff = x - self.base
        if diff < 45: return 0
        elif diff > 50: return 1
        else: return 3 * (self.T2(x))**2 - 2 * (self.T2(x))**3



class EnemyHP(BaseScaling):
    def __init__(self, base_level: int, current_level: int, base_health: int = 1):
        super().__init__(base_level, current_level)
        self.base = base_level
        self.current = current_level
        self.hp = base_health

    def f1(self, x):
        return 1 + 0.015 * (x - self.base)**2
    
    def f2(self, x):
        return 1 + ((24 * sqrt(5)) / 5) * (x - self.base)**0.5

    def get_multi(self):
        return (self.f1(self.current) * (1 - self.S1(self.current))) + (self.f2(self.current) * self.S1(self.current))

    def calc(self):
        return self.hp * self.get_multi()


class EnemyShields(BaseScaling):
    def __init__(self, base_level: int, current_level: int, base_shields: int = 1):
        super().__init__(base_level, current_level)
        self.base = base_level
        self.current = current_level
        self.S1hields = base_shields


    def f1(self, x):
        return 1 + 0.02 * (x - self.base)**1.75
    
    def f2(self, x):
        return 1 + 1.6 * (x - self.base)**0.75

    def get_multi(self):
        return (self.f1(self.current) * (1 - self.S1(self.current))) + (self.f2(self.current) * self.S1(self.current))

    def calc(self):
        return self.S1hields * self.get_multi()


class EnemyArmor(BaseScaling):
    def __init__(self, base_level: int, current_level: int, base_armor: int = 1):
        super().__init__(base_level, current_level)
        self.base = base_level
        self.current = current_level
        self.armor = base_armor


    def f1(self, x):
        return 1 + 0.005 * (x - self.base)**1.75
    
    def f2(self, x):
        return 1 + 0.4 * (x - self.base)**0.75

    def get_multi(self):
        return (self.f1(self.current) * (1 - self.S1(self.current))) + (self.f2(self.current) * self.S1(self.current))

    def calc(self):
        return self.armor * self.get_multi()

class EnemyOverguard(BaseScaling):
    def __init__(self, base_level: int, current_level: int, base_overguard: int = 1):
        super().__init__(base_level, current_level)
        self.base = base_level
        self.current = current_level
        self.overguard = base_overguard


    def f1(self, x):
        return 1 + 0.0015 * (x - self.base)**4
    
    def f2(self, x):
        return 1 + 260 * (x - self.base)**0.9

    def get_multi(self):
        return (self.f1(self.current) * (1 - self.S2(self.current))) + (self.f2(self.current) * self.S2(self.current))

    def calc(self):
        return self.overguard * self.get_multi()

class EnemyDamage(BaseScaling):
    def __init__(self, base_level: int, current_level: int, base_damage: int = 1):
        super().__init__(base_level, current_level)
        self.base = base_level
        self.current = current_level
        self.dmg = base_damage

    def f1(self):
        return
    
    def f2(self):
        return

    def calc(self):
        return self.dmg * (1 + 0.015 * (self.current - self.base)**1.55)

class EnemyAffinity(BaseScaling):
    def __init__(self, current_level: int, base_affinity: int = 1):
        self.current = current_level
        self.aff = base_affinity

    def f1(self):
        return
    
    def f2(self):
        return

    def calc(self):
        return self.aff * (1 + (0.1425 * (self.current**0.5)))

