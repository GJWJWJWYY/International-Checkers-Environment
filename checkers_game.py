"""
完整的国际跳棋游戏环境
International Checkers (10x10) - Complete Implementation

规则说明：
1. 10x10棋盘，每方20个棋子
2. 强制吃子，必须选择吃最多棋子的路径
3. 王可以沿对角线飞行任意距离
4. 50步规则（双方各25回合无吃子或成王，符合FMJD标准）
5. 三次重复局面自动判和
6. 无合法移动判负
"""

import pygame
import copy
from collections import defaultdict

# 颜色定义
WHITE = "white"
BLACK = "black"
BLUE = "blue"
GREY1 = "lightyellow"
GREY2 = "goldenrod"
Background_color = "goldenrod"
PEACE = "peace"

# 棋盘信息
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 10, 10
SIZE = 80

# 加载王棋图片
try:
    WHITE_CROWN = pygame.transform.scale(pygame.image.load(r'.\crown\white.jpg'), (44, 25))
    BLACK_CROWN = pygame.transform.scale(pygame.image.load(r'.\crown\black.jpg'), (44, 25))
except:
    WHITE_CROWN = None
    BLACK_CROWN = None


class Piece:
    """棋子类"""
    PADDING = 10
    
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.is_king = False
        self.x = SIZE * self.col + SIZE // 2
        self.y = SIZE * self.row + SIZE // 2
    
    def draw_piece(self, win):
        """绘制棋子"""
        pygame.draw.circle(win, GREY2, (self.x, self.y), SIZE // 2 - self.PADDING + 2)
        pygame.draw.circle(win, self.color, (self.x, self.y), SIZE // 2 - self.PADDING)
        if self.is_king and WHITE_CROWN and BLACK_CROWN:
            crown = WHITE_CROWN if self.color == WHITE else BLACK_CROWN
            win.blit(crown, (self.x - crown.get_width() // 2, self.y - crown.get_height() // 2 - 3))
    
    def move(self, row, col):
        """移动棋子"""
        self.row = row
        self.col = col
        self.x = SIZE * self.col + SIZE // 2
        self.y = SIZE * self.row + SIZE // 2
    
    def __hash__(self):
        return hash((self.row, self.col, self.color, self.is_king))
    
    def __eq__(self, other):
        if isinstance(other, Piece):
            return (self.row, self.col, self.color, self.is_king) == \
                   (other.row, other.col, other.color, other.is_king)
        return False
    
    def __repr__(self):
        k = "K" if self.is_king else ""
        c = "W" if self.color == WHITE else "B"
        return f"{c}{k}({self.row},{self.col})"


class Board:
    """棋盘类 - 实现完整的国际跳棋规则"""
    
    def __init__(self):
        self.pieces = []
        self.white_kings = 0
        self.black_kings = 0
        self.white_left = 20
        self.black_left = 20
        self.init_pieces()
        
        # 游戏状态追踪
        self.move_count_since_capture_or_king = 0  # 50步规则计数器（FMJD标准）
        self.position_history = []  # 局面历史（用于三次重复判定）
        self.current_state = None
    
    def init_pieces(self):
        """初始化棋盘和棋子"""
        for row in range(ROWS):
            self.pieces.append([])
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    if row < 4:
                        self.pieces[row].append(Piece(row, col, BLACK))
                    elif row >= 6:
                        self.pieces[row].append(Piece(row, col, WHITE))
                    else:
                        self.pieces[row].append(0)
                else:
                    self.pieces[row].append(0)
        
        self._update_position_hash()
    
    def _update_position_hash(self, turn=None):
        """
        更新局面哈希
        参数:
            turn: 当前轮到谁（WHITE/BLACK），用于三次重复判定
        """
        state = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.pieces[row][col]
                if piece != 0:
                    state.append((piece.row, piece.col, piece.color, piece.is_king))
        # 加入轮到谁，确保相同棋盘但不同行棋方算作不同局面
        self.current_state = (tuple(sorted(state)), turn) if turn else tuple(sorted(state))
    
    def record_position(self, turn=None):
        """
        记录局面
        参数:
            turn: 当前轮到谁（WHITE/BLACK）
        """
        # 如果提供了 turn，更新哈希后再记录
        if turn:
            self._update_position_hash(turn)
        self.position_history.append(self.current_state)
    
    def check_threefold_repetition(self):
        """检查三次重复局面"""
        if not self.current_state:
            return False
        count = self.position_history.count(self.current_state)
        return count >= 3
    
    def draw(self, win):
        """绘制棋盘"""
        win.fill(GREY1)
        for row in range(ROWS):
            for col in range((row + 1) % 2, ROWS, 2):
                pygame.draw.rect(win, Background_color, (col * SIZE, row * SIZE, SIZE, SIZE))
        
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.pieces[row][col]
                if piece != 0:
                    piece.draw_piece(win)
    
    def is_in_board(self, row, col):
        """检查位置是否在棋盘内"""
        return 0 <= row < ROWS and 0 <= col < COLS
    
    def make_king(self, piece):
        """将棋子升级为王"""
        if not piece.is_king:
            if piece.row == ROWS - 1 and piece.color == BLACK:
                piece.is_king = True
                self.black_kings += 1
                return True
            elif piece.row == 0 and piece.color == WHITE:
                piece.is_king = True
                self.white_kings += 1
                return True
        return False
    
    def move_piece(self, piece, row, col):
        """移动棋子到新位置"""
        self.pieces[piece.row][piece.col] = 0
        piece.move(row, col)
        self.pieces[row][col] = piece
        became_king = self.make_king(piece)
        return became_king
    
    def remove_pieces(self, pieces_to_remove):
        """移除被吃掉的棋子"""
        for piece in pieces_to_remove:
            self.pieces[piece.row][piece.col] = 0
            if piece.color == WHITE:
                self.white_left -= 1
            else:
                self.black_left -= 1
    
    def get_all_pieces(self, color):
        """获取指定颜色的所有棋子"""
        pieces = []
        for row in self.pieces:
            for piece in row:
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces
    
    def _get_flying_king_moves(self, row, col, capture=False):
        """
        获取飞行王的移动（国际跳棋关键规则）
        王可以沿对角线飞行任意距离
        """
        moves = {}
        piece = self.pieces[row][col]
        if not piece.is_king:
            return moves
        
        # 四个对角线方向
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        if not capture:
            # 普通移动：沿对角线飞行到任意空位
            for dr, dc in directions:
                distance = 1
                while True:
                    new_row = row + dr * distance
                    new_col = col + dc * distance
                    
                    if not self.is_in_board(new_row, new_col):
                        break
                    
                    target = self.pieces[new_row][new_col]
                    if target != 0:
                        break  # 被阻挡
                    
                    moves[(new_row, new_col)] = []
                    distance += 1
        else:
            # 吃子移动：飞越一个敌子后可以落在任意空位
            for dr, dc in directions:
                distance = 1
                found_enemy = None
                enemy_pos = None
                
                while True:
                    new_row = row + dr * distance
                    new_col = col + dc * distance
                    
                    if not self.is_in_board(new_row, new_col):
                        break
                    
                    target = self.pieces[new_row][new_col]
                    
                    if target != 0:
                        if target.color != piece.color and found_enemy is None:
                            # 找到第一个敌子
                            found_enemy = target
                            enemy_pos = (new_row, new_col)
                        else:
                            # 被己方棋子或第二个棋子阻挡
                            break
                    elif found_enemy is not None:
                        # 找到敌子后的空位，这是有效的落点
                        moves[(new_row, new_col)] = [found_enemy]
                    
                    distance += 1
        
        return moves
    
    def _get_normal_piece_moves(self, row, col):
        """获取普通棋子的移动（向前一格）"""
        moves = {}
        piece = self.pieces[row][col]
        
        # 根据颜色确定移动方向
        if piece.color == WHITE:
            directions = [(-1, -1), (-1, 1)]  # 白棋向上
        else:
            directions = [(1, -1), (1, 1)]    # 黑棋向下
        
        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            
            if self.is_in_board(new_row, new_col):
                if self.pieces[new_row][new_col] == 0:
                    moves[(new_row, new_col)] = []
        
        return moves
    
    def _get_normal_piece_captures(self, row, col, captured_so_far=[]):
        """普通棋子吃子（可后向吃）"""
        moves = {}
        piece = self.pieces[row][col]
        
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            jump_row = row + dr * 2
            jump_col = col + dc * 2
            mid_row = row + dr
            mid_col = col + dc
            
            if not self.is_in_board(jump_row, jump_col):
                continue
            
            middle_piece = self.pieces[mid_row][mid_col]
            landing_piece = self.pieces[jump_row][jump_col]
            
            if (middle_piece != 0 and 
                middle_piece.color != piece.color and 
                middle_piece not in captured_so_far and
                landing_piece == 0):
                
                new_captured = captured_so_far + [middle_piece]
                
                temp_board = self._simulate_capture(row, col, jump_row, jump_col, [middle_piece])
                further_captures = temp_board._get_normal_piece_captures(
                    jump_row, jump_col, new_captured
                )
                
                if further_captures:
                    for final_pos, captured_lists in further_captures.items():
                        for captured_list in captured_lists:
                            full_path = new_captured + captured_list[len(new_captured):]
                            if final_pos not in moves:
                                moves[final_pos] = []
                            moves[final_pos].append(full_path)
                else:
                    if (jump_row, jump_col) not in moves:
                        moves[(jump_row, jump_col)] = []
                    moves[(jump_row, jump_col)].append(new_captured)
        
        return moves
    
    def _get_king_captures(self, row, col, captured_so_far=[]):
        """王的吃子"""
        moves = {}
        piece = self.pieces[row][col]
        
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            distance = 1
            found_enemy = None
            
            while True:
                check_row = row + dr * distance
                check_col = col + dc * distance
                
                if not self.is_in_board(check_row, check_col):
                    break
                
                current = self.pieces[check_row][check_col]
                
                if current != 0:
                    if current.color != piece.color and found_enemy is None:
                        if current not in captured_so_far:
                            found_enemy = current
                    else:
                        break
                elif found_enemy is not None:
                    new_captured = captured_so_far + [found_enemy]
                    
                    temp_board = self._simulate_capture(row, col, check_row, check_col, [found_enemy])
                    further_captures = temp_board._get_king_captures(
                        check_row, check_col, new_captured
                    )
                    
                    if further_captures:
                        for final_pos, captured_lists in further_captures.items():
                            for captured_list in captured_lists:
                                full_path = new_captured + captured_list[len(new_captured):]
                                if final_pos not in moves:
                                    moves[final_pos] = []
                                moves[final_pos].append(full_path)
                    else:
                        if (check_row, check_col) not in moves:
                            moves[(check_row, check_col)] = []
                        moves[(check_row, check_col)].append(new_captured)
                
                distance += 1
        
        return moves
    
    def _simulate_capture(self, from_row, from_col, to_row, to_col, captured):
        """模拟吃子移动，返回新棋盘"""
        temp_board = copy.deepcopy(self)
        temp_piece = temp_board.pieces[from_row][from_col]
        temp_board.pieces[from_row][from_col] = 0
        temp_board.pieces[to_row][to_col] = temp_piece
        temp_piece.row = to_row
        temp_piece.col = to_col
        
        for piece in captured:
            temp_board.pieces[piece.row][piece.col] = 0
        
        return temp_board
    
    def get_valid_moves(self, color):
        """
        获取所有合法移动
        返回格式: {piece: {(target_row, target_col): [captured_pieces_list]}}
        其中 captured_pieces_list 是列表的列表，每个内层列表代表一条吃子路径
        """
        all_pieces = self.get_all_pieces(color)
        capture_moves = {}
        normal_moves = {}
        max_captures = 0
        
        for piece in all_pieces:
            if piece.is_king:
                captures = self._get_king_captures(piece.row, piece.col)
                if captures:
                    capture_moves[piece] = captures
                    for move, captured_lists in captures.items():
                        for captured_list in captured_lists:
                            max_captures = max(max_captures, len(captured_list))
                
                if not capture_moves:
                    normal = self._get_flying_king_moves(piece.row, piece.col, capture=False)
                    if normal:
                        normal_moves[piece] = normal
            else:
                captures = self._get_normal_piece_captures(piece.row, piece.col)
                if captures:
                    capture_moves[piece] = captures
                    for move, captured_lists in captures.items():
                        for captured_list in captured_lists:
                            max_captures = max(max_captures, len(captured_list))
                
                if not capture_moves:
                    normal = self._get_normal_piece_moves(piece.row, piece.col)
                    if normal:
                        normal_moves[piece] = normal
        
        # 强制吃子且吃最多
        if capture_moves:
            filtered_captures = {}
            for piece, moves in capture_moves.items():
                filtered_moves = {}
                for pos, captured_lists in moves.items():
                    max_len_paths = [
                        captured_list 
                        for captured_list in captured_lists 
                        if len(captured_list) == max_captures
                    ]
                    if max_len_paths:
                        filtered_moves[pos] = max_len_paths
                if filtered_moves:
                    filtered_captures[piece] = filtered_moves
            return filtered_captures
        
        return normal_moves
    
    def make_move(self, piece, target_pos, captured_pieces):
        """
        执行移动
        返回：是否有吃子发生
        """
        has_capture = len(captured_pieces) > 0
        became_king = False
        
        # 移除被吃的棋子
        if has_capture:
            self.remove_pieces(captured_pieces)
            self.move_count_since_capture_or_king = 0
        
        # 移动棋子
        became_king = self.move_piece(piece, target_pos[0], target_pos[1])
        
        # 如果成王，重置计数器
        if became_king:
            self.move_count_since_capture_or_king = 0
        else:
            self.move_count_since_capture_or_king += 1
        
        # 更新局面哈希
        self._update_position_hash()
        
        return has_capture or became_king
    
    def winner(self):
        """
        判断游戏结果
        返回：WHITE/BLACK/PEACE/None
        """
        # 检查是否有一方无子
        if self.white_left <= 0:
            return BLACK
        if self.black_left <= 0:
            return WHITE
        
        # 50步规则（FMJD标准：双方各25回合）
        if self.move_count_since_capture_or_king >= 50:
            return PEACE
        
        # 三次重复局面
        if self.check_threefold_repetition():
            return PEACE
        
        return None
    
    def has_valid_moves(self, color):
        """检查是否有合法移动"""
        return bool(self.get_valid_moves(color))
    
    def get_board_state(self):
        """获取棋盘状态的字符串表示（用于调试）"""
        state = []
        for row in range(ROWS):
            row_str = []
            for col in range(COLS):
                piece = self.pieces[row][col]
                if piece == 0:
                    row_str.append('.')
                elif piece.color == WHITE:
                    row_str.append('W' if not piece.is_king else 'K')
                else:
                    row_str.append('b' if not piece.is_king else 'k')
            state.append(' '.join(row_str))
        return '\n'.join(state)


class Game:
    """游戏控制类"""
    
    def __init__(self, win=None):
        self.win = win
        self.board = Board()
        self.turn = WHITE  # 白方先手
        self.selected_piece = None
        self.valid_moves = {}
        self.game_over = False
        self.winner = None
        
        # 路径选择状态
        self.path_selection_mode = False  # 是否在路径选择模式
        self.path_selection_target = None  # 选择路径的目标位置
        self.current_path_index = 0  # 当前选择的路径索引
    
    def select_piece(self, row, col):
        """选择棋子"""
        piece = self.board.pieces[row][col]
        if piece != 0 and piece.color == self.turn:
            self.selected_piece = piece
            all_moves = self.board.get_valid_moves(self.turn)
            self.valid_moves = all_moves.get(piece, {})
            return True
        return False
    
    def get_path_count(self, row, col):
        """
        获取到达指定位置的路径数量
        返回: int 路径数量，如果位置无效返回0
        """
        if not self.selected_piece:
            return 0
        
        target_pos = (row, col)
        if target_pos not in self.valid_moves:
            return 0
        
        captured_data = self.valid_moves[target_pos]
        
        # 检查有多少条路径
        if isinstance(captured_data, list) and captured_data:
            if isinstance(captured_data[0], list):
                # 新格式：列表的列表
                return len(captured_data)
        
        return 1  # 只有一条路径或普通移动
    
    def get_path_info(self, row, col, path_index):
        """
        获取指定路径的详细信息
        返回: 被吃棋子的位置列表
        """
        if not self.selected_piece:
            return []
        
        target_pos = (row, col)
        if target_pos not in self.valid_moves:
            return []
        
        captured_data = self.valid_moves[target_pos]
        
        if isinstance(captured_data, list) and captured_data:
            if isinstance(captured_data[0], list):
                # 新格式：列表的列表
                if path_index < len(captured_data):
                    return [(p.row, p.col) for p in captured_data[path_index]]
        
        return []
    
    def cycle_path(self):
        """
        在路径选择模式下，切换到下一条路径
        """
        if not self.path_selection_mode or not self.path_selection_target:
            return
        
        row, col = self.path_selection_target
        path_count = self.get_path_count(row, col)
        
        if path_count > 1:
            self.current_path_index = (self.current_path_index + 1) % path_count
    
    def confirm_path(self):
        """
        在路径选择模式下，确认当前选择的路径
        """
        if not self.path_selection_mode or not self.path_selection_target:
            return False
        
        row, col = self.path_selection_target
        return self.move_piece(row, col, self.current_path_index)
    
    def move_piece(self, row, col, path_index=None):
        """
        移动选中的棋子
        参数:
            row, col: 目标位置
            path_index: 当有多条路径到达同一位置时，选择哪条路径。
                       None表示自动处理（如果多路径则进入选择模式）
        返回:
            'path_select' - 需要用户选择路径
            True - 移动成功
            False - 移动失败
        """
        if not self.selected_piece:
            return False
        
        target_pos = (row, col)
        if target_pos not in self.valid_moves:
            return False
        
        captured_data = self.valid_moves[target_pos]
        
        # 检查是否有多条路径
        path_count = self.get_path_count(row, col)
        
        # 如果有多条路径且未指定 path_index，进入路径选择模式
        if path_count > 1 and path_index is None:
            self.path_selection_mode = True
            self.path_selection_target = target_pos
            self.current_path_index = 0
            return 'path_select'
        
        # 确定使用的路径索引
        if path_index is None:
            path_index = 0
        
        # 处理新格式：根据 path_index 选择路径
        if isinstance(captured_data, list) and captured_data:
            if isinstance(captured_data[0], list):
                # 新格式：列表的列表，选择指定的路径
                if path_index < len(captured_data):
                    captured = captured_data[path_index]
                else:
                    # 如果 path_index 超出范围，使用第一条
                    captured = captured_data[0]
            else:
                # 旧格式或空列表
                captured = captured_data
        else:
            captured = []
        
        self.board.make_move(self.selected_piece, target_pos, captured)
        
        # 重置路径选择状态
        self.path_selection_mode = False
        self.path_selection_target = None
        self.current_path_index = 0
        
        # 确定下一个行棋方
        next_turn = BLACK if self.turn == WHITE else WHITE
        
        # 记录局面（带上下一个行棋方）
        self.board.record_position(next_turn)
        
        # 切换回合
        self.change_turn()
        
        # 检查游戏是否结束
        self.check_game_over()
        
        return True
    
    def change_turn(self):
        """切换回合"""
        self.turn = BLACK if self.turn == WHITE else WHITE
        self.selected_piece = None
        self.valid_moves = {}
        self.path_selection_mode = False
        self.path_selection_target = None
        self.current_path_index = 0
    
    def check_game_over(self):
        """检查游戏是否结束"""
        # 检查胜负
        result = self.board.winner()
        if result:
            self.game_over = True
            self.winner = result
            return True
        
        # 检查当前玩家是否有合法移动
        if not self.board.has_valid_moves(self.turn):
            self.game_over = True
            self.winner = BLACK if self.turn == WHITE else WHITE
            return True
        
        return False
    
    def draw(self):
        """绘制游戏画面"""
        if not self.win:
            return
        
        self.board.draw(self.win)
        
        # 绘制可移动位置
        for pos in self.valid_moves.keys():
            row, col = pos
            
            # 如果在路径选择模式且这是目标位置，用特殊颜色标记
            if self.path_selection_mode and self.path_selection_target == pos:
                # 高亮显示当前选择的路径将吃掉的棋子
                path_info = self.get_path_info(row, col, self.current_path_index)
                for capture_row, capture_col in path_info:
                    pygame.draw.circle(
                        self.win, (255, 0, 0),  # 红色标记将被吃的子
                        (capture_col * SIZE + SIZE // 2, capture_row * SIZE + SIZE // 2),
                        20, 3
                    )
                # 目标位置用黄色
                pygame.draw.circle(
                    self.win, (255, 255, 0),
                    (col * SIZE + SIZE // 2, row * SIZE + SIZE // 2),
                    18
                )
            else:
                # 普通可移动位置用蓝色
                pygame.draw.circle(
                    self.win, BLUE,
                    (col * SIZE + SIZE // 2, row * SIZE + SIZE // 2),
                    15
                )
        
        # 显示回合信息
        font = pygame.font.SysFont('simhei', 30)
        turn_text = f'Turn: {"WHITE" if self.turn == WHITE else "BLACK"}'
        text_surface = font.render(turn_text, True, (0, 0, 0))
        self.win.blit(text_surface, (30, HEIGHT - 35))
        
        # 显示50步计数器
        counter_text = f'No capture/king: {self.board.move_count_since_capture_or_king}/50'
        counter_surface = font.render(counter_text, True, (100, 100, 100))
        self.win.blit(counter_surface, (WIDTH - 400, HEIGHT - 35))
        
        # 如果在路径选择模式，显示提示
        if self.path_selection_mode and self.path_selection_target:
            row, col = self.path_selection_target
            path_count = self.get_path_count(row, col)
            hint_text = f'Path {self.current_path_index + 1}/{path_count} - Click again to cycle, or click target to confirm'
            hint_surface = font.render(hint_text, True, (255, 0, 0))
            self.win.blit(hint_surface, (WIDTH // 2 - 300, 20))
        
        pygame.display.update()
    
    def draw_winner(self):
        """显示获胜者"""
        if not self.win or not self.winner:
            return
        
        if self.winner == WHITE:
            text = 'White Wins!'
        elif self.winner == BLACK:
            text = 'Black Wins!'
        elif self.winner == PEACE:
            text = 'Draw!'
        else:
            return
        
        font = pygame.font.SysFont('simhei', 48)
        text_surface = font.render(text, True, (255, 0, 0))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.win.blit(text_surface, text_rect)
        pygame.display.update()
        pygame.time.delay(3000)


def main():
    """主程序 - 带图形界面的游戏"""
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("International Checkers (10x10)")
    
    game = Game(win)
    clock = pygame.time.Clock()
    running = True
    
    while running:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
                pos = pygame.mouse.get_pos()
                row = pos[1] // SIZE
                col = pos[0] // SIZE
                
                # 如果在路径选择模式
                if game.path_selection_mode:
                    # 点击目标位置确认当前路径
                    if (row, col) == game.path_selection_target:
                        game.confirm_path()
                    # 点击其他地方取消路径选择，重新选择棋子
                    else:
                        game.path_selection_mode = False
                        game.path_selection_target = None
                        game.current_path_index = 0
                        game.select_piece(row, col)
                elif game.selected_piece:
                    # 尝试移动
                    result = game.move_piece(row, col)
                    if result == 'path_select':
                        # 进入路径选择模式，不做其他操作
                        pass
                    elif not result:
                        # 移动失败，尝试选择新棋子
                        game.select_piece(row, col)
                else:
                    # 选择棋子
                    game.select_piece(row, col)
            
            # 添加键盘支持：空格键切换路径
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game.path_selection_mode:
                    game.cycle_path()
        
        game.draw()
        
        if game.game_over:
            game.draw_winner()
            running = False
    
    pygame.quit()


if __name__ == "__main__":
    main()
