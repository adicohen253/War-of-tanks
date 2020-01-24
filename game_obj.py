import pygame
import random
import time

# general constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# war of tanks
IMG_PLY = "project images/tank_player.png"
BULLET = "project images/bullet.png"
SURPRISE = "project images/surprise.png"
EXPLODE = "1.png"


class Tank(pygame.sprite.Sprite):
	MOVES = [(3, 0), (2, -2), (0, -3), (-2, -2), (-3, 0), (-2, 2), (0, 3), (2, 2)]

	NUM_BULLETS = 10
	START_HEALTH = 30

	def __init__(self, rect, direct=0, new_color=RED):
		super(Tank, self).__init__()
		self.__image = pygame.image.load(IMG_PLY).convert()
		self.__image.set_colorkey(WHITE)
		self.rect = self.__image.get_rect()  # the location of the player
		self.__tank_direct = direct  # uses as direct of the tank
		self.rect.x, self.rect.y = rect
		self.__color = list(RED)
		self.change_player_color(list(new_color))  # set color header
		self.__original_image = self.__image  # original image uses to rotate the tank in every direct
		self.__image = pygame.transform.rotate(self.__original_image, direct * 45)

		self.__num_bullet = self.NUM_BULLETS  # the current number of bullets
		self.__health = self.START_HEALTH  # health of the player
		self.__need_pointing = True

		self.__last_time_of_shot = time.time()
		self.reload_time = time.time()  # time passes from the last reload
		self.__eternal_ammo_mode = False  # flag is tank has infinite ammo now, lasts for 6 seconds
		self.__eternal_ammo_time = None  # the moment it became to be with endless ammo
		# (when eternal ammo mode is of the time is none)
		self.__ghost_mode = False  # flag is tank in ghost mode, lasts for 5 seconds
		self.__is_stuck_in_ghost = False  # turn to true when ghost mode turn of and tank still in wall
		self.__ghost_time = None  # the moment it became to be ghost
		# (when ghost mode is of the time is none)

	def change_player_color(self, new_color):
		"""change the image of the player to the new color
		argument:
			new_color = type: list, the new color for the player (rgb format)
		"""
		for element in range(len(new_color)):
			new_color[element] = int(new_color[element])
		# if color is totally white, set_colorkey make to color disappear
		if new_color == list(WHITE):
			new_color[0] -= 1
		if new_color == list(BLACK):
			new_color[0] += 1
		for x in range(self.__image.get_size()[0]):
			for y in range(self.__image.get_size()[1]):
				if self.__image.get_at((x, y)) != BLACK and self.__image.get_at((x, y)) != WHITE:
					self.__image.set_at((x, y), new_color)
		self.__color = new_color

	def is_done_ghost(self):
		""""Checks if it's time to turn off ghost mode"""
		if self.__ghost_time is not None:
			if time.time() - self.__ghost_time >= 5:
				# print "ghost mode over"
				self.__ghost_time = None
				self.__ghost_mode = False
				self.__is_stuck_in_ghost = True

	def is_done_eternal_ammo(self):
		"""Checks if it's time to turn off eternal mode"""
		if self.__eternal_ammo_time is not None:
			if time.time() - self.__eternal_ammo_time >= 6:
				self.__num_bullet = self.NUM_BULLETS
				self.__eternal_ammo_time = None
				self.__eternal_ammo_mode = False

	def reload_ammo(self):
		"""taking care about load the ammo of the tank"""
		if time.time() - self.reload_time >= 10:
			flag = False
			if self.__num_bullet == 0:
				self.__num_bullet = self.NUM_BULLETS
				if self.__eternal_ammo_mode is False:
					flag = True
			self.reload_time = time.time()
			return flag
		return False

	def active_ghost_mode(self):
		self.__ghost_mode = True
		self.__ghost_time = time.time()  # start be ghost

	def active_eternal_ammo_mode(self):
		self.__eternal_ammo_mode = True
		self.__eternal_ammo_time = time.time()  # start use eternal ammo

	def set_enemy_pointer(self, point):
		"""update enemy point
		argument:
			point: type - int, the new enemy direct
		"""
		self.__tank_direct = point
		self.__image = pygame.transform.rotate(self.__original_image, point * 45)

	def update_enemy_loc(self, x, y):
		"""
		set a new location of the enemy
		argument:
			x - int, the horizontal axis
			y - int, the vertical axis
		"""
		self.rect.x = x
		self.rect.y = y

	def move_tank(self, walls):
		"""make the tank move forward
		:argument:
			walls: type- list of walls, every wall in the game
		"""
		if self.__ghost_mode:
			walls = walls[0:4]
		keys = pygame.key.get_pressed()
		if keys[pygame.K_UP] or keys[pygame.K_LEFT] or \
				keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
			if pygame.sprite.spritecollide(self, walls, False):
				self.rect.x -= self.MOVES[self.__tank_direct][0]
				self.rect.y -= self.MOVES[self.__tank_direct][1]
				return False
			self.__need_pointing = False
			if keys[pygame.K_RIGHT] and keys[pygame.K_UP]:
				self.__tank_direct = 1
			elif keys[pygame.K_LEFT] and keys[pygame.K_UP]:
				self.__tank_direct = 3
			elif keys[pygame.K_LEFT] and keys[pygame.K_DOWN]:
				self.__tank_direct = 5
			elif keys[pygame.K_RIGHT] and keys[pygame.K_DOWN]:
				self.__tank_direct = 7
			elif pygame.key.get_pressed()[pygame.K_RIGHT]:
				self.__tank_direct = 0
			elif pygame.key.get_pressed()[pygame.K_UP]:
				self.__tank_direct = 2
			elif pygame.key.get_pressed()[pygame.K_LEFT]:
				self.__tank_direct = 4
			elif pygame.key.get_pressed()[pygame.K_DOWN]:
				self.__tank_direct = 6
			self.__image = pygame.transform.rotate(self.__original_image, self.__tank_direct * 45)
			if not pygame.sprite.spritecollide(self, walls, False):
				self.__is_stuck_in_ghost = False
				self.update_loc()
				return False
			else:
				if self.__is_stuck_in_ghost:
					self.update_loc()
					return False
		return False

	def shoot_bullet(self, event, bullets, enemy_shoot_flag):
		"""add new bullets to the bullets in the battlefield, if there option to shoot
		argument:
			event: type- event (pygame class)
			bullets: type - list of bullet, all the bullets in the battlefield
		"""
		if event == pygame.K_f:
			if self.__eternal_ammo_mode is False:
				self.update_num_bullet()
			bullet = Bullet(self, enemy_shoot_flag)
			bullets.append(bullet)
			self.__last_time_of_shot = time.time()
			return True, bullet
		elif (event.key == pygame.K_SPACE) and (self.__num_bullet > 0):
			if time.time() - self.__last_time_of_shot >= 0.5:
				if self.__eternal_ammo_mode is False:
					self.update_num_bullet()
				bullet = Bullet(self, -1)
				bullets.append(bullet)
				self.__last_time_of_shot = time.time()
				return True, bullet
		return False, None

	def get_is_ghost_mode(self):
		return self.__ghost_mode

	def get_is_eternal_ammo_mode(self):
		return self.__eternal_ammo_mode

	def is_need_pointing(self):
		return self.__need_pointing

	def set_demo_tank_image(self, img):
		self.__image = img

	def get_color(self):
		return self.__color

	def get_health(self):
		return self.__health

	def heal_health(self):
		self.__health += 1

	def lost_health(self, injury):
		self.__health -= injury

	def get_num_bullet(self):
		return self.__num_bullet

	def update_num_bullet(self):
		self.__num_bullet -= 1

	def get_loc(self):
		return self.rect.x, self.rect.y

	def update_loc(self):
		"""move the tank in the current direct"""
		self.rect.x += self.MOVES[self.__tank_direct][0]
		self.rect.y += self.MOVES[self.__tank_direct][1]

	def get_image(self):
		return self.__image

	def get_pointer(self):
		return self.__tank_direct


