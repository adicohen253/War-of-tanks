import pygame
import random
import time

# general colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# classes tank and wall used also in server-side in map builder program


class Tank(pygame.sprite.Sprite):
	"""The tank of the player during the match with other player,
	holds the data about the player during the match, such as health, ammo, location etc'
	"""
	MOVES = [(3, 0), (2, -2), (0, -3), (-2, -2),
		(-3, 0), (-2, 2), (0, 3), (2, 2)]  # the amount of pixel moving each direction
	NUM_BULLETS = 10
	START_HEALTH = 30
	DEFAULT_COLOR = (77, 120, 78)
	TANK_IMAGE = "wot images/Tank.png"  # tank image
	
	def __init__(self, rect, direction=0, new_color=DEFAULT_COLOR):
		super(Tank, self).__init__()
		self.__image = pygame.image.load(self.TANK_IMAGE)
		self.rect = self.__image.get_rect()
		self.rect.x, self.rect.y = rect  # the location of the tank
		self.__tank_direction = direction  # the direction of the tank
		self.__color = list(new_color)
		if new_color != self.DEFAULT_COLOR:
			self.change_player_color(new_color)  # paint the tank in the new color
		self.__original_image = self.__image  # original image uses to rotate the tank in every angle
		self.__image = pygame.transform.rotate(self.__original_image, direction * 45)

		self.__num_bullet = self.NUM_BULLETS  # the current number of bullets
		self.__health = self.START_HEALTH  # health of the player
		self.__need_pointing = True  # for let the player know who he is in the beginning

		self.__last_time_of_shot = time.time()  # last time player shot a bullet
		self.__reload_time = time.time()  # time passes from the last reload
		
		self.__infinity_ammo_mode = False  # flag is tank has infinite ammo now, lasts for 6 seconds
		self.__infinity_ammo_time = None  # the moment it became to be with endless ammo
		
		self.__ghost_mode = False  # flag is tank in ghost mode, lasts for 5 seconds
		self.__is_stuck_while_ghost = False  # turn to true when ghost mode turn off and tank still in wall
		self.__ghost_time = None  # the moment it became to be ghost

	def change_player_color(self, color):
		"""changes the image of the player to the new color and paints tank's image
		parameters:
			color: type list, the new color for the player (rgb format)
		"""
		if color == list(WHITE):
			color[0] -= 1
		if color == list(BLACK):
			color[0] += 1
		for x in range(self.__image.get_size()[0]):
			for y in range(self.__image.get_size()[1]):
				if self.__image.get_at((x, y))[:3] != BLACK and self.__image.get_at((x, y))[:3] != WHITE:
					self.__image.set_at((x, y), color)
		self.__color = color
	
	def active_ghost_mode(self):
		self.__ghost_mode = True
		self.__ghost_time = time.time()  # starts use ghost mode

	def is_done_ghost(self):
		""""Turns off the ghost mode if 6 seconds elapsed"""
		if self.__ghost_time is not None:
			if time.time() - self.__ghost_time >= 6:
				self.__ghost_time = None
				self.__ghost_mode = False
				self.__is_stuck_while_ghost = True
	
	def turn_of_ghost(self):
		"""Used only for server side (Map builder program)"""
		self.__ghost_time = None
		self.__ghost_mode = False
		self.__is_stuck_while_ghost = True
	
	def active_infinity_ammo(self):
		self.__infinity_ammo_mode = True
		self.__infinity_ammo_time = time.time()  # starts use infinity ammo mode

	def is_done_infinity_ammo(self):
		"""Turns off the infinity ammo if 6 seconds elapsed"""
		if self.__infinity_ammo_time is not None:
			if time.time() - self.__infinity_ammo_time >= 6:
				self.__num_bullet = self.NUM_BULLETS
				self.__infinity_ammo_time = None
				self.__infinity_ammo_mode = False

	def reload_ammo(self):
		"""loads the ammo of the tank if 10 seconds elapsed
		returns:
			boolean, if need to use loading sound"""
		if time.time() - self.__reload_time >= 10:
			flag = False
			if self.__num_bullet == 0:
				self.__num_bullet = self.NUM_BULLETS
				if self.__infinity_ammo_mode is False:
					flag = True
			self.__reload_time = time.time()
			return flag
		return False

	def update_direction(self, direction):
		self.__tank_direction = direction
		self.__image = pygame.transform.rotate(self.__original_image, direction * 45)

	def update_loc(self, x=None, y=None):
		"""updates to location of the tank on the screen
		if x and y or None moves the tank depending on the direction
		parameters:
			x: type int, the x coordinate
			y: type int, the y coordinate
		"""
		if x is None and y is None:
			self.rect.x += self.MOVES[self.__tank_direction][0]
			self.rect.y += self.MOVES[self.__tank_direction][1]
		else:
			self.rect.x = x
			self.rect.y = y

	def move_tank(self, walls):
		"""Controls the movements of the tank all over the compass rose (8 directions)
		:parameters:
			walls: type list, every wall of the map
		"""
		if self.__ghost_mode:
			walls = walls[0:4]  # only the frame of the screen
		keys = pygame.key.get_pressed()
		if keys[pygame.K_UP] or keys[pygame.K_LEFT] or \
				keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
			if pygame.sprite.spritecollide(self, walls, False) and not self.__is_stuck_while_ghost:
				# if got into the wall when ghost mode is off
				self.rect.x -= self.MOVES[self.__tank_direction][0]
				self.rect.y -= self.MOVES[self.__tank_direction][1]
				return
			self.__need_pointing = False
			# sets the new direction
			if keys[pygame.K_RIGHT] and keys[pygame.K_UP]:
				self.__tank_direction = 1
			elif keys[pygame.K_LEFT] and keys[pygame.K_UP]:
				self.__tank_direction = 3
			elif keys[pygame.K_LEFT] and keys[pygame.K_DOWN]:
				self.__tank_direction = 5
			elif keys[pygame.K_RIGHT] and keys[pygame.K_DOWN]:
				self.__tank_direction = 7
			elif keys[pygame.K_RIGHT]:
				self.__tank_direction = 0
			elif keys[pygame.K_UP]:
				self.__tank_direction = 2
			elif keys[pygame.K_LEFT]:
				self.__tank_direction = 4
			elif keys[pygame.K_DOWN]:
				self.__tank_direction = 6
			self.__image = pygame.transform.rotate(self.__original_image, self.__tank_direction * 45)
			if not pygame.sprite.spritecollide(self, walls, False):
				self.__is_stuck_while_ghost = False
			self.update_loc()

	def shoot_bullet(self, event, bullets, direction):
		"""shoots new bullet and adds it the the bullets list, (if there is bullets)
		parameters:
			event: type event (pygame class)
			bullets: type list of bullet, all the bullets in the battlefield
			direction: type int, the direction of the new bullet (when the enemy shot)
		"""
		if event == pygame.K_f:  # enemy shot a bullet
			bullet = Bullet(self, direction)
			bullets.append(bullet)
		elif (event.key == pygame.K_SPACE) and (self.__num_bullet > 0):  # player shoot a bullet
			if time.time() - self.__last_time_of_shot >= 0.5:
				if self.__infinity_ammo_mode is False:
					self.__num_bullet -= 1
				bullet = Bullet(self, -1)  # sets the direction of the player's tank
				bullets.append(bullet)
				self.__last_time_of_shot = time.time()
				return True, bullet
		return False, None
	
	def tank_destroyed(self, screen, explodes):
		"""Actives the gif of explosion
		parameters:
			screen: type surface, the screen of the game
			explodes, type list, the images of the explosion gif
		"""
		image = explodes.next()
		while image is not False:
			screen.blit(image, (self.rect.x - 12, self.rect.y - 10))
			pygame.display.flip()
			image = explodes.next()
			time.sleep(0.07)
		explodes.repeat_strip()
	
	def trap_affect(self, trap):
		"""Actives the trap attribute on the player
		parameters:
			trap: type trap, the trap the tank just activated
		"""
		if trap.get_attribute() == 1:  # lost 1 hp
			self.lost_health(1)
		if trap.get_attribute() == 2:  # heal by 1 hp
			if self.get_health() <= 29:
				self.__health += 1
		if trap.get_attribute() == 3:  # gets infinity bullets for 6 seconds
			self.active_infinity_ammo()
			return True
		if trap.get_attribute() == 4:  # can go through walls for 6 seconds
			self.active_ghost_mode()
			return True

	def is_ghost_mode(self):
		return self.__ghost_mode

	def is_infinity_ammo(self):
		return self.__infinity_ammo_mode

	def is_need_pointing(self):
		return self.__need_pointing

	def set_demo_tank_image(self):
		self.__image = pygame.transform.scale(self.__image, [100, 100])

	def get_color(self):
		return self.__color

	def get_health(self):
		return self.__health

	def heal_health(self):
		self.__health += 1
	
	def update_health(self, newhealth):
		self.__health = newhealth

	def lost_health(self, injury):
		self.__health -= injury

	def get_num_bullet(self):
		return self.__num_bullet

	def get_loc(self):
		return self.rect.x, self.rect.y

	def get_rect(self):
		return self.rect

	def get_image(self):
		return self.__image

	def get_direction(self):
		return self.__tank_direction


