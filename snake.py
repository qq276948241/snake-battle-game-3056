import curses
import random
import time
from powerup import PowerUpManager, ActiveEffects, TYPE_STAR, TYPE_SHIELD, POWERUP_COLOR

WIDTH = 30
HEIGHT = 20
BASE_SPEED = 120
BOOST_SPEED = 60

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

SNAKE1_COLOR = 1
SNAKE2_COLOR = 2
FOOD_COLOR = 3
WALL_COLOR = 4
DEAD_COLOR = 5
SCORE_COLOR = 6
STAR_COLOR = 7
SHIELD_COLOR = 8
EFFECT_COLOR = 9


class Snake:
    def __init__(self, start_x, start_y, direction, color_pair, head_char, body_char):
        self.body = [(start_x, start_y)]
        for i in range(1, 4):
            dx, dy = direction
            self.body.append((start_x - dx * i, start_y - dy * i))
        self.direction = direction
        self.next_direction = direction
        self.color_pair = color_pair
        self.head_char = head_char
        self.body_char = body_char
        self.alive = True
        self.score = 0
        self.grow = 0

    def set_direction(self, direction):
        dx, dy = self.direction
        nx, ny = direction
        if (dx + nx, dy + ny) != (0, 0):
            self.next_direction = direction

    def move(self):
        if not self.alive:
            return
        self.direction = self.next_direction
        hx, hy = self.body[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)
        self.body.insert(0, new_head)
        if self.grow > 0:
            self.grow -= 1
        else:
            self.body.pop()

    def head(self):
        return self.body[0]

    def occupy_set(self):
        return set(self.body)


def spawn_food(occupied, width, height):
    available = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if (x, y) not in occupied:
                available.append((x, y))
    if not available:
        return None
    return random.choice(available)


def draw_game(stdscr, snake1, snake2, food, pu_manager, effects1, effects2, now, game_over):
    stdscr.clear()
    for x in range(WIDTH):
        stdscr.addch(0, x, ord('#'), curses.color_pair(WALL_COLOR))
        stdscr.addch(HEIGHT - 1, x, ord('#'), curses.color_pair(WALL_COLOR))
    for y in range(HEIGHT):
        stdscr.addch(y, 0, ord('#'), curses.color_pair(WALL_COLOR))
        stdscr.addch(y, WIDTH - 1, ord('#'), curses.color_pair(WALL_COLOR))

    if food:
        fx, fy = food
        stdscr.addch(fy, fx, ord('*'), curses.color_pair(FOOD_COLOR) | curses.A_BOLD)

    for pu in pu_manager.powerups:
        try:
            stdscr.addch(pu.y, pu.x, ord(pu.char()), curses.color_pair(pu.color()) | curses.A_BOLD)
        except curses.error:
            pass

    for i, (x, y) in enumerate(snake1.body):
        if 0 < x < WIDTH - 1 and 0 < y < HEIGHT - 1:
            ch = snake1.head_char if i == 0 else snake1.body_char
            color = snake1.color_pair if snake1.alive else DEAD_COLOR
            attr = curses.color_pair(color)
            if i == 0 and effects1.has_speed(now):
                attr |= curses.A_BLINK
            try:
                stdscr.addch(y, x, ord(ch), attr)
            except curses.error:
                pass

    for i, (x, y) in enumerate(snake2.body):
        if 0 < x < WIDTH - 1 and 0 < y < HEIGHT - 1:
            ch = snake2.head_char if i == 0 else snake2.body_char
            color = snake2.color_pair if snake2.alive else DEAD_COLOR
            attr = curses.color_pair(color)
            if i == 0 and effects2.has_speed(now):
                attr |= curses.A_BLINK
            try:
                stdscr.addch(y, x, ord(ch), attr)
            except curses.error:
                pass

    score_y = HEIGHT + 1
    p1_status = f"Player1[WASD]: {snake1.score}"
    if effects1.has_speed(now):
        p1_status += f" [SPD {effects1.speed_remaining(now):.1f}s]"
    if effects1.has_shield():
        p1_status += f" [SHD x{effects1.shield_count}]"
    stdscr.addstr(score_y, 0, p1_status, curses.color_pair(SNAKE1_COLOR) | curses.A_BOLD)

    p2_status = f"Player2[Arrows]: {snake2.score}"
    if effects2.has_speed(now):
        p2_status += f" [SPD {effects2.speed_remaining(now):.1f}s]"
    if effects2.has_shield():
        p2_status += f" [SHD x{effects2.shield_count}]"
    stdscr.addstr(score_y, WIDTH - 30, p2_status, curses.color_pair(SNAKE2_COLOR) | curses.A_BOLD)

    legend_y = HEIGHT + 2
    stdscr.addstr(legend_y, 0, "*=Food  +=Speed(2s)  S=Shield(1hit)", curses.color_pair(EFFECT_COLOR))

    if game_over:
        center_x = WIDTH // 2 - 8
        center_y = HEIGHT // 2
        stdscr.addstr(center_y - 1, center_x, "=== GAME OVER ===", curses.color_pair(FOOD_COLOR) | curses.A_BOLD)
        stdscr.addstr(center_y + 1, center_x, f"P1: {snake1.score}  vs  P2: {snake2.score}", curses.color_pair(SCORE_COLOR) | curses.A_BOLD)
        if snake1.score > snake2.score:
            result = "Player 1 Wins!"
        elif snake2.score > snake1.score:
            result = "Player 2 Wins!"
        else:
            result = "It's a Draw!"
        stdscr.addstr(center_y + 2, center_x + 2, result, curses.color_pair(FOOD_COLOR) | curses.A_BOLD)
        stdscr.addstr(center_y + 4, center_x - 2, "Press Q to quit, R to restart", curses.A_DIM)

    stdscr.refresh()


