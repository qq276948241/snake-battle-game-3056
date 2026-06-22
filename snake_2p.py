import curses
import random
import sys
import time

from config import *

OPPOSITE = {
    (0, -1): (0, 1),
    (0, 1): (0, -1),
    (-1, 0): (1, 0),
    (1, 0): (-1, 0),
}

P1_KEYS = {
    ord('w'): (0, -1), ord('W'): (0, -1),
    ord('s'): (0, 1), ord('S'): (0, 1),
    ord('a'): (-1, 0), ord('A'): (-1, 0),
    ord('d'): (1, 0), ord('D'): (1, 0),
}

P2_KEYS = {
    curses.KEY_UP: (0, -1),
    curses.KEY_DOWN: (0, 1),
    curses.KEY_LEFT: (-1, 0),
    curses.KEY_RIGHT: (1, 0),
}


class Snake:
    def __init__(self, init_pos, init_dir, key_map, head_char, body_char,
                 head_color, body_color, label):
        self._init_pos = init_pos
        self._init_dir = init_dir
        self.key_map = key_map
        self.head_char = head_char
        self.body_char = body_char
        self.head_color = head_color
        self.body_color = body_color
        self.label = label
        self.reset()

    def reset(self):
        self.body = list(self._init_pos)
        self.direction = self._init_dir
        self.score = 0
        self.boost_end = None

    def set_direction(self, key):
        if key in self.key_map:
            new_dir = self.key_map[key]
            if new_dir != OPPOSITE.get(self.direction):
                self.direction = new_dir

    def next_head(self):
        hx, hy = self.body[0]
        dx, dy = self.direction
        return (hx + dx, hy + dy)

    def move(self, grow):
        new_head = self.next_head()
        self.body.insert(0, new_head)
        if not grow:
            self.body.pop()

    def is_boosted(self, now=None):
        if now is None:
            now = time.time()
        return self.boost_end is not None and now < self.boost_end

    def activate_boost(self):
        self.boost_end = time.time() + BOOST_DURATION_SEC

    def boost_remaining(self, now=None):
        if now is None:
            now = time.time()
        if self.boost_end and now < self.boost_end:
            return self.boost_end - now
        return 0

    def occupied_set(self):
        return set(self.body)

    def hits_wall(self, head=None):
        if head is None:
            head = self.body[0]
        x, y = head
        return x < 1 or x > MAP_WIDTH or y < 1 or y > MAP_HEIGHT

    def hits_self(self, head):
        return head in self.body[1:]


