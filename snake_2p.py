import curses
import random
import sys
import time

from config import *

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


def init_colors():
    try:
        curses.start_color()
        curses.use_default_colors()
        if curses.COLORS >= 8:
            curses.init_pair(COLOR_P1_HEAD, curses.COLOR_GREEN, -1)
            curses.init_pair(COLOR_P1_BODY, curses.COLOR_GREEN, -1)
            curses.init_pair(COLOR_P2_HEAD, curses.COLOR_BLUE, -1)
            curses.init_pair(COLOR_P2_BODY, curses.COLOR_BLUE, -1)
            curses.init_pair(COLOR_FOOD, curses.COLOR_RED, -1)
            curses.init_pair(COLOR_BOOST, curses.COLOR_YELLOW, -1)
            curses.init_pair(COLOR_BORDER, curses.COLOR_WHITE, -1)
            return True
    except curses.error:
        pass
    return False


def init_snakes():
    return list(P1_INIT_POS), list(P2_INIT_POS)


def get_empty_cells(p1_snake, p2_snake, food=None, boost=None):
    occupied = set(p1_snake) | set(p2_snake)
    if food:
        occupied.add(food)
    if boost:
        occupied.add(boost)
    empty = []
    for x in range(1, MAP_WIDTH + 1):
        for y in range(1, MAP_HEIGHT + 1):
            if (x, y) not in occupied:
                empty.append((x, y))
    return empty


def spawn_food(p1_snake, p2_snake, boost=None):
    empty = get_empty_cells(p1_snake, p2_snake, boost=boost)
    if not empty:
        return None
    return random.choice(empty)


def spawn_boost(p1_snake, p2_snake, food):
    if not BOOST_ENABLED:
        return None
    empty = get_empty_cells(p1_snake, p2_snake, food=food)
    if not empty:
        return None
    if random.random() < BOOST_SPAWN_CHANCE:
        return random.choice(empty)
    return None


def addch_color(stdscr, y, x, ch, color_pair, use_color):
    try:
        if use_color:
            stdscr.addch(y, x, ch, curses.color_pair(color_pair))
        else:
            stdscr.addch(y, x, ch)
    except curses.error:
        pass


def addstr_color(stdscr, y, x, s, color_pair, use_color):
    try:
        if use_color:
            stdscr.addstr(y, x, s, curses.color_pair(color_pair))
        else:
            stdscr.addstr(y, x, s)
    except curses.error:
        pass


