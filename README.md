# 国际跳棋环境 (International Checkers Environment)

完整的10x10国际跳棋游戏环境实现，符合标准规则。

## 📋 特性

### ✅ 完整实现的规则
1. **10x10棋盘** - 标准国际跳棋尺寸
2. **每方20个棋子** - 标准配置
3. **强制吃子** - 可以吃子时必须吃子
4. **最大吃子规则** - 必须选择吃最多棋子的路径
5. **连续吃子** - 一次移动中可以连续吃多个棋子
6. **飞行王规则** ⭐ - 王可以沿对角线飞行任意距离
7. **王的吃子** ⭐ - 王可以飞越敌子后落在任意空位
8. **成王** - 到达对方底线升级为王
9. **50步规则** ⭐ - 双方各25回合无吃子或成王判和（FMJD标准）
10. **三次重复局面** - 相同局面出现3次自动判和（考虑行棋方）
11. **无合法移动判负** - 无子可动则判负
12. **后向吃子** - 普通棋子可以向后吃子（但不能后退普通移动）

### 🎯 两个版本

#### 1. `checkers_env.py` - 纯接口版本（推荐用于AI）
- 不依赖任何图形库
- 提供标准的黑白双方接口
- 适合AI训练和对战
- 轻量级，运行快速

#### 2. `checkers_game.py` - 带GUI版本
- 使用Pygame显示图形界面
- 支持鼠标点击操作
- **多路径选择**: 
  - 当有多条吃子路径到达同一位置时，点击目标进入路径选择模式
  - 显示红色圆圈标记即将被吃的棋子
  - 再次点击目标确认当前路径，或按**空格键**切换路径
- 可视化游戏过程
- 需要安装Pygame

## 🚀 快速开始

### 安装依赖

```bash
# 仅使用纯接口版本，无需安装任何依赖

# 使用图形界面版本
pip install pygame
```

### 使用纯接口版本

```python
from checkers_env import CheckersGame, WHITE, BLACK

# 创建游戏
game = CheckersGame()

# 获取当前状态
state = game.get_state()
print(f"当前回合: {state['turn']}")
print(f"棋盘状态: {state['board']}")

# 获取合法移动
valid_moves = game.get_valid_moves()
# 格式: [((from_row, from_col), (to_row, to_col), captured_count, path_index), ...]

# 执行移动
if valid_moves:
    from_pos, to_pos, captures, path_idx = valid_moves[0]
    success = game.make_move(from_pos, to_pos, path_idx)
    
# 检查游戏状态
if game.is_game_over():
    winner = game.get_winner()
    print(f"游戏结束！获胜方: {winner}")

# 重置游戏
game.reset()
```

### 使用图形界面版本

```python
# 直接运行
python checkers_game.py
```

或在代码中使用：

```python
from checkers_game import Game
import pygame

pygame.init()
win = pygame.display.set_mode((800, 800))
game = Game(win)

# 游戏循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            row, col = pos[1] // 80, pos[0] // 80
            # 处理点击...
    
    game.draw()

pygame.quit()
```

## 📚 API 文档

### CheckersGame 类

主要游戏控制类，提供完整的游戏接口。

#### 方法

##### `__init__()`
创建新游戏实例。

##### `reset() -> dict`
重置游戏到初始状态。
- **返回**: 初始游戏状态

##### `get_state() -> dict`
获取当前游戏状态。
- **返回**: 
  ```python
  {
      'board': [[...], ...],      # 10x10棋盘状态
      'turn': 'white'/'black',    # 当前回合
      'valid_moves': [...],       # 合法移动列表
      'game_over': False,         # 是否结束
      'winner': None,             # 获胜方
      'move_count': 0,            # 25步计数
      'white_pieces': 20,         # 白方棋子数
      'black_pieces': 20          # 黑方棋子数
  }
  ```

##### `get_valid_moves() -> list`
获取当前玩家的所有合法移动。
- **返回**: `[((from_row, from_col), (to_row, to_col), captured_count, path_index), ...]`
  - 每条不同的吃子路径都作为独立的移动返回
  - `path_index`: 当多条路径到达同一位置时的路径索引

