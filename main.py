import os
import time
import arcade
import numpy as np
import itertools
from arcade.sound import Sound

arcade.Sprite

# --- Constants ---
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Tetris"

GRID_ROWS = 20
GRID_COLS = 10


# Set the working directory (where we expect to find files) to the same
# directory this .py file is in. You can leave this out of your own
# code, but it is needed to easily run the examples using "python -m"
# as mentioned at the top of this program.
file_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_path)

BLOCK_WIDTH = 20
BLOCK_HEIGHT = 20

BLOCK_EMPTY = 0
BLOCK_ORANGE = 1
BLOCK_BLUE = 2
BLOCK_CYAN = 3
BLOCK_GREEN = 4
BLOCK_RED = 5
BLOCK_VIOLET = 6
BLOCK_YELLOW = 7

BLOCK_TEXTURES = [
    None,  # Block index start from 1 because 0 represents no block.
    arcade.load_texture("images/block-orange.png"),
    arcade.load_texture("images/block-blue.png"),
    arcade.load_texture("images/block-cyan.png"),
    arcade.load_texture("images/block-green2.png"),
    arcade.load_texture("images/block-red.png"),
    arcade.load_texture("images/block-violet.png"),
    arcade.load_texture("images/block-yellow.png")
]

TETRIMINOS = [
    np.array([[0, 0, 0, 0],
              [1, 1, 1, 1],
              [0, 0, 0, 0],
              [0, 0, 0, 0]]) * BLOCK_CYAN,
    np.array([[1, 0, 0],
              [1, 1, 1],
              [0, 0, 0]], ) * BLOCK_BLUE,
    np.array([[0, 0, 1],
              [1, 1, 1],
              [0, 0, 0]]) * BLOCK_ORANGE,
    np.array([[1, 1],
              [1, 1]]) * BLOCK_YELLOW,
    np.array([[0, 1, 1],
              [1, 1, 0],
              [0, 0, 0]]) * BLOCK_GREEN,
    np.array([[1, 1, 0],
              [0, 1, 1],
              [0, 0, 0]]) * BLOCK_RED,
    np.array([[0, 1, 0],
              [1, 1, 1],
              [0, 0, 0]]) * BLOCK_VIOLET,
]

UPCOMING_TETRIMINOS_INDICES = np.random.randint(len(TETRIMINOS), size=100000)


