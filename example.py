import colorsys
import math

from pygameloop import Scene, GameObject, singleton_scene, time
import pygame
from pygame.locals import *


class Player(GameObject):
    radius = 15
    speed = 15
    color = (1.0, 0.0, 0.0)
    color_speed = 1/8.0

    def awake(self):
        self.color = self.color
        self.x = 0
        self.y = 0
        self.movex = 0
        self.movey = 0

    def fixed_update(self):
        if not self.movex and not self.movey:
            return
        move_angle = math.atan2(self.movex, self.movey)
        self.x += math.sin(move_angle) * self.speed
        self.y += math.cos(move_angle) * self.speed

    def on_keydown(self, event):
        if event.key == K_LEFT:
            self.movex = -1
        elif event.key == K_RIGHT:
            self.movex = 1
        elif event.key == K_UP:
            self.movey = -1
        elif event.key == K_DOWN:
            self.movey = 1

    def on_keyup(self, event):
        if event.key in (K_LEFT, K_RIGHT):
            self.movex = 0
        elif event.key in (K_UP, K_DOWN):
            self.movey = 0
        elif event.key == K_ESCAPE:
            singleton_scene.quit()

    def update(self):
        hsv = colorsys.rgb_to_hsv(*self.color)
        hsv = list(hsv)
        hsv[0] += self.color_speed * time.delta_time % 1.0
        self.color = colorsys.hsv_to_rgb(*hsv)

    def draw(self, surface: pygame.Surface):
        screen_size = singleton_scene.config.screen_size
        offset_x = screen_size[0] // 2
        offset_y = screen_size[1] // 2
        color = tuple(int(x*255) for x in self.color)
        pygame.draw.circle(surface, color, (offset_x + int(self.x), offset_y + int(self.y)), self.radius)


def main():
    scene = Scene()
    scene.config.background_color = (0, 0, 0)
    scene.instantiate(Player)
    scene.run()


if __name__ == '__main__':
    import sys
    sys.exit(main())
