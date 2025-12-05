from . import log
import asyncio
from random import randint

from pyray import *

CTRL_B_KEY =                chr(2)
CTRL_C_KEY =                chr(3)
CTRL_D_KEY =                chr(4)
CTRL_F_KEY =                chr(6)
CTRL_H_KEY =                chr(8)
TAB_KEY =                   chr(9)
CTRL_I_KEY =                chr(9)
CTRL_J_KEY =                chr(10)
CTRL_K_KEY =                chr(11)
ENTER_KEY =                 chr(13)
CTRL_L_KEY =                chr(12)
CTRL_N_KEY =                chr(14)
CTRL_O_KEY =                chr(15)
CTRL_P_KEY =                chr(16)
CTRL_R_KEY =                chr(18)
CTRL_S_KEY =                chr(19)
CTRL_T_KEY =                chr(20)
CTRL_U_KEY =                chr(21)
CTRL_V_KEY =                chr(22)
CTRL_W_KEY =                chr(23)
CTRL_X_KEY =                chr(24)
ESC_KEY =                   chr(27)
CTRL_BACKSLASH_KEY =        chr(28)
CTRL_CLOSE_BRACKET_KEY =    chr(29)
BACKSPACE_KEY =             chr(127)

themes = {
        'default': {
            'floor': {
                'fill': [
                    #001845
                    Color(0x00, 0x18, 0x45, 0xFF),
                    #002855
                    Color(0x00, 0x28, 0x55, 0xFF),
                    ],
                'lines': [
                    #33415c
                    Color(0x33, 0x41, 0x5C, 0xFF),
                    #5c677d
                    Color(0x5C, 0x67, 0x7D, 0xFF),
                    ]
            },
            'failed': {
                'floor': [
                    Color(0x54, 0x3B, 0x24, 0xFF),
                    Color(0x57, 0x3D, 0x24, 0xFF),
                    ]
                },
            }
        }

