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

class Snake:
    def __init__(self, x, y, direction, color_char, name):
        self.body = [(x, y), (x - direction[0], y - direction[1])]
        self.direction = direction
        self.next_direction = direction
        self.color_char = color_char
        self.name = name
        self.score = 0
        self.alive = True

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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_map(snake1, snake2, foods):
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

    if snake1.alive:
        for i, (x, y) in enumerate(snake1.body):
            if 0 < y < HEIGHT - 1 and 0 < x < WIDTH - 1:
                grid[y][x] = snake1.color_char.upper() if i == 0 else snake1.color_char.lower()

    if snake2.alive:
        for i, (x, y) in enumerate(snake2.body):
            if 0 < y < HEIGHT - 1 and 0 < x < WIDTH - 1:
                grid[y][x] = snake2.color_char.upper() if i == 0 else snake2.color_char.lower()

    output = []
    for row in grid:
        output.append(''.join(row))
    output.append('')
    output.append(f'{snake1.name}(WASD): {snake1.score}  |  {snake2.name}(Arrows): {snake2.score}')
    output.append('蛇头用大写字母，身体用小写。吃到*得1分。撞墙或撞蛇即死。')
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

def random_food(snake1, snake2, existing_foods, count=1):
    all_bodies = set()
    if snake1.alive:
        all_bodies.update(snake1.body)
    if snake2.alive:
        all_bodies.update(snake2.body)
    all_bodies.update(existing_foods)

    new_foods = list(existing_foods)
    while len(new_foods) < count:
        x = random.randint(1, WIDTH - 2)
        y = random.randint(1, HEIGHT - 2)
        if (x, y) not in all_bodies:
            new_foods.append((x, y))
            all_bodies.add((x, y))
    return new_foods

def check_collision(snake, other_snake):
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

def main():
    snake1 = Snake(8, 10, RIGHT, 'X', 'Player1')
    snake2 = Snake(WIDTH - 9, 10, LEFT, 'O', 'Player2')
    foods = random_food(snake1, snake2, [], 3)

    tick_rate = 0.12
    last_tick = time.time()
    key_buffer = []

    while snake1.alive or snake2.alive:
        current_time = time.time()
        elapsed = current_time - last_tick

        key = get_key()
        if key:
            key_buffer.append(key)

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
                    snake1.score += 1

            if snake2.alive:
                head2 = snake2.body[0]
                new_head2 = (head2[0] + snake2.direction[0], head2[1] + snake2.direction[1])
                if new_head2 in foods and new_head2 in new_foods:
                    grow2 = True
                    new_foods.remove(new_head2)
                    snake2.score += 1

            if snake1.alive:
                snake1.move(grow=grow1)
            if snake2.alive:
                snake2.move(grow=grow2)

            foods = new_foods
            foods = random_food(snake1, snake2, foods, 3)

            if snake1.alive and check_collision(snake1, snake2):
                snake1.alive = False
            if snake2.alive and check_collision(snake2, snake1):
                snake2.alive = False

            if snake1.alive and snake2.alive:
                if snake1.body[0] == snake2.body[0]:
                    snake1.alive = False
                    snake2.alive = False

            clear_screen()
            draw_map(snake1, snake2, foods)

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
