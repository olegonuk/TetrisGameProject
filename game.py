"""Tetris Game => Game.py"""
import sys
from os import path
from random import choice

import pygame

from settings import (
    GAME_WIDTH, GAME_HEIGHT, CELL_SIZE, COLUMNS, ROWS, PADDING,
    LINE_COLOR, TETROMINOS, BLOCK_OFFSET, GRAY,
    UPDATE_START_SPEED, MOVE_WAIT_TIME, ROTATE_WAIT_TIME,
    SCORE_DATA
)

from timer import Timer


class Game:
    """Клас Game"""
    def __init__(self, get_next_shape, update_score):

        # Загальні
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.display_surface = pygame.display.get_surface()
        self.rect = self.surface.get_rect(topleft = (PADDING, PADDING))
        self.sprites = pygame.sprite.Group()

        # Підключення до гри
        self.get_next_shape = get_next_shape
        self.update_score = update_score

        # Лінії
        self.line_surface = self.surface.copy()
        self.line_surface.fill((0, 255, 0))
        self.line_surface.set_colorkey((0, 255, 0))
        self.line_surface.set_alpha(120)

        # Tetromino
        self.field_data =[[0 for x in range(COLUMNS)] for y in range(ROWS)]
        self.tetromino = Tetromino(
            choice(list(TETROMINOS.keys())),
            self.sprites,
            self.create_new_tetromino,
            self.field_data
        )

        # Таймер
        self.down_speed = UPDATE_START_SPEED
        self.down_speed_faster = self.down_speed * 0.3
        self.down_pressed = False
        self.timers = {
            'vertical move': Timer(UPDATE_START_SPEED, True, self.move_down),
            'horizontal move': Timer(MOVE_WAIT_TIME),
            'rotate': Timer(ROTATE_WAIT_TIME)
        }
        self.timers['vertical move'].activate()

        # Рахунок(очки)
        self.current_level = 1
        self.current_score = 0
        self.current_lines = 0

        # Звук
        self.landing_sound = pygame.mixer.Sound(
            path.join('.', 'assets', 'sound', 'assets_sound_landing.wav')
        )
        self.landing_sound.set_volume(0.1)

    def calculate_score(self, num_lines):
        """Метод обрахування очок"""
        self.current_score += num_lines
        self.current_score += SCORE_DATA[num_lines] * self.current_level

        if self.current_lines / 10 > self.current_level:
            self.current_level += 1
            self.down_speed *= 0.75
            self.down_speed_faster = self.down_speed * 0.3
            self.timers['vertical move'].duration = self.down_speed

        self.update_score(self.current_lines, self.current_score, self.current_level)

    def check_game_over(self):
        """Метод перевірки ігрового поля на закінчення гри"""
        for block in self.tetromino.blocks:
            if block.pos.y < 0:
                sys.exit()

    def create_new_tetromino(self):
        """Метод створення фігурки в ігровому полі"""
        self.landing_sound.play()
        self.check_game_over()
        self.check_finished_rows()
        self.tetromino = Tetromino(
            self.get_next_shape(),
            self.sprites,
            self.create_new_tetromino,
            self.field_data
        )

    def timer_update(self):
        """Метод оновлення таймера"""
        for timer in self.timers.values():
            timer.update()

    def move_down(self):
        """Метод руху фігурки вниз"""
        self.tetromino.move_down()

    def draw_grid(self):
        """Метод відображення сітки ігрового поля"""
        for col in range(1, COLUMNS):
            x = col * CELL_SIZE
            pygame.draw.line(
                self.line_surface, LINE_COLOR, (x, 0),
                (x, self.surface.get_height()), 1)

        for row in range(1, ROWS):
            y = row * CELL_SIZE
            pygame.draw.line(
                self.line_surface, LINE_COLOR, (0, y),
                (self.surface.get_width(), y), 1)

        self.surface.blit(self.line_surface, (0, 0))

    def input(self):
        """Метод зчитування натискання клавіатури"""
        keys = pygame.key.get_pressed()

        # Горизонтальний рух
        if not self.timers['horizontal move'].active:
            if keys[pygame.K_LEFT]:
                self.tetromino.move_horizontal(-1)
                self.timers['horizontal move'].activate()
            if keys[pygame.K_RIGHT]:
                self.tetromino.move_horizontal(1)
                self.timers['horizontal move'].activate()

        # Перевертання фігурки
        if not self.timers['rotate'].active:
            if keys[pygame.K_UP]:
                self.tetromino.rotate()
                self.timers['rotate'].activate()

        # Збільшення швидкості вниз
        if not self.down_pressed and keys[pygame.K_DOWN]:
            self.down_pressed = True
            self.timers['vertical move'].duration = self.down_speed_faster

        if self.down_pressed and not keys[pygame.K_DOWN]:
            self.down_pressed = False
            self.timers['vertical move'].duration = self.down_speed

    def check_finished_rows(self):
        """Метод перевірки зібраного ряду"""

        # Отримання всього ігрового поля(індекс схема)
        delete_rows = []
        for i, row in enumerate(self.field_data):
            if all(row):
                delete_rows.append(i)

        if delete_rows:
            for delete_row in delete_rows:

                # Видалити зібраний ряд
                for block in self.field_data[delete_row]:
                    block.kill()

                # Перемістити блоки вниз
                for row in self.field_data:
                    for block in row:
                        if block and block.pos.y < delete_row:
                            block.pos.y += 1

            # Перебудова ігрового поля
            self.field_data = [[0 for x in range(COLUMNS)] for y in range(ROWS)]
            for block in self.sprites:
                self.field_data[int(block.pos.y)][int(block.pos.x)] = block

            # Оновлення очок
            self.calculate_score(len(delete_rows))

    def run(self):
        """Метод запуску кроку"""

        # Оновлення
        self.input()
        self.timer_update()
        self.sprites.update()

        # Відображення
        self.surface.fill(GRAY)
        self.sprites.draw(self.surface)

        self.draw_grid()
        self.display_surface.blit(self.surface, (PADDING, PADDING))
        pygame.draw.rect(self.display_surface, LINE_COLOR, self.rect, 2, 2)


