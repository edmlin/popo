import pygame as pg
import math
import random
import time


class Color:
    colors = [pg.Color('red'), pg.Color('green'), pg.Color('blue'), pg.Color('yellow'), pg.Color('orange'),
              pg.Color('cyan'), pg.Color('pink'), pg.Color('violet')]

    def get_color(self):
        return random.choice(Color.colors)

class Ball:
    radius = 20
    light_pos = (0.4, 0.4)
    initial_speed=1

    def __init__(self, board, angle, color):
        self.speed = Ball.initial_speed
        self.board = board
        self.x, self.y = (board.left+board.width / 2, board.height)
        self.color = color
        self.angle = angle
        self.may_drop = False
        self.hanging = False
        self.surf = None
        self.create_surf()
        self.row, self.col = -100, -100
        self.last_move=time.time()

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
        now=time.time()
        self.x -= math.cos(self.angle) * self.speed *(now-self.last_move)*1000
        self.y -= math.sin(self.angle) * self.speed *(now-self.last_move)*1000
        self.last_move=now
        if (self.x <= self.board.left+self.radius) or (self.x + self.radius >= self.board.left+self.board.width):
            self.angle = math.pi - self.angle
        if self in self.board.balls and (self.y<=self.board.top+self.radius or self.hit_ball(self.board.balls)):
            self.speed=0
            self.x, self.y, self.row, self.col = self.board.closest(self.x, self.y)
            self.board.ball_stopped(self)
        if self.y>=self.board.height and self in self.board.dropping_balls:
            self.board.dropping_balls.remove(self)

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
            if ball.speed==0 and self != ball:
                if math.sqrt((self.x - ball.x) ** 2 + (self.y - ball.y) ** 2) <= self.radius * 2:
                    return ball
        return None

