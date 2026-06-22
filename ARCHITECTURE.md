# 双人贪吃蛇 架构文档

## 项目概览

基于 Python `curses` 库实现的终端双人对战贪吃蛇游戏。支持 WASD / 方向键双控、实时碰撞检测、加速道具、颜色渲染、得分结算等完整功能。

---

## 文件结构

| 文件 | 职责 | 行数 |
|---|---|---|
| `snake_2p.py` | 游戏主程序，包含所有核心逻辑类 | ~400 |
| `config.py` | 全局配置常量，所有可调参数集中管理 | ~35 |
| `README.md` | 游戏说明与运行指南 | - |
| `.gitignore` | Git 忽略配置 | - |

---

## 依赖关系图

```
snake_2p.py
    ├─  from config import *         (配置常量)
    ├─  Snake                        (蛇的状态与行为)
    ├─  Renderer                     (所有绘制逻辑)
    └─  Game                         (游戏状态与主循环)
          ├─  self.p1 (Snake)
          ├─  self.p2 (Snake)
          └─  self.renderer (Renderer)
```

---

## 核心类设计

### 1. Snake 类

**职责**：封装单条蛇的所有状态和行为，不涉及任何绘制或全局游戏逻辑。

**构造参数**：
- `init_pos`：初始身体坐标列表
- `init_dir`：初始移动方向
- `key_map`：按键 → 方向的映射字典
- `head_char` / `body_char`：头/身显示字符
- `head_color` / `body_color`：颜色对 ID
- `label`：HUD/结算显示的玩家名

**关键方法**：

| 方法 | 签名 | 作用 |
|---|---|---|
| `reset()` | `()` | 重置身体、方向、得分、buff |
| `set_direction(key)` | `(int)` | 根据按键更新方向（自动防反方向） |
| `next_head()` | `() -> tuple` | 计算下一帧头部坐标（**只读，不修改状态**） |
| `move(grow)` | `(bool)` | 执行移动，`grow=True` 时不截尾 |
| `is_boosted([now])` | `([float]) -> bool` | 是否处于加速状态，时间到自动清理 |
| `activate_boost()` | `()` | 激活加速，设置 `boost_end = now + 5s` |
| `boost_remaining([now])` | `([float]) -> float` | 加速剩余秒数，返回 0 表示未加速 |
| `occupied_set()` | `() -> set` | 返回身体坐标集合（供空格计算） |
| `hits_wall([head])` | `([tuple]) -> bool` | 撞墙检测，可传入任意坐标 |
| `hits_self(head)` | `(tuple) -> bool` | 是否撞到自己身体（不含头） |

**状态字段**：
- `body`：`list[tuple]`，`body[0]` 是蛇头
- `direction`：`tuple(dx, dy)`
- `score`：`int`，当前得分
- `boost_end`：`float / None`，加速到期时间戳

---

### 2. Renderer 类

**职责**：所有绘制逻辑的容器，纯展示层，**不读取或修改任何游戏规则状态**（只读传入的参数）。

**构造参数**：
- `stdscr`：curses 标准屏幕对象
- `use_color`：是否启用颜色（终端不支持时降级）

**绘制方法**：

| 方法 | 作用 |
|---|---|
| `_addch(y, x, ch, color)` | 私有：画一个字符（自动处理颜色降级） |
| `_addstr(y, x, s[, color])` | 私有：画字符串（自动处理颜色降级） |
| `draw_border()` | 画 `#` 号围墙 |
| `draw_snake(snake)` | 画单条蛇（从 Snake 对象取字符/颜色） |
| `draw_food(food)` | 画食物 `*`（红色） |
| `draw_boost(boost, visible)` | 画闪烁加速道具（黄色） |
| `draw_hud(snakes)` | 画底部 HUD：得分 + 加速倒计时 |
| `draw_game_over(winner)` | 画结算画面 |
| `draw(...)` | 总入口：按顺序调用上述方法 + `erase` + `refresh` |

---

### 3. Game 类

**职责**：全局游戏状态管理 + 主循环流程编排。

**构造参数**：
- `stdscr`：curses 标准屏幕对象

**初始化时完成**：
1. curses 环境配置（`curs_set(0)`、`nodelay(1)`、`keypad(1)` 等）
2. 颜色初始化（`_init_colors()`）
3. 创建两个 `Snake` 实例
4. 创建 `Renderer` 实例

**核心方法**：

| 方法 | 作用 |
|---|---|
| `_init_colors()` | 初始化 7 组颜色对（P1绿/P2蓝/食物红/道具黄/边界白） |
| `_reset_round()` | 重开一局：重置蛇、食物、道具、死亡状态 |
| `_get_empty_cells()` | 计算所有不被蛇/食物/道具占用的空格坐标 |
| `_spawn_food()` | 在随机空格刷食物 |
| `_try_spawn_boost()` | 每 15s 有 30% 概率刷加速道具 |
| `_update_boost_blink()` | 道具闪烁逻辑（150ms 反转一次可见性） |
| `_current_tick()` | 根据加速状态计算当前帧间隔（`BASE_TICK_MS // 2` 或 `BASE_TICK_MS`） |
| `_compute_next_bodies(new_heads, grows)` | 预计算所有蛇移动后的身体快照（无副作用） |
| `_check_collisions(new_heads, next_bodies)` | 碰撞检测，返回 `[p1_dead, p2_dead]` |
| `_apply_pickups(new_heads)` | 处理吃食物（加分、刷新食物）和吃道具（激活加速） |
| `_build_winner_msg(dead)` | 生成胜负结算文案（含最终得分） |
| `run()` | 游戏主循环 |

---

## 游戏主循环 — 单帧处理流程