class Wall(pygame.sprite.Sprite):
	"""Represent the wall of the maps during a battle"""
	WALL_COLOR = (43, 65, 28)
	
	def __init__(self, screen, start_pos, end_pose):
		super(Wall, self).__init__()
		self.__surface = screen
		self.__start_pos = start_pos
		self.__end_pos = end_pose
		self.__width = 7  # constant width
		self.rect = self.draw_line()

	def get_start_pos(self):
		return self.__start_pos

	def get_end_pos(self):
		return self.__end_pos
	
	def get_rect(self):
		return self.rect
	
	def update_rect(self, pixels, axis):
		if axis == 1:
			if 0 < self.__start_pos[1] < 600:
				self.__start_pos = (self.__start_pos[0], self.__start_pos[1] + pixels)
			if 0 < self.__end_pos[1] < 600:
				self.__end_pos = (self.__end_pos[0], self.__end_pos[1] + pixels)
		else:
			if 0 < self.__start_pos[0] < 800:
				self.__start_pos = (self.__start_pos[0] + pixels, self.__start_pos[1])
			if 0 < self.__end_pos[0] < 800:
				self.__end_pos = (self.__end_pos[0] + pixels, self.__end_pos[1])
		
	def draw_line(self):
		return pygame.draw.line(self.__surface, self.WALL_COLOR,
		    self.__start_pos, self.__end_pos, self.__width)


