import pygame
import os
from time import sleep
from wot_objects import Wall, Tank


class MapBuilder:
	LEFT = 1
	RIGHT = 3
	FPS = 60
	WHITE = (255, 255, 255)
	BLACK = (0, 0, 0)
	BROWN = (129, 97, 60)
	SIZE = (1500, 600)
	ICON = "MapBuilder_icon.png"
	PLAYER = pygame.image.load("wot images/Tank.png")
	BACKGROUND = pygame.image.load("wot images/zone.jpg")
	COORDINATES = [((0, 3), (799, 3)), ((3, 0), (3, 592)), ((796, 0), (796, 592)), ((0, 596), (799, 596))] # base walls for map builder
	"""This class used by the server's admin for building more maps which the players can fight,
	in addition enable to run the map with a demo player to check the walls that the admin build
	after the building process the map and its data saved in the data base and photographed for display later"""
	
	def __init__(self,connection, maps=None):
		pygame.display.init()
		pygame.font.init()
		self.__screen = pygame.display.set_mode(self.SIZE)
		pygame.display.set_caption("Map builder")
		pygame.display.set_icon(pygame.image.load(self.ICON))
		self.__maps = maps  # the list of maps to add the new map to
		self.__tanks = []  # the player's tanks which are placed in the map
		self.__font = pygame.font.SysFont('Arial', 40)
		self.__walls = [Wall(self.__screen, x[0], x[1]) for x in self.COORDINATES]  # built-in walls
		self.__conn = connection
	
	def start(self):
		"""Runs the builder, if a minor function of the calls returns -1, means the admin close the builder"""
		to_build_wall = self.__font.render("Click left to build wall", 1, self.WHITE)
		to_destroy = self.__font.render("Press D to destroy last wall", True, self.WHITE)
		to_place_tanks = self.__font.render("Press P to place the tanks", 1, self.WHITE)
		to_save = self.__font.render("Press S to save and quit", 1, self.WHITE)
		to_run = self.__font.render("Press R to run map", 1, self.WHITE)
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					return
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_p:
						if self.place_tanks() == -1:
							pygame.quit()
							return
					elif event.key == pygame.K_r:
						if self.run_map() == -1:
							pygame.quit()
							return
					elif event.key == pygame.K_s:
						if self.save() == -1:
							pygame.quit()
							return
					elif event.key == pygame.K_d and len(self.__walls) > 4:
						self.__walls.remove(self.__walls[-1])
					self.move_last_wall(event)
				
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == self.LEFT:
					if 0 <= pygame.mouse.get_pos()[0] <= 800:
						start_pos = pygame.mouse.get_pos()
						axis = self.choose_axis()
						if axis == -1:
							pygame.quit()
							return
						elif axis is not None:
							self.build_wall(start_pos, axis)
			
			self.__screen.blit(self.BACKGROUND, [0, 0])
			self.__screen.fill(self.BROWN, (800, 0, 700, 600))
			self.__screen.blit(to_build_wall, [850, 50])
			self.__screen.blit(to_destroy, [815, 100])
			self.__screen.blit(to_place_tanks, [815, 150])
			self.__screen.blit(to_save, [835, 200])
			self.__screen.blit(to_run, [855, 250])
			for wall in self.__walls:
				wall.draw_line()
			for tank in self.__tanks:
				self.__screen.blit(tank.get_image(), tank.get_loc())
			self.__screen.blit(self.__font.render("Mouse pos: "
			                                      + str(pygame.mouse.get_pos()), True, self.WHITE), [855, 300])
			
			pygame.display.flip()
	
	def run_map(self):
		"""Tests the map using demo tank which can get in/out ghost mode for checking the walls"""
		to_go_back = self.__font.render("Press backspace to go back", True, self.WHITE)
		to_switch = self.__font.render("Press space to switch modes", True, self.WHITE)
		on = self.__font.render("Ghost mode: on", True, self.WHITE)
		off = self.__font.render("Ghost mode: off", True, self.WHITE)
		clock = pygame.time.Clock()
		check_tank = Tank((100, 200), new_color=self.WHITE)
		check_tank.active_ghost_mode()
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return -1
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_BACKSPACE:
						return
					elif event.key == pygame.K_SPACE:
						if check_tank.is_ghost_mode():
							check_tank.turn_of_ghost()
						else:
							check_tank.active_ghost_mode()
			
			check_tank.move_tank(self.__walls)
			
			self.__screen.blit(self.BACKGROUND, [0, 0])
			self.__screen.fill(self.BROWN, (800, 0, 700, 600))
			self.__screen.blit(to_go_back, [805, 50])
			self.__screen.blit(to_switch, [805, 100])
			for wall in self.__walls:
				wall.draw_line()
			self.__screen.blit(check_tank.get_image(), check_tank.get_loc())
			if check_tank.is_ghost_mode():
				self.__screen.blit(on, [805, 170])
			else:
				self.__screen.blit(off, [805, 170])
			self.__screen.blit(self.__font.render("Mouse pos: "
			                                      + str(pygame.mouse.get_pos()), True, self.WHITE), [855, 300])
			
			pygame.display.flip()
			clock.tick(self.FPS)
	
	def place_tanks(self):
		"""Lets the admin decide where to place the two tanks of the players
		(recommended after the map has been built)
		"""
		for_place_tank = self.__font.render("Click left to place tank", True, self.WHITE)
		for_delete_tank = self.__font.render("Click right on tank to delete", True, self.WHITE)
		for_save_and_quit = self.__font.render("Press backspace to go back", True, self.WHITE)
		full_capacity = self.__font.render("Full capacity of tanks", True, self.WHITE)
		pygame.mouse.set_visible(False)
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return -1
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_BACKSPACE:
						pygame.mouse.set_visible(True)
						return
				
				if event.type == pygame.MOUSEBUTTONDOWN:
					if event.button == self.LEFT:
						if self.is_valid_pos(event.pos) and len(self.__tanks) < 2:
							self.__tanks.append(Tank((event.pos[0], event.pos[1])))
							self.__tanks[-1].update_direction(6 *
							                                  (not self.__tanks.index(self.__tanks[-1])))
					elif event.button == self.RIGHT:
						self.remove_tank(event.pos)
			
			self.__screen.blit(self.BACKGROUND, [0, 0])
			self.__screen.fill(self.BROWN, (800, 0, 700, 600))
			self.__screen.blit(for_place_tank, [805, 50])
			self.__screen.blit(for_delete_tank, [805, 100])
			self.__screen.blit(for_save_and_quit, [805, 150])
			for wall in self.__walls:
				wall.draw_line()
			for tank in self.__tanks:
				self.__screen.blit(tank.get_image(), tank.get_loc())
			self.__screen.blit(self.PLAYER, pygame.mouse.get_pos())
			if len(self.__tanks) == 2:
				self.__screen.blit(full_capacity, [830, 300])
			self.__screen.blit(self.__font.render("Mouse pos: "
			                                      + str(pygame.mouse.get_pos()), True, self.WHITE), [855, 350])
			
			pygame.display.flip()
	
	def move_last_wall(self, event):
		"""Allows the admin to arrange the current wall by a few pixels for each side for accuracy
		parameters:
			event: type pygame.event, the key which been pressed
		"""
		if len(self.__walls) > 4:
			if event.key == pygame.K_UP:
				self.__walls[-1].update_rect(-1, 1)
			elif event.key == pygame.K_DOWN:
				self.__walls[-1].update_rect(1, 1)
			elif event.key == pygame.K_LEFT:
				self.__walls[-1].update_rect(-1, 0)
			elif event.key == pygame.K_RIGHT:
				self.__walls[-1].update_rect(1, 0)
	
	def is_valid_pos(self, pos):
		"""Checks if the asked position in screen is valid for placing a player's tank
		parameters:
			pos: type tuple, the position which been asked
		"""
		if pos[0] > 800:
			return False
		for wall in self.__walls:
			if wall.get_rect().colliderect(pygame.Rect(pos[0], pos[1], 30, 30)):
				return False
		return True
	
	def remove_tank(self, pos):
		"""Delete the tank which the user right-click on
		parameters:
			pos: type tuple, the position of the mouse
		"""
		for tank in self.__tanks:
			if tank.get_rect().colliderect(pygame.Rect(pos[0], pos[1], 1, 1)):
				self.__tanks.remove(tank)
	
	def choose_axis(self):
		"""Asked the admin which axis the next wall will be on, (X/Y)
		returns 1 if for y axis, and 0 for x axis"""
		which_axis = self.__font.render("Which axis?", True, self.WHITE)
		option1 = self.__font.render("Press X for horizontal", True, self.WHITE)
		option2 = self.__font.render("Press Z for vertical", True, self.WHITE)
		for_cancel = self.__font.render("Press backspace to cancel", True, self.WHITE)
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return -1
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_BACKSPACE:
						return
					elif event.key == pygame.K_z:
						return 1
					elif event.key == pygame.K_x:
						return 0
			
			self.__screen.blit(self.BACKGROUND, [0, 0])
			self.__screen.fill(self.BROWN, (800, 0, 700, 600))
			self.__screen.blit(which_axis, [810, 50])
			self.__screen.blit(option1, [810, 90])
			self.__screen.blit(option2, [810, 130])
			self.__screen.blit(for_cancel, [810, 190])
			for wall in self.__walls:
				wall.draw_line()
			for tank in self.__tanks:
				self.__screen.blit(tank.get_image(), tank.get_loc())
			self.__screen.blit(self.__font.render("Mouse pos: "
			                                      + str(pygame.mouse.get_pos()), True, self.WHITE), [855, 300])
			pygame.display.flip()
	
	def build_wall(self, start_pos, free_axis):
		"""travels with the mouse for decided where to end the current wall
		parameters:
			start_pos: type tuple, the position the wall begin in
			free_axis: type int, the axis which the wall built on
		"""
		for_cancel = self.__font.render("Press backspace to cancel", True, self.WHITE)
		for_build = self.__font.render("Click left to build", True, self.WHITE)
		end_pos = None
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return -1
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_BACKSPACE:
						return
				if event.type == pygame.MOUSEBUTTONDOWN:
					if event.button == self.LEFT:
						self.__walls.append(Wall(self.__screen, start_pos, end_pos))
						return
			self.__screen.blit(self.BACKGROUND, [0, 0])
			self.__screen.fill(self.BROWN, (800, 0, 700, 600))
			self.__screen.blit(for_build, [810, 90])
			self.__screen.blit(for_cancel, [810, 150])
			for wall in self.__walls:
				wall.draw_line()
			for tank in self.__tanks:
				self.__screen.blit(tank.get_image(), tank.get_loc())
			
			if free_axis:
				end_pos = (start_pos[0], pygame.mouse.get_pos()[1])
			else:
				end_pos = (pygame.mouse.get_pos()[0], start_pos[1])
			if end_pos[0] > 799:
				end_pos = (799, end_pos[1])
			pygame.draw.line(self.__screen, Wall.WALL_COLOR, start_pos, end_pos, 7)
			self.__screen.blit(self.__font.render("Mouse pos: "
			                                      + str(pygame.mouse.get_pos()), True, self.WHITE), [855, 300])
			pygame.display.flip()
	
	def save(self):
		"""after the admin finished build the map, the builder saves the map's data
		 in the databases and took a picture of the map for displaying later
		 """
		if len(self.__tanks) < 2:
			self.cant_save()  # there are missing tanks for the players
			return
		
		map_scratches = [x for x in os.listdir("Maps/") if x.endswith(".png")]
		new_map = "Map" + str(max([int(x.split(".")[0][3:]) for x in map_scratches]) + 1)  # the next map number
		pygame.image.save(self.__screen.subsurface((0, 0, 800, 600)), "Maps/" + new_map + ".png")
		
		# build the string of walls
		walls = ""
		for wall in self.__walls:
			x_start, y_start, x_end, y_end = wall.get_start_pos() + wall.get_end_pos()
			line = f"{x_start},{y_start} {x_end},{y_end}\n"
			walls += line
		walls = walls[:-1]
		tanks_locations = f"{self.__tanks[0].get_loc()[0]},{self.__tanks[0].get_loc()[1]} " \
		                  f"{self.__tanks[1].get_loc()[0]},{self.__tanks[1].get_loc()[1]}"
		# save in local database
		
		curs = self.__conn.cursor()
		curs.execute("INSERT INTO Maps VALUES(%s, %s, %s, %s, %s)", ("<admin>", new_map, "<admin>-" + new_map, walls, tanks_locations))
		self.__conn.commit()
		curs.close()
		if self.__maps is not None:
			self.__maps.append(Map("<admin>", new_map, "<admin>-" + new_map, walls, tanks_locations))
		return -1
	
	def cant_save(self):
		"""error output if admin tries to save the map without placing 2 tanks for the players"""
		output = self.__font.render("Need 2 tanks in map!", True, self.BLACK)
		self.__screen.blit(output, [200, 90])
		pygame.display.flip()
		sleep(1.5)