class Renderer:
    def __init__(self, stdscr, use_color):
        self.stdscr = stdscr
        self.use_color = use_color

    def _addch(self, y, x, ch, color_pair):
        try:
            if self.use_color:
                self.stdscr.addch(y, x, ch, curses.color_pair(color_pair))
            else:
                self.stdscr.addch(y, x, ch)
        except curses.error:
            pass

    def _addstr(self, y, x, s, color_pair=None):
        try:
            if color_pair and self.use_color:
                self.stdscr.addstr(y, x, s, curses.color_pair(color_pair))
            else:
                self.stdscr.addstr(y, x, s)
        except curses.error:
            pass

    def draw_border(self):
        for y in range(MAP_HEIGHT + 2):
            for x in range(MAP_WIDTH + 2):
                if x == 0 or x == MAP_WIDTH + 1 or y == 0 or y == MAP_HEIGHT + 1:
                    self._addch(y, x, BORDER_CHAR, COLOR_BORDER)

    def draw_snake(self, snake):
        for i, (x, y) in enumerate(snake.body):
            if i == 0:
                self._addch(y + 1, x + 1, snake.head_char, snake.head_color)
            else:
                self._addch(y + 1, x + 1, snake.body_char, snake.body_color)

    def draw_food(self, food):
        if food:
            self._addch(food[1] + 1, food[0] + 1, FOOD_CHAR, COLOR_FOOD)

    def draw_boost(self, boost, visible):
        if boost and visible:
            self._addch(boost[1] + 1, boost[0] + 1, BOOST_CHAR, COLOR_BOOST)

    def draw_hud(self, snakes):
        now = time.time()
        info_y = MAP_HEIGHT + 3
        parts = []
        for s in snakes:
            status = "{}: {}".format(s.label, s.score)
            if s.is_boosted(now):
                status += " [BOOST {:.1f}s]".format(s.boost_remaining(now))
            parts.append(status)
        self._addstr(info_y, 0, "  |  ".join(parts))

    def draw_game_over(self, winner):
        result_lines = winner.split(" Final Score - ")
        result_line = result_lines[0]
        score_line = "Final Score - " + result_lines[1] if len(result_lines) > 1 else ""
        hint = "Press 'r' to restart or 'q' to quit"
        msg_y = MAP_HEIGHT // 2 - 1
        center = MAP_WIDTH + 2
        if score_line:
            self._addstr(msg_y, max(0, (center - len(result_line)) // 2), result_line)
            self._addstr(msg_y + 1, max(0, (center - len(score_line)) // 2), score_line)
            self._addstr(msg_y + 3, max(0, (center - len(hint)) // 2), hint)
        else:
            self._addstr(msg_y, max(0, (center - len(winner)) // 2), winner)
            self._addstr(msg_y + 2, max(0, (center - len(hint)) // 2), hint)

    def draw(self, snakes, food, boost, boost_visible, game_over, winner):
        self.stdscr.erase()
        self.draw_border()
        for s in snakes:
            self.draw_snake(s)
        self.draw_food(food)
        self.draw_boost(boost, boost_visible)
        self.draw_hud(snakes)
        if game_over:
            self.draw_game_over(winner)
        self.stdscr.refresh()


class Game:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        stdscr.nodelay(1)
        stdscr.timeout(BASE_TICK_MS)
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(1)
        self.use_color = self._init_colors()
        self.renderer = Renderer(stdscr, self.use_color)
        self.p1 = Snake(
            list(P1_INIT_POS), P1_INIT_DIR, P1_KEYS,
            P1_HEAD_CHAR, P1_BODY_CHAR, COLOR_P1_HEAD, COLOR_P1_BODY, "P1 (WASD)")
        self.p2 = Snake(
            list(P2_INIT_POS), P2_INIT_DIR, P2_KEYS,
            P2_HEAD_CHAR, P2_BODY_CHAR, COLOR_P2_HEAD, COLOR_P2_BODY, "P2 (Arrows)")
        self.snakes = [self.p1, self.p2]

    @staticmethod
    def _init_colors():
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

    def _reset_round(self):
        for s in self.snakes:
            s.reset()
        self.food = self._spawn_food()
        self.boost = None
        self.boost_visible = True
        self.last_boost_spawn = time.time()
        self.last_boost_blink = time.time()
        self.game_over = False
        self.winner = ""

    def _get_empty_cells(self):
        occupied = set()
        for s in self.snakes:
            occupied |= s.occupied_set()
        if self.food:
            occupied.add(self.food)
        if self.boost:
            occupied.add(self.boost)
        return [(x, y)
                for x in range(1, MAP_WIDTH + 1)
                for y in range(1, MAP_HEIGHT + 1)
                if (x, y) not in occupied]

    def _spawn_food(self):
        empty = self._get_empty_cells()
        return random.choice(empty) if empty else None

    def _try_spawn_boost(self):
        if not BOOST_ENABLED:
            return
        now = time.time()
        if now - self.last_boost_spawn < BOOST_SPAWN_INTERVAL_SEC:
            return
        self.last_boost_spawn = now
        empty = self._get_empty_cells()
        if empty and random.random() < BOOST_SPAWN_CHANCE:
            self.boost = random.choice(empty)
            self.boost_visible = True
            self.last_boost_blink = now

    def _update_boost_blink(self):
        if not self.boost:
            return
        now = time.time()
        if now - self.last_boost_blink >= 0.15:
            self.boost_visible = not self.boost_visible
            self.last_boost_blink = now

    def _current_tick(self):
        now = time.time()
        if any(s.is_boosted(now) for s in self.snakes):
            return max(20, BASE_TICK_MS // BOOST_SPEED_MULTIPLIER)
        return BASE_TICK_MS

    def _check_collisions(self, new_heads):
        dead = [False, False]

        for i, (snake, head) in enumerate(zip(self.snakes, new_heads)):
            if snake.hits_wall(head):
                dead[i] = True

        if new_heads[0] == new_heads[1]:
            dead[0] = True
            dead[1] = True

        for i, (snake, head) in enumerate(zip(self.snakes, new_heads)):
            if dead[i]:
                continue
            if snake.hits_self(head):
                dead[i] = True

        for i, (snake, head) in enumerate(zip(self.snakes, new_heads)):
            if dead[i]:
                continue
            j = 1 - i
            other = self.snakes[j]
            other_grow = (self.food is not None and new_heads[j] == self.food)
            if not dead[j]:
                temp_other = list(other.body)
                temp_other.insert(0, new_heads[j])
                if not other_grow:
                    temp_other.pop()
                if head in temp_other:
                    dead[i] = True
            else:
                if head in other.body:
                    dead[i] = True

        return dead

    def _apply_pickups(self, new_heads):
        p1_grow = self.food is not None and new_heads[0] == self.food
        p2_grow = self.food is not None and new_heads[1] == self.food
        p1_got_boost = self.boost is not None and new_heads[0] == self.boost
        p2_got_boost = self.boost is not None and new_heads[1] == self.boost

        if p1_grow:
            self.p1.score += FOOD_SCORE
        if p2_grow:
            self.p2.score += FOOD_SCORE

        if p1_grow or p2_grow:
            self.food = self._spawn_food()

        if p1_got_boost:
            self.p1.activate_boost()
            self.boost = None
            self.last_boost_spawn = time.time()
        if p2_got_boost:
            self.p2.activate_boost()
            self.boost = None
            self.last_boost_spawn = time.time()

        return p1_grow, p2_grow

    def _build_winner_msg(self, dead):
        score_info = "Final Score - {}: {} | {}: {}".format(
            self.p1.label, self.p1.score, self.p2.label, self.p2.score)
        if all(dead):
            return "DRAW! Both died! " + score_info
        if dead[0]:
            return "{} WINS! ".format(self.p2.label) + score_info
        return "{} WINS! ".format(self.p1.label) + score_info

    def run(self):
        while True:
            self._reset_round()

            while True:
                self.stdscr.timeout(self._current_tick())

                if self.boost:
                    self._update_boost_blink()
                else:
                    self._try_spawn_boost()

                if not self.game_over:
                    self.renderer.draw(
                        self.snakes, self.food, self.boost, self.boost_visible,
                        self.game_over, self.winner)

                key = self.stdscr.getch()

                if self.game_over:
                    if key in (ord('r'), ord('R')):
                        break
                    if key in (ord('q'), ord('Q')):
                        return
                    continue

                if key in (ord('q'), ord('Q')):
                    return

                for s in self.snakes:
                    s.set_direction(key)

                new_heads = [s.next_head() for s in self.snakes]

                dead = self._check_collisions(new_heads)

                if any(dead):
                    self.winner = self._build_winner_msg(dead)
                    self.game_over = True
                    self.renderer.draw(
                        self.snakes, self.food, self.boost, self.boost_visible,
                        self.game_over, self.winner)
                    continue

                p1_grow, p2_grow = self._apply_pickups(new_heads)

                self.p1.move(p1_grow)
                self.p2.move(p2_grow)


if __name__ == '__main__':
    try:
        curses.wrapper(lambda stdscr: Game(stdscr).run())
    except KeyboardInterrupt:
        print("\nGame exited.")
        sys.exit(0)
