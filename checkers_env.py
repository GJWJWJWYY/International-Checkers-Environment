"""
国际跳棋环境 - 纯接口版本（不依赖Pygame）
International Checkers Environment - Pure Interface

提供标准的黑白双方接口，可用于AI训练和对战
"""

import copy
from collections import defaultdict

# 颜色常量
WHITE = "white"
BLACK = "black"
PEACE = "peace"

# 棋盘尺寸
ROWS = 10
COLS = 10


class Piece:
    """棋子类"""
    
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.is_king = False
    
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


class CheckersBoard:
    """
    国际跳棋棋盘环境
    
    完整实现：
    1. 10x10棋盘
    2. 强制吃子，必须吃最多
    3. 飞行王（可沿对角线飞行任意距离）
    4. 25步规则（无吃子或成王）
    5. 三次重复局面判和
    6. 无合法移动判负
    """
    
    def __init__(self):
        self.pieces = []
        self.white_kings = 0
        self.black_kings = 0
        self.white_left = 20
        self.black_left = 20
        self.init_pieces()
        
        # 游戏状态
        self.move_count_since_capture_or_king = 0
        self.position_history = []
        self.current_state = None
    
    def init_pieces(self):
        """初始化棋盘"""
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
    
    def reset(self):
        """重置棋盘"""
        self.pieces = []
        self.white_kings = 0
        self.black_kings = 0
        self.white_left = 20
        self.black_left = 20
        self.move_count_since_capture_or_king = 0
        self.position_history = []
        self.current_state = None
        self.init_pieces()
    
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
        """检查三次重复"""
        if not self.current_state:
            return False
        return self.position_history.count(self.current_state) >= 3
    
    def is_in_board(self, row, col):
        """检查位置合法性"""
        return 0 <= row < ROWS and 0 <= col < COLS
    
    def make_king(self, piece):
        """升王"""
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
        """移动棋子"""
        self.pieces[piece.row][piece.col] = 0
        piece.row = row
        piece.col = col
        self.pieces[row][col] = piece
        return self.make_king(piece)
    
    def remove_pieces(self, pieces_to_remove):
        """移除棋子"""
        for piece in pieces_to_remove:
            self.pieces[piece.row][piece.col] = 0
            if piece.color == WHITE:
                self.white_left -= 1
            else:
                self.black_left -= 1
    
    def get_all_pieces(self, color):
        """获取所有棋子"""
        pieces = []
        for row in self.pieces:
            for piece in row:
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces
    
    def _get_flying_king_moves(self, row, col, capture=False):
        """飞行王移动"""
        moves = {}
        piece = self.pieces[row][col]
        if not piece.is_king:
            return moves
        
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        if not capture:
            # 普通移动
            for dr, dc in directions:
                distance = 1
                while True:
                    new_row = row + dr * distance
                    new_col = col + dc * distance
                    
                    if not self.is_in_board(new_row, new_col):
                        break
                    
                    if self.pieces[new_row][new_col] != 0:
                        break
                    
                    moves[(new_row, new_col)] = []
                    distance += 1
        else:
            # 吃子移动
            for dr, dc in directions:
                distance = 1
                found_enemy = None
                
                while True:
                    new_row = row + dr * distance
                    new_col = col + dc * distance
                    
                    if not self.is_in_board(new_row, new_col):
                        break
                    
                    target = self.pieces[new_row][new_col]
                    
                    if target != 0:
                        if target.color != piece.color and found_enemy is None:
                            found_enemy = target
                        else:
                            break
                    elif found_enemy is not None:
                        moves[(new_row, new_col)] = [found_enemy]
                    
                    distance += 1
        
        return moves
    
    def _get_normal_piece_moves(self, row, col):
        """普通棋子移动"""
        moves = {}
        piece = self.pieces[row][col]
        
        if piece.color == WHITE:
            directions = [(-1, -1), (-1, 1)]
        else:
            directions = [(1, -1), (1, 1)]
        
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
        """模拟吃子"""
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
        参数:
            piece: 要移动的棋子
            target_pos: 目标位置 (row, col)
            captured_pieces: 被吃的棋子列表
        返回:
            bool: 是否有吃子或成王
        """
        has_capture = len(captured_pieces) > 0
        
        if has_capture:
            self.remove_pieces(captured_pieces)
            self.move_count_since_capture_or_king = 0
        
        became_king = self.move_piece(piece, target_pos[0], target_pos[1])
        
        if became_king:
            self.move_count_since_capture_or_king = 0
        else:
            self.move_count_since_capture_or_king += 1
        
        self._update_position_hash()
        
        return has_capture or became_king
    
    def winner(self):
        """
        判断游戏结果
        返回: WHITE/BLACK/PEACE/None
        """
        if self.white_left <= 0:
            return BLACK
        if self.black_left <= 0:
            return WHITE
        
        # 25步规则
        if self.move_count_since_capture_or_king >= 25:
            return PEACE
        
        # 三次重复
        if self.check_threefold_repetition():
            return PEACE
        
        return None
    
    def has_valid_moves(self, color):
        """检查是否有合法移动"""
        return bool(self.get_valid_moves(color))
    
    def get_board_state(self):
        """
        获取棋盘状态
        返回: 10x10的二维列表
            0: 空位
            1: 白色普通棋子
            2: 黑色普通棋子  
            3: 白色王
            4: 黑色王
        """
        state = []
        for row in range(ROWS):
            row_state = []
            for col in range(COLS):
                piece = self.pieces[row][col]
                if piece == 0:
                    row_state.append(0)
                elif piece.color == WHITE:
                    row_state.append(3 if piece.is_king else 1)
                else:
                    row_state.append(4 if piece.is_king else 2)
            state.append(row_state)
        return state
    
    def print_board(self):
        """打印棋盘（调试用）"""
        print("\n  ", end="")
        for i in range(COLS):
            print(f"{i} ", end="")
        print()
        
        for row in range(ROWS):
            print(f"{row} ", end="")
            for col in range(COLS):
                piece = self.pieces[row][col]
                if piece == 0:
                    print(". ", end="")
                elif piece.color == WHITE:
                    print("W " if not piece.is_king else "K ", end="")
                else:
                    print("b " if not piece.is_king else "k ", end="")
            print()
        print()


class CheckersGame:
    """
    国际跳棋游戏环境
    
    提供标准接口供AI使用
    """
    
    def __init__(self):
        self.board = CheckersBoard()
        self.turn = WHITE  # 白方先手
        self.game_over = False
        self.winner_color = None
        self.move_history = []
    
    def reset(self):
        """重置游戏"""
        self.board.reset()
        self.turn = WHITE
        self.game_over = False
        self.winner_color = None
        self.move_history = []
        return self.get_state()
    
    def get_state(self):
        """
        获取当前状态
        返回字典包含:
            - board: 棋盘状态
            - turn: 当前回合
            - valid_moves: 合法移动
            - game_over: 是否结束
            - winner: 获胜方
        """
        return {
            'board': self.board.get_board_state(),
            'turn': self.turn,
            'valid_moves': self.get_valid_moves(),
            'game_over': self.game_over,
            'winner': self.winner_color,
            'move_count': self.board.move_count_since_capture_or_king,
            'white_pieces': self.board.white_left,
            'black_pieces': self.board.black_left
        }
    
    def get_valid_moves(self):
        """
        获取当前玩家的所有合法移动
        返回格式: [((from_row, from_col), (to_row, to_col), captured_count, path_index), ...]
        每条不同的吃子路径都作为独立的移动返回
        """
        moves_dict = self.board.get_valid_moves(self.turn)
        moves_list = []
        
        for piece, targets in moves_dict.items():
            for target_pos, captured_lists in targets.items():
                # 如果是普通移动（空列表）
                if isinstance(captured_lists, list) and len(captured_lists) == 0:
                    moves_list.append((
                        (piece.row, piece.col),
                        target_pos,
                        0,
                        0  # 普通移动没有路径选择，path_index = 0
                    ))
                # 如果是吃子移动（列表的列表）
                elif isinstance(captured_lists, list) and captured_lists:
                    if isinstance(captured_lists[0], list):
                        # 新格式：每条路径作为独立移动
                        for path_idx, captured_list in enumerate(captured_lists):
                            moves_list.append((
                                (piece.row, piece.col),
                                target_pos,
                                len(captured_list),
                                path_idx
                            ))
                    else:
                        # 兼容旧格式
                        moves_list.append((
                            (piece.row, piece.col),
                            target_pos,
                            len(captured_lists),
                            0
                        ))
        
        return moves_list
    
    def make_move(self, from_pos, to_pos, path_index=0):
        """
        执行移动
        参数:
            from_pos: (row, col) 起始位置
            to_pos: (row, col) 目标位置
            path_index: int 当有多条吃子路径到达同一位置时，选择哪条路径（默认0）
        返回:
            bool: 移动是否成功
        """
        if self.game_over:
            return False
        
        # 获取棋子
        piece = self.board.pieces[from_pos[0]][from_pos[1]]
        if piece == 0 or piece.color != self.turn:
            return False
        
        # 获取合法移动
        valid_moves = self.board.get_valid_moves(self.turn)
        if piece not in valid_moves:
            return False
        
        if to_pos not in valid_moves[piece]:
            return False
        
        # 执行移动
        captured_data = valid_moves[piece][to_pos]
        
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
        
        self.board.make_move(piece, to_pos, captured)
        
        # 切换回合
        next_turn = BLACK if self.turn == WHITE else WHITE
        
        # 记录局面（带上下一个行棋方）
        self.board.record_position(next_turn)
        
        # 记录移动
        self.move_history.append({
            'from': from_pos,
            'to': to_pos,
            'captured': len(captured),
            'path_index': path_index,
            'turn': self.turn
        })
        
        # 应用回合切换
        self.turn = next_turn
        
        # 检查游戏结束
        self._check_game_over()
        
        return True
    
    def _check_game_over(self):
        """检查游戏是否结束"""
        # 检查胜负
        result = self.board.winner()
        if result:
            self.game_over = True
            self.winner_color = result
            return
        
        # 检查是否有合法移动
        if not self.board.has_valid_moves(self.turn):
            self.game_over = True
            self.winner_color = BLACK if self.turn == WHITE else WHITE
    
    def get_winner(self):
        """获取获胜方"""
        return self.winner_color
    
    def is_game_over(self):
        """游戏是否结束"""
        return self.game_over
    
    def print_state(self):
        """打印当前状态"""
        self.board.print_board()
        print(f"Turn: {self.turn}")
        print(f"White pieces: {self.board.white_left}, Black pieces: {self.board.black_left}")
        print(f"Moves since capture/king: {self.board.move_count_since_capture_or_king}/25")
        if self.game_over:
            print(f"Game Over! Winner: {self.winner_color}")


# 使用示例
if __name__ == "__main__":
    # 创建游戏
    game = CheckersGame()
    
    print("=== 国际跳棋环境测试 ===\n")
    
    # 打印初始状态
    print("初始棋盘:")
    game.print_state()
    
    # 获取合法移动
    valid_moves = game.get_valid_moves()
    print(f"白方有 {len(valid_moves)} 个合法移动")
    if valid_moves:
        print(f"示例移动: {valid_moves[0]}")
    
    # 执行一步移动
    if valid_moves:
        from_pos, to_pos, captures, path_idx = valid_moves[0]
        success = game.make_move(from_pos, to_pos, path_idx)
        print(f"\n执行移动 {from_pos} -> {to_pos} (吃{captures}个, 路径{path_idx}): {'成功' if success else '失败'}")
        game.print_state()
    
    print("\n=== 环境接口说明 ===")
    print("1. CheckersGame() - 创建游戏实例")
    print("2. reset() - 重置游戏")
    print("3. get_state() - 获取完整状态")
    print("4. get_valid_moves() - 获取合法移动列表")
    print("5. make_move(from_pos, to_pos, path_index=0) - 执行移动")
    print("6. is_game_over() - 检查游戏是否结束")
    print("7. get_winner() - 获取获胜方")