每一帧（约 100ms，加速时 50ms）按以下顺序执行：

```
Game.run() 主循环
├─ 0. 每局开始时调用 _reset_round() 初始化
│
└─ 每帧循环：
    ├─ 1. 设置帧间隔：_current_tick() → stdscr.timeout()
    │
    ├─ 2. 道具更新：
    │   ├─ if self.boost: _update_boost_blink()     ← 闪烁
    │   └─ else:         _try_spawn_boost()         ← 尝试刷新
    │
    ├─ 3. 渲染：renderer.draw(...)                  ← 仅在未结束时
    │
    ├─ 4. 读按键：key = stdscr.getch()
    │
    ├─ 5. 结算分支：
    │   ├─ 若 game_over：处理 r/q 按键
    │   └─ 否则：继续
    │
    ├─ 6. 全局 q 退出
    │
    ├─ 7. 方向更新：
    │   └─ for s in self.snakes: s.set_direction(key)
    │
    ├─ 8. 预计算下一帧状态（纯函数，无副作用）：
    │   ├─ new_heads = [s.next_head() for s in snakes]
    │   ├─ grows = [新头是否命中食物]
    │   └─ next_bodies = _compute_next_bodies(new_heads, grows)
    │
    ├─ 9. 碰撞检测：dead = _check_collisions(new_heads, next_bodies)
    │   └─ 若 any(dead): 结算 → continue
    │
    ├─ 10. 处理拾取：_apply_pickups(new_heads)
    │   ├─ 加分、刷新食物、激活加速
    │   └─ 道具被吃后重置刷新计时
    │
    └─ 11. 真正移动：
        ├─ p1.move(grows[0])
        └─ p2.move(grows[1])
```

**关键设计原则**：
- 「**先预测，再检测，最后才真正移动**」——所有碰撞检测基于预测的 `next_bodies`，不会因为某条蛇先移动了而影响另一条蛇的判定
- 每帧的副作用（实际移动、状态变更）只发生在最后一步，前面全是只读计算

---

## 碰撞检测逻辑

`_check_collisions(new_heads, next_bodies)` 按以下**固定顺序**四层判定，每层之间用 `dead[i]` 做短路跳过：

```
第 1 层：撞墙检测
  for 每条蛇:
    if hits_wall(new_head): dead[i] = True

第 2 层：蛇头对撞检测（独立于其他检测）
  if new_heads[0] == new_heads[1]: dead = [True, True]

第 3 层：撞自己检测
  for 每条蛇:
    if dead[i]: continue
    if new_head in snake.body[1:]: dead[i] = True

第 4 层：互撞检测
  for 每条蛇 i:
    if dead[i]: continue
    for 每条其他蛇 j:
      if j 未死:
        other_body = next_bodies[j]      # j 移动后的身体
      else:
        other_body = snakes[j].body      # j 已死，用旧身体
      if new_heads[i] in other_body:
        dead[i] = True
        break
```

**为什么是这个顺序？**
- 撞墙和对撞是无条件的，先判
- 撞自己只需要自己的旧身体，先判能早点跳过后续计算
- 互撞最复杂（需要考虑对方是否也死了），放最后

**无顺序依赖保证**：`next_bodies` 在调用 `_check_collisions` 之前已经**统一预计算完毕**，第 4 层检测时无需再临时构建对方的 temp 身体，从根源消除了「先检查 P1 还是 P2」导致的判定不一致问题。

---

## 配置系统

所有可调参数集中在 `config.py`，代码中无硬编码的魔法数字。主要分类：

### 地图与基础参数
```python
MAP_WIDTH = 30              # 地图宽度（格）
MAP_HEIGHT = 20             # 地图高度（格）
BASE_TICK_MS = 100          # 基础帧间隔（毫秒）
FOOD_SCORE = 10             # 每个食物加分
```

### 玩家初始配置
```python
P1_INIT_POS = [(5, 10), (4, 10), (3, 10)]
P2_INIT_POS = [(24, 10), (25, 10), (26, 10)]
P1_INIT_DIR = (1, 0)        # 向右
P2_INIT_DIR = (-1, 0)       # 向左
```

### 道具参数
```python
BOOST_ENABLED = True
BOOST_DURATION_SEC = 5
BOOST_SPEED_MULTIPLIER = 2
BOOST_SPAWN_INTERVAL_SEC = 15
BOOST_SPAWN_CHANCE = 0.3
```

### 显示字符
```python
BOOST_CHAR = '*'
FOOD_CHAR = '*'
BORDER_CHAR = '#'
P1_HEAD_CHAR = 'O'
P1_BODY_CHAR = 'o'
P2_HEAD_CHAR = 'X'
P2_BODY_CHAR = 'x'
```

### 颜色对 ID
```python
COLOR_P1_HEAD = 1
COLOR_P1_BODY = 2
...
```

**修改配置**：直接改 `config.py` 即可，无需动 `snake_2p.py`。

---

## 扩展指南

### 加第三个玩家
1. 在 `Game.__init__` 里新增 `self.p3 = Snake(...)`
2. 把 `self.p3` 加入 `self.snakes` 列表
3. 所有核心逻辑（碰撞、拾取、渲染）都是基于 `self.snakes` 列表迭代的，无需修改

### 加新道具类型
1. 在 `config.py` 加道具配置（刷新间隔、持续时间等）
2. 在 `Game` 中加 `self.new_item` 状态字段
3. 在 `_try_spawn_boost` 附近加新道具刷新逻辑
4. 在 `_apply_pickups` 加拾取处理
5. 在 `Renderer` 加绘制方法

### 改判定规则
- 只改 `_check_collisions`，不影响渲染或蛇的行为
- 例如想取消「撞自己会死」，删除第 3 层即可
