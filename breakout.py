#!/usr/bin/env python

import sys, pygame, random, time, math, glob
assert sys.version_info >= (3,4), 'This script requires at least Python 3.4'


NORTH = math.pi
NORTHEAST = 5/4*math.pi
EAST = 3/2*math.pi
SOUTHEAST = 7/4*math.pi
SOUTH = 0.0
SOUTHWEST = math.pi/4
WEST = math.pi/2
NORTHWEST = 3/4*math.pi


def addVectors(vect1, vect2):
	""" Returns the sum of two vectors """
	(angle1, length1) = vect1
	(angle2, length2) = vect2
	x  = math.sin(angle1) * length1 + math.sin(angle2) * length2
	y  = math.cos(angle1) * length1 + math.cos(angle2) * length2
	
	angle  = 0.5 * math.pi - math.atan2(y, x)
	length = math.hypot(x, y)

	return (angle, length)

class Game:
	def __init__(self, font, color, points_position, lives_position):
		self.font = font
		self.color = color
		self.points_position = points_position
		self.lives_position = lives_position
		
	def draw_points(self,screen,points):
		points = str(points)
		f = self.font.render(points,True,self.color)
		screen.blit(f,points_position)

	def draw_lives(self,screen,lives):
		lives = str(lives)
		f = self.font.render(lives,True,self.color)
		screen.blit(f,lives_position)


