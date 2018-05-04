import pygame as pg
import math
import random
import time


class Color:
    colors = [pg.Color('red'), pg.Color('green'), pg.Color('blue'), pg.Color('yellow'), pg.Color('orange'),
              pg.Color('cyan'), pg.Color('pink'), pg.Color('violet')]

    def get_color(self):
        return random.choice(Color.colors)


class Board:
    width = 300
    height = 600

    def __init__(self, screen):
        self.gun = Gun(self)
        self.balls = []
        self.dropping_balls = []
        self.screen = screen
        self.next_color = Color().get_color()
        self.top = 0
        self.ball_positions = []
        self.move_delay = 3
        self.last_move = time.time()
        self.generate_ball_positions()

    def generate_ball_positions(self):
        self.ball_positions = []
        x = Ball.radius
        y = Ball.radius + self.top
        row, column = 0, 0
        while y <= self.height - Ball.radius:
            self.ball_positions.append([])
            while x < self.width - Ball.radius:
                self.ball_positions[row].append((x, y))
                x += Ball.radius * 2
            row += 1
            if row % 2 == 0:
                x = Ball.radius
            else:
                x = Ball.radius * 2
            y += math.sqrt(3) * Ball.radius
            y = round(y)

    def mouse_move(self, x, y):
        if x == self.width / 2:
            self.gun.angle = math.pi / 2
        else:
            self.gun.angle = math.atan((self.height - y) / (self.width / 2 - x))
            if self.gun.angle < 0:
                self.gun.angle += math.pi
        self.draw()

    def mouse_down(self, x, y):
        if x == self.width / 2:
            self.gun.angle = math.pi / 2
        else:
            self.gun.angle = math.atan((self.height - y) / (self.width / 2 - x))
            if self.gun.angle < 0:
                self.gun.angle += math.pi
        ball = Ball(self, angle=self.gun.angle, color=self.next_color)
        self.balls.append(ball)
        self.next_color = Color().get_color()
        while True:
            ball.move()
            self.draw()
            if ball.hit_wall():
                break
            if ball.hit_ball(self.balls):
                break
        ball.x, ball.y, ball.row, ball.col = self.closest(ball.x, ball.y)
        self.draw()
        for b in self.balls:
            b.may_drop = False
            b.hanging = False
        self.mark_drop(ball)
        self.drop()
        self.draw()

    def closest(self, x, y):
        dis = 100
        new_x, new_y = x, y
        new_row, new_col = 0, 0
        for row in self.ball_positions:
            for col in row:
                new_dis = math.sqrt((x - col[0]) ** 2 + (y - col[1]) ** 2)
                if new_dis < dis:
                    new_x, new_y = col
                    dis = new_dis
                    new_row, new_col = self.ball_positions.index(row), row.index(col)
        return new_x, new_y, new_row, new_col

    def draw(self):
        self.screen.fill((255, 255, 255))
        self.gun.draw()

        for row in self.ball_positions:
            for col in row:
                pg.draw.circle(self.screen, (0, 0, 0), col, 1, 1)

        for ball in self.balls:
            ball.draw()
        for ball in self.dropping_balls:
            ball.draw()
        pg.display.flip()

    def get_ball_by_pos(self, row, col):
        if row < 0 or col < 0:
            return None
        for ball in self.balls:
            if ball.row == row and ball.col == col:
                return ball
        return None

    def get_balls_by_row(self, row):
        result = []
        for ball in self.balls:
            if ball.row == row:
                result.append(ball)
        return result

    def get_touching_balls(self, ball):
        result = [
            self.get_ball_by_pos(ball.row, ball.col - 1),
            self.get_ball_by_pos(ball.row, ball.col + 1),
            self.get_ball_by_pos(ball.row - 1, ball.col),
            self.get_ball_by_pos(ball.row + 1, ball.col)
        ]
        if ball.row % 2 == 0:
            result.append(self.get_ball_by_pos(ball.row - 1, ball.col - 1))
            result.append(self.get_ball_by_pos(ball.row + 1, ball.col - 1))
        else:
            result.append(self.get_ball_by_pos(ball.row - 1, ball.col + 1))
            result.append(self.get_ball_by_pos(ball.row + 1, ball.col + 1))
        while None in result:
            result.remove(None)
        return result

    def mark_drop(self, ball):
        ball.may_drop = True
        for b in self.get_touching_balls(ball):
            if b.color == ball.color and not b.may_drop:
                b.may_drop = True
                self.mark_drop(b)

    def check_attached(self, ball):
        if ball.row == 0:
            return True
        for b in self.get_touching_balls(ball):
            if self.check_attached(b):
                return True
        return False

    def drop(self):
        total_drop = 0
        for ball in self.balls:
            if ball.may_drop:
                total_drop += 1
        if total_drop >= 3:
            for ball in self.balls[:]:
                if ball.may_drop:
                    self.balls.remove(ball)
                    ball.angle = -math.pi / 2
                    self.dropping_balls.append(ball)
            for ball in self.get_balls_by_row(0):
                self.mark_hang(ball)
            for ball in self.balls[:]:
                if not ball.hanging:
                    self.balls.remove(ball)
                    ball.angle = -math.pi / 2
                    self.dropping_balls.append(ball)
            while len(self.dropping_balls) > 0:
                for ball in self.dropping_balls[:]:
                    ball.move()
                    if ball.y >= self.height:
                        self.dropping_balls.remove(ball)
                self.draw()

    def mark_hang(self, ball):
        if ball.row == 0:
            ball.hanging = True
        if ball.hanging:
            for b in self.get_touching_balls(ball):
                if not b.hanging:
                    b.hanging = True
                    self.mark_hang(b)

    def move(self):
        if time.time() - self.last_move > self.move_delay:
            self.last_move = time.time()
            delta = Ball.radius // 2
            self.top += delta
            for ball in self.balls:
                ball.y += delta
            self.generate_ball_positions()
            self.draw()


