import pygame
import sys
import random
import time
from copy import deepcopy

# ---------- Config ----------
WINDOW_SIZE = 600
GRID_POS = (20, 20)
GRID_SIZE = WINDOW_SIZE - 2 * GRID_POS[0]
CELL_SIZE = GRID_SIZE // 9
FPS = 60

# Colors
BG = (28, 30, 40)
GRID_COLOR = (200, 200, 200)
LINE_COLOR = (100, 100, 100)
HIGHLIGHT_COLOR = (80, 120, 200)
GIVEN_COLOR = (200, 200, 200)
USER_COLOR = (230, 230, 230)
CONFLICT_COLOR = (200, 100, 100)
TEXT_COLOR = (230, 230, 230)
SUBTEXT_COLOR = (170, 170, 170)

# Fonts (initialized later)
FONT = None
SMALL_FONT = None

# ---------- Sample Puzzles ----------
PUZZLES = [
    # Easy
    [
        [5,3,0, 0,7,0, 0,0,0],
        [6,0,0, 1,9,5, 0,0,0],
        [0,9,8, 0,0,0, 0,6,0],

        [8,0,0, 0,6,0, 0,0,3],
        [4,0,0, 8,0,3, 0,0,1],
        [7,0,0, 0,2,0, 0,0,6],

        [0,6,0, 0,0,0, 2,8,0],
        [0,0,0, 4,1,9, 0,0,5],
        [0,0,0, 0,8,0, 0,7,9],
    ],
    # Medium
    [
        [0,0,0, 2,6,0, 7,0,1],
        [6,8,0, 0,7,0, 0,9,0],
        [1,9,0, 0,0,4, 5,0,0],

        [8,2,0, 1,0,0, 0,4,0],
        [0,0,4, 6,0,2, 9,0,0],
        [0,5,0, 0,0,3, 0,2,8],

        [0,0,9, 3,0,0, 0,7,4],
        [0,4,0, 0,5,0, 0,3,6],
        [7,0,3, 0,1,8, 0,0,0],
    ],
    # Hard
    [
        [0,0,0, 0,0,0, 2,0,0],
        [0,8,0, 0,0,7, 0,9,0],
        [6,0,2, 0,0,0, 5,0,0],

        [0,7,0, 0,6,0, 0,0,0],
        [0,0,0, 9,0,1, 0,0,0],
        [0,0,0, 0,2,0, 0,4,0],

        [0,0,5, 0,0,0, 6,0,3],
        [0,9,0, 4,0,0, 0,7,0],
        [0,0,6, 0,0,0, 0,0,0],
    ],
]