def run_game(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(0)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(SNAKE1_COLOR, curses.COLOR_CYAN, -1)
    curses.init_pair(SNAKE2_COLOR, curses.COLOR_YELLOW, -1)
    curses.init_pair(FOOD_COLOR, curses.COLOR_RED, -1)
    curses.init_pair(WALL_COLOR, curses.COLOR_WHITE, -1)
    curses.init_pair(DEAD_COLOR, curses.COLOR_RED, -1)
    curses.init_pair(SCORE_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(STAR_COLOR, curses.COLOR_MAGENTA, -1)
    curses.init_pair(SHIELD_COLOR, curses.COLOR_GREEN, -1)
    curses.init_pair(EFFECT_COLOR, curses.COLOR_BLUE, -1)

    pu_manager = PowerUpManager(WIDTH, HEIGHT)

    while True:
        snake1 = Snake(5, HEIGHT // 2, RIGHT, SNAKE1_COLOR, '@', 'o')
        snake2 = Snake(WIDTH - 6, HEIGHT // 2, LEFT, SNAKE2_COLOR, 'X', 'x')
        effects1 = ActiveEffects()
        effects2 = ActiveEffects()
        pu_manager.reset()

        occupied = snake1.occupy_set() | snake2.occupy_set()
        food = spawn_food(occupied, WIDTH, HEIGHT)

        game_over = False
        last_tick = time.time()

        while True:
            now = time.time()
            key = stdscr.getch()

            if key != -1:
                if not game_over:
                    if key == ord('w') or key == ord('W'):
                        snake1.set_direction(UP)
                    elif key == ord('s') or key == ord('S'):
                        snake1.set_direction(DOWN)
                    elif key == ord('a') or key == ord('A'):
                        snake1.set_direction(LEFT)
                    elif key == ord('d') or key == ord('D'):
                        snake1.set_direction(RIGHT)
                    elif key == curses.KEY_UP:
                        snake2.set_direction(UP)
                    elif key == curses.KEY_DOWN:
                        snake2.set_direction(DOWN)
                    elif key == curses.KEY_LEFT:
                        snake2.set_direction(LEFT)
                    elif key == curses.KEY_RIGHT:
                        snake2.set_direction(RIGHT)

                if game_over:
                    if key == ord('q') or key == ord('Q'):
                        return
                    elif key == ord('r') or key == ord('R'):
                        break

            p1_speed = BOOST_SPEED if effects1.has_speed(now) else BASE_SPEED
            p2_speed = BOOST_SPEED if effects2.has_speed(now) else BASE_SPEED
            tick_speed = min(p1_speed, p2_speed)

            if not game_over and (now - last_tick) >= tick_speed / 1000.0:
                last_tick = now

                snake1.move()
                snake2.move()

                occupied_all = snake1.occupy_set() | snake2.occupy_set()
                if food:
                    occupied_all.add(food)
                pu_manager.update(now, occupied_all)

                for snake, effects, other in [(snake1, effects1, snake2), (snake2, effects2, snake1)]:
                    if not snake.alive:
                        continue
                    hx, hy = snake.head()
                    dead = False
                    hit_wall = hx <= 0 or hx >= WIDTH - 1 or hy <= 0 or hy >= HEIGHT - 1
                    if hit_wall:
                        dead = True
                    else:
                        for seg in snake.body[1:]:
                            if snake.head() == seg:
                                dead = True
                                break
                        if not dead and snake.head() in other.occupy_set():
                            dead = True
                    if dead:
                        if effects.has_shield():
                            effects.consume_shield()
                            snake.body.pop(0)
                            snake.direction = (-snake.direction[0], -snake.direction[1])
                            snake.next_direction = snake.direction
                        else:
                            snake.alive = False

                for snake, effects in [(snake1, effects1), (snake2, effects2)]:
                    if not snake.alive:
                        continue
                    pu = pu_manager.try_collect(snake.head())
                    if pu:
                        pu_manager.apply_effect(pu.type, effects, now)

                if snake1.alive and food and snake1.head() == food:
                    snake1.score += 10
                    snake1.grow += 1
                    food = None

                if snake2.alive and food and snake2.head() == food:
                    snake2.score += 10
                    snake2.grow += 1
                    food = None

                if food is None:
                    occupied = snake1.occupy_set() | snake2.occupy_set() | pu_manager.occupy_set()
                    food = spawn_food(occupied, WIDTH, HEIGHT)

                if not snake1.alive or not snake2.alive:
                    game_over = True

            draw_game(stdscr, snake1, snake2, food, pu_manager, effects1, effects2, now, game_over)
            time.sleep(0.01)


def main():
    print("=== Two-Player Snake Game with PowerUps ===")
    print("Player 1: W/A/S/D    Player 2: Arrow Keys")
    print("Eat food(*) to grow & score +10")
    print("PowerUps:  +=Speed Boost (2s)   S=Shield (blocks 1 lethal hit)")
    print("Hit wall/self/other = dead! Shield saves you once!")
    print("Press any key to start...")
    curses.wrapper(run_game)


if __name__ == '__main__':
    main()
