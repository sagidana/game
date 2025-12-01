from . import log
import asyncio

from pyray import *

class Screen():
    def __init__(self, input_queue, updates_queue, main_loop):
        self.main_loop = main_loop
        self.input_queue = input_queue
        self.updates_queue = updates_queue
        self.height = 1200
        self.width = 800
        self.ctrl_c_happened = False


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
                # if item[0] == 2: # position
                    # user = item[1]
                    # x, y = item[2], item[3]
        except asyncio.QueueEmpty:
            item = None
        return True

    def run(self):
        init_window(self.height,
                    self.width,
                    "Vimpire")
        set_target_fps(30)

        while not window_should_close():
            self.forward_key_presses()

            begin_drawing()
            draw_fps(0, 0)
            clear_background(BLACK)


            if not self.handle_updates():
                end_drawing()
                break

            end_drawing()

        close_window()