# ---------- Sudoku tools ----------
def find_empty(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                return r, c
    return None

def valid(board, num, pos):
    r, c = pos
    # Row
    for j in range(9):
        if board[r][j] == num and j != c:
            return False
    # Column
    for i in range(9):
        if board[i][c] == num and i != r:
            return False
    # Box
    br = (r // 3) * 3
    bc = (c // 3) * 3
    for i in range(br, br + 3):
        for j in range(bc, bc + 3):
            if board[i][j] == num and (i, j) != (r, c):
                return False
    return True

def solve_board(board, visualize=None, delay=0.01):
    empty = find_empty(board)
    if not empty:
        return True
    r, c = empty
    for num in range(1, 10):
        if valid(board, num, (r, c)):
            board[r][c] = num
            if visualize:
                visualize(deepcopy(board))
                # allow small processing time
                time.sleep(delay)
            if solve_board(board, visualize, delay):
                return True
            board[r][c] = 0
            if visualize:
                visualize(deepcopy(board))
                time.sleep(delay)
    return False

def board_is_complete_and_valid(board):
    for i in range(9):
        for j in range(9):
            v = board[i][j]
            if v == 0 or not valid(board, v, (i,j)):
                return False
    return True

# ---------- Pygame UI ----------
class SudokuApp:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.puzzle_idx = random.randrange(len(PUZZLES))
        self.original = deepcopy(PUZZLES[self.puzzle_idx])
        self.board = deepcopy(self.original)
        self.selected = None  # (row, col)
        self.start_time = time.time()
        self.errors = 0
        self.solved = False
        self.anim_board = None
        self.animating = False
        self._anim_stop_request = False

    def new_puzzle(self):
        self.puzzle_idx = random.randrange(len(PUZZLES))
        self.original = deepcopy(PUZZLES[self.puzzle_idx])
        self.board = deepcopy(self.original)
        self.selected = None
        self.start_time = time.time()
        self.errors = 0
        self.solved = False

    def reset_puzzle(self):
        self.board = deepcopy(self.original)
        self.selected = None
        self.start_time = time.time()
        self.errors = 0
        self.solved = False

    def draw(self):
        self.screen.fill(BG)
        grid_x, grid_y = GRID_POS

        # draw cell backgrounds / highlights
        for i in range(9):
            for j in range(9):
                x = grid_x + j * CELL_SIZE
                y = grid_y + i * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                # selected highlight (semi)
                if self.selected == (i, j):
                    pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, rect)
                else:
                    # subtle fill for given cells
                    if self.original[i][j] != 0:
                        pygame.draw.rect(self.screen, (40, 40, 40), rect)

        # Draw grid border
        pygame.draw.rect(self.screen, GRID_COLOR, (grid_x, grid_y, GRID_SIZE, GRID_SIZE), 2)

        # Draw numbers and thin lines
        for i in range(9):
            for j in range(9):
                x = grid_x + j * CELL_SIZE
                y = grid_y + i * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                val = self.board[i][j]
                if val != 0:
                    given = (self.original[i][j] != 0)
                    color = GIVEN_COLOR if given else USER_COLOR
                    # conflict detection
                    if not valid(self.board, val, (i, j)):
                        pygame.draw.rect(self.screen, CONFLICT_COLOR, rect, 3)
                    txt = FONT.render(str(val), True, color)
                    tw, th = txt.get_size()
                    tx = x + (CELL_SIZE - tw) // 2
                    ty = y + (CELL_SIZE - th) // 2
                    self.screen.blit(txt, (tx, ty))

                pygame.draw.rect(self.screen, LINE_COLOR, rect, 1)

        # heavy block lines
        for k in range(10):
            lw = 3 if k % 3 == 0 else 1
            # horizontal
            pygame.draw.line(self.screen, GRID_COLOR,
                             (grid_x, grid_y + k * CELL_SIZE),
                             (grid_x + GRID_SIZE, grid_y + k * CELL_SIZE), lw)
            # vertical
            pygame.draw.line(self.screen, GRID_COLOR,
                             (grid_x + k * CELL_SIZE, grid_y),
                             (grid_x + k * CELL_SIZE, grid_y + GRID_SIZE), lw)

        # Info text
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        time_surf = SMALL_FONT.render(time_str, True, SUBTEXT_COLOR)
        self.screen.blit(time_surf, (GRID_POS[0], GRID_POS[1] + GRID_SIZE + 10))

        err_surf = SMALL_FONT.render(f"Errors: {self.errors}", True, SUBTEXT_COLOR)
        self.screen.blit(err_surf, (GRID_POS[0] + 150, GRID_POS[1] + GRID_SIZE + 10))

        hint_surf = SMALL_FONT.render("H:Hint  SPACE:Solve  N:New  R:Reset", True, SUBTEXT_COLOR)
        self.screen.blit(hint_surf, (GRID_POS[0] + 320, GRID_POS[1] + GRID_SIZE + 10))

        if self.solved:
            win_surf = FONT.render("Puzzle Solved!", True, HIGHLIGHT_COLOR)
            self.screen.blit(win_surf, (GRID_POS[0] + GRID_SIZE - 220, GRID_POS[1] + GRID_SIZE + 6))

        pygame.display.flip()

    def click_cell(self, pos):
        x, y = pos
        gx, gy = GRID_POS
        if gx <= x < gx + GRID_SIZE and gy <= y < gy + GRID_SIZE:
            col = (x - gx) // CELL_SIZE
            row = (y - gy) // CELL_SIZE
            self.selected = (row, col)
        else:
            self.selected = None

    def place_number(self, num):
        if self.selected is None:
            return
        r, c = self.selected
        # don't allow editing givens
        if self.original[r][c] != 0:
            return
        if num == 0:
            self.board[r][c] = 0
            return
        if valid(self.board, num, (r, c)):
            self.board[r][c] = num
            if board_is_complete_and_valid(self.board):
                self.solved = True
        else:
            # keep it but count error
            self.board[r][c] = num
            self.errors += 1

    def hint(self):
        solver_board = deepcopy(self.board)
        if not solve_board(solver_board):
            return
        empties = [(i,j) for i in range(9) for j in range(9) if self.board[i][j] == 0]
        if not empties:
            return
        i,j = random.choice(empties)
        self.board[i][j] = solver_board[i][j]
        if board_is_complete_and_valid(self.board):
            self.solved = True

    def auto_solve(self):
        if self.animating:
            return
        self.animating = True
        self._anim_stop_request = False
        board_copy = deepcopy(self.board)

        def visualize(b):
            # allow stop by setting flag
            if self._anim_stop_request:
                return
            self.anim_board = deepcopy(b)
            # draw animation frame (non-blocking)
            self.draw_anim_board()
            pygame.display.flip()
            # process events so window stays responsive
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self._anim_stop_request = True

        solved = solve_board(board_copy, visualize=visualize, delay=0.02)
        if solved and not self._anim_stop_request:
            self.board = board_copy
            self.solved = True
        self.animating = False
        self.anim_board = None

    def draw_anim_board(self):
        # Draw same UI but show anim_board if present
        self.screen.fill(BG)
        grid_x, grid_y = GRID_POS

        # backgrounds
        for i in range(9):
            for j in range(9):
                x = grid_x + j * CELL_SIZE
                y = grid_y + i * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                if self.selected == (i, j):
                    pygame.draw.rect(self.screen, HIGHLIGHT_COLOR, rect)
                else:
                    if self.original[i][j] != 0:
                        pygame.draw.rect(self.screen, (40, 40, 40), rect)

        pygame.draw.rect(self.screen, GRID_COLOR, (grid_x, grid_y, GRID_SIZE, GRID_SIZE), 2)

        board_to_draw = self.anim_board if self.anim_board is not None else self.board

        for i in range(9):
            for j in range(9):
                x = grid_x + j * CELL_SIZE
                y = grid_y + i * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                val = board_to_draw[i][j]
                if val != 0:
                    txt = FONT.render(str(val), True, TEXT_COLOR)
                    tw, th = txt.get_size()
                    tx = x + (CELL_SIZE - tw) // 2
                    ty = y + (CELL_SIZE - th) // 2
                    self.screen.blit(txt, (tx, ty))
                pygame.draw.rect(self.screen, LINE_COLOR, rect, 1)

        for k in range(10):
            lw = 3 if k % 3 == 0 else 1
            pygame.draw.line(self.screen, GRID_COLOR,
                             (grid_x, grid_y + k * CELL_SIZE),
                             (grid_x + GRID_SIZE, grid_y + k * CELL_SIZE), lw)
            pygame.draw.line(self.screen, GRID_COLOR,
                             (grid_x + k * CELL_SIZE, grid_y),
                             (grid_x + k * CELL_SIZE, grid_y + GRID_SIZE), lw)

        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.screen.blit(SMALL_FONT.render(f"Time: {minutes:02d}:{seconds:02d}", True, SUBTEXT_COLOR),
                         (GRID_POS[0], GRID_POS[1] + GRID_SIZE + 10))
        self.screen.blit(SMALL_FONT.render(f"Errors: {self.errors}", True, SUBTEXT_COLOR),
                         (GRID_POS[0] + 150, GRID_POS[1] + GRID_SIZE + 10))

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            # If animating, we still want to process quit/escape quickly
            if not self.animating:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.click_cell(event.pos)
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                            if self.selected and self.original[self.selected[0]][self.selected[1]] == 0:
                                self.board[self.selected[0]][self.selected[1]] = 0
                        elif event.key == pygame.K_h:
                            self.hint()
                        elif event.key == pygame.K_SPACE:
                            self.auto_solve()
                        elif event.key == pygame.K_n:
                            self.new_puzzle()
                        elif event.key == pygame.K_r:
                            self.reset_puzzle()
                        else:
                            # Use event.unicode for typed characters (works for keypad and top-row numbers)
                            ch = event.unicode
                            if ch and ch.isdigit():
                                d = int(ch)
                                if 1 <= d <= 9:
                                    self.place_number(d)
                self.draw()
            else:
                # while animation is running, process events to allow quitting
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        # request animation stop
                        self._anim_stop_request = True
                # draw current anim frame if present
                if self.anim_board is not None:
                    self.draw_anim_board()
                    pygame.display.flip()

        pygame.quit()
        sys.exit()

# ---------- Main ----------
def main():
    global FONT, SMALL_FONT
    pygame.init()
    pygame.display.set_caption("Sudoku - Pygame (fixed)")
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 60))
    # choose a simple monospace-like system font; fallback to default if not available
    try:
        FONT = pygame.font.SysFont("consolas", max(22, CELL_SIZE // 2))
        SMALL_FONT = pygame.font.SysFont("consolas", 18)
    except Exception:
        FONT = pygame.font.Font(None, max(22, CELL_SIZE // 2))
        SMALL_FONT = pygame.font.Font(None, 18)

    app = SudokuApp(screen)
    app.run()

if __name__ == "__main__":
    main()
