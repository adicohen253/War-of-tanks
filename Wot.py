import sys
import pygame
import time
import socket
import game_objects
import random
import threading
import pyaudio
import string
# from tendo import singleton
from select import select
from re import findall
from struct import unpack
from codecs import encode, decode
from RSA import RsaEncryption

# --------------------------------
# author: Adi cohen
# Final project: WOT Online
# --------------------------------

# constants
SIZE = (1200, 600)
TIME_TO_WAIT = 1.6
BARS_POINTER_POS = ([630, 165], [630, 255])
CONNECTING_INPUT_FIELD_POS = ([900, 190], [900, 270])
ASKED_IP_LEN_PACKET = 15
FPS_RATE = 50
PACKET_SENDING_RATE = 60
SECS_TO_PLAY = 10  # 2:30 minutes
BATTLE_TO_DEATH = 0
BATTLE_ON_TIME = 1

# screens and widgets
POINTER = "game images/pointer.png"
SIGN_UP_SCREEN = "game images/Sign up.jpg"
LOGIN_SCREEN = "game images/Login.jpg"
COLOR_SCREEN = "game images/colors.jpg"
SETTINGS_SCREEN = "game images/settings.jpg"
SETTINGS_SCREEN_PART_2 = "game images/settings1.jpg"
MAIN_SCREEN = "game images/Main.jpg"
MENU_SCREEN = "game images/menu.jpg"
SCORE_BOARD = "game images/scoreboard.png"
CHOOSE_MODE_SCREEN = "game images/modes.png"
CONNECT = "game images/connect.jpg"
FIELD = "game images/zone.jpg"
MY_PLAYER_POINT = "game images/player_point.png"
EXPLODE_SHEET = "game images/explode.png"

# fonts
FONT = "game fonts/font.ttf"
EVENT_FONT = "game fonts/events font.ttf"

# sounds
DRAW = "game sounds/draw.mp3"
BOOST = "game sounds/boost.mp3"
ERROR_INPUT = "game sounds/error.mp3"
DEFEAT = "game sounds/losing.mp3"
VICTORY = "game sounds/wining.mp3"
FIRE = "game sounds/shot.mp3"
BRAKE = "game sounds/brake.mp3"
RELOAD = "game sounds/reload.mp3"

# Outputs
WAITING_TO_ANOTHER = "Waiting for another player"
SERVER_DOWN = "Server shut down"
ACCOUNT_DELETED = "Admin deleted your account"
ACCOUNT_BANNED = "Admin banned your account until: "
CANT_CONNECT = "Cant connect to server"
ILLEGAL_USERNAME = "username must start with character"
INVALID_USERNAME = "invalid account change username please"
REGISTER_WORKED = "Registration accepted"
LOGIN_WORKED = "Login successful"
ALREADY_TAKEN = "cant login, another player use this account"
LOGIN_FAILED = "Login failed"
BATTLES_LOCKED = "Server forbids new battle for now"
PLAYER_WIN = "Congratulations you won"
PLAYER_LOSE = "you lost"
PLAYER_DRAW = "Draw"

# colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
KELLY = (76, 187, 23)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
BROWN = (129, 97, 60)
GREEN = (0, 255, 0)
NEON = (57, 255, 20)

# network
SERVER_IP = "192.168.1.35"
SERVER_PORT = 2020
GAME_PORT = 5120
STREAM_PORT = 32000

# voice stream
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WIDTH = 2

pygame.init()
screen = pygame.display.set_mode(SIZE)


