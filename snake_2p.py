import curses
import random
import sys
import time

MAP_WIDTH = 30
MAP_HEIGHT = 20

P1_KEYS = {
    ord('w'): (0, -1),
    ord('s'): (0, 1),
    ord('a'): (-1, 0),
    ord('d'): (1, 0),
    ord('W'): (0, -1),
    ord('S'): (0, 1),
    ord('A'): (-1, 0),
    ord('D'): (1, 0),
}

P2_KEYS = {
    curses.KEY_UP: (0, -1),
    curses.KEY_DOWN: (0, 1),
    curses.KEY_LEFT: (-1, 0),
    curses.KEY_RIGHT: (1, 0),
}

OPPOSITE = {
    (0, -1): (0, 1),
    (0, 1): (0, -1),
    (-1, 0): (1, 0),
    (1, 0): (-1, 0),
}


def init_snakes():
    p1_snake = [
        (5, MAP_HEIGHT // 2),
        (4, MAP_HEIGHT // 2),
        (3, MAP_HEIGHT // 2),
    ]
    p2_snake = [
        (MAP_WIDTH - 6, MAP_HEIGHT // 2),
        (MAP_WIDTH - 5, MAP_HEIGHT // 2),
        (MAP_WIDTH - 4, MAP_HEIGHT // 2),
    ]
    return p1_snake, p2_snake


def spawn_food(p1_snake, p2_snake):
    occupied = set(p1_snake) | set(p2_snake)
    empty = []
    for x in range(1, MAP_WIDTH):
        for y in range(1, MAP_HEIGHT):
            if (x, y) not in occupied:
                empty.append((x, y))
    if not empty:
        return None
    return random.choice(empty)


def draw_map(stdscr, p1_snake, p2_snake, food, p1_score, p2_score, game_over, winner):
    stdscr.erase()

    for y in range(MAP_HEIGHT + 2):
        for x in range(MAP_WIDTH + 2):
            if x == 0 or x == MAP_WIDTH + 1 or y == 0 or y == MAP_HEIGHT + 1:
                try:
                    stdscr.addch(y, x, '#')
                except curses.error:
                    pass

    p1_head = p1_snake[0]
    p2_head = p2_snake[0]

    for i, (x, y) in enumerate(p1_snake):
        try:
            if i == 0:
                stdscr.addch(y + 1, x + 1, 'O')
            else:
                stdscr.addch(y + 1, x + 1, 'o')
        except curses.error:
            pass

    for i, (x, y) in enumerate(p2_snake):
        try:
            if i == 0:
                stdscr.addch(y + 1, x + 1, 'X')
            else:
                stdscr.addch(y + 1, x + 1, 'x')
        except curses.error:
            pass

    if food:
        try:
            stdscr.addch(food[1] + 1, food[0] + 1, '*')
        except curses.error:
            pass

    info_y = MAP_HEIGHT + 3
    try:
        stdscr.addstr(info_y, 0, "P1 (WASD): {}  |  P2 (Arrows): {}".format(p1_score, p2_score))
    except curses.error:
        pass

    if game_over:
        msg_y = MAP_HEIGHT // 2
        msg_x = (MAP_WIDTH - len(winner)) // 2
        try:
            stdscr.addstr(msg_y, max(0, msg_x), winner)
            stdscr.addstr(msg_y + 2, 0, "Press 'r' to restart or 'q' to quit")
        except curses.error:
            pass

    stdscr.refresh()


def check_wall_collision(head):
    x, y = head
    return x < 1 or x >= MAP_WIDTH or y < 1 or y >= MAP_HEIGHT


def check_snake_collision(head, snake, exclude_head=False):
    start = 1 if exclude_head else 0
    return head in snake[start:]


def move_snake(snake, direction, grow):
    head = snake[0]
    new_head = (head[0] + direction[0], head[1] + direction[1])
    new_snake = [new_head] + list(snake)
    if not grow:
        new_snake.pop()
    return new_snake


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)

    try:
        curses.start_color()
        curses.use_default_colors()
    except curses.error:
        pass

    while True:
        p1_snake, p2_snake = init_snakes()
        p1_dir = (1, 0)
        p2_dir = (-1, 0)
        p1_score = 0
        p2_score = 0
        food = spawn_food(p1_snake, p2_snake)
        game_over = False
        winner = ""

        while True:
            if not game_over:
                draw_map(stdscr, p1_snake, p2_snake, food, p1_score, p2_score, game_over, winner)

            key = stdscr.getch()

            if game_over:
                if key == ord('r') or key == ord('R'):
                    break
                if key == ord('q') or key == ord('Q'):
                    return
                continue

            if key == ord('q') or key == ord('Q'):
                return

            if key in P1_KEYS:
                new_dir = P1_KEYS[key]
                if new_dir != OPPOSITE.get(p1_dir):
                    p1_dir = new_dir
            elif key in P2_KEYS:
                new_dir = P2_KEYS[key]
                if new_dir != OPPOSITE.get(p2_dir):
                    p2_dir = new_dir

            p1_head = p1_snake[0]
            p1_new_head = (p1_head[0] + p1_dir[0], p1_head[1] + p1_dir[1])
            p2_head = p2_snake[0]
            p2_new_head = (p2_head[0] + p2_dir[0], p2_head[1] + p2_dir[1])

            p1_grow = (food is not None and p1_new_head == food)
            p2_grow = (food is not None and p2_new_head == food)

            p1_dead = False
            p2_dead = False

            if check_wall_collision(p1_new_head):
                p1_dead = True
            if check_wall_collision(p2_new_head):
                p2_dead = True

            if p1_new_head == p2_new_head:
                p1_dead = True
                p2_dead = True

            if not p1_dead:
                if check_snake_collision(p1_new_head, p1_snake, exclude_head=True):
                    p1_dead = True
                temp_p2 = move_snake(p2_snake, p2_dir, p2_grow) if not p2_dead else p2_snake
                if check_snake_collision(p1_new_head, temp_p2, exclude_head=False):
                    p1_dead = True

            if not p2_dead:
                if check_snake_collision(p2_new_head, p2_snake, exclude_head=True):
                    p2_dead = True
                temp_p1 = move_snake(p1_snake, p1_dir, p1_grow) if not p1_dead else p1_snake
                if check_snake_collision(p2_new_head, temp_p1, exclude_head=False):
                    p2_dead = True

            if p1_dead or p2_dead:
                if p1_dead and p2_dead:
                    winner = "DRAW! Both died!"
                elif p1_dead:
                    winner = "P2 WINS!"
                else:
                    winner = "P1 WINS!"
                game_over = True
                draw_map(stdscr, p1_snake, p2_snake, food, p1_score, p2_score, game_over, winner)
                continue

            p1_snake = move_snake(p1_snake, p1_dir, p1_grow)
            p2_snake = move_snake(p2_snake, p2_dir, p2_grow)

            if p1_grow:
                p1_score += 10
            if p2_grow:
                p2_score += 10

            if p1_grow or p2_grow:
                food = spawn_food(p1_snake, p2_snake)


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nGame exited.")
        sys.exit(0)