class Ball(pygame.sprite.Sprite):
	def __init__(self,size,position,vector,max_speed,elasticity,color,constraints):
		pygame.sprite.Sprite.__init__(self)
		self.size = size
		(self.angle,self.speed) = self.vector = vector
		self.init_vector = vector
		self.color = color
		self.constraints = constraints
		self.elasticity = elasticity
		self.image = pygame.Surface((size*2, size*2))
		self.image.fill((0, 0, 0))
		pygame.draw.circle(self.image, color, (size,size), size)
		self.image.set_colorkey((0,0,0))
		self.rect = self.image.get_rect()
		self.init_position = position
		(self.x, self.y) = position
		self.rect.x = int(self.x)
		self.rect.y = int(self.y)
		self.max_speed = max_speed
		self.min_speed = self.speed
		self.dying = False
		self.dead = False

	def update(self,paddles,blocks):
		if self.dying:
			self.dead = True
			return
		for s in range(0,int(self.speed)):
			self.bounce_off_wall()
			for paddle in paddles:
				if pygame.sprite.collide_rect(self,paddle):
					self.bounce_off_paddle(paddle)
			for block in blocks:
				if pygame.sprite.collide_rect(self,block):
					self.bounce_off_block(block)
					block.dying = True
			self.check_max_speed()
			(self.x,self.y) = self.get_next_pos()
			self.rect.x = int(self.x)
			self.rect.y = int(self.y)

	def check_max_speed(self):
		(self.angle,self.speed) = self.vector
		if self.speed > self.max_speed:
			self.speed = self.max_speed
		if self.speed < self.min_speed:
			self.speed = self.min_speed
		while self.angle < 0:
			self.angle += 2*math.pi
		while self.angle > 2*math.pi:
			self.angle -= 2*math.pi

		# try to keep the angle close to multiples of 45 degrees
		if self.angle < math.pi/4:
			self.angle += math.pi/float(random.randrange(6,12))
		elif self.angle > math.pi/4 and self.angle <= math.pi/2:
			self.angle -= math.pi/float(random.randrange(6,12))
		elif self.angle > math.pi/2 and self.angle < 3/4*math.pi:
			self.angle += math.pi/float(random.randrange(6,12))
		elif self.angle > 3/4*math.pi and self.angle <= math.pi:
			self.angle -= math.pi/float(random.randrange(6,12))
		elif self.angle > math.pi and self.angle < 5/4*math.pi:
			self.angle += math.pi/float(random.randrange(6,12))
		elif self.angle > 5/4*math.pi and self.angle <= 3/2*math.pi:
			self.angle -= math.pi/float(random.randrange(6,12))
		elif self.angle > 3/2*math.pi and self.angle < 7/4*math.pi:
			self.angle += math.pi/float(random.randrange(6,12))
		elif self.angle > 7/4*math.pi and self.angle <= 2*math.pi:
			self.angle -= math.pi/float(random.randrange(6,12))
		self.vector = (self.angle,self.speed)
		

	def get_next_pos(self):
		x = self.x + math.sin(self.angle)
		y = self.y + math.cos(self.angle)
		return (x,y)
			
	def bounce_off_wall(self):
		(width,height) = self.constraints
		wall_speed = self.speed*2*self.elasticity
		direction = -1
		if self.rect.right >= width:
			direction = EAST
			self.rect.right = width-1
		elif self.rect.left <= 0:
			direction = WEST
			self.rect.left = 1
		if self.rect.top <= 0:
			direction = SOUTH
			self.rect.top = 1
		elif self.rect.bottom >= height:
			direction = NORTH
			self.rect.bottom = height-1
			self.dying = True
		if direction >= 0:
			self.vector = addVectors(self.vector,(direction,wall_speed))
			(self.angle,self.speed) = self.vector

	def bounce_off_paddle(self,paddle):
		paddle_speed = self.speed*2
		direction = NORTH
		if self.rect.right == paddle.rect.left and self.rect.bottom == paddle.rect.top:
			direction = NORTHWEST
		elif self.rect.left == paddle.rect.right and self.rect.bottom == paddle.rect.top:
			direction = NORTHEAST
		elif self.rect.left == paddle.rect.right and self.rect.top == paddle.rect.bottom:
			direction = SOUTHEAST
		elif self.rect.right == paddle.rect.left and self.rect.top == paddle.rect.bottom:
			direction = SOUTHWEST
		if self.rect.bottom <= paddle.rect.centery:
			direction = NORTH
		elif self.rect.top > paddle.rect.centery:
			direction = SOUTH
		elif self.rect.left > paddle.rect.centerx:
			direction = WEST
		elif self.rect.right < paddle.rect.centerx:
			direction = EAST
		else:
			direction = NORTH
		self.vector = addVectors(self.vector,(direction,paddle_speed))
		(self.angle,self.speed) = self.vector

	def bounce_off_block(self,block):
		block_speed = self.speed*2
		#corners first
		if self.rect.right == block.rect.left and self.rect.bottom == block.rect.top:
			direction = NORTHWEST
		elif self.rect.left == block.rect.right and self.rect.bottom == block.rect.top:
			direction = NORTHEAST
		elif self.rect.left == block.rect.right and self.rect.top == block.rect.bottom:
			direction = SOUTHEAST
		elif self.rect.right == block.rect.left and self.rect.top == block.rect.bottom:
			direction = SOUTHWEST
		if self.rect.bottom <= block.rect.centery:
			direction = NORTH
		elif self.rect.top > block.rect.centery:
			direction = SOUTH
		elif self.rect.left > block.rect.centerx:
			direction = EAST
		elif self.rect.right < block.rect.centerx:
			direction = WEST
		else:
			direction = SOUTH
		self.vector = addVectors(self.vector,(direction,block_speed))
		(self.angle,self.speed) = self.vector

	def set_forces(self,gravity):
		self.gravity = gravity

	def reset(self):
		(self.angle,self.speed) = self.vector = self.init_vector
		(self.x,self.y) = self.position = self.init_position
		self.rect.x = int(self.x)
		self.rect.y = int(self.y)
		self.dying = False
		self.dead = False

	def draw(self,screen):	
		screen.blit(self.image, (self.rect.x, self.rect.y))
	
class Paddle(pygame.sprite.Sprite):
	def __init__(self,size,position,max_speed,color,constraints):
		pygame.sprite.Sprite.__init__(self)
		self.color = color
		self.constraints = constraints
		self.vector = (0.0,0)
		(self.w, self.h) = size
		self.image = pygame.Surface((self.w, self.h))
		self.image.fill(color)
		self.rect = self.image.get_rect()
		(x, y) = position
		self.rect.x = x
		self.rect.y = y
		self.max_speed = max_speed

	def update(self,position):
		(x,y) = position
		(width,height) = self.constraints
		if x + self.w > width:
			x = width - self.w
		self.position = (x,self.rect.y)
		self.rect.x = x
		self.rect.y = self.rect.y	

	def set_forces(self,gravity):
		self.gravity = gravity

	def draw(self,screen):	
		screen.blit(self.image, (self.rect.x, self.rect.y))