def draw_map(stdscr, p1_snake, p2_snake, food, boost, boost_visible,
             p1_score, p2_score, p1_boost_end, p2_boost_end,
             game_over, winner, use_color):
    stdscr.erase()

    for y in range(MAP_HEIGHT + 2):
        for x in range(MAP_WIDTH + 2):
            if x == 0 or x == MAP_WIDTH + 1 or y == 0 or y == MAP_HEIGHT + 1:
                addch_color(stdscr, y, x, BORDER_CHAR, COLOR_BORDER, use_color)

    for i, (x, y) in enumerate(p1_snake):
        color = COLOR_P1_HEAD if i == 0 else COLOR_P1_BODY
        ch = P1_HEAD_CHAR if i == 0 else P1_BODY_CHAR
        addch_color(stdscr, y + 1, x + 1, ch, color, use_color)

    for i, (x, y) in enumerate(p2_snake):
        color = COLOR_P2_HEAD if i == 0 else COLOR_P2_BODY
        ch = P2_HEAD_CHAR if i == 0 else P2_BODY_CHAR
        addch_color(stdscr, y + 1, x + 1, ch, color, use_color)

    if food:
        addch_color(stdscr, food[1] + 1, food[0] + 1, FOOD_CHAR, COLOR_FOOD, use_color)

    if boost and boost_visible:
        addch_color(stdscr, boost[1] + 1, boost[0] + 1, BOOST_CHAR, COLOR_BOOST, use_color)

    info_y = MAP_HEIGHT + 3
    now = time.time()
    p1_status = ""
    p2_status = ""
    if p1_boost_end and now < p1_boost_end:
        p1_status = " [BOOST {:.1f}s]".format(p1_boost_end - now)
    if p2_boost_end and now < p2_boost_end:
        p2_status = " [BOOST {:.1f}s]".format(p2_boost_end - now)

    info_str = "P1 (WASD): {}{}  |  P2 (Arrows): {}{}".format(
        p1_score, p1_status, p2_score, p2_status)
    try:
        stdscr.addstr(info_y, 0, info_str)
    except curses.error:
        pass

    if game_over:
        try:
            result_lines = winner.split(" Final Score - ")
            result_line = result_lines[0]
            score_line = "Final Score - " + result_lines[1] if len(result_lines) > 1 else ""

            msg_y = MAP_HEIGHT // 2 - 1
            if score_line:
                stdscr.addstr(msg_y, max(0, (MAP_WIDTH + 2 - len(result_line)) // 2), result_line)
                stdscr.addstr(msg_y + 1, max(0, (MAP_WIDTH + 2 - len(score_line)) // 2), score_line)
                hint = "Press 'r' to restart or 'q' to quit"
                stdscr.addstr(msg_y + 3, max(0, (MAP_WIDTH + 2 - len(hint)) // 2), hint)
            else:
                stdscr.addstr(msg_y, max(0, (MAP_WIDTH + 2 - len(winner)) // 2), winner)
                hint = "Press 'r' to restart or 'q' to quit"
                stdscr.addstr(msg_y + 2, max(0, (MAP_WIDTH + 2 - len(hint)) // 2), hint)
        except curses.error:
            pass

    stdscr.refresh()


def check_wall_collision(head):
    x, y = head
    return x < 1 or x > MAP_WIDTH or y < 1 or y > MAP_HEIGHT


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


def get_current_tick(p1_boost_end, p2_boost_end):
    now = time.time()
    p1_boosted = p1_boost_end and now < p1_boost_end
    p2_boosted = p2_boost_end and now < p2_boost_end
    if p1_boosted or p2_boosted:
        return max(20, BASE_TICK_MS // BOOST_SPEED_MULTIPLIER)
    return BASE_TICK_MS


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(BASE_TICK_MS)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)

    use_color = init_colors()

    while True:
        p1_snake, p2_snake = init_snakes()
        p1_dir = P1_INIT_DIR
        p2_dir = P2_INIT_DIR
        p1_score = 0
        p2_score = 0
        p1_boost_end = None
        p2_boost_end = None
        food = spawn_food(p1_snake, p2_snake)
        boost = None
        last_boost_spawn = time.time()
        boost_visible = True
        last_boost_blink = time.time()
        game_over = False
        winner = ""

        while True:
            current_tick = get_current_tick(p1_boost_end, p2_boost_end)
            stdscr.timeout(current_tick)

            now = time.time()
            if boost:
                if now - last_boost_blink >= 0.15:
                    boost_visible = not boost_visible
                    last_boost_blink = now
            else:
                if BOOST_ENABLED and now - last_boost_spawn >= BOOST_SPAWN_INTERVAL_SEC:
                    boost = spawn_boost(p1_snake, p2_snake, food)
                    if boost:
                        boost_visible = True
                        last_boost_blink = now
                    last_boost_spawn = now

            if not game_over:
                draw_map(stdscr, p1_snake, p2_snake, food, boost, boost_visible,
                         p1_score, p2_score, p1_boost_end, p2_boost_end,
                         game_over, winner, use_color)

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
            p1_boost = (boost is not None and p1_new_head == boost)
            p2_boost = (boost is not None and p2_new_head == boost)

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
                score_info = "Final Score - P1: {} | P2: {}".format(p1_score, p2_score)
                if p1_dead and p2_dead:
                    winner = "DRAW! Both died! " + score_info
                elif p1_dead:
                    winner = "P2 WINS! " + score_info
                else:
                    winner = "P1 WINS! " + score_info
                game_over = True
                draw_map(stdscr, p1_snake, p2_snake, food, boost, boost_visible,
                         p1_score, p2_score, p1_boost_end, p2_boost_end,
                         game_over, winner, use_color)
                continue

            p1_snake = move_snake(p1_snake, p1_dir, p1_grow)
            p2_snake = move_snake(p2_snake, p2_dir, p2_grow)

            if p1_grow:
                p1_score += FOOD_SCORE
            if p2_grow:
                p2_score += FOOD_SCORE

            if p1_grow or p2_grow:
                food = spawn_food(p1_snake, p2_snake, boost=boost)

            if p1_boost:
                p1_boost_end = time.time() + BOOST_DURATION_SEC
                boost = None
                last_boost_spawn = time.time()
            if p2_boost:
                p2_boost_end = time.time() + BOOST_DURATION_SEC
                boost = None
                last_boost_spawn = time.time()


if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nGame exited.")
        sys.exit(0)
