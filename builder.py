from game_objects import Wall, Tank
from server_objects import Map
from time import sleep
from sqlite3 import *
import pygame
import os


LEFT = 1
SCROLL = 2
RIGHT = 3
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (129, 97, 60)
SIZE = (1270, 600)
LOCAL_DB = "my database.db"
ICON = "Map Builder icon.png"
PLAYER = pygame.image.load(Tank.TANK_IMAGE)
BACKGROUND = pygame.image.load("game images/zone.jpg")
COORDINATES = [((0, 3), (799, 3)), ((3, 0), (3, 592)), ((796, 0), (796, 592)), ((0, 596), (799, 596))]


class MapBuilder:
	def __init__(self, firebase=None, maps=None):
		pygame.init()
		self.__screen = pygame.display.set_mode(SIZE)
		pygame.display.set_caption("Map builder")
		pygame.display.set_icon(pygame.image.load(ICON))
		self.__firebase_app = firebase
		self.__maps = maps
		self.__tanks = []
		self.__font = pygame.font.SysFont('Arial', 40)
		self.__walls = [Wall(self.__screen, x[0], x[1]) for x in COORDINATES]  # built-in walls
	
	def start(self):
		to_build_wall = self.__font.render("Click left to build wall", 1, WHITE)
		to_destroy = self.__font.render("Press D to destroy last wall", True, WHITE)
		to_place_tanks = self.__font.render("Press P to place the tanks", 1, WHITE)
		to_save = self.__font.render("Press S to save and quit", 1, WHITE)
		to_run = self.__font.render("Press R to run map", 1, WHITE)
		clock = pygame.time.Clock()
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
					
				if event.type == pygame.MOUSEBUTTONDOWN and event.button == LEFT:
					if 0 <= pygame.mouse.get_pos()[0] <= 800:
						start_pos = pygame.mouse.get_pos()
						axis = self.choose_axis()
						if axis == -1:
							pygame.quit()
							return
						elif axis is not None:
							self.build_wall(start_pos, axis)
			
			self.__screen.blit(BACKGROUND, [0, 0])
			self.__screen.fill(BROWN, (800, 0, 470, 600))
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
                + str(pygame.mouse.get_pos()), True, WHITE), [855, 300])
			pygame.display.flip()
			clock.tick(FPS)
	
	def run_map(self):
		to_go_back = self.__font.render("Press backspace to go back", True, WHITE)
		to_switch = self.__font.render("Press space to switch modes", True, WHITE)
		on = self.__font.render("Ghost mode: on", True, WHITE)
		off = self.__font.render("Ghost mode: off", True, WHITE)
		clock = pygame.time.Clock()
		check_tank = Tank((100, 200), new_color=WHITE)
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
			self.__screen.blit(BACKGROUND, [0, 0])
			self.__screen.fill(BROWN, (800, 0, 470, 600))
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
				+ str(pygame.mouse.get_pos()), True, WHITE), [855, 300])
			pygame.display.flip()
			clock.tick(FPS)

	def place_tanks(self):
		for_place_tank = self.__font.render("Click left to place tank", True, WHITE)
		for_delete_tank = self.__font.render("Click right on tank to delete", True, WHITE)
		for_save_and_quit = self.__font.render("Press backspace to go back", True, WHITE)
		full_capacity = self.__font.render("Full capacity of tanks", True, WHITE)
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
					if event.button == LEFT:
						if self.is_valid_pos(event.pos) and len(self.__tanks) < 2:
							self.__tanks.append(Tank((event.pos[0], event.pos[1])))
							self.__tanks[-1].update_direction(6 *
							    (not self.__tanks.index(self.__tanks[-1])))
					elif event.button == RIGHT:
						self.remove_tank(event.pos)
						
			self.__screen.blit(BACKGROUND, [0, 0])
			self.__screen.fill(BROWN, (800, 0, 470, 600))
			self.__screen.blit(for_place_tank, [805, 50])
			self.__screen.blit(for_delete_tank, [805, 100])
			self.__screen.blit(for_save_and_quit, [805, 150])
			for wall in self.__walls:
				wall.draw_line()
			for tank in self.__tanks:
				self.__screen.blit(tank.get_image(), tank.get_loc())
			self.__screen.blit(PLAYER, pygame.mouse.get_pos())
			if len(self.__tanks) == 2:
				self.__screen.blit(full_capacity, [830, 300])
			self.__screen.blit(self.__font.render("Mouse pos: "
                + str(pygame.mouse.get_pos()), True, WHITE), [855, 300])
			pygame.display.flip()
	
	def move_last_wall(self, event):
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
		if pos[0] > 800:
			return False
		for wall in self.__walls:
			if wall.get_rect().colliderect(pygame.Rect(pos[0], pos[1], 30, 30)):
				return False
		return True

	def remove_tank(self, pos):
		for tank in self.__tanks:
			if tank.get_rect().colliderect(pygame.Rect(pos[0], pos[1], 1, 1)):
				self.__tanks.remove(tank)
	
	def choose_axis(self):
		which_axis = self.__font.render("Which axis?", True, WHITE)
		option1 = self.__font.render("Press X for horizontal", True, WHITE)
		option2 = self.__font.render("Press Z for vertical", True, WHITE)
		for_cancel = self.__font.render("Press backspace to cancel", True, WHITE)
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
			
			self.__screen.blit(BACKGROUND, [0, 0])
			self.__screen.fill(BROWN, (800, 0, 470, 600))
			self.__screen.blit(which_axis, [810, 50])
			self.__screen.blit(option1, [810, 90])
			self.__screen.blit(option2, [810, 130])
			self.__screen.blit(for_cancel, [810, 190])
			for wall in self.__walls:
				wall.draw_line()
			for tank in self.__tanks:
				self.__screen.blit(tank.get_image(), tank.get_loc())
			self.__screen.blit(self.__font.render("Mouse pos: "
                + str(pygame.mouse.get_pos()), True, WHITE), [855, 300])
			pygame.display.flip()
	
	def build_wall(self, start_pos, free_axis):
		for_cancel = self.__font.render("Press backspace to cancel", True, WHITE)
		for_build = self.__font.render("Click left to build", True, WHITE)
		end_pos = None
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return -1
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_BACKSPACE:
						return
				if event.type == pygame.MOUSEBUTTONDOWN:
					if event.button == LEFT:
						self.__walls.append(Wall(self.__screen, start_pos, end_pos))
						return
			self.__screen.blit(BACKGROUND, [0, 0])
			self.__screen.fill(BROWN, (800, 0, 470, 600))
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
				+ str(pygame.mouse.get_pos()), True, WHITE), [855, 300])
			pygame.display.flip()
	
	def save(self):
		if len(self.__tanks) < 2:
			self.cant_save()
			return
		map_scratches = [x for x in os.listdir("Maps/") if x.endswith(".png")]
		new_map = "Map" + str(max([int(x.split(".")[0][3:]) for x in map_scratches]) + 1)  # the next map number
		pygame.image.save(self.__screen.subsurface((0, 0, 800, 600)), "Maps/" + new_map + ".png")
		walls = ""
		for wall in self.__walls:
			x_start, y_start, x_end, y_end = wall.get_start_pos() + wall.get_end_pos()
			line = f"{x_start},{y_start} {x_end},{y_end}\n"
			walls += line
		walls = walls[:-1]
		tanks_locations = f"{self.__tanks[0].get_loc()[0]},{self.__tanks[0].get_loc()[1]} " \
		                 f"{self.__tanks[1].get_loc()[0]},{self.__tanks[1].get_loc()[1]}"
		token = ''
		conn = connect(LOCAL_DB)
		curs = conn.cursor()
		curs.execute("INSERT INTO Maps VALUES(?, ?, ?, ?, ?, ?)", ("<admin>", new_map,
		    "<admin>-" + new_map, walls, tanks_locations, token))
		if self.__firebase_app is not None:
			token = self.__firebase_app.post("Maps/", {"Creator": "<admin>", "Name": new_map,
               "MapId": "<admin>-" + new_map, "Walls": walls, "PlayersLocations": tanks_locations})['name']
			curs.execute("UPDATE Maps SET Netoken = (?) WHERE MapId = (?)", (token, "<admin>-"+new_map))
		conn.commit()
		if self.__maps is not None:
			self.__maps.append(Map("<admin>", new_map, "<admin>-" + new_map, walls, tanks_locations, token))
		return -1
	
	def cant_save(self):
		output = self.__font.render("Need 2 tanks in map!", True, BLACK)
		self.__screen.blit(output, [200, 90])
		pygame.display.flip()
		sleep(1.5)
		

def main():
	mb = MapBuilder()
	mb.start()


if __name__ == '__main__':
	main()