class Wall(pygame.sprite.Sprite):
	def __init__(self, screen, start_pos, end_pose):
		super(Wall, self).__init__()
		self.__surface = screen
		self.__start_pos = start_pos
		self.__end_pos = end_pose
		self.width = 7  # constant width
		self.rect = self.draw_line()

	def get_start_pos(self):
		return self.__start_pos

	def get_end_pos(self):
		return self.__end_pos

	def draw_line(self):
		return pygame.draw.line(self.__surface, BLACK, self.__start_pos, self.__end_pos, self.width)


class Bullet(pygame.sprite.Sprite):
	RIGHT_SIGNAL = 1
	LEFT_SIGNAL = 2
	SHIFTING_DIRECT = {1: 3, 2: -3}
	BULLET_MOVES = [(4, 0, 30, 13), (3, -3, 33, -7), (0, -4, 12, -11), (-3, -3, -10, -9),
					(-4, 0, -11, 12), (-3, 3, 2, 27), (0, 4, 12, 30), (3, 3, 27, 24)]
	MAX_BULLET_HOPS = 6

	def __init__(self, tank, enemy_shoot=-1):  # get the tank's as shooter
		super(Bullet, self).__init__()
		self.__image = pygame.image.load(BULLET).convert()
		self.__image.set_colorkey(WHITE)
		if enemy_shoot == -1:
			self.__bullet_direct = tank.get_pointer()
		else:
			self.__bullet_direct = enemy_shoot
		self.rect = self.__image.get_rect()
		self.rect.x, self.rect.y = tank.get_loc()
		self.place_bullet()  # place the bullet in position in front of tank's canon
		self.ttl = self.MAX_BULLET_HOPS  # number of times that bullet can hit the walls

	def update_loc(self):
		"""update the location of the bullet"""
		self.rect.x += self.BULLET_MOVES[self.__bullet_direct][0]
		self.rect.y += self.BULLET_MOVES[self.__bullet_direct][1]

	def place_bullet(self):
		"""place the bullet in order to direct of the shooter tank"""
		self.rect.x += self.BULLET_MOVES[self.__bullet_direct][2]
		self.rect.y += self.BULLET_MOVES[self.__bullet_direct][3]

	def get_direct(self):
		return self.__bullet_direct

	def hit_wall(self):
		if self.__bullet_direct % 2 == 0:
			self.rect.x -= self.BULLET_MOVES[self.__bullet_direct][0] * 2
			self.rect.y -= self.BULLET_MOVES[self.__bullet_direct][1] * 2
			self.__bullet_direct += 4
			self.absolute_pointer()
		else:
			self.rect.x -= self.BULLET_MOVES[self.__bullet_direct][0]
			self.rect.y -= self.BULLET_MOVES[self.__bullet_direct][1]
			self.__bullet_direct += 2
			self.absolute_pointer()
			self.rect.x += self.BULLET_MOVES[self.__bullet_direct][0]
			self.rect.y += self.BULLET_MOVES[self.__bullet_direct][1]
		self.ttl -= 1

	def get_ttl(self):
		return self.ttl

	def absolute_pointer(self):
		"""consider the pointer for always point to legal index on BULLET MOVE"""
		if self.__bullet_direct >= len(self.BULLET_MOVES):
			self.__bullet_direct -= len(self.BULLET_MOVES)

	def get_loc(self):
		return self.rect.x, self.rect.y

	def get_image(self):
		return self.__image