class Ball:
    radius = 20
    light_pos = (0.4, 0.4)

    def __init__(self, board, angle, color):
        self.speed = 0.6
        self.board = board
        self.x, self.y = (board.width / 2, board.height)
        self.color = color
        self.angle = angle
        self.may_drop = False
        self.hanging = False
        self.surf = None
        self.create_surf()
        self.row, self.col = 0, 0

    def create_surf(self):
        x0 = self.radius
        y0 = self.radius
        x1 = x0 + int(self.light_pos[0] * self.radius)
        y1 = y0 + int(self.light_pos[1] * self.radius)

        transparent = pg.Color('white')
        self.surf = pg.surface.Surface((x0 * 2 + 1, y0 * 2 + 1))
        self.surf.fill(transparent)
        self.surf.set_colorkey(transparent)

        for i in range(x0 * 2 + 1):
            for j in range(y0 * 2 + 1):
                d = ((i - x0) ** 2 + (j - y0) ** 2) ** 0.5
                if d > self.radius + 1:
                    continue
                else:
                    # rate of color intensity change
                    d2 = min(1, ((i - x1) ** 2 + (j - y1) ** 2) ** 0.5 / self.radius)

                    # apply color
                    color = [255 - (255 - x) * d2 for x in self.color]

                    if d > self.radius:  # anti-alising
                        alfa = d - self.radius
                        bg = pg.Color('white')
                        color = [c * (1 - alfa) + b * alfa for c, b in zip(color, bg)]

                    self.surf.set_at((i, j), color)

    def move(self):
        self.x -= math.cos(self.angle) * self.speed
        self.y -= math.sin(self.angle) * self.speed

    def draw(self):
        # pg.draw.circle(self.board.screen, tuple(color), (round(self.x), round(self.y)), self.radius,0)
        self.board.screen.blit(self.surf, (int(self.x - self.radius), int(self.y - self.radius)))
        # pg.draw.circle(self.board.screen, (0, 0, 0), (round(self.x), round(self.y)), self.radius, 1)

    def hit_wall(self):
        if (self.x <= self.radius) or (self.x + self.radius >= self.board.width):
            self.angle = math.pi - self.angle
        return self.y <= self.board.top + self.radius

    def hit_ball(self, balls):
        for ball in balls:
            if self != ball:
                if math.sqrt((self.x - ball.x) ** 2 + (self.y - ball.y) ** 2) <= self.radius * 2:
                    return ball
        return None


class Gun:
    length = 50

    def __init__(self, board):
        self.board = board
        self.angle = math.pi / 2

    def draw(self):
        pg.draw.line(self.board.screen, (0, 0, 0), (self.board.width / 2, self.board.height),
                     (self.board.width / 2 - self.length * math.cos(self.angle),
                      self.board.height - self.length * math.sin(self.angle)))
        pg.draw.circle(self.board.screen, self.board.next_color, (self.board.width // 2, self.board.height), 10, 0)
        pg.draw.circle(self.board.screen, (0, 0, 0), (self.board.width // 2, self.board.height), 10, 1)


class Game:
    def run(self):
        pg.init()
        screen = pg.display.set_mode((Board.width, Board.height))
        board = Board(screen)
        board.screen = screen
        board.draw()
        running = True
        while running:
            board.move()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.MOUSEMOTION:
                    (x, y) = event.pos
                    board.mouse_move(x, y)
                if event.type == pg.MOUSEBUTTONDOWN:
                    (x, y) = event.pos
                    board.mouse_down(x, y)
        pg.quit()

Game().run()