class Tetromino:
    """Класс Tetromino"""
    def __init__(self, shape, group, create_new_tetromino, field_data):

        # Налаштування
        self.shape = shape
        self.block_position = TETROMINOS[shape]['shape']
        self.color = TETROMINOS[shape]['color']
        self.create_new_tetromino = create_new_tetromino
        self.field_data = field_data

        # Створення блоку фігурки
        self.blocks = [Block(group, pos, self.color) for pos in self.block_position]

    # Зіткнення фігурки
    def next_move_horizontal_collide(self, _blocks, amount):
        """Метод формування координат зіткнень"""
        collision_list = [
            block.horizontal_collide(int(block.pos.x + amount), self.field_data)
            for block in self.blocks
        ]
        return True if any(collision_list) else False

    def next_move_vertical_collide(self, _blocks, amount):
        """Метод формування координат зіткнень"""
        collision_list = [block.vertical_collide(int(block.pos.y + amount), self.field_data) for block in self.blocks]
        return True if any(collision_list) else False

    # Рух фігурки
    def move_horizontal(self, amount):
        """Метод горизонтального руху"""
        if not self.next_move_horizontal_collide(self.blocks, amount):
            for block in self.blocks:
                block.pos.x += amount

    def move_down(self):
        """Метод вертикального руху"""
        if not self.next_move_vertical_collide(self.blocks, 1):
            for block in self.blocks:
                block.pos.y += 1
        else:
            for block in self.blocks:
                self.field_data[int(block.pos.y)][int(block.pos.x)] = block
            self.create_new_tetromino()

    # Перевертання фігурки
    def rotate(self):
        """Метод перевертання фігурки"""
        if self.shape != 'O':

            #1. Точка повороту
            pivot_pos = self.blocks[0].pos

            #2. Нові позиції блоків
            new_block_positions = [block.rotate(pivot_pos) for block in self.blocks]

            #3. Перевірка зіткнення
            for pos in new_block_positions:

                # Горизонтально
                if pos.x < 0 or pos.x >= COLUMNS:
                    return

                # Перевірка поля -> зіткнення з іншими частинами
                if self.field_data[int(pos.y)][int(pos.x)]:
                    return

                # Вертикально / дно поля перевірка
                if pos.y > ROWS:
                    return

            #4. застосування нових позицій
            for i, block in enumerate(self.blocks):
                block.pos = new_block_positions[i]


class Block(pygame.sprite.Sprite):
    """Класс Block"""
    def __init__(self, group, pos, color):

        # Загальні
        super().__init__(group)
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill(color)

        # Позиція
        self.pos = pygame.Vector2(pos) + BLOCK_OFFSET
        self.rect = self.image.get_rect(topleft = self.pos * CELL_SIZE)

    def rotate(self, pivot_pos):
        """Метод обертання фігурки"""
        return pivot_pos + (self.pos - pivot_pos).rotate(90)

    def horizontal_collide(self, x, field_data):
        """Метод горизонтального зіткнення з краєм поля"""
        if not 0 <= x < COLUMNS:
            return True

        if field_data[int(self.pos.y)][x]:
            return True

    def vertical_collide(self, y, field_data):
        """Метод вертикального зіткнення з краєм поля"""
        if y >= ROWS:
            return True

        if y >= 0 and field_data[y][int(self.pos.x)]:
            return True

    def update(self):
        """Update block rect position"""
        self.rect.topleft = self.pos * CELL_SIZE
