from . import log
import asyncio

from pyray import *

class Screen():
    def __init__(self, input_queue, updates_queue, main_loop):
        self.main_loop = main_loop
        self.input_queue = input_queue
        self.updates_queue = updates_queue
        self.ctrl_c_happened = False

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
        self.map_data = 0

        self.current_x = 0
        self.current_y = 0
        self.others = {}

    def send_key_to_main_loop(self, key):
        future = asyncio.run_coroutine_threadsafe(self.input_queue.put(key),
                                                  self.main_loop)
        future.result()

    def forward_key_presses(self):
        if  is_key_down(KeyboardKey.KEY_LEFT_CONTROL) and \
            is_key_down(KeyboardKey.KEY_C):
            if not self.ctrl_c_happened:
                self.send_key_to_main_loop('\x03')
                self.ctrl_c_happened = True

        if is_key_down(KeyboardKey.KEY_H): self.send_key_to_main_loop('h')
        if is_key_down(KeyboardKey.KEY_J): self.send_key_to_main_loop('j')
        if is_key_down(KeyboardKey.KEY_K): self.send_key_to_main_loop('k')
        if is_key_down(KeyboardKey.KEY_L): self.send_key_to_main_loop('l')

    def handle_updates(self) -> bool:
        try:
            while True:
                item = self.updates_queue.get_nowait()
                if item[0] == 1:
                    return False

                if item[0] == 2: # map update
                    self.map_x = item[1]
                    self.map_y = item[2]
                    self.map_width = item[3]
                    self.map_height = item[4]
                    self.map_data = item[5]
                    log.glog(f"{self.map_width, self.window_width, self.map_height, self.window_height}")

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

                draw_rectangle(x_in_pxls, y_in_pxls, self.block_width, self.block_height, BLACK);

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
        init_window(self.window_width_in_pxls,
                    self.window_height_in_pxls,
                    "Vimpire")
        set_target_fps(30)

        while not window_should_close():
            self.forward_key_presses()

            begin_drawing()
            clear_background(WHITE)

            self.draw_map()

            if not self.handle_updates():
                end_drawing()
                break

            self.draw_current()
            self.draw_others()

            draw_fps(0, 0)
            end_drawing()

        close_window()