class Tetrimino(object):
    def __init__(self, tetris_grid, tetrimino):
        self.tetris_grid = tetris_grid
        self.tetrimino = tetrimino
        self.placed = False
        self.last_move_epoch = None
        self.put_at_screen_top()

    def is_valid_position(self, tetrimino, row, col):
        """
        Determines whether the given tetrimino at the given position (row, col)
        is valid or not. It checks all the non-empty blocks occupied by the
        tetrimino at the given position and if there is any overlap with a
        non-empty block in the grid, it returns false. This function is used by
        the different moving and rotation functions to determine whether a
        certain move or rotation is valid or not.

        Returns: True or False
        """
        for tetrimino_row, tetrimino_col in list(itertools.product(
                *map(range, tetrimino.shape))):
            if tetrimino[tetrimino_row, tetrimino_col] == BLOCK_EMPTY:
                continue
            grid_row = row + tetrimino_row
            grid_col = col + tetrimino_col
            if grid_row < 0:
                # This row is still out of screen, so we don't check it.
                return True
            if grid_row >= self.tetris_grid.rows:
                return False
            if grid_col < 0 or grid_col >= self.tetris_grid.cols:
                return False
            if self.tetris_grid.get_block(grid_row, grid_col) != BLOCK_EMPTY:
                return False
        return True

    def rotate_cw(self):
        rotated_tetrimino = np.rot90(self.tetrimino, 1, (1, 0))
        row = self.row  # + self.tetrimino.shape[0] // 2
        col = self.col  # + self.tetrimino.shape[1] // 2
        if self.is_valid_position(rotated_tetrimino, row, col):
            self.tetrimino = rotated_tetrimino
            self.row = row
            self.col = col

    def rotate_ccw(self):
        rotated_tetrimino = np.rot90(self.tetrimino, 1, (0, 1))
        row = self.row  # + self.tetrimino.shape[0] // 2
        col = self.col  # + self.tetrimino.shape[1] // 2
        if self.is_valid_position(rotated_tetrimino, row, col):
            self.tetrimino = rotated_tetrimino
            self.row = row
            self.col = col

    def move_left(self):
        if self.is_valid_position(self.tetrimino, self.row, self.col - 1):
            self.col -= 1
            return True
        return False

    def move_right(self):
        if self.is_valid_position(self.tetrimino, self.row, self.col + 1):
            self.col += 1
            return True
        return False

    def move_down(self):
        # check whether it can move down, and mark it as placed if it cannot.
        if self.is_valid_position(self.tetrimino, self.row + 1, self.col):
            self.row += 1
            return True
        else:
            self.placed = True
            return False

    def drop(self):
        while self.move_down():
            pass
    
    def put_at_screen_top(self):
        rows, cols = self.tetrimino.shape
        self.row = -rows + 1
        self.col = (GRID_COLS - cols)//2

    def update(self, game):
        if self.last_move_epoch is None:
            self.last_move_epoch = game.epoch
            return

        if game.epoch - self.last_move_epoch > self.tetris_grid.pace:
            self.move_down()
            self.last_move_epoch = game.epoch

    def place_on_grid(self):
        for row, col in list(itertools.product(*map(range, self.tetrimino.shape))):
            grid_row = row + self.row
            grid_col = col + self.col
            if grid_row < 0 or grid_row >= self.tetris_grid.rows or \
                    grid_col < 0 or grid_col >= self.tetris_grid.cols:
                continue
            if self.tetrimino[row, col] != BLOCK_EMPTY and \
                    self.tetris_grid.get_block(grid_row, grid_col) == BLOCK_EMPTY:
                self.tetris_grid.set_block(
                    grid_row, grid_col, self.tetrimino[row, col])

    def remove_from_grid(self):
        for row, col in list(itertools.product(*map(range, self.tetrimino.shape))):
            grid_row = row + self.row
            grid_col = col + self.col
            if grid_row < 0 or grid_row >= self.tetris_grid.rows or \
                    grid_col < 0 or grid_col >= self.tetris_grid.cols:
                continue
            if self.tetrimino[row, col] != BLOCK_EMPTY:
                self.tetris_grid.set_block(grid_row, grid_col, BLOCK_EMPTY)


