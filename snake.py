import sys
import os
import time
import random
import msvcrt
import ctypes

MAP_WIDTH = 30
MAP_HEIGHT = 20
TICK_INTERVAL = 0.12

GREEN = '\x1b[32m'
CYAN = '\x1b[36m'
YELLOW = '\x1b[33m'
WHITE = '\x1b[37m'
RED = '\x1b[31m'
BOLD = '\x1b[1m'
REVERSE = '\x1b[7m'
RESET = '\x1b[0m'

P1_KEYS = {
    b'w': (0, -1), b'W': (0, -1),
    b's': (0, 1),  b'S': (0, 1),
    b'a': (-1, 0), b'A': (-1, 0),
    b'd': (1, 0),  b'D': (1, 0),
}

P2_KEYS = {
    b'H': (0, -1),
    b'P': (0, 1),
    b'K': (-1, 0),
    b'M': (1, 0),
}


def enable_ansi():
    kernel32 = ctypes.windll.kernel32
    STD_OUTPUT_HANDLE = -11
    handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    mode = ctypes.c_ulong()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    ENABLE_PROCESSED_OUTPUT = 0x0001
    mode.value |= ENABLE_VIRTUAL_TERMINAL_PROCESSING | ENABLE_PROCESSED_OUTPUT
    kernel32.SetConsoleMode(handle, mode)


def hide_cursor():
    sys.stdout.write('\x1b[?25l')
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write('\x1b[?25h')
    sys.stdout.flush()


def clear_screen():
    sys.stdout.write('\x1b[2J\x1b[H')
    sys.stdout.flush()


def move_cursor(y, x):
    sys.stdout.write(f'\x1b[{y+1};{x+1}H')


def get_terminal_size():
    try:
        size = os.get_terminal_size()
        return size.lines, size.columns
    except OSError:
        return MAP_HEIGHT + 4, MAP_WIDTH + 4