##### `make_move(from_pos, to_pos, path_index=0) -> bool`
执行移动。
- **参数**:
  - `from_pos`: `(row, col)` 起始位置
  - `to_pos`: `(row, col)` 目标位置
  - `path_index`: `int` 路径索引，默认0（当有多条吃子路径到达同一位置时使用）
- **返回**: 移动是否成功

##### `is_game_over() -> bool`
检查游戏是否结束。

##### `get_winner() -> str|None`
获取获胜方。
- **返回**: `'white'`, `'black'`, `'peace'`, 或 `None`

##### `print_state()`
打印当前游戏状态（调试用）。

### CheckersBoard 类

底层棋盘逻辑类。

#### 棋盘状态表示

棋盘状态是10x10的二维列表：
- `0`: 空位
- `1`: 白色普通棋子
- `2`: 黑色普通棋子
- `3`: 白色王
- `4`: 黑色王

## 🎮 游戏规则详解

### 基本移动

- **普通棋子**: 只能向前斜向移动一格
- **王棋**: 可以沿对角线飞行任意距离（国际跳棋特色）

### 吃子规则

1. **强制吃子**: 如果有吃子机会，必须吃子
2. **最大吃子**: 如果有多个吃子选择，必须选择吃最多棋子的
3. **连续吃子**: 吃掉一个棋子后，如果还能继续吃，必须继续
4. **后向吃子**: 普通棋子可以向后吃子（但不能后退普通移动）
5. **飞行吃子**: 王可以飞越敌子后落在任意空位

### 成王

- 棋子到达对方底线时升级为王
- 白方棋子到达第0行成王
- 黑方棋子到达第9行成王

### 胜负判定

#### 获胜
- 吃掉对方所有棋子
- 对方无合法移动

#### 平局
- **50步规则** ⭐: 双方各25回合（共50个单步）无吃子且无棋子成王（FMJD标准）
- **三次重复**: 相同局面（包括轮到谁）出现3次

## 📊 示例代码

### 完整的AI对战示例

```python
from checkers_env import CheckersGame, WHITE, BLACK
import random

class RandomAI:
    """随机AI示例"""
    def get_move(self, game):
        moves = game.get_valid_moves()
        if moves:
            return random.choice(moves)
        return None

# 创建游戏和AI
game = CheckersGame()
white_ai = RandomAI()
black_ai = RandomAI()

# 对战循环
move_count = 0
while not game.is_game_over():
    # 选择当前AI
    current_ai = white_ai if game.turn == WHITE else black_ai
    
    # 获取移动
    move = current_ai.get_move(game)
    if move:
        from_pos, to_pos, captures = move
        game.make_move(from_pos, to_pos)
        move_count += 1
        
        if captures > 0:
            print(f"第{move_count}步: {game.turn} 从 {from_pos} 到 {to_pos}, 吃掉 {captures} 个棋子")
    else:
        break

# 显示结果
print(f"\n游戏结束！")
print(f"获胜方: {game.get_winner()}")
print(f"总步数: {move_count}")
```

### 人类 vs AI 示例

```python
from checkers_env import CheckersGame, WHITE, BLACK

game = CheckersGame()

while not game.is_game_over():
    game.print_state()
    
    if game.turn == WHITE:
        # 人类玩家
        valid_moves = game.get_valid_moves()
        print(f"\n可选移动 ({len(valid_moves)} 个):")
        for i, (from_pos, to_pos, captures, path_idx) in enumerate(valid_moves):
            print(f"{i}: {from_pos} -> {to_pos} (吃{captures}个, 路径{path_idx})")
        
        choice = int(input("选择移动编号: "))
        from_pos, to_pos, captures, path_idx = valid_moves[choice]
        game.make_move(from_pos, to_pos, path_idx)
    else:
        # AI玩家
        import random
        moves = game.get_valid_moves()
        if moves:
            from_pos, to_pos, captures, path_idx = random.choice(moves)
            game.make_move(from_pos, to_pos, path_idx)
            print(f"黑方移动: {from_pos} -> {to_pos}")

print(f"\n游戏结束！获胜方: {game.get_winner()}")
```