class Block(pygame.sprite.Sprite):
	def __init__(self,size,points,color):
		pygame.sprite.Sprite.__init__(self)
		
		self.color = color
		(self.w, self.h) = size
		self.image = pygame.Surface((self.w, self.h))
		self.image.fill(color)
		self.rect = self.image.get_rect()
		self.rect.x = 0
		self.rect.y = -100
		self.points = points
		self.dying = False
		self.dead = False
	
	def move_to(self,origin,size,margin,col,row):
		(o_x,o_y) = origin
		(w,h) = size
		(x,y) = (o_x+col*(w+margin),o_y+row*(h+margin))
		self.rect.x = x
		self.rect.y = y

	def set_forces(self,gravity):
		self.gravity = gravity
	
	def update(self):
		if self.dying:
			self.dead = True
	
	def draw(self,screen):	
		screen.blit(self.image, (self.rect.x, self.rect.y))



screen_size = (800,768)
FPS = 30
points_position = (10,10)
lives_position = (750,10)
display_color = (100,65,150)

paddle_pos = (0,700)
paddle_size = (80,15)
paddle_color = (100,65,150)
paddle_max_speed = 60

num_blocks = 10
num_block_rows = 4
block_pos = (50,50)
block_size = (65,15)
block_margin = 4
block_points = 10
block_color = (255,25,25)

ball_pos = (200,300)
ball_size = 10
ball_elasticity = 1
ball_color = (255,255,255)
ball_initial_vector = (7/4*math.pi, 15.0)
ball_max_speed = 30.0

gravity = (math.pi,9.8)

def main():
	pygame.init()
	font = pygame.font.SysFont("arial",30)
	screen = pygame.display.set_mode(screen_size)
	game = Game(font,display_color,points_position,lives_position)
	clock = pygame.time.Clock()
	lives = 5
	points = 0
	balls = pygame.sprite.Group()
	paddles = pygame.sprite.Group()
	blocks = pygame.sprite.Group()
	pos = (0,0)

	(start_x,start_y) = block_pos
	(block_w,block_h) = block_size
	for r in range(0,num_block_rows):
		for b in range(0,num_blocks):
			points = block_points*(r+1)
			block = Block(block_size,points,block_color)
			block.move_to(block_pos,block_size,block_margin,b,r)
			blocks.add(block)
	balls.add(Ball(ball_size,ball_pos,ball_initial_vector,ball_max_speed,ball_elasticity,ball_color,screen_size))
	paddles.add(Paddle(paddle_size,paddle_pos,paddle_max_speed,paddle_color,screen_size))
	
	while lives >= 0 and len(blocks):
		clock.tick(FPS)
		screen.fill((0,0,0))
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit(0)
			if event.type == pygame.MOUSEMOTION:
				pos = pygame.mouse.get_pos()
			if event.type == pygame.MOUSEBUTTONUP:
				pos = pygame.mouse.get_pos()
			if event.type == pygame.MOUSEBUTTONDOWN:
				pos = pygame.mouse.get_pos()
			if event.type == pygame.KEYDOWN:
				keys = pygame.key.get_pressed()

		for ball in balls:
			ball.set_forces(gravity)
		balls.update(paddles,blocks)
		balls.draw(screen)

		for paddle in paddles:
			paddle.set_forces(gravity)
		paddles.update(pos)
		paddles.draw(screen)

		for block in blocks:
			block.set_forces(gravity)
		blocks.update()
		blocks.draw(screen)
		for block in blocks:
			if block.dead:
				points += block.points
				blocks.remove(block)
		for ball in balls:
			if ball.dead:
				lives -= 1
				ball.reset()

		game.draw_lives(screen,lives)
		game.draw_points(screen,points)
		pygame.display.flip()

if __name__ == '__main__':
	main()