class Bullet(pygame.sprite.Sprite):
	"""The bullet that were shot from the player's/enemy's tank"""
	BULLET_IMAGE = "Wot images/bullet.png"
	BULLET_MOVES = [(4, 0), (3, -3), (0, -4), (-3, -3),
		(-4, 0), (-3, 3), (0, 4), (3, 3)]  # the amount of pixel moving each direction
	BULLET_ADJUSTMENT = [(30, 13), (33, -7), (12, -11), (-10, -9),
	    (-11, 12), (2, 27), (12, 30), (27, 14)]  # For setting bullet in front of the tank's cannon
	MAX_BULLET_HOPS = 7  # maximum times bullet can hit walls

	def __init__(self, tank, direction=-1):  # get the tank's as shooter
		super(Bullet, self).__init__()
		self.__image = pygame.image.load(self.BULLET_IMAGE)
		if direction == -1:
			self.__bullet_direction = tank.get_direction()  # player shoot the bullet
		else:
			self.__bullet_direction = direction  # enemy shot the bullet
		self.rect = self.__image.get_rect()
		self.rect.x, self.rect.y = tank.get_loc()  # the location of the bullet when it has been shot
		self.place_bullet()  # place the bullet in position in front of tank's canon
		self.ttl = self.MAX_BULLET_HOPS  # number of times that bullet can hit the walls

	def update_loc(self):
		"""update the location of the bullet"""
		self.rect.x += self.BULLET_MOVES[self.__bullet_direction][0]
		self.rect.y += self.BULLET_MOVES[self.__bullet_direction][1]

	def place_bullet(self):
		"""place the bullet right in front of the tank who shot it"""
		self.rect.x += self.BULLET_ADJUSTMENT[self.__bullet_direction][0]
		self.rect.y += self.BULLET_ADJUSTMENT[self.__bullet_direction][1]

	def get_direct(self):
		return self.__bullet_direction

	def hit_wall(self):
		"""redirects the bullet after get into a wall"""
		if self.__bullet_direction % 2 == 0:
			self.rect.x -= self.BULLET_MOVES[self.__bullet_direction][0] * 2
			self.rect.y -= self.BULLET_MOVES[self.__bullet_direction][1] * 2
			self.__bullet_direction += 4
			self.absolute_direct()
		else:
			self.rect.x -= self.BULLET_MOVES[self.__bullet_direction][0]
			self.rect.y -= self.BULLET_MOVES[self.__bullet_direction][1]
			self.__bullet_direction += 2
			self.absolute_direct()
			self.rect.x += self.BULLET_MOVES[self.__bullet_direction][0]
			self.rect.y += self.BULLET_MOVES[self.__bullet_direction][1]
		self.ttl -= 1  # reduce the amount of hops

	def get_ttl(self):
		return self.ttl

	def absolute_direct(self):
		"""Sets the direction to be always point to legal index on BULLET MOVE"""
		if self.__bullet_direction >= len(self.BULLET_MOVES):
			self.__bullet_direction -= len(self.BULLET_MOVES)

	def get_loc(self):
		return self.rect.x, self.rect.y

	def get_image(self):
		return self.__image