class Trap(pygame.sprite.Sprite):
	def __init__(self, x, y, attr=None):
		super(Trap, self).__init__()
		self.__image = pygame.image.load(SURPRISE).convert()
		self.__image.set_colorkey(WHITE)
		self.rect = self.__image.get_rect()
		self.rect.x, self.rect.y = x, y
		if attr is None:
			#  create the surprise
			self.attribute = random.randint(1, 4)
		else:
			# get info about surprise from the main player
			self.attribute = attr

	def get_attribute(self):
		return self.attribute

	def get_loc(self):
		return self.rect.x, self.rect.y

	def get_image(self):
		return self.__image


class Spritesheet(object):
	def __init__(self, filename, rect, cols, rows, colorkey=None):
		self.sheet = pygame.image.load(filename).convert()
		self.images = self.load_strip(rect, cols, rows, colorkey)
		self.i = 0

	def image_at(self, rectangle, colorkey=None):
		"""Loads image from x,y,x+offset,y+offset"""
		rect = pygame.Rect(rectangle)
		image = pygame.Surface(rect.size).convert()
		image.blit(self.sheet, (0, 0), rect)
		if colorkey is not None:
			if colorkey is -1:
				colorkey = image.get_at((0, 0))
			image.set_colorkey(colorkey, pygame.RLEACCEL)
		return image

	# Load a whole bunch of images and return them as a list
	def images_at(self, rects, colorkey=None):
		return [self.image_at(rect, colorkey) for rect in rects]

	# Load a whole strip of images
	def load_strip(self, rect, cols, rows, colorkey=None):
		"""Loads a strip of images and returns them as a list"""
		tups = []
		for y in range(cols):
			for x in range(rows):
				tups.append((rect[0] + rect[2] * x, rect[1] + rect[3] * y, rect[2], rect[3]))
		# tups = [(rect[0] + rect[2] * x, rect[1], rect[2], rect[3]) for x in range(count)]
		return self.images_at(tups, colorkey)

	def next(self):
		if self.i >= len(self.images):
			return False
		image = self.images[self.i]
		self.i += 1
		return image


def main():
	pass


if __name__ == '__main__':
	main()
