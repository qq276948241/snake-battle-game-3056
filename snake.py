import msvcrt
import random
import os
import time

WIDTH = 30
HEIGHT = 20

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

BASE_TICK = 0.12
POWERUP_DURATION = 5.0
POWERUP_SPAWN_INTERVAL = 10.0
MAX_POWERUPS = 2
FOOD_COUNT = 3

SPEED = 'speed'
SHIELD = 'shield'
DOUBLE = 'double'

POWERUP_TYPES = [SPEED, SHIELD, DOUBLE]
POWERUP_SYMBOLS = {
    SPEED: '>',
    SHIELD: '@',
    DOUBLE: '!',
}
POWERUP_NAMES = {
    SPEED: '加速',
    SHIELD: '无敌',
    DOUBLE: '双倍',
}

class Snake:
    def __init__(self, x, y, direction, color_char, name):
        self.body = [(x, y), (x - direction[0], y - direction[1])]
        self.direction = direction
        self.next_direction = direction
        self.color_char = color_char
        self.name = name
        self.score = 0
        self.alive = True
        self.buffs = {}

    def move(self, grow=False):
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        self.body.insert(0, new_head)
        if not grow:
            self.body.pop()

    def set_direction(self, new_dir):
        if (new_dir[0] + self.direction[0], new_dir[1] + self.direction[1]) != (0, 0):
            self.next_direction = new_dir

    def update_direction(self):
        self.direction = self.next_direction

    def add_buff(self, buff_type, now, duration=POWERUP_DURATION):
        self.buffs[buff_type] = now + duration

    def has_buff(self, buff_type, now):
        return buff_type in self.buffs and self.buffs[buff_type] > now

    def update_buffs(self, now):
        expired = [k for k, v in self.buffs.items() if v <= now]
        for k in expired:
            del self.buffs[k]

    def remaining_buff_time(self, buff_type, now):
        if not self.has_buff(buff_type, now):
            return 0
        return max(0, self.buffs[buff_type] - now)

    def active_buffs_str(self, now):
        parts = []
        for t in POWERUP_TYPES:
            if self.has_buff(t, now):
                remain = self.remaining_buff_time(t, now)
                parts.append(f'{POWERUP_NAMES[t]}({remain:.1f}s)')
        return ', '.join(parts) if parts else '无'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_map(snake1, snake2, foods, powerups, now):
    grid = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]

    for x in range(WIDTH):
        grid[0][x] = '#'
        grid[HEIGHT - 1][x] = '#'
    for y in range(HEIGHT):
        grid[y][0] = '#'
        grid[y][WIDTH - 1] = '#'

    for fx, fy in foods:
        if 0 <= fy < HEIGHT and 0 <= fx < WIDTH:
            grid[fy][fx] = '*'

    for px, py, ptype in powerups:
        if 0 <= py < HEIGHT and 0 <= px < WIDTH:
            grid[py][px] = POWERUP_SYMBOLS[ptype]

    if snake1.alive:
        for i, (x, y) in enumerate(snake1.body):
            if 0 < y < HEIGHT - 1 and 0 < x < WIDTH - 1:
                if grid[y][x] == ' ':
                    grid[y][x] = snake1.color_char.upper() if i == 0 else snake1.color_char.lower()

    if snake2.alive:
        for i, (x, y) in enumerate(snake2.body):
            if 0 < y < HEIGHT - 1 and 0 < x < WIDTH - 1:
                if grid[y][x] == ' ':
                    grid[y][x] = snake2.color_char.upper() if i == 0 else snake2.color_char.lower()

    output = []
    for row in grid:
        output.append(''.join(row))
    output.append('')
    output.append(f'{snake1.name}(WASD): {snake1.score}  |  {snake2.name}(Arrows): {snake2.score}')
    output.append(f'道具: >加速 @无敌 !双倍    食物:*')
    output.append(f'{snake1.name} Buff: {snake1.active_buffs_str(now)}')
    output.append(f'{snake2.name} Buff: {snake2.active_buffs_str(now)}')
    print('\n'.join(output))

def get_key():
    if msvcrt.kbhit():
        ch = msvcrt.getch()
        if ch == b'\xe0':
            ch2 = msvcrt.getch()
            if ch2 == b'H':
                return 'UP'
            elif ch2 == b'P':
                return 'DOWN'
            elif ch2 == b'K':
                return 'LEFT'
            elif ch2 == b'M':
                return 'RIGHT'
        else:
            try:
                return ch.decode('ascii').lower()
            except:
                return None
    return None

def random_food(snake1, snake2, existing_foods, powerups, count=FOOD_COUNT):
    all_occupied = set()
    if snake1.alive:
        all_occupied.update(snake1.body)
    if snake2.alive:
        all_occupied.update(snake2.body)
    all_occupied.update(existing_foods)
    all_occupied.update((px, py) for px, py, _ in powerups)

    new_foods = list(existing_foods)
    while len(new_foods) < count:
        x = random.randint(1, WIDTH - 2)
        y = random.randint(1, HEIGHT - 2)
        if (x, y) not in all_occupied:
            new_foods.append((x, y))
            all_occupied.add((x, y))
    return new_foods

def random_powerup(snake1, snake2, foods, existing_powerups, count=1):
    all_occupied = set()
    if snake1.alive:
        all_occupied.update(snake1.body)
    if snake2.alive:
        all_occupied.update(snake2.body)
    all_occupied.update(foods)
    all_occupied.update((px, py) for px, py, _ in existing_powerups)

    new_powerups = list(existing_powerups)
    attempts = 0
    while len(new_powerups) < count and attempts < 100:
        attempts += 1
        x = random.randint(1, WIDTH - 2)
        y = random.randint(1, HEIGHT - 2)
        if (x, y) not in all_occupied:
            ptype = random.choice(POWERUP_TYPES)
            new_powerups.append((x, y, ptype))
            all_occupied.add((x, y))
    return new_powerups