class Snake:
    def __init__(self, x, y, dx, dy, body_char, head_char, color):
        self.body = [(x, y), (x - dx, y - dy), (x - 2 * dx, y - 2 * dy)]
        self.dir = (dx, dy)
        self.next_dir = (dx, dy)
        self.score = 0
        self.alive = True
        self.body_char = body_char
        self.head_char = head_char
        self.color = color
        self.grow_pending = 0

    def set_direction(self, dx, dy):
        if (dx, dy) != (-self.dir[0], -self.dir[1]):
            self.next_dir = (dx, dy)

    def move(self):
        if not self.alive:
            return
        self.dir = self.next_dir
        head = self.body[0]
        new_head = (head[0] + self.dir[0], head[1] + self.dir[1])
        self.body.insert(0, new_head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def grow(self):
        self.grow_pending += 1


def spawn_food(snakes, width, height):
    occupied = set()
    for snake in snakes:
        for seg in snake.body:
            occupied.add(seg)
    available = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if (x, y) not in occupied:
                available.append((x, y))
    if not available:
        return None
    return random.choice(available)


def check_collision(snake, snakes, width, height):
    head = snake.body[0]
    x, y = head
    if x <= 0 or x >= width - 1 or y <= 0 or y >= height - 1:
        return True
    for other in snakes:
        for i, seg in enumerate(other.body):
            if other is snake and i == 0:
                continue
            if seg == head:
                return True
    return False


def build_map_buffer(snakes, food, width, height, offset_x, offset_y, game_over, winner_msg):
    lines = []

    for y in range(height):
        row_chars = []
        row_colors = []
        for x in range(width):
            row_chars.append(' ')
            row_colors.append('')

        if y == 0 or y == height - 1:
            for x in range(width):
                row_chars[x] = '#'
        else:
            row_chars[0] = '#'
            row_chars[width - 1] = '#'

        lines.append([row_chars, row_colors])

    score_line = f" P1(WASD): {snakes[0].score}  |  P2(Arrows): {snakes[1].score} "
    score_x = max(0, (width - len(score_line)) // 2)
    for i, ch in enumerate(score_line):
        if score_x + i < width:
            lines[0][0][score_x + i] = ch
            lines[0][1][score_x + i] = WHITE + BOLD

    for snake in snakes:
        for i, (x, y) in enumerate(snake.body):
            if 0 < x < width - 1 and 0 < y < height - 1:
                ch = snake.head_char if i == 0 else snake.body_char
                lines[y][0][x] = ch
                lines[y][1][x] = snake.color if snake.alive else RED

    if food:
        fx, fy = food
        if 0 < fx < width - 1 and 0 < fy < height - 1:
            lines[fy][0][fx] = '*'
            lines[fy][1][fx] = YELLOW

    if not game_over:
        hint = "P1:WASD  P2:Arrows"
        hx = max(0, (width - len(hint)) // 2)
        for i, ch in enumerate(hint):
            if hx + i < width:
                lines[height - 1][0][hx + i] = ch
                lines[height - 1][1][hx + i] = WHITE

    output_lines = []
    output_lines.append('')
    for y in range(height):
        row_out = []
        last_color = ''
        for x in range(width):
            ch = lines[y][0][x]
            color = lines[y][1][x]
            if color != last_color:
                if last_color:
                    row_out.append(RESET)
                if color:
                    row_out.append(color)
                last_color = color
            row_out.append(ch)
        if last_color:
            row_out.append(RESET)
        output_lines.append(''.join(row_out))

    if game_over:
        msgs = [
            " GAME OVER ",
            f" P1: {snakes[0].score}  |  P2: {snakes[1].score} ",
            winner_msg,
            " Press any key to exit ",
        ]
        mid_y = height // 2
        for i, msg in enumerate(msgs):
            target_y = mid_y - 2 + i
            if 0 <= target_y < height:
                mx = max(0, (width - len(msg)) // 2)
                padded = ' ' * mx + REVERSE + BOLD + WHITE + msg + RESET
                output_lines[target_y + 1] = padded + RESET

    return '\n'.join(output_lines)


def read_key_nonblocking():
    keys = []
    while msvcrt.kbhit():
        ch = msvcrt.getch()
        keys.append(ch)
        if ch in (b'\xe0', b'\x00'):
            if msvcrt.kbhit():
                ch2 = msvcrt.getch()
                keys.append(ch2)
    return keys


def main():
    enable_ansi()
    hide_cursor()
    clear_screen()

    term_h, term_w = get_terminal_size()
    if term_h < MAP_HEIGHT + 4 or term_w < MAP_WIDTH + 4:
        show_cursor()
        print(f"Terminal too small! Need at least {MAP_WIDTH + 4} columns x {MAP_HEIGHT + 4} rows")
        print(f"Current: {term_w}x{term_h}")
        return

    offset_x = max(0, (term_w - MAP_WIDTH) // 2)
    offset_y = max(0, (term_h - MAP_HEIGHT) // 2)

    p1 = Snake(8, MAP_HEIGHT // 2, 1, 0, 'o', 'O', GREEN)
    p2 = Snake(MAP_WIDTH - 9, MAP_HEIGHT // 2, -1, 0, 'x', 'X', CYAN)
    snakes = [p1, p2]

    food = spawn_food(snakes, MAP_WIDTH, MAP_HEIGHT)
    game_over = False
    winner_msg = ""
    last_output = ""

    try:
        while True:
            start_time = time.time()

            keys = read_key_nonblocking()
            if game_over:
                if keys:
                    break
            else:
                i = 0
                while i < len(keys):
                    k = keys[i]
                    if k in P1_KEYS:
                        dx, dy = P1_KEYS[k]
                        p1.set_direction(dx, dy)
                    if k in P2_KEYS:
                        dx, dy = P2_KEYS[k]
                        p2.set_direction(dx, dy)
                    if k in (b'\xe0', b'\x00') and i + 1 < len(keys):
                        k2 = keys[i + 1]
                        if k2 in P2_KEYS:
                            dx, dy = P2_KEYS[k2]
                            p2.set_direction(dx, dy)
                        i += 2
                        continue
                    i += 1

            if not game_over:
                for s in snakes:
                    s.move()

                for s in snakes:
                    if s.alive and check_collision(s, snakes, MAP_WIDTH, MAP_HEIGHT):
                        s.alive = False

                heads = {}
                for s in snakes:
                    if s.alive:
                        h = s.body[0]
                        if h in heads:
                            s.alive = False
                            heads[h].alive = False
                        else:
                            heads[h] = s

                for s in snakes:
                    if s.alive and food and s.body[0] == food:
                        s.score += 10
                        s.grow()
                        food = spawn_food(snakes, MAP_WIDTH, MAP_HEIGHT)

                if not any(s.alive for s in snakes):
                    game_over = True
                    if p1.score > p2.score:
                        winner_msg = " Player 1 Wins! "
                    elif p2.score > p1.score:
                        winner_msg = " Player 2 Wins! "
                    else:
                        winner_msg = " It's a Tie! "

            output = build_map_buffer(snakes, food, MAP_WIDTH, MAP_HEIGHT,
                                      offset_x, offset_y, game_over, winner_msg)

            if output != last_output:
                move_cursor(0, 0)
                sys.stdout.write(output)
                sys.stdout.flush()
                last_output = output

            elapsed = time.time() - start_time
            remaining = TICK_INTERVAL - elapsed
            if remaining > 0:
                time.sleep(remaining)

    except KeyboardInterrupt:
        pass
    finally:
        show_cursor()
        sys.stdout.write(RESET)
        clear_screen()
        print(f"\nFinal Score - P1: {p1.score} | P2: {p2.score}\n")


if __name__ == '__main__':
    main()
