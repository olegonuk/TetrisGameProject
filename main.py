"""Tetris Game => Main.py"""
import sys
from os.path import join
from random import choice

import pygame

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TETROMINOS, GRAY

from game import Game
from score import Score
from preview import Preview


class Main:
    """Класс Main"""
    def __init__(self):

        # Загальні
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption('Tetris Game')

        # Фігури
        self.next_shapes = [choice(list(TETROMINOS.keys())) for shape in range(3)]

        # Компоненти
        self.game = Game(self.get_next_shape, self.update_score)
        self.score = Score()
        self.preview = Preview()

        # Аудіо
        self.music = pygame.mixer.Sound(join('.', 'assets', 'sound', 'assets_sound_music.wav'))
        self.music.set_volume(0.05)
        self.music.play(-1)

    def update_score(self, lines, score, level):
        """Метод оновлення очок"""
        self.score.lines = lines
        self.score.score = score
        self.score.level = level

    def get_next_shape(self):
        """Метод вибору наступної фігури"""
        next_shape = self.next_shapes.pop(0)
        self.next_shapes.append(choice(list(TETROMINOS.keys())))
        return next_shape

    def run(self):
        """Метод запуску гри"""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            # Дисплей гри
            self.display_surface.fill(GRAY)

            # Компоненти
            self.game.run()
            self.score.run()
            self.preview.run(self.next_shapes)

            # Оновлення гри
            pygame.display.update()
            self.clock.tick(60)

if __name__ == '__main__':
    main = Main()
    main.run()
