
"""
Cursor Trail Raylib — Kitty-style block cursor implementation with adjustable fading opacity speed
"""

import math
from typing import List, Tuple

from pyray import *

CURSOR_TRAIL_DECAY_FAST = 0.03
CURSOR_TRAIL_DECAY_SLOW = 0.35
FADE_OUT_SPEED = 0.2  # multiplier for fade out speed
FADE_IN_SPEED = 8.0   # multiplier for fade in speed

def norm(x: float, y: float) -> float:
    return math.hypot(x, y)

class Trail:
    def __init__(self, cursor_width, cursor_height, color):
        self.color = color
        self.cursor_width = cursor_width
        self.cursor_height = cursor_height
        self.corner_x: List[float] = list([0.0,0.0,0.0,0.0])
        self.corner_y: List[float] = list([0.0,0.0,0.0,0.0])
        self.opacity: float = 0.0
        self.updated_at: float = 0.0
        self.edge_x: Tuple[float,float] = (0.0,0.0)
        self.edge_y: Tuple[float,float] = (0.0,0.0)

    def set_target_from_rect(self, x: float, y: float) -> bool:
        left, right = x, x + self.cursor_width
        top, bottom = y, y + self.cursor_height
        changed = (self.edge_x != (left,right) or self.edge_y != (top,bottom))
        self.edge_x = (left,right)
        self.edge_y = (top,bottom)
        return changed

    def update_corners(self, now: float):
        corner_index = [[1,1,0,0],[0,1,1,0]]
        dt = now - self.updated_at
        cursor_center_x = (self.edge_x[0]+self.edge_x[1])*0.5
        cursor_center_y = (self.edge_y[0]+self.edge_y[1])*0.5
        cursor_diag_2 = norm(self.edge_x[1]-self.edge_x[0], self.edge_y[1]-self.edge_y[0])*0.5

        dx = [0.0]*4
        dy = [0.0]*4
        dot = [0.0]*4

        for i in range(4):
            dx[i] = self.edge_x[corner_index[0][i]] - self.corner_x[i]
            dy[i] = self.edge_y[corner_index[1][i]] - self.corner_y[i]
            denom = cursor_diag_2 * norm(dx[i], dy[i])
            dot[i] = 0.0 if denom==0 else (dx[i]*(self.edge_x[corner_index[0][i]]-cursor_center_x)+dy[i]*(self.edge_y[corner_index[1][i]]-cursor_center_y))/denom

        min_dot, max_dot = min(dot), max(dot)
        for i in range(4):
            if dx[i]==0 and dy[i]==0: continue
            decay = CURSOR_TRAIL_DECAY_SLOW if min_dot==max_dot else CURSOR_TRAIL_DECAY_SLOW + (CURSOR_TRAIL_DECAY_FAST-CURSOR_TRAIL_DECAY_SLOW)*(dot[i]-min_dot)/(max_dot-min_dot)
            step = 1.0 - math.pow(2.0, -10.0*dt/decay)
            self.corner_x[i] += dx[i]*step
            self.corner_y[i] += dy[i]*step

    def update_opacity(self, now: float, cursor_moved: bool):
        dt = now - self.updated_at
        # fade out
        self.opacity -= dt / CURSOR_TRAIL_DECAY_SLOW * FADE_OUT_SPEED
        self.opacity = max(0.0, min(1.0, self.opacity))
        # fade in when cursor moves
        if cursor_moved:
            self.opacity += dt / CURSOR_TRAIL_DECAY_SLOW * FADE_IN_SPEED
            self.opacity = min(1.0, self.opacity)

    def update(self, x, y) -> bool:
        now = get_time()
        moved = self.set_target_from_rect(x, y)
        if self.updated_at==0.0:
            corner_index=[[1,1,0,0],[0,1,1,0]]
            for i in range(4):
                self.corner_x[i] = self.edge_x[corner_index[0][i]]
                self.corner_y[i] = self.edge_y[corner_index[1][i]]
            self.updated_at = now-0.016
        self.update_corners(now)
        self.update_opacity(now, moved)
        self.updated_at = now
        return self.opacity>0.01

    def corners_as_list(self) -> List[Tuple[float,float]]:
        return [(self.corner_x[i], self.corner_y[i]) for i in range(4)]

    def draw(self):
        c = self.corners_as_list()
        alpha = int(self.opacity*200)
        color = Color(self.color[0], self.color[1], self.color[2], alpha)
        draw_triangle(Vector2(c[3][0],c[3][1]), Vector2(c[2][0],c[2][1]), Vector2(c[1][0],c[1][1]), color)
        draw_triangle(Vector2(c[1][0],c[1][1]), Vector2(c[0][0],c[0][1]), Vector2(c[3][0],c[3][1]), color)

if __name__ == '__main__':
    # --- Raylib Demo ---
    SCREEN_W, SCREEN_H = 800, 600
    init_window(SCREEN_W, SCREEN_H, "Kitty Block Cursor Trail")
    set_target_fps(60)
    cursor_w, cursor_h = 40, 28
    trail = Trail(cursor_w, cursor_h, WHITE)

    while not window_should_close():
        mx, my = get_mouse_x(), get_mouse_y()
        cx, cy = mx-cursor_w/2, my-cursor_h/2
        trail.update(cx, cy)

        begin_drawing()
        clear_background(Color(18,18,18,255))

        trail.draw()

        draw_rectangle(int(cx), int(cy), int(cursor_w), int(cursor_h), Color(240,240,240,255))
        end_drawing()

    close_window()