class TetrisGrid(object):
    def __init__(self, center_x, center_y, rows, cols):
        self.grid = np.zeros(shape=(rows, cols), dtype='int32')
        self.rows = rows
        self.cols = cols
        self.center_x = center_x
        self.center_y = center_y
        self.grid_width = cols * BLOCK_WIDTH
        self.grid_height = rows * BLOCK_HEIGHT
        self.grid_left = center_x - self.grid_width//2
        self.grid_top = center_y + self.grid_height//2
        self.current_tetrimino = None
        self.shelved_tetrimino = None
        self.next_tetrimino_index = 0
        self.pace = 0.5  # initial pace; move the tetrimino down each second

    def set_block(self, row, col, val):
        if row < 0 or row >= self.rows or \
                col < 0 or col >= self.cols:
            raise IndexError(
                f"Row and/or column are out of range: row {row}, col {col}.")
        self.grid[row, col] = val

    def get_block(self, row, col):
        if row < 0 or row >= self.rows or \
                col < 0 or col >= self.cols:
            raise IndexError(
                f"Row and/or column are out of range: row {row}, col {col}.")
        return self.grid[row, col]

    def get_block_screen_pos(self, row, col):
        return (self.grid_left + col*BLOCK_WIDTH + BLOCK_WIDTH//2,
                self.grid_top - row*BLOCK_HEIGHT - BLOCK_HEIGHT//2)

    def render_border(self):
        arcade.draw_rectangle_outline(self.center_x, self.center_y, self.grid_width, self.grid_height,
                                      arcade.color.GREEN)

    def __render_blocks(self, blocks, row_shift=0, col_shift=0):
        block_x_shift = BLOCK_WIDTH // 2
        block_y_shift = BLOCK_HEIGHT // 2
        for row, col in list(itertools.product(*map(range, blocks.shape))):
            block = blocks[row, col]
            if block == BLOCK_EMPTY:
                continue
            center_x, center_y = self.get_block_screen_pos(
                row + row_shift, col + col_shift)
            arcade.draw_texture_rectangle(
                center_x, center_y, BLOCK_WIDTH, BLOCK_HEIGHT, BLOCK_TEXTURES[block])

    def render_grid(self):
        self.__render_blocks(self.grid)

    def render_upcoming_tetriminos(self):
        for i in range(3):
            idx = UPCOMING_TETRIMINOS_INDICES[self.next_tetrimino_index+i]
            tetrimino = TETRIMINOS[idx].copy()
            self.__render_blocks(tetrimino, self.rows - 5*(i+1), -5)

    def render_shelved_tetrimino(self):
        if self.shelved_tetrimino is None:
            return
        self.__render_blocks(self.shelved_tetrimino.tetrimino, self.rows - 5*(5), -5)

    def remove_complete_rows(self):
        target_row = self.rows - 1
        new_grid = np.zeros(shape=(self.rows, self.cols), dtype='int32')
        for row in range(self.rows-1, -1, -1):
            if self.grid[row, :].all():
                continue
            new_grid[target_row, :] = self.grid[row, :]
            target_row -= 1
        self.grid = new_grid

    def new_tetrimino(self):
        idx = UPCOMING_TETRIMINOS_INDICES[self.next_tetrimino_index]
        self.next_tetrimino_index += 1
        t = TETRIMINOS[idx].copy()
        self.current_tetrimino = Tetrimino(self, t)

    def place_current_tetrimino(self):
        if self.current_tetrimino is not None:
            self.current_tetrimino.place_on_grid()
            self.remove_complete_rows()

    def shelve_tetrimino(self):
        if self.current_tetrimino is None:
            return
        self.current_tetrimino.remove_from_grid()
        if self.shelved_tetrimino is not None:
            self.current_tetrimino, self.shelved_tetrimino = \
                self.shelved_tetrimino, self.current_tetrimino
            self.current_tetrimino.put_at_screen_top()
        else:
            self.shelved_tetrimino = self.current_tetrimino
            self.new_tetrimino()

    def update(self, game):
        if self.current_tetrimino is None or self.current_tetrimino.placed:
            self.place_current_tetrimino()
            self.new_tetrimino()
        self.current_tetrimino.update(game)

    def render(self, game):
        self.current_tetrimino.place_on_grid()
        self.render_border()
        self.render_grid()
        self.render_upcoming_tetriminos()
        self.render_shelved_tetrimino()
        self.current_tetrimino.remove_from_grid()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.RIGHT:
            self.current_tetrimino.move_right()
        if key == arcade.key.LEFT:
            self.current_tetrimino.move_left()
        if key == arcade.key.DOWN:
            self.current_tetrimino.move_down()
        if key == arcade.key.UP or key == arcade.key.SPACE:
            self.current_tetrimino.drop()
        if key == arcade.key.A:
            self.current_tetrimino.rotate_ccw()
        if key == arcade.key.E:
            self.current_tetrimino.rotate_cw()
        if key == arcade.key.O:
            self.shelve_tetrimino()


class TetrisGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.epoch = None
        self.last_epoch = None
        self.background = None
        self.objects = []

    def setup(self):
        self.background = arcade.load_texture("images/background.jpg")
        self.play_music()

    def play_music(self):
        try:
            file_name = "music/Tetris.mp3"
            sound = Sound(file_name)
            sound.play()
        except Exception as e:
            print(f'Unable to load sound file: "{file_name}". Exception: {e}.')

    def add_object(self, obj):
        """
        Adds an object to the game.

        Keyword arguments:
        obj -- the object to be added
        """

        self.objects.append(obj)

    def update_scene(self):
        # Last epoch and epoch can be useful for objects.
        self.last_epch = self.epoch
        self.epoch = time.time()

        # Call the update method for all game objects.
        for obj in self.objects:
            obj.update(self)

    def render_scene(self):
        # This command has to happen before we start drawing
        arcade.start_render()

        # Draw the background texture
        arcade.draw_texture_rectangle(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                      SCREEN_WIDTH, SCREEN_HEIGHT, self.background)

        # Draw all the objects in the order they are added.
        for obj in self.objects:
            obj.render(self)

    def on_key_press(self, key, modifiers):
        # Pass on key press event to game objects.
        for obj in self.objects:
            if hasattr(obj, "on_key_press"):
                obj.on_key_press(key, modifiers)

    def on_draw(self):
        """
        Update and render the scene.
        """

        self.update_scene()
        self.render_scene()


def main():
    """ Main method """
    game = TetrisGame()
    game.setup()
    game.add_object(TetrisGrid(
        SCREEN_WIDTH//2, SCREEN_HEIGHT//2, GRID_ROWS, GRID_COLS))
    arcade.run()


if __name__ == "__main__":
    main()
