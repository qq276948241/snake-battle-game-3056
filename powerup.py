import random
import time


TYPE_STAR = 'star'
TYPE_SHIELD = 'shield'

STAR_DURATION = 2.0
SHIELD_HITS = 1

POWERUP_COLOR = {
    TYPE_STAR: 7,
    TYPE_SHIELD: 8,
}

POWERUP_CHAR = {
    TYPE_STAR: '+',
    TYPE_SHIELD: 'S',
}

ALL_TYPES = [TYPE_STAR, TYPE_SHIELD]

SPAWN_INTERVAL = 5.0
MAX_ON_MAP = 2


class PowerUp:
    def __init__(self, x, y, ptype):
        self.x = x
        self.y = y
        self.type = ptype

    def pos(self):
        return (self.x, self.y)

    def char(self):
        return POWERUP_CHAR[self.type]

    def color(self):
        return POWERUP_COLOR[self.type]


class ActiveEffects:
    def __init__(self):
        self.speed_until = 0.0
        self.shield_count = 0

    def has_speed(self, now):
        return now < self.speed_until

    def speed_remaining(self, now):
        return max(0.0, self.speed_until - now)

    def activate_speed(self, now, duration=STAR_DURATION):
        self.speed_until = max(self.speed_until, now) + duration

    def has_shield(self):
        return self.shield_count > 0

    def activate_shield(self, hits=SHIELD_HITS):
        self.shield_count += hits

    def consume_shield(self):
        if self.shield_count > 0:
            self.shield_count -= 1
            return True
        return False


class PowerUpManager:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.powerups = []
        self.last_spawn = 0.0

    def reset(self):
        self.powerups = []
        self.last_spawn = 0.0

    def occupy_set(self):
        s = set()
        for p in self.powerups:
            s.add(p.pos())
        return s

    def _available_cells(self, occupied):
        cells = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if (x, y) not in occupied:
                    cells.append((x, y))
        return cells

    def update(self, now, occupied):
        if len(self.powerups) < MAX_ON_MAP and (now - self.last_spawn) >= SPAWN_INTERVAL:
            available = self._available_cells(occupied | self.occupy_set())
            if available:
                x, y = random.choice(available)
                ptype = random.choice(ALL_TYPES)
                self.powerups.append(PowerUp(x, y, ptype))
                self.last_spawn = now

    def try_collect(self, head_pos):
        for i, p in enumerate(self.powerups):
            if p.pos() == head_pos:
                collected = self.powerups.pop(i)
                return collected
        return None

    def apply_effect(self, ptype, effects, now):
        if ptype == TYPE_STAR:
            effects.activate_speed(now)
        elif ptype == TYPE_SHIELD:
            effects.activate_shield()