## 🔧 技术实现细节

### 飞行王实现

王可以沿对角线飞行任意距离，这是国际跳棋的关键特性：

```python
def _get_flying_king_moves(self, row, col, capture=False):
    # 沿四个对角线方向搜索
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for dr, dc in directions:
        distance = 1
        while True:
            new_row = row + dr * distance
            new_col = col + dc * distance
            
            # 检查边界
            if not self.is_in_board(new_row, new_col):
                break
            
            # 普通移动：遇到棋子停止
            # 吃子移动：飞越敌子后继续搜索落点
            # ...
            
            distance += 1
```

### 50步规则（FMJD标准）

```python
# 每次移动后
if has_capture or became_king:
    self.move_count_since_capture_or_king = 0
else:
    self.move_count_since_capture_or_king += 1

# 判断平局（双方各25回合 = 50个单步）
if self.move_count_since_capture_or_king >= 50:
    return PEACE
```

### 三次重复检测

```python
def _update_position_hash(self, turn=None):
    # 将棋盘转换为不可变的元组，并加入轮到谁
    state = tuple(sorted([
        (piece.row, piece.col, piece.color, piece.is_king)
        for row in self.pieces
        for piece in row
        if piece != 0
    ]))
    # 确保相同棋盘但不同行棋方算作不同局面
    self.current_state = (state, turn) if turn else state

def record_position(self, turn=None):
    # 记录局面时包含轮到谁
    if turn:
        self._update_position_hash(turn)
    self.position_history.append(self.current_state)

def check_threefold_repetition(self):
    # 检查当前局面出现次数
    return self.position_history.count(self.current_state) >= 3
```

## 📁 文件结构

```
International_Checkers_Environment/
├── checkers_env.py          # 纯接口版本（推荐）
├── checkers_game.py         # 图形界面版本
├── test_environment.py      # 测试文件
├── README.md                # 本文档
└── crown/                   # 王棋图片
    ├── white.jpg
    └── black.jpg
```

## 🧪 测试

运行测试文件：

```bash
python test_environment.py
```

测试包括：
- 基本移动功能
- 吃子规则
- 飞行王移动
- **50步规则**（双方各25回合）
- 三次重复检测（考虑行棋方）
- 胜负判定

## ⚠️ 注意事项

1. **坐标系统**: 使用 (row, col)，row=0 是顶部（黑方底线），row=9 是底部（白方底线）
2. **颜色常量**: 使用 `WHITE` 和 `BLACK` 字符串常量
3. **移动格式**: 
   - `get_valid_moves()` 返回 4元组：`(from_pos, to_pos, captured_count, path_index)`
   - `make_move()` 需要 3个参数：`(from_pos, to_pos, path_index)`
4. **多路径吃子**: 当有多条路径到达同一位置时，每条路径都作为独立的移动返回
5. **50步规则**: 计数器统计单步数，50步 = 双方各25回合（符合FMJD标准）
6. **三次重复**: 判定时会考虑轮到谁，相同棋盘但不同行棋方算作不同局面
7. **深拷贝**: 内部使用深拷贝模拟移动，确保状态正确

## 🔄 更新日志

### v2.1 (2025-11-07) - FMJD标准修正 ⭐
- ✅ **修正**: 50步规则（原25步）- 符合FMJD官方标准（双方各25回合）
- ✅ **改进**: 更严格符合国际跳棋联合会（FMJD）规范

### v2.0 (2025-11-07) - 重大更新
- ✅ **修复**: 示例代码现在正确解包4元组（Bug #1）
- ✅ **新增**: GUI支持多路径选择，两段式点击+空格切换（Bug #2）
- ✅ **修复**: 三次重复规则现在正确考虑行棋方（Bug #3）
- ✅ **改进**: 多条吃子路径现在都作为独立移动返回
- ✅ **增强**: 完整的路径选择可视化反馈

### v1.0 - 初始版本
- ✅ 完整的国际跳棋规则实现
- ✅ 飞行王、三次重复
- ✅ 纯接口版本和GUI版本