class Game:
	# constant widgets
	BULLET = pygame.image.load("game images/bullet.png").convert()
	BULLET.set_colorkey(WHITE)
	BULLET = pygame.transform.scale(BULLET, (50, 50))
	
	GHOST = pygame.image.load("game images/ghost.png").convert()
	GHOST.set_colorkey(WHITE)
	SOUND_OFF = pygame.image.load("game images/Sound off.png").convert()
	SOUND_OFF.set_colorkey(WHITE)
	SOUND_ON = pygame.image.load("game images/Sound on.png").convert()
	SOUND_ON.set_colorkey(WHITE)
	
	ENDLESS_AMMO = pygame.image.load("game images/Endless_Ammo.png").convert()
	ENDLESS_AMMO.set_colorkey(WHITE)
	
	def __init__(self, game_screen):
		self.__screen = game_screen
		self.__ip = socket.gethostbyname(socket.gethostname())
		self.__server_ip = SERVER_IP
		self.__encryption = RsaEncryption()
		self.__input_font = pygame.font.Font(FONT, 40)
		self.__events_font = pygame.font.Font(EVENT_FONT, 35)
		self.__events_font.set_bold(True)
		self.__demo_player = game_objects.Tank((500, 400))
		self.__demo_player.set_demo_tank_image(pygame.transform.scale(self.__demo_player.get_image(), [100, 100]))
		self.__client = socket.socket()
		self.__last_time_check_server = time.time()
		self.__account = ["", ""]
		self.__flags = [False, False]  # for ending battle
		self.__explodes = game_objects.Spritesheet(EXPLODE_SHEET, (0, 0, 70, 70), 5, 5, (0, 0, 0))
		
		# game start and it's functions manage these attributes
		self.__is_sound_active = True  # flag for active voice chat
		self.__p = pyaudio.PyAudio()
		self.__is_collide_happened = False
		self.__new_bullet = None  # new object of bullet to send to enemy
		self.__new_trap = None  # new object of trap to send to enemy
		self.__enemy = None
		self.__player = None
		self.__voice_socket = None  # socket for voice chat
		self.__enemy_socket = None  # socket for communication
		self.__enemy_ip = ""
		self.__traps = []  # list of the traps in map
		self.__bullets = []  # list of the bullets in map
		self.__walls = []  # list of the walls in map
	
	def tank_destroyed(self, rect):
		"""Active the gif of explosion
		argument:
			rect: type - pygame.rect - to location of the tank that uses the gif
		"""
		image = self.__explodes.next()
		while image is not False:
			self.__screen.blit(image, (rect[0] - 12, rect[1] - 10))
			pygame.display.flip()
			image = self.__explodes.next()
			time.sleep(0.07)
		self.__explodes.reload_strip()
	
	def _make_connection_with_server(self):
		"""Return if client success to connect the game server, None otherwise"""
		self.__client.settimeout(2)
		try:
			self.__client.connect((self.__server_ip, SERVER_PORT))
			# configure key for encryption with server
			# get server's key
			length = ord(self.__client.recv(1))
			self.__encryption.set_partner_public_key(
				[int(x) for x in decode(self.__client.recv(length)[::-1], 'base64').decode().split(',')])
			
			# send user's key
			pk_to_send = encode(','.join([str(i) for i in self.__encryption.get_public()]).encode(), 'base64')[::-1]
			pk_to_send = chr(len(pk_to_send)).encode() + pk_to_send
			self.__client.send(pk_to_send)
		except (socket.error, socket.timeout):
			failed_output = self.__events_font.render(CANT_CONNECT, True, BLACK)
			self.__screen.blit(failed_output, [350, 250])
			pygame.display.flip()
			time.sleep(TIME_TO_WAIT)
			sys.exit()
		finally:
			self.__client.settimeout(5)
				
	def server_down_protocol(self):
		"""Protocol of error when try to communicate with server"""
		output = self.__events_font.render(SERVER_DOWN, True, BLACK)
		self.__screen.blit(output, [420, 250])
		pygame.display.flip()
		self.__client.close()
		time.sleep(2)
		sys.exit()
	
	def _send_to_server(self, message_to_send):
		"""Send to server the message, if gets  an error close the game
		argument:
			message_to_send: type - bytes, to message to send to server
		"""
		try:
			self.__client.send(self.__encryption.encrypt(message_to_send))
		except socket.error:
			self.server_down_protocol()
	
	def _receive_from_server(self):
		"""Receive and decrypt to message from server
		if gets an error close the game.
		Returns the decrypted message
		"""
		try:
			length = ord(self.__client.recv(1))
			message = self.__encryption.decrypt(self.__client.recv(length).decode())
			if message == "":
				raise socket.error
			return message
		except socket.error:
			self.server_down_protocol()
	
	def keep_alive(self):
		"""Checks if server is down or user's account is now invalid
		close the game is so, or if server is down"""
		if time.time() - self.__last_time_check_server >= 3:
			rlist, _, _ = select([self.__client], [], [], 0)
			if self.__client in rlist:
				length = self.__client.recv(1).decode()
				if length == "":  # server shut down
					self.server_down_protocol()
				respond = self.__encryption.decrypt(self.__client.recv(ord(length)).decode())
				if "@" in respond:  # client's account deleted
					self.__flags[0] = True
					output = self.__events_font.render(ACCOUNT_DELETED, True, BLACK)
					self.__screen.blit(output, [330, 200])
					pygame.display.flip()
					self.__client.close()
					time.sleep(2)
					sys.exit()
				elif "!" in respond:  # client's account banned
					self.__flags[0] = True
					length = self.__client.recv(1).decode()
					bandate = self.__encryption.decrypt(self.__client.recv(ord(length)).decode())
					output = self.__events_font.render(ACCOUNT_BANNED + bandate, True, BLACK)
					self.__screen.blit(output, [150, 200])
					pygame.display.flip()
					time.sleep(2)
					sys.exit()
			self.__last_time_check_server = time.time()
	
	def _ask_for_color(self):
		"""Ask the server for the player's colors, (maybe server restore all data to default)
		set the color in the demo tank"""
		self._send_to_server("GetColor")
		respond = self._receive_from_server()
		saved_color = findall("..?", respond)
		self.__demo_player.change_player_color([int(x, base=16) for x in saved_color])
	
	def _home_screen(self):
		"""Make sure that user will connect to valid account before start playing
		in addition, generate a key for encryption and set the key of the server
		"""
		main_s = pygame.image.load(MAIN_SCREEN).convert()
		self.__screen.blit(main_s, [0, 0])
		pygame.display.flip()
		self._make_connection_with_server()
		
		while True:
			self.keep_alive()
			events = pygame.event.get()
			for event in events:
				if event.type == pygame.QUIT:
					self._send_to_server("exit")
					self.__client.close()
					sys.exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self._send_to_server("exit")
						self.__client.close()
						sys.exit()
					elif event.key == pygame.K_l:
						self.__account = self._register_and_login_screen(True)
						if self.__account == ["", ""]:
							self.__screen.blit(main_s, [0, 0])
							pygame.display.flip()
					elif event.key == pygame.K_s:
						self.__account = self._register_and_login_screen(False)
						if self.__account == ["", ""]:
							self.__screen.blit(main_s, [0, 0])
							pygame.display.flip()
							self.__screen.blit(main_s, [0, 0])
							pygame.display.flip()
			if self.__account != ["", ""]:
				return
	
	def _register_and_login_screen(self, is_login_now):
		"""get the data of from the user, (username and password)
		argument:
			is_login_now: type - boolean, flag of if player try to login or sign_up
		"""
		pointer_to_bar = pygame.image.load(POINTER).convert()
		pointer_to_bar.set_colorkey(WHITE)
		if is_login_now:
			connection_screen = pygame.image.load(LOGIN_SCREEN).convert()
		else:
			connection_screen = pygame.image.load(SIGN_UP_SCREEN).convert()
		self.__screen.blit(connection_screen, [0, 0])
		pygame.display.flip()
		for i in range(len(self.__account)):
			pointer_pos = BARS_POINTER_POS[i]
			while True:
				self.keep_alive()
				events = pygame.event.get()
				self.__account[i], end_collecting = \
					self._get_input_from_user(self.__account[i], events, 10,
								self.legal_chars_for_username_and_password)
				if end_collecting is None:
					self.__account = ["", ""]
					return self.__account
				if end_collecting:
					break
				self.__screen.blit(connection_screen, [0, 0])
				self.__screen.blit(pointer_to_bar, pointer_pos)
				for index in range(len(self.__account)):
					if self.__account[index] != "":
						account_field_pos = CONNECTING_INPUT_FIELD_POS[index]
						account_field_input = self.__input_font.render(self.__account[index], True, KELLY)
						self.__screen.blit(account_field_input, account_field_pos)
				pygame.display.flip()
		if not self._take_care_connection_cases(is_login_now):
			pygame.event.clear()
			self.__account = self._register_and_login_screen(is_login_now)
		return self.__account
	
	def _take_care_connection_cases(self, is_login_now=False):
		"""take care of every case of signing up or login to username
		argument:
			is_login_now: type - boolean, flag of if player tries to login or register
		"""
		msg_pos = 100, 500
		output = ""
		if not self.__account[0][0].isalpha():  # username must start with alphabetical letter
			output = self.__input_font.render(ILLEGAL_USERNAME, True, BLUE)
			self.__screen.blit(output, msg_pos)
			pygame.display.flip()
			time.sleep(TIME_TO_WAIT)
			return False
		
		legal_case = False
		if is_login_now:
			self._send_to_server("login " + self.__account[0] + "," + self.__account[1])
			respond = self._receive_from_server()
			if respond == "O":  # Ok
				output = self.__input_font.render(LOGIN_WORKED, True, GREEN)
				legal_case = True
			elif respond == "B":  # Ban
				date = self._receive_from_server()
				output = self.__input_font.render(ACCOUNT_BANNED + date, True, RED)
			elif respond == "T":  # Taken
				output = self.__input_font.render(ALREADY_TAKEN, True, RED)
			elif respond == "F":  # Failed
				output = self.__input_font.render(LOGIN_FAILED, True, RED)
		else:
			self._send_to_server("Signup " + self.__account[0] + "," + self.__account[1])
			respond = self._receive_from_server()
			if respond == "Y":
				output = self.__input_font.render(REGISTER_WORKED, True, GREEN)
				legal_case = True
			elif respond == "N":
				output = self.__input_font.render(INVALID_USERNAME, True, RED)
		self.__screen.blit(output, msg_pos)
		pygame.display.flip()
		time.sleep(TIME_TO_WAIT)
		return legal_case
	
	def _color_choose_screen(self):
		"""build the new color of the player as list values of rgb (red, green, blue)
		argument:
		"""
		self._ask_for_color()
		rainbow_screen = pygame.image.load(COLOR_SCREEN).convert()
		self.__screen.blit(rainbow_screen, [0, 0])
		my_color = ["0", "0", "0"]
		for i in range(len(my_color)):
			my_color[i] = ""
			finish = False
			while not finish:
				self.keep_alive()
				events = pygame.event.get()
				my_color[i], end_collecting = self._get_input_from_user(my_color[i],
						events, 3, str.isdigit, self.limit_color_value)
				if end_collecting is None:
					return
				if end_collecting:
					if my_color[i] == "":
						my_color[i] = "0"
					finish = True
				self.__screen.blit(rainbow_screen, [0, 0])
				for element in range(len(my_color)):
					color_pos = 200 + 300 * element, 310
					show_color = self.__input_font.render(my_color[element], True, WHITE)
					self.__screen.blit(show_color, color_pos)
				self.__screen.blit(self.__demo_player.get_image(), self.__demo_player.get_loc())
				pygame.display.flip()
		self.__demo_player.change_player_color(my_color)
		self.__screen.blit(self.__demo_player.get_image(), self.__demo_player.get_loc())
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self._send_to_server("exit")
					sys.exit()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return 
					if event.key == pygame.K_t:
						return self._color_choose_screen()
					if event.key == pygame.K_d:
						my_new_color = "%02x%02x%02x" % tuple(self.__demo_player.get_color())
						self._send_to_server("SetColor " + my_new_color)
						return
	
	# filter for getting input from user in color and connect screens
	@staticmethod
	def legal_chars_for_username_and_password(data):
		"""filter for username data in account"""
		return data.isdigit() or (data in string.ascii_letters)
	
	@staticmethod
	def limit_color_value(data):
		"""filter of max value for element in rgb - player's color"""
		return int(data) > 255
	
	def _get_input_from_user(self, previous_data, events, limit_data_len, filter1, filter2=lambda x: False):
		"""add the input from the player to the current data status - (account color etc),
		plus change the size of the screen.
		argument:
			previous_data: type -  str, the current data
			events: type - pygame.event, all the input from the user
			limit data len: type - str, the length limit of the data
			filter1: type - function, if can add that char to previous_data
			filter2: type - function, if there is need to remove last char from previous_data from some reason
		"""
		for event in events:
			if event.type == pygame.QUIT:
				self._send_to_server("exit")
				self.__client.close()
				sys.exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					return previous_data, None
				if filter1(event.unicode):
					if len(previous_data) < limit_data_len:
						previous_data += event.unicode
					if filter2(previous_data):
						previous_data = previous_data[:-1]
				elif (event.key == pygame.K_BACKSPACE) and (len(previous_data) > 0):
					previous_data = previous_data[:-1]
				elif event.key == pygame.K_RETURN:
					if previous_data == "":
						return "", True
					else:
						return previous_data, True
				else:
					pygame.mixer.music.load(ERROR_INPUT)  # not must
					pygame.mixer.music.play()
					pygame.event.clear()
		return previous_data, False
	
	def _instructions_screen(self):
		"""Explains the game keys"""
		settings = [pygame.image.load(SETTINGS_SCREEN).convert(),
			pygame.image.load(SETTINGS_SCREEN_PART_2).convert()]
		time_to_exchange = time.time()
		self.__screen.blit(settings[0], [0, 0])
		settings[0], settings[1] = settings[1], settings[0]
		pygame.display.flip()
		while True:
			self.keep_alive()
			if time.time() - time_to_exchange >= 0.8:
				self.__screen.blit(settings[0], [0, 0])
				settings[0], settings[1] = settings[1], settings[0]
				pygame.display.flip()
				time_to_exchange = time.time()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self._send_to_server("exit")
					self.__client.close()
					sys.exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return
	
	def _rating_screen(self):
		rating_screen = pygame.image.load(SCORE_BOARD).convert()
		self.__screen.blit(rating_screen, [0, 0])
		self._send_to_server("rating")
		respond = self._receive_from_server()
		champ_data, user_data, index = respond.split("\n")  # for be sure
		champ_data = self.__input_font.render(champ_data, True, BLUE)
		user_data = self.__input_font.render(self.__account[0] + " " + user_data, True, BLUE)
		index = self.__input_font.render(index, True, BLUE)
		for i, element in enumerate([champ_data, user_data, index]):
			self.__screen.blit(element, [400, 150 + 100 * i])
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self._send_to_server("exit")
					self.__client.close()
					sys.exit()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return
	
	def game_menu(self):
		"""manage the game - (color, introductions etc), but first ask for connection to an account"""
		self._home_screen()
		menu_screen = pygame.image.load(MENU_SCREEN).convert()
		self.__screen.blit(menu_screen, [0, 0])
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self._send_to_server("exit")
					self.__client.close()
					sys.exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self._send_to_server("exit")
						self.__client.close()
						sys.exit()
						
					elif event.key == pygame.K_s:  # player look for a match
						mode_code = self._choose_battle_mode()
						if mode_code is not None:
							self._battle_start(mode_code)
							self.__screen.blit(menu_screen, (0, 0))
							pygame.display.flip()
					
					elif event.key == pygame.K_i:  # introductions of game's buttons
						self._instructions_screen()
						self.__screen.blit(menu_screen, (0, 0))
						pygame.display.flip()
						
					elif event.key == pygame.K_c:  # player want to change his tank's color
						self._color_choose_screen()
						self.__screen.blit(menu_screen, (0, 0))
						pygame.display.flip()
						
					elif event.key == pygame.K_r:
						self._rating_screen()
						self.__screen.blit(menu_screen, (0, 0))
						pygame.display.flip()
						
				pygame.event.clear()
	
	def _choose_battle_mode(self):
		modes_screen = pygame.image.load(CHOOSE_MODE_SCREEN).convert()
		self.__screen.blit(modes_screen, [0, 0])
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self._send_to_server("exit")
					self.__client.close()
					sys.exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return None
					elif event.key == pygame.K_1:
						return BATTLE_TO_DEATH
					elif event.key == pygame.K_2:
						return BATTLE_ON_TIME
					
	def output_battle_result(self, is_win):
		self.__events_font.set_bold(False)
		if is_win:
			output = self.__events_font.render(PLAYER_WIN, True, NEON)
			pos = [420, 250]
		elif is_win is False:
			output = self.__events_font.render(PLAYER_LOSE, True, NEON)
			pos = [420, 250]
		else:
			output = self.__events_font.render(PLAYER_DRAW, True, NEON)
			pos = [420, 250]
		self.__events_font.set_bold(True)
		self.__screen.blit(output, pos)
		pygame.display.flip()
	
	def _battle_start(self, mode_code=BATTLE_TO_DEATH):
		"""all the process of the game
		argument:
			account: type list, the username and password
			client: type - socket - the connection to the server
			demo_player: type - tank, for the color of the player
			
		"""
		self._ask_for_color()
		battlefield = pygame.image.load(FIELD).convert()
		self._send_to_server("game " + str(mode_code))
		respond = self._receive_from_server()
		if respond == "#":  # Battlefields are locked
			output = self.__events_font.render(BATTLES_LOCKED, True, BLACK)
			self.__screen.blit(output, [270, 280])
			pygame.display.flip()
			time.sleep(2)
			return
		player_point = pygame.image.load(MY_PLAYER_POINT).convert()
		player_point.set_colorkey(WHITE)
		clock = pygame.time.Clock()
		
		main_player = self._receive_from_server()
		main_player = (main_player == "T")
		if main_player:
			waiting = pygame.image.load(CONNECT).convert()
			self.__screen.blit(waiting, [0, 0])
			pygame.display.flip()
			
			stream_socket = socket.socket()
			stream_socket.bind((self.__ip, STREAM_PORT))  # for voice stream
			stream_socket.listen(1)
			
			main_socket = socket.socket()
			main_socket.bind((self.__ip, GAME_PORT))  # for game communicate
			main_socket.listen(1)
			
			rect1, rect2 = self._build_map()
			if rect1 is None or rect1 is False:
				return
			self.__enemy_socket, address = main_socket.accept()
			self.__enemy_ip = address[0]  # only ip address
			self.__enemy_socket.send(("%02x%02x%02x" % tuple(self.__demo_player.get_color())).encode())
			enemy_color = [int(x, base=16) for x in findall("..?", self.__enemy_socket.recv(6).decode())]
			self.__player = game_objects.Tank(rect1, direct=6, new_color=self.__demo_player.get_color())
			self.__enemy = game_objects.Tank(rect2, direct=0, new_color=enemy_color)
			
			self.__voice_socket = stream_socket.accept()[0]
			main_socket.close()
			stream_socket.close()
		# main player create the server
		# (waiting for another one for starting the game)
		
		else:  # player makes connection with main player
			self.__enemy_ip = self._receive_from_server()
			rect1, rect2 = self._build_map()
			if rect1 is None or rect1 is False:
				return
			self.__enemy_socket = socket.socket()
			self.__enemy_socket.connect((self.__enemy_ip, GAME_PORT))
			self.__enemy_socket.send(("%02x%02x%02x" % tuple(self.__demo_player.get_color())).encode())
			enemy_color = [int(x, base=16) for x in findall("..?", self.__enemy_socket.recv(6).decode())]
			self.__player = game_objects.Tank(rect2, direct=0, new_color=self.__demo_player.get_color())
			self.__enemy = game_objects.Tank(rect1, direct=6, new_color=enemy_color)
			
			self.__voice_socket = socket.socket()
			self.__voice_socket.connect((self.__enemy_ip, STREAM_PORT))
		
		self.__enemy_socket.settimeout(0.5)
		self.__voice_socket.settimeout(1)
		self.__enemy.change_player_color(enemy_color)
		self.__screen.blit(battlefield, [0, 0])
		self.__screen.blit(self.__player.get_image(), self.__player.get_loc())
		self.__screen.blit(self.__enemy.get_image(), self.__enemy.get_loc())
		pygame.display.flip()
		
		start_battle_from = time.time()  # for time battle mode
		
		last_trap_moment = time.time()
		random_time_for_trap = random.randint(3, 5)
		
		threading.Thread(target=self._channeling_with_the_enemy).start()
		threading.Thread(target=self.stream_in).start()  # not using voice chat now
		threading.Thread(target=self.stream_out).start()
		
		while not self.__flags[0]:
			self.keep_alive()
			events = pygame.event.get()
			for event in events:
				if event.type == pygame.QUIT:
					self.__flags[0] = True
					pygame.mixer.music.load(DEFEAT)
					pygame.mixer.music.play()
					self._send_to_server("exit")
					# self.output_battle_result(False)
					time.sleep(TIME_TO_WAIT)
					self.__client.close()
					sys.exit()
				
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.__flags[0] = True
						self._send_to_server("Defeat")
						pygame.mixer.music.load(DEFEAT)
						# self.output_battle_result(False)
						break
						
					elif event.key == pygame.K_BACKSPACE:
						self.__is_sound_active = not self.__is_sound_active
					
					is_shoot, self.__new_bullet = self.__player.shoot_bullet(event, self.__bullets, -1)
					if is_shoot:
						pygame.mixer.music.load(FIRE)
						pygame.mixer.music.play()
			
			if self.__flags[0]:
				if self.__is_collide_happened:  # enemy player detected collide
					pygame.mixer.music.load(DRAW)
				break
			
			if self.__flags[1]:
				self._send_to_server("Victory")
				# self.output_battle_result(True)
				pygame.mixer.music.load(VICTORY)
				break
			
			if pygame.sprite.spritecollide(self.__player, [self.__enemy], False):
				self.__is_collide_happened = True
				self._send_to_server("Draw")
				# self.output_battle_result(None)
				pygame.mixer.music.load(DRAW)
				break
			
			if main_player and time.time() - last_trap_moment >= random_time_for_trap:
				last_trap_moment, random_time_for_trap = self._create_trap()
				self.__new_trap = self.__traps[-1]
			
			if len(self.__traps) > 4:
				self.__traps.remove(self.__traps[0])
			
			for bullet in self.__bullets:
				bullet.update_loc()
				
				if pygame.sprite.spritecollide(bullet, self.__walls, False):
					bullet.hit_wall()
					if bullet.get_ttl() == 0:
						self.__bullets.remove(bullet)
				
				elif pygame.sprite.spritecollide(bullet, [self.__player], False):
					self.__bullets.remove(bullet)
					self.__player.lost_health(1)
				
				elif pygame.sprite.spritecollide(bullet, [self.__enemy], False):
					self.__bullets.remove(bullet)
					self.__enemy.lost_health(1)
			
			for t in self.__traps:
				if pygame.sprite.spritecollide(t, [self.__player], False):
					self._trap_affect(t, True)
					self.__traps.remove(t)
				
				elif pygame.sprite.spritecollide(t, [self.__enemy], False):
					self._trap_affect(t, False)
					self.__traps.remove(t)
			
			if self.__player.get_health() <= 0:
				self._send_to_server("Defeat")
				self.tank_destroyed(self.__player.get_loc())
				# self.output_battle_result(False)
				pygame.mixer.music.load(DEFEAT)
				self.__flags[0] = True
				break
			
			elif self.__enemy.get_health() <= 0:
				self._send_to_server("Victory")
				self.tank_destroyed(self.__enemy.get_loc())
				# self.output_battle_result(True)
				pygame.mixer.music.load(VICTORY)
				self.__flags[0] = True
				break
			
			self.__player.move_tank(self.__walls)
			self.__player.is_done_eternal_ammo()
			self.__player.is_done_ghost()
			
			self._flip_screen(battlefield)
			if self.__player.is_need_pointing():
				self.__screen.blit(player_point, [self.__player.get_loc()[0], self.__player.get_loc()[1] - 50])
			if mode_code == BATTLE_ON_TIME:
				if self._take_care_time_mode(start_battle_from):  # time is up
					break
			pygame.display.flip()
			if self.__player.reload_ammo():  # only makes sound of reload when the player reloads
				pygame.mixer.music.load(RELOAD)
				pygame.mixer.music.play(2)
			
			clock.tick(FPS_RATE)
		pygame.mixer.music.play()
		time.sleep(TIME_TO_WAIT)
		self.clean_match_data()
	
	def clean_match_data(self):
		self.__enemy = None
		self.__player = None
		self.__enemy_socket = None
		self.__voice_socket = None
		self.__enemy_ip = ""
		self.__traps = []
		self.__bullets = []
		self.__walls = []
		self.__is_collide_happened = False
		self.__flags = [False, False]
		self.__is_sound_active = True
	
	def _flip_screen(self, zone):
		"""shows all the data of the surface (pixels) plus the data of the players
		argument:
			players: type - list of tanks,(player and enemy)
			zone: type - surface, the image of the field
			ammo: type - list of bullets, all the bullets in the field
			traps: all the mines in the battlefield
		"""
		# constants of UI to battle screen":
		output_list = [["my health:", (850, 30)], ["my ammo:", (850, 90)],
			["enemy health:", (850, 150)], [str(self.__player.get_health()), (1000, 33)],
			[str(self.__enemy.get_health()), (1050, 153)],
			[str(self.__player.get_num_bullet()) + " X", (990, 90)],
			["Sound:", (850, 210)]]
		self.__screen.fill(BROWN)
		self.__screen.blit(zone, [0, 0])
		self.__screen.blit(self.BULLET, (1060, 82))
		
		if self.__is_sound_active:
			self.__screen.blit(self.SOUND_ON, (950, 205))
		else:
			self.__screen.blit(self.SOUND_OFF, (950, 205))
		
		if self.__player.get_is_ghost_mode():
			self.__screen.blit(self.GHOST, (850, 270))
		for player in [self.__player, self.__enemy]:
			self.__screen.blit(player.get_image(), player.get_loc())
		for i in self.__bullets:
			self.__screen.blit(i.get_image(), i.get_loc())
		for trap in self.__traps:
			self.__screen.blit(trap.get_image(), trap.get_loc())
		for wall in self.__walls:
			wall.draw_line()
		for element in output_list:
			if output_list.index(element) == 5 and self.__player.get_is_eternal_ammo_mode():  # in case of endless ammo
				self.__screen.blit(self.ENDLESS_AMMO, element[1])
				continue
			self.__screen.blit(self.__input_font.render(element[0], True, WHITE), element[1])
	
	def _channeling_with_the_enemy(self):
		clock = pygame.time.Clock()
		while not self.__flags[0]:
			packet_to_send = \
				f"D{self.__player.get_pointer()}\n" \
				f"L{self.__player.get_loc()[0]},{self.__player.get_loc()[1]}\n"
			if self.__new_trap is not None:  # new trap
				packet_to_send += f"T{self.__new_trap.get_attribute()}" \
							f"{self.__new_trap.get_loc()[0]}.{self.__new_trap.get_loc()[1]}\n"
				self.__new_trap = None
			if self.__new_bullet is not None:
				packet_to_send += f"B{self.__new_bullet.get_direct()}\n"
				self.__new_bullet = None
			if self.__is_collide_happened:
				packet_to_send += "C\n"
				self.__flags[0] = True
			
			try:
				self.__enemy_socket.send((chr(len(packet_to_send))).encode()
					+ packet_to_send.encode())
			except socket.error:
				self.__flags[1] = True  # enemy quit
				break
			rlist, _, _ = select([self.__enemy_socket], [], [], 0)
			if self.__enemy_socket in rlist:
				length = self.__enemy_socket.recv(1).decode()
				if length == "":  # enemy quit
					self.__flags[1] = True
					break
				else:
					enemy_data = self.__enemy_socket.recv(ord(length)).decode().split()
					self._take_care_enemy_packet(enemy_data)
			clock.tick(PACKET_SENDING_RATE)
		self.__enemy_socket.close()
		self.__voice_socket.close()
	
	def _take_care_enemy_packet(self, enemy_data):
		for header in enemy_data:
			if "D" in header:
				self.__enemy.set_enemy_pointer(int(header[1]))
			if "L" in header:
				x_pos, y_pos = header[1:].split(",")
				self.__enemy.update_enemy_loc(int(x_pos), int(y_pos))
			if "T" in header:
				trap_attribute = header[1]
				trap_pos_x, trap_pox_y = header[2:].split(".")
				self.__traps.append(game_objects.Trap(int(trap_pos_x), int(trap_pox_y), int(trap_attribute)))
			if "B" in header:
				self.__enemy.shoot_bullet(pygame.K_f, self.__bullets, int(header[1]))
			if ("C" in header) and not self.__is_collide_happened:
				self._send_to_server("Draw")
				self.__is_collide_happened = True
				self.__flags[0] = True
	
	def stream_in(self):
		try:
			microphone = self.__p.open(format=FORMAT, channels=CHANNELS,
					rate=RATE, input=True, frames_per_buffer=CHUNK)
			while not (self.__flags[0] or self.__flags[1]):
				try:
					self.__voice_socket.send(microphone.read(CHUNK))
				except (IOError, socket.error):
					break
			microphone.stop_stream()
			microphone.close()
		except OSError:
			pass
	
	def stream_out(self):
		try:
			speaker = self.__p.open(format=FORMAT, channels=CHANNELS,
				rate=RATE, output=True, frames_per_buffer=CHUNK)
			while not (self.__flags[0] or self.__flags[1]):
				try:
					data = self.__voice_socket.recv(CHUNK)
					if self.__is_sound_active:
						speaker.write(data)
				except (IOError, socket.error):
					break
			speaker.stop_stream()
			speaker.close()
		except OSError:
			pass
	
	def _build_map(self):
		connect_img = pygame.image.load(CONNECT)
		self.__screen.blit(connect_img, [0, 0])
		output = self.__input_font.render(WAITING_TO_ANOTHER + "...", True, (0, 0, 255))
		screen.blit(output, [75, 520])
		pygame.display.flip()
		while True:
			rlist, _, _ = select([self.__client], [], [], 0)
			if self.__client in rlist:
				length = self.__client.recv(2)
				if length == b"":
					self.server_down_protocol()
				if length == b"##":  # server closed battlefields
					output = self.__events_font.render(BATTLES_LOCKED, True, WHITE)
					self.__screen.blit(output, [270, 280])
					pygame.display.flip()
					time.sleep(2)
					return False, False
				length = unpack("<H", length)[0]
				all_walls, rects = self.__encryption.decrypt_map_data(self.__client.recv(length).decode())
				break
				
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self._send_to_server("exit")
					self.__client.close()
					exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self._send_to_server("%")
						return None, None
			self.refresh_connection_screen(connect_img)
		all_walls = all_walls.split("\n")
		rects = [int(x) for x in findall(r"\d+", rects)]
		rects = [[rects[0]] + [rects[1]], [rects[2]] + [rects[3]]]
		for wall in all_walls:
			s_pos, e_pos = wall.split(" ")
			s_pos, e_pos = [int(x) for x in s_pos.split(",")], [int(y) for y in e_pos.split(",")]
			self.__walls.append(game_objects.Wall(self.__screen, s_pos, e_pos))
		return rects
	
	def refresh_connection_screen(self, img):
		screen.blit(img, (0, 0))
		output = self.__input_font.render(WAITING_TO_ANOTHER, True, (0, 0, 255))
		screen.blit(output, [75, 520])
		pygame.display.flip()
		for i in range(4):
			output = self.__input_font.render("." * i, True, (0, 0, 255))
			screen.blit(output, [405, 520])
			pygame.display.flip()
			time.sleep(0.3)
	
	def _take_care_time_mode(self, start_time):
		time_to_play = SECS_TO_PLAY - (time.time() - start_time)
		if time_to_play <= 0:
			if self.__player.get_health() > self.__enemy.get_health():
				self._send_to_server("Victory")
				self.output_battle_result(True)
				pygame.mixer.music.load(VICTORY)
				self.__flags[0] = True
			elif self.__player.get_health() < self.__enemy.get_health():
				self._send_to_server("Defeat")
				self.output_battle_result(False)
				pygame.mixer.music.load(DEFEAT)
				self.__flags[0] = True
			else:
				self._send_to_server("Draw")
				self.output_battle_result(None)
				pygame.mixer.music.load(DRAW)
				self.__flags[0] = True
			return True
		else:
			time_to_play = time.strftime("%M:%S", time.gmtime(time_to_play))
			self.__screen.blit(self.__input_font.render(time_to_play, True, WHITE), [900, 420])
	
	def _trap_affect(self, trap, is_myself):
		"""active the trap attribute on the player"""
		if is_myself:
			tank = self.__player
		else:
			tank = self.__enemy
		if trap.get_attribute() == 1:
			tank.lost_health(1)
		if trap.get_attribute() == 2:
			if tank.get_health() <= 29:
				tank.heal_health()
		if trap.get_attribute() == 3:
			tank.active_eternal_ammo_mode()
			pygame.mixer.music.load(BOOST)
			pygame.mixer.music.play(1)
		if trap.get_attribute() == 4:
			tank.active_ghost_mode()
			pygame.mixer.music.load(BOOST)
			pygame.mixer.music.play(1)
	
	def _create_trap(self):
		"""create a new mine (location is safe)
		argument:
			surprise: type - list, the all traps in the battlefield
			walls_and_players: type - list of all objects that's can block location for a new mine
		"""
		x_surprise_loc = random.randint(0, 759)
		y_surprise_loc = random.randint(0, 559)
		new_surprise = game_objects.Trap(x_surprise_loc, y_surprise_loc)
		while pygame.sprite.spritecollide(new_surprise,
			self.__walls + self.__traps + [self.__player, self.__enemy], False):
			x_surprise_loc = random.randint(0, 759)
			y_surprise_loc = random.randint(0, 559)
			new_surprise = game_objects.Trap(x_surprise_loc, y_surprise_loc)
		self.__traps.append(new_surprise)
		return time.time(), random.randint(3, 5)


def main():
	# try:
	#     _ = singleton.SingleInstance()
	# except singleton.SingleInstanceException:
	#     exit()
	pygame.mixer.init()
	pygame.mixer.music.set_volume(1)
	pygame.display.set_caption("War Of Tanks")
	game = Game(screen)
	game.game_menu()


if __name__ == '__main__':
	main()