class Account:
	"""The class used by the server to organize the player's data and manage them """
	def __init__(self, username, password, wins, loses, draws, points, color,
	             bandate):
		self.__username = username  # account's username
		self.__password = password  # account's password
		self.__wins = wins  # number of wins
		self.__loses = loses  # number of loses
		self.__draws = draws  # number of ties
		self.__points = points  # all the points the account gathers
		self.__favorite_color = color  # tank's color
		self.__battle_id = 0  # the number of the arena the player fights in
		self.__ban_date = bandate  # until player can log in again
		if self.__ban_date != "00/00/0000":  # account is banned
			self.__client_status = "Banned"
		else:  # account isn't banned
			self.__client_status = "Offline"
	
	def get_status(self):
		return self.__client_status
	
	def get_username(self):
		return self.__username
	
	def get_password(self):
		return self.__password
	
	def get_wins(self):
		return self.__wins
	
	def get_loses(self):
		return self.__loses
	
	def get_draws(self):
		return self.__draws
	
	def get_color(self):
		return self.__favorite_color
	
	def get_battle_id(self):
		return self.__battle_id
	
	def get_ban_date(self):
		return self.__ban_date
	
	def get_points(self):
		return self.__points
	
	def set_battle_id(self, new_battle_id):
		self.__battle_id = new_battle_id
	
	def reset_account(self):
		"""Clean the data of the account to default settings"""
		self.__wins = 0
		self.__loses = 0
		self.__draws = 0
		self.__points = 0
		self.__favorite_color = "4d784e"
		self.__ban_date = "00/00/0000"
		if self.__client_status == "Banned":
			self.__client_status = "Offline"
   
	def set_status(self, status):
		self.__client_status = status
	
	
	def set_ban_until(self, new_date):
		"""set a new ban date
		parameters:
			new_date: type string, the new date to set
		"""
		self.__ban_date = new_date
		self.__client_status = "Banned"
	
	def free(self):
		"""free the account from being banned"""
		self.__ban_date = "00/00/0000"
		self.__client_status = "Offline"
	
	def get_bonus(self, bonus):
		"""account receive a bonus by kill of the 3 best players"""
		self.__points += bonus
	
	def add_win(self):
		self.__wins += 1
		self.__points += 2
	
	def add_lose(self):
		self.__loses += 1
	
	def add_draws(self):
		self.__draws += 1
		self.__points += 1
	
	def update_color(self, newcolor):
		self.__favorite_color = newcolor
	
	def __str__(self):
		"""make a string to describe all the account members"""
		return f"{self.__username} {self.__password} " \
		       f"{self.__wins} {self.__loses} {self.__draws} {self.__points} " \
		       f"{self.__favorite_color} {self.__client_status} " \
		       f"{self.__ban_date} {self.__battle_id}"


class Map:
	"""As the Account class, organizes the maps data for the server to access and manage them
	in this version of the project there is only one creator - the admin.
	However, the foundation for multiple creators (like players) already exist"""
	def __init__(self, creator, map_name, map_id, walls, players_locations):
		self.__creator = creator  # the creator of the map, for now there is only "<admin>"
		self.__map_name = map_name  # also the map image's file name
		self.__map_id = map_id  # the primary value of each map, (for identify)
		self.__walls = walls
		self.__players_locations = players_locations
	
	def __str__(self):
		"""generates a string of the relevant information about the map to sending to players"""
		s = f"{self.__walls}+{self.__players_locations}"
		return s
	
	def get_name(self):
		return self.__map_name
	
	def get_creator(self):
		return self.__creator
	
	def get_map_id(self):
		return self.__map_id

if __name__ == '__main__':
	pass