class Trap(pygame.sprite.Sprite):
	"""The trap in the map, has 4 different abilities:
		*reduces 1 point of the tank's health
		*heals 1 point of the tank's health
		*Actives tank's ghost mode
		*Actives tank's infinity ammo mode
	"""
	TRAP = "Wot images/Trap.png"
	
	def __init__(self, x, y, attr=None):
		super(Trap, self).__init__()
		self.__image = pygame.image.load(self.TRAP)
		self.rect = self.__image.get_rect()
		self.rect.x, self.rect.y = x, y  # the location of the trap
		if attr is None:  # player create the trap
			#  create the surprise
			self.attribute = random.randint(1, 4)
		else:  # player got the trap's information from other player
			# get info about surprise from the main player
			self.attribute = attr  # the special ability of the trap

	def get_attribute(self):
		return self.attribute

	def get_loc(self):
		return self.rect.x, self.rect.y

	def get_image(self):
		return self.__image


class Spritesheet(object):
	"""This class used for using giff from a image file on the pygame's screen,
	 the file need to include the images of the giff shaped in 2D"""
	def __init__(self, filename, rect, cols, rows, colorkey=None):
		"""set the strip of images of the wanted giff
		arguments:
			filename: type string, the name of the photo which include the giff's images
			rect: type tuple, the size oh each images in the strip
			cols: type int, the amount of columns in the file
			rows: type int, the amount of rows in the file
			colorkey: type tuple, the rgb values the make transparent
		"""
		self.__sheet = pygame.image.load(filename)
		self.__rect = rect
		self.__color_key = colorkey
		self.__cols = cols
		self.__rows = rows
		self.__images = self.load_strip()
		self.__i = 0
		
	def repeat_strip(self):
		self.__i = 0
		
	def image_at(self, rectangle):
		"""Loads image from given rectangle
		parameters:
			rectangle: type tuple, (x, y, width, height)
		returns:
			surface, the image in this pixels of the file
		"""
		rect = pygame.Rect(rectangle)
		image = pygame.Surface(rect.size)
		image.blit(self.__sheet, (0, 0), rect)
		if self.__color_key is not None:
			colorkey = self.__color_key
			if self.__color_key == -1:
				colorkey = image.get_at((0, 0))
			image.set_colorkey(colorkey, pygame.RLEACCEL)
		return image
	
	def load_strip(self):
		"""Loads a strip of images and returns them as a list of surfaces"""
		tups = []
		for y in range(self.__rows):
			for x in range(self.__cols):
				tups.append((self.__rect[0] * x, self.__rect[1] * y, self.__rect[0], self.__rect[1]))
		return [self.image_at(rectangle) for rectangle in tups]

	def next(self):
		"""returns the next image in the strip"""
		if self.__i >= len(self.__images):
			return False
		image = self.__images[self.__i]
		self.__i += 1
		return image


def main():
	pass


if __name__ == '__main__':
	main()