def check_collision(snake, other_snake, now):
    if snake.has_buff(SHIELD, now):
        return False
    head = snake.body[0]
    hx, hy = head
    if hx <= 0 or hx >= WIDTH - 1 or hy <= 0 or hy >= HEIGHT - 1:
        return True
    for seg in snake.body[1:]:
        if head == seg:
            return True
    if other_snake.alive:
        for seg in other_snake.body:
            if head == seg:
                return True
    return False

def get_effective_tick(snake1, snake2, now):
    min_tick = BASE_TICK
    if snake1.alive and snake1.has_buff(SPEED, now):
        min_tick = min(min_tick, BASE_TICK / 2)
    if snake2.alive and snake2.has_buff(SPEED, now):
        min_tick = min(min_tick, BASE_TICK / 2)
    return min_tick

def main():
    snake1 = Snake(8, 10, RIGHT, 'X', 'Player1')
    snake2 = Snake(WIDTH - 9, 10, LEFT, 'O', 'Player2')
    foods = random_food(snake1, snake2, [], [], FOOD_COUNT)
    powerups = []

    start_time = time.time()
    last_tick = start_time
    last_powerup_spawn = start_time
    key_buffer = []

    while snake1.alive or snake2.alive:
        current_time = time.time()

        key = get_key()
        if key:
            key_buffer.append(key)

        tick_rate = get_effective_tick(snake1, snake2, current_time)
        elapsed = current_time - last_tick

        if snake1.alive:
            snake1.update_buffs(current_time)
        if snake2.alive:
            snake2.update_buffs(current_time)

        if len(powerups) < MAX_POWERUPS and (current_time - last_powerup_spawn) >= POWERUP_SPAWN_INTERVAL:
            powerups = random_powerup(snake1, snake2, foods, powerups, len(powerups) + 1)
            last_powerup_spawn = current_time

        if elapsed >= tick_rate:
            last_tick = current_time

            for k in key_buffer:
                if k == 'w':
                    snake1.set_direction(UP)
                elif k == 's':
                    snake1.set_direction(DOWN)
                elif k == 'a':
                    snake1.set_direction(LEFT)
                elif k == 'd':
                    snake1.set_direction(RIGHT)
                elif k == 'UP':
                    snake2.set_direction(UP)
                elif k == 'DOWN':
                    snake2.set_direction(DOWN)
                elif k == 'LEFT':
                    snake2.set_direction(LEFT)
                elif k == 'RIGHT':
                    snake2.set_direction(RIGHT)
            key_buffer = []

            if snake1.alive:
                snake1.update_direction()
            if snake2.alive:
                snake2.update_direction()

            grow1 = False
            grow2 = False
            new_foods = list(foods)

            if snake1.alive:
                head1 = snake1.body[0]
                new_head1 = (head1[0] + snake1.direction[0], head1[1] + snake1.direction[1])
                if new_head1 in foods:
                    grow1 = True
                    new_foods.remove(new_head1)
                    gain = 2 if snake1.has_buff(DOUBLE, current_time) else 1
                    snake1.score += gain

            if snake2.alive:
                head2 = snake2.body[0]
                new_head2 = (head2[0] + snake2.direction[0], head2[1] + snake2.direction[1])
                if new_head2 in foods and new_head2 in new_foods:
                    grow2 = True
                    new_foods.remove(new_head2)
                    gain = 2 if snake2.has_buff(DOUBLE, current_time) else 1
                    snake2.score += gain

            foods = new_foods

            new_powerups = list(powerups)
            if snake1.alive:
                head1 = snake1.body[0]
                new_head1 = (head1[0] + snake1.direction[0], head1[1] + snake1.direction[1])
                for i, (px, py, ptype) in enumerate(new_powerups):
                    if new_head1 == (px, py):
                        snake1.add_buff(ptype, current_time)
                        new_powerups.pop(i)
                        break

            if snake2.alive:
                head2 = snake2.body[0]
                new_head2 = (head2[0] + snake2.direction[0], head2[1] + snake2.direction[1])
                for i, (px, py, ptype) in enumerate(new_powerups):
                    if new_head2 == (px, py):
                        snake2.add_buff(ptype, current_time)
                        new_powerups.pop(i)
                        break
            powerups = new_powerups

            if snake1.alive:
                snake1.move(grow=grow1)
            if snake2.alive:
                snake2.move(grow=grow2)

            foods = random_food(snake1, snake2, foods, powerups, FOOD_COUNT)

            if snake1.alive and check_collision(snake1, snake2, current_time):
                snake1.alive = False
            if snake2.alive and check_collision(snake2, snake1, current_time):
                snake2.alive = False

            if snake1.alive and snake2.alive:
                if snake1.body[0] == snake2.body[0]:
                    if not snake1.has_buff(SHIELD, current_time):
                        snake1.alive = False
                    if not snake2.has_buff(SHIELD, current_time):
                        snake2.alive = False

            clear_screen()
            draw_map(snake1, snake2, foods, powerups, current_time)

    print('')
    print('=== GAME OVER ===')
    print(f'{snake1.name} 最终得分: {snake1.score}')
    print(f'{snake2.name} 最终得分: {snake2.score}')
    if snake1.score > snake2.score:
        print(f'>>> {snake1.name} 获胜！ <<<')
    elif snake2.score > snake1.score:
        print(f'>>> {snake2.name} 获胜！ <<<')
    else:
        print('>>> 平局！ <<<')
    print('')
    print('按任意键退出...')
    msvcrt.getch()

if __name__ == '__main__':
    main()