class Screen():
    def __init__(self, input_queue, updates_queue, main_loop):
        self.main_loop = main_loop
        self.input_queue = input_queue
        self.updates_queue = updates_queue

        self.window_height_in_pxls = 800
        self.window_width_in_pxls = 1200
        self.block_height = 20
        self.block_width = 12
        self.window_width = int(self.window_width_in_pxls / self.block_width)
        self.window_height = int(self.window_height_in_pxls / self.block_height)

        self.window_x = 0
        self.window_y = 0
        self.map_x = 0
        self.map_y = 0
        self.map_height = 0
        self.map_width = 0
        self.map_data = []

        self.current_x = 0
        self.current_y = 0
        self.others = {}

    def send_key_to_main_loop(self, key):
        future = asyncio.run_coroutine_threadsafe(self.input_queue.put(key),
                                                  self.main_loop)
        future.result()

    def forward_key_presses(self):
        if is_key_pressed(KeyboardKey.KEY_C):
            if  is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
                self.send_key_to_main_loop(CTRL_C_KEY)
        if is_key_pressed(KeyboardKey.KEY_U):
            if  is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
                self.send_key_to_main_loop(CTRL_U_KEY)
            else: pass
        if is_key_pressed(KeyboardKey.KEY_D):
            if  is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
                self.send_key_to_main_loop(CTRL_D_KEY)
            else: pass
        if is_key_pressed(KeyboardKey.KEY_H):
            self.send_key_to_main_loop('h')
        if is_key_pressed(KeyboardKey.KEY_J):
            self.send_key_to_main_loop('j')
        if is_key_pressed(KeyboardKey.KEY_K):
            self.send_key_to_main_loop('k')
        if is_key_pressed(KeyboardKey.KEY_L):
            self.send_key_to_main_loop('l')
        if is_key_pressed(KeyboardKey.KEY_F):
            if  is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
                self.send_key_to_main_loop(CTRL_F_KEY)
            else:
                self.send_key_to_main_loop('f')
        if is_key_pressed(KeyboardKey.KEY_B):
            if  is_key_down(KeyboardKey.KEY_LEFT_CONTROL):
                self.send_key_to_main_loop(CTRL_B_KEY)
            else:
                pressed = 'b'
                if  is_key_down(KeyboardKey.KEY_LEFT_SHIFT): pressed = 'B'
                self.send_key_to_main_loop(pressed)
        if is_key_pressed(KeyboardKey.KEY_W):
            pressed = 'w'
            if  is_key_down(KeyboardKey.KEY_LEFT_SHIFT): pressed = 'W'
            self.send_key_to_main_loop(pressed)

    def initialize_map(self, update):
        self.map_x = update[1]
        self.map_y = update[2]
        self.map_width = update[3]
        self.map_height = update[4]
        self.map_data = update[5]
        self.local_map_data = [BLACK] * len(self.map_data)

        for x in range(self.map_width):
            for y in range(self.map_height):
                curr_index = y * self.map_width + x
                map_value = self.map_data[curr_index]
                # log.glog(f"{map_value=}")
                if map_value == ord('0'): # floor
                    self.local_map_data[curr_index] = themes['default']['floor']['fill'][randint(0, len(themes['default']['floor']['fill']) - 1)]
                    continue

                # unknown type is black
                self.local_map_data[curr_index] = BLACK

    def handle_updates(self) -> bool:
        try:
            while True:
                item = self.updates_queue.get_nowait()
                if item[0] == 1:
                    return False

                if item[0] == 2: # map update
                    self.initialize_map(item)

                if item[0] == 3: # current
                    _ = item[1] # id
                    current_x = item[2]
                    current_y = item[3]

                    # TODO: movement animation
                    log.glog(f"[+] current move: {current_x}, {current_y}")

                    self.current_x = current_x
                    self.current_y = current_y

                if item[0] == 4: # others update
                    player_id = item[1]
                    player_x = item[2]
                    player_y = item[3]

                    self.others[player_id] = [player_x, player_y]

        except asyncio.QueueEmpty:
            item = None
        return True

    def draw_tile(self, x, y):
        pass
    def draw_map(self):
        # TODO: window x and y adjustments based on current position

        # no map data to show
        if self.window_x < self.map_x: return
        if self.window_y < self.map_y: return
        if self.window_x + self.window_width > self.map_x + self.map_width: return
        if self.window_y + self.window_height > self.map_y + self.map_height: return

        for x in range(self.window_width):
            for y in range(self.window_height):
                x_in_pxls = self.block_width * x
                y_in_pxls = self.block_height * y

                map_position_x = self.window_x + x
                map_position_y = self.window_y + y

                curr_block_value = self.map_data[map_position_y * self.map_width + map_position_x]
                local_block_value = self.local_map_data[map_position_y * self.map_width + map_position_x]

                rectangle = Rectangle(x_in_pxls, y_in_pxls, self.block_width, self.block_height)

                if curr_block_value == ord('0'): # floor
                    draw_rectangle_rec(rectangle, local_block_value);
                    # draw_rectangle(x_in_pxls,
                                   # y_in_pxls,
                                   # self.block_width,
                                   # self.block_height,
                                   # local_block_value);

                    # draw_rectangle_lines_ex(rectangle, 0.5, Color(0,0,0,255));
                    # draw_rectangle_lines_ex(x_in_pxls,
                                         # y_in_pxls,
                                         # self.block_width,
                                         # self.block_height,
                                         # Color(0,0,0,255));
                if curr_block_value == ord('1'):
                    draw_rectangle(x_in_pxls, y_in_pxls, self.block_width, self.block_height, GRAY);

    def draw_current(self):
        x_in_pxls = (self.current_x - self.window_x) * self.block_width
        y_in_pxls = (self.current_y - self.window_y) * self.block_height
        draw_rectangle(x_in_pxls, y_in_pxls, self.block_width, self.block_height, WHITE);

    def draw_others(self):
        for other_id in self.others:
            other_x = self.others[other_id][0]
            other_y = self.others[other_id][1]

            # TODO add check if in window

            x_in_pxls = (other_x - self.window_x) * self.block_width
            y_in_pxls = (other_y - self.window_y) * self.block_height
            draw_rectangle(x_in_pxls, y_in_pxls, self.block_width, self.block_height, RED);

    def run(self):
        init_window(self.window_width_in_pxls, self.window_height_in_pxls, "Vimpire")
        set_exit_key(KeyboardKey.KEY_NULL) # disable esc closing raylib window
        # set_target_fps(60)

        while not window_should_close():
            if not self.handle_updates(): break
            self.forward_key_presses()

            begin_drawing()

            clear_background(WHITE)

            self.draw_map()

            self.draw_current()
            self.draw_others()

            draw_fps(0, 0)
            end_drawing()

        close_window()