class Board:
    width = Ball.radius*12*2+1
    height = 600

    def __init__(self, screen,left=0):
        self.gun = Gun(self)
        self.balls = []
        self.dropping_balls = []
        self.screen = screen
        self.next_color = Color().get_color()
        self.next_next_color = Color().get_color()
        self.left=left
        self.top = 0
        self.ball_positions = []
        self.move_delay = 3
        self.last_move = time.time()
        self.generate_ball_positions()
        self.left_key=self.right_key=self.fine_left_key=self.fine_right_key=self.shoot_key=self.assistant_key=None
        self.opponent=None

    def generate_ball_positions(self):
        self.ball_positions = []
        x = self.left+Ball.radius
        y = Ball.radius + self.top
        row, column = 0, 0
        while y <= self.height - Ball.radius:
            self.ball_positions.append([])
            while x <= self.left+self.width - Ball.radius:
                self.ball_positions[row].append((x, y))
                x += Ball.radius * 2
            row += 1
            if row % 2 == 0:
                x = self.left+Ball.radius
            else:
                x = self.left+Ball.radius * 2
            y += math.sqrt(3) * Ball.radius
            y = round(y)

    def mouse_move(self, x, y):
        if not pg.Rect(self.left,self.top,self.width,self.height).collidepoint(x,y):
            return
        if x == self.left+self.width / 2:
            self.gun.angle = math.pi / 2
        else:
            self.gun.angle = math.atan((self.height - y) / (self.left+self.width / 2 - x))
            if self.gun.angle < 0:
                self.gun.angle += math.pi
        self.draw()

    def mouse_down(self, x, y):
        if not pg.Rect(self.left,self.top,self.width,self.height).collidepoint(x,y):
            return
        if x == self.left+self.width / 2:
            self.gun.angle = math.pi / 2
        else:
            self.gun.angle = math.atan((self.height - y) / (self.left+self.width / 2 - x))
            if self.gun.angle < 0:
                self.gun.angle += math.pi
        self.shoot()

    def shoot(self):
        ball = Ball(self, angle=self.gun.angle, color=self.next_color)
        self.balls.append(ball)
        self.next_color=self.next_next_color
        self.next_next_color = Color().get_color()

    def ball_stopped(self,ball):
        for b in self.balls:
            b.may_drop = False
            b.hanging = False
        self.mark_drop(ball)
        self.drop()

    def process(self):
        for ball in self.balls:
            if ball.speed!=0:
                ball.move()
        for ball in self.dropping_balls:
            if ball.speed!=0:
                ball.move()
        self.gun.turn()
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
        pg.draw.rect(self.screen,(255, 255, 255),pg.Rect(self.left-1,0,self.width+2,self.height),0)
        pg.draw.rect(self.screen,(0,0,0),pg.Rect(self.left-1,0,self.width+2,self.height),1)
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
                    self.drop_ball(ball)
            for ball in self.get_balls_by_row(0):
                self.mark_hang(ball)
            for ball in self.balls[:]:
                if (not ball.hanging) and (ball.speed==0):
                    total_drop+=1
                    self.drop_ball(ball)
            self.opponent.add_random_balls(total_drop)

    def drop_ball(self,ball):
        self.balls.remove(ball)
        ball.angle = -math.pi / 2
        ball.speed = Ball.initial_speed
        ball.last_move=time.time()
        self.dropping_balls.append(ball)

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

    def key_down(self,event):
        if event.key==self.assistant_key:
            self.gun.assistance=True
        if event.key == self.left_key:
            self.gun.turning_left=True
        if event.key == self.fine_left_key:
            self.gun.turning_left_fine=True
        if event.key == self.right_key:
            self.gun.turning_right=True
        if event.key == self.fine_right_key:
            self.gun.turning_right_fine=True
        if event.key == self.shoot_key:
            self.shoot()

    def key_up(self,event):
        if event.key==self.assistant_key:
            self.gun.assistance=False
        if event.key == self.left_key:
            self.gun.turning_left=False
        if event.key == self.fine_left_key:
            self.gun.turning_left_fine=False
        if event.key == self.right_key:
            self.gun.turning_right=False
        if event.key == self.fine_right_key:
            self.gun.turning_right_fine=False

    def add_random_balls(self,number):
        number=min(number,self.width//(Ball.radius*2))
        pos=list(range(self.width//(Ball.radius*2)))
        random.shuffle(pos)
        pos=pos[:number]
        for i in pos:
            ball = Ball(self, angle=math.pi/2, color=Color().get_color())
            ball.x=self.left+i*Ball.radius*2+Ball.radius
            ball.y=self.height
            self.balls.append(ball)

class Gun:
    length = 60

    def __init__(self, board):
        self.board = board
        self.angle = math.pi / 2
        self.angle_turned=0
        self.assistance=False
        self.turning_left=self.turning_right=self.turning_left_fine=self.turning_right_fine=False
        self.turning_speed=math.pi/5
        self.turning_fine_speed=math.pi/20
        self.last_turned=time.time()

    def turn(self):
        now=time.time()
        if self.turning_left:
            self.angle_turned = - self.turning_speed * (now-self.last_turned)
        elif self.turning_right:
            self.angle_turned = self.turning_speed * (now - self.last_turned)
        elif self.turning_left_fine:
            self.angle_turned = - self.turning_fine_speed * (now-self.last_turned)
        elif self.turning_right_fine:
            self.angle_turned = self.turning_fine_speed * (now - self.last_turned)
        else:
            self.angle_turned=0
        if (self.angle>0 and self.angle_turned<0) or (self.angle<math.pi and self.angle_turned>0):
            self.angle+=self.angle_turned
        self.last_turned=now

    def draw(self):
        radius=10
        if self.assistance:
            if self.angle==math.pi/2:
                y=0
                x=self.board.left+self.board.width/2
            elif math.atan(self.board.height/(self.board.width/2))<self.angle<math.pi-math.atan(self.board.height/(self.board.width/2)):
                y=0
                x=self.board.left+self.board.width/2-self.board.height/math.tan(self.angle)
            elif self.angle<math.atan(self.board.height/(self.board.width/2)):
                x=self.board.left
                y=self.board.height-self.board.width/2*math.tan(self.angle)
            else:
                x=self.board.left+self.board.width
                y = self.board.height- self.board.width / 2 * math.tan(math.pi-self.angle)
            pg.draw.line(self.board.screen, (200,200,200), (self.board.left + self.board.width / 2, self.board.height),
                         (x,y))
            pg.draw.line(self.board.screen, (0, 0, 0), (self.board.left + self.board.width / 2, self.board.height),
                         (self.board.left + self.board.width / 2 - self.length * math.cos(self.angle),
                          self.board.height - self.length * math.sin(self.angle)))
        pg.draw.line(self.board.screen, (0, 0, 0), (self.board.left+self.board.width / 2, self.board.height),
                     (self.board.left+self.board.width / 2 - self.length * math.cos(self.angle),
                      self.board.height - self.length * math.sin(self.angle)))
        c1=( int(self.board.left+self.board.width/2-math.cos(self.angle)*radius*3),
             int(self.board.height-math.sin(self.angle)*radius*3) )
        c2 = (int(self.board.left+self.board.width / 2 - math.cos(self.angle) * radius),
              int(self.board.height - math.sin(self.angle) * radius))
        pg.draw.circle(self.board.screen, self.board.next_color, c1, radius, 0)
        pg.draw.circle(self.board.screen, (0, 0, 0), c1, radius, 1)
        pg.draw.circle(self.board.screen, self.board.next_next_color, c2, radius, 0)
        pg.draw.circle(self.board.screen, (0, 0, 0), c2, radius, 1)


class Game:
    def run(self):
        pg.init()
        screen = pg.display.set_mode(((Board.width+2)*2, Board.height))
        board = Board(screen,1)
        board2=Board(screen,Board.width+3)
        board.opponent=board2
        board2.opponent=board

        board.screen = screen
        board.draw()
        board2.screen=screen
        board.assistant_key=pg.K_SPACE
        board.left_key=pg.K_a
        board.right_key=pg.K_d
        board.fine_left_key=pg.K_q
        board.fine_right_key=pg.K_e
        board.shoot_key=pg.K_w

        board2.left_key=pg.K_KP1
        board2.right_key=pg.K_KP3
        board2.fine_left_key=pg.K_KP4
        board2.fine_right_key=pg.K_KP6
        board2.shoot_key=pg.K_KP5
        board2.assistant_key=pg.K_KP0
        board2.draw()
        running = True

        while running:
            #board.move()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.MOUSEMOTION:
                    (x, y) = event.pos
                    board.mouse_move(x, y)
                    board2.mouse_move(x, y)
                if event.type == pg.MOUSEBUTTONDOWN:
                    (x, y) = event.pos
                    board.mouse_down(x, y)
                    board2.mouse_down(x, y)
                if event.type==pg.KEYDOWN:
                    print(pg.key.name(event.key))
                    board.key_down(event)
                    board2.key_down(event)
                if event.type == pg.KEYUP:
                    board.key_up(event)
                    board2.key_up(event)
            board.process()
            board2.process()
        pg.quit()

Game().run()
