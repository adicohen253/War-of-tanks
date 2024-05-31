import socket
import threading
import pyaudio
from wot_objects import *
from sys import exit
from string import ascii_letters
from select import select
from re import findall
from struct import unpack
from codecs import encode, decode
from RSA import RsaEncryption

# Constants
SIZE = (1200, 600)
TIME_TO_WAIT = 1.5
ENTRIES_POINTER_POS = ([630, 165], [630, 255]) # For resgistration and login screens
CONNECTING_INPUT_FIELD_POS = ([900, 190], [900, 270])
RGB_VALUES_POS = ([200, 310], [500, 310], [800, 310])
FPS_RATE = 60
SECS_TO_PLAY = 180  # Time for time mode battle in secodns
LIFE_MODE = 0
TIME_MODE = 1

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
KELLY = (76, 187, 23)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
BROWN = (129, 97, 60)
GREEN = (0, 255, 0)
NEON = (57, 255, 20)

# Screens
SIGN_UP_SCREEN = "wot images/Sign up.jpg"
LOGIN_SCREEN = "wot images/Login.jpg"
COLOR_SCREEN = "wot images/colors.jpg"
SETTINGS_SCREEN = "wot images/instructions.jpg"
MAIN_SCREEN = "wot images/Main.jpg"
MENU_SCREEN = "wot images/menu.jpg"
SCORE_BOARD = "wot images/rating.png"
CHOOSE_MODE_SCREEN = "wot images/modes.png"
WAITING_SCREEN = "wot images/waiting.jpg"

# General elements
LOGO = "wot images/logo.ico"
GOLD = "wot images/gold.png"
SILVER = "wot images/silver.png"
BRONZE = "wot images/bronze.png"
POINTER = "wot images/Account fields pointer.png"

# Battle widgets
BULLET = pygame.transform.scale(pygame.image.load("wot images/bullet.png"), (50, 50))
GHOST = pygame.image.load("wot images/ghost.png")
SOUND_OFF = pygame.image.load("wot images/Sound off.png")
SOUND_ON = pygame.image.load("wot images/Sound on.png")
ENDLESS_AMMO = pygame.image.load("wot images/Endless Ammo.png")
BATTLEFIELD_BACKGROUND = pygame.image.load("wot images/zone.jpg")
PLAYER_POINTER = "wot images/Tank pointer.png"
EXPLODE_SHEET = "wot images/explode.png"

# Fonts
FONT = "wot fonts/ifont.ttf"
EVENT_FONT = "wot fonts/ofont.ttf"

# Sounds
DRAW = "wot sounds/draw.mp3"
BOOST = "wot sounds/boost.mp3"
ERROR_INPUT = "wot sounds/error.mp3"
DEFEAT = "wot sounds/losing.mp3"
VICTORY = "wot sounds/wining.mp3"
FIRE = "wot sounds/shot.mp3"
RELOAD = "wot sounds/reload.mp3"

# Text Outputs
WAITING_TO_ANOTHER = "Waiting for another player"
SERVER_DOWN = "Server shut down"
ACCOUNT_DELETED = "Admin deleted your account"
ACCOUNT_BANNED = "Admin banned your account until: "
CANT_CONNECT = "Cant connect to server"
ILLEGAL_USERNAME = "username must start with character"
INVALID_USERNAME = "invalid account change username please"
INVALID_ACCOUNT_INPUT = "invalid account input check fields please"

REGISTER_WORKED = "Registration accepted"
LOGIN_WORKED = "Login successful"
ALREADY_TAKEN = "cant login, another player use this account"
LOGIN_FAILED = "Login failed"
ENEMY_GONE = "enemy doesn't connected"
BATTLES_LOCKED = "Server forbids new battle for now"
PLAYER_WIN = "Victory"
PLAYER_LOSE = "Defeat"
PLAYER_DRAW = "Draw"

# Network
SERVER_ADDRESS = None
with open("serverhost.txt", "r") as file:
    SERVER_ADDRESS = (file.readline(), 31000)
GAME_PORT = 5120
STREAM_PORT = 32000

# Voice stream
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WIDTH = 2


class Game:
	"""
	Manages client side and all the properties of the game such like:
		->Game interface (using pygame library)
		->Encrypted Communication with the server
		->Communication with enemies while fight in battle
		->Handling Errors and exceptions from server side
		->Fights with other player and the communication with them during the fights
	"""
	
	def __init__(self, game_screen):
		self.__screen = game_screen  # the screen of pygame
		pygame.display.set_icon(pygame.image.load(LOGO))
		self.__encryption = RsaEncryption()  # the encryption used for communicate
		# with server (decryption stored here too)
		self.__input_font = pygame.font.Font(FONT, 40)  # font for player's input - username, password and color
		self.__output_font = pygame.font.Font(EVENT_FONT, 45)  # font for output and events
		# (wins, losing connection etc')
		self.__demo_player = Tank((500, 400))
		self.__demo_player.set_demo_tank_image()
		self.__client = None  # communicate with server
		self.__last_time_check_server = time.time()  # last time check if server identify
		# events (account delete/banned et'c)
		self.__account = ["", ""]
		self.__flags = [False, False]  # for ending battle
		self.__explodes = Spritesheet(EXPLODE_SHEET, (70, 70), 5, 5, (0, 0, 0))
		self.__audio = pyaudio.PyAudio()  # for audio devices
		
		# this attributes initialized during a fight
		self.__is_voice_chat_active = True  # flag for active voice chat
		self.__new_bullet = None  # new object of bullet to send to enemy
		self.__new_trap = None  # new object of trap to send to enemy
		self.__player = None  # the player's tank
		self.__player_start_pos = None
		self.__last_hp_sending_time = None
		self.__enemy = None  # the enemy's tank
		self.__enemy_start_pos = None
		self.__enemy_username = ""
		self.__enemy_ip = ""
		self.__collide_signal = ""
		self.__voice_socket = None  # socket for voice chat
		self.__enemy_socket = None  # socket for communication
		self.__traps = []  # list of the traps in map
		self.__bullets = []  # list of the bullets in map
		self.__walls = []  # list of the walls in map
	
	def make_connection_with_server(self):
		"""Sets connection with server, in addition config the encryption of the client"""
		try:
			self.__client = socket.create_connection(SERVER_ADDRESS, 3)
			self.__ip = self.__client.getsockname()[0]
			# Getting server's public key
			length = ord(self.__client.recv(1))
			self.__encryption.set_partner_public_key(
				[int(x) for x in decode(self.__client.recv(length)[::-1], 'base64').decode().split(',')])
			
			# Sending client's public key
			pk_to_send = encode(','.join([str(i) for i in self.__encryption.get_public()]).encode(), 'base64')[::-1]
			pk_to_send = chr(len(pk_to_send)).encode() + pk_to_send
			self.__client.send(pk_to_send)
			self.send_to_server(self.__ip)
			self.__client.settimeout(None)
		except (socket.error, socket.timeout):
			# cant access to server so shut down the program
			failed_output = self.__output_font.render(CANT_CONNECT, True, BLACK)
			self.__screen.blit(failed_output, [450, 250])
			pygame.display.flip()
			time.sleep(TIME_TO_WAIT)
			exit()
	
	def send_to_server(self, message_to_send):
		"""Encrypts the message and sends to server, if gets an error close the game
		parameters:
			message_to_send: type string, the message to send to server
		"""
		try:
			self.__client.send(self.__encryption.encrypt(message_to_send))
		except socket.error:
			self.server_down_protocol()
	
	def receive_from_server(self):
		"""Receives and decrypt the message from server, if gets an error close the game.
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
	
	def server_down_protocol(self):
		"""Protocol of error when try to communicate with server"""
		output = self.__output_font.render(SERVER_DOWN, True, BLACK)
		self.__screen.blit(output, [420, 250])
		pygame.display.flip()
		self.__client.close()
		time.sleep(2)
		exit()
	
	def keep_alive(self):
		"""Checks if server is down or user's account is now invalid
		close the game is so, or if server is down"""
		if time.time() - self.__last_time_check_server >= 3:  # check's every 3 seconds
			rlist, _, _ = select([self.__client], [], [], 0)
			if self.__client in rlist:
				length = self.__client.recv(1).decode()
				if length == "":  # server is gone
					self.server_down_protocol()
				respond = self.__encryption.decrypt(self.__client.recv(ord(length)).decode())
				if "@" in respond:  # client's account deleted
					self.__flags[0] = True
					output = self.__output_font.render(ACCOUNT_DELETED, True, BLACK)
					self.__screen.blit(output, [330, 200])
					pygame.display.flip()
					self.__client.close()
					time.sleep(2)
					exit()
				elif "!" in respond:  # client's account banned
					self.__flags[0] = True
					length = self.__client.recv(1).decode()
					bandate = self.__encryption.decrypt(self.__client.recv(ord(length)).decode())
					output = self.__output_font.render(ACCOUNT_BANNED + bandate, True, BLACK)
					self.__screen.blit(output, [150, 200])
					pygame.display.flip()
					time.sleep(2)
					exit()
			self.__last_time_check_server = time.time()  # update last time of checking
	
	def get_input_from_user(self, current_data, events, limit_data_len, filter1, filter2=lambda x: False):
		"""add the input from the player to the current data - (account buffers or color rgb values)
		parameters:
			previous_data: type str, the current data
			events: type pygame.event, the events from keyboard, mouse etc'
			limit data len: type int, the length limit of the data
			filter1: type function, if can add that char to previous_data
			filter2: type function, is need to remove last char from current data from some reason
		returns:
			string, the current data
			boolean, if need to keep collecting
			boolean, if need to refresh the screen (because the input is different now)
		"""
		is_need_refresh = False
		for event in events:
			if event.type == pygame.QUIT:
				self.send_to_server("exit")
				self.__client.close()
				exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					return current_data, None, False
				if filter1(event.unicode):
					if len(current_data) < limit_data_len:
						current_data += event.unicode
						is_need_refresh = True
					else:
						pygame.mixer.music.load(ERROR_INPUT)
						pygame.mixer.music.play()
						pygame.event.clear()
					if filter2(current_data):
						current_data = current_data[:-1]
				elif (event.key == pygame.K_BACKSPACE) and (len(current_data) > 0):
					current_data = current_data[:-1]
					is_need_refresh = True
				elif event.key == pygame.K_RETURN:
					if current_data == "":
						return "", True, is_need_refresh
					else:
						return current_data, True, is_need_refresh
				else:
					pygame.mixer.music.load(ERROR_INPUT)  # not must
					pygame.mixer.music.play()
					pygame.event.clear()
		return current_data, False, is_need_refresh
	
	def home_screen(self):
		"""The home screen of the game, player can get to the menu screen
		 only if he signs in
		"""
		home_screen = pygame.image.load(MAIN_SCREEN).convert()
		self.__screen.blit(home_screen, [0, 0])
		pygame.display.flip()
		self.make_connection_with_server()
		while True:
			self.keep_alive()
			events = pygame.event.get()
			for event in events:
				if event.type == pygame.QUIT:
					self.send_to_server("exit")
					self.__client.close()
					exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.send_to_server("exit")
						self.__client.close()
						exit()
					elif event.key == pygame.K_l:  # player login
						self.__account = self.register_and_login_screen(True)
						if self.__account != ["", ""]:
							return
						self.__screen.blit(home_screen, [0, 0])
						pygame.display.flip()
					elif event.key == pygame.K_s:  # player signs up
						self.__account = self.register_and_login_screen(False)
						if self.__account != ["", ""]:
							return
						self.__screen.blit(home_screen, [0, 0])
						pygame.display.flip()
	
	def register_and_login_screen(self, is_login_now):
		"""Gets the data from the user (username and password), continue recursively
		 until a valid account is assigned to the client or until client is quit.
		 stores the new account's data in account attribute
		parameters:
			is_login_now: type boolean, flag of if player try to login or sign_up
		"""
		pointer_to_entry = pygame.image.load(POINTER).convert()
		if is_login_now:
			connection_screen = pygame.image.load(LOGIN_SCREEN).convert()
		else:
			connection_screen = pygame.image.load(SIGN_UP_SCREEN).convert()
		self.__screen.blit(connection_screen, [0, 0])
		pygame.display.flip()
		for i in range(len(self.__account)):
			is_need_refresh = True
			pointer_pos = ENTRIES_POINTER_POS[i]
			while True:
				self.keep_alive()
				if is_need_refresh:  # refresh the screen
					self.__screen.blit(connection_screen, [0, 0])
					self.__screen.blit(pointer_to_entry, pointer_pos)
					for index in range(2):
						account_field_pos = CONNECTING_INPUT_FIELD_POS[index]
						account_field_input = self.__input_font.render(self.__account[index], True, KELLY)
						self.__screen.blit(account_field_input, account_field_pos)
				pygame.display.flip()
				events = pygame.event.get()
				self.__account[i], is_end_collecting, is_need_refresh = self.get_input_from_user(
					self.__account[i], events, 10, self.legal_chars_for_username_and_password)
				if is_end_collecting is None:  # if player went back to home screen
					self.__account = ["", ""]
					return self.__account
				if is_end_collecting:  # end collect data for the current entry
					break
		if not self.take_care_connection_cases(is_login_now):
			pygame.event.clear()
			self.__account = self.register_and_login_screen(is_login_now)
		return self.__account
	
	@staticmethod
	def legal_chars_for_username_and_password(data):
		"""filter for username and password data in account"""
		return data.isdigit() or (data in ascii_letters)
	
	def take_care_connection_cases(self, is_login_now=False):
		"""Takes care of every case of signing up or login to valid username
		parameters:
			is_login_now: type boolean, flag of if player tries to login or register
		returns:
			boolean, is the client gets permission for using the asked account
		"""
		msg_pos = 100, 500
		output = ""
		if len(self.__account[0]) > 0 and not self.__account[0][
			0].isalpha():  # username must start with alphabetical letter
			output = self.__input_font.render(ILLEGAL_USERNAME, True, BLUE)
			self.__screen.blit(output, msg_pos)
			pygame.display.flip()
			time.sleep(TIME_TO_WAIT)
			return False
		
		legal_case = False
		if is_login_now:
			self.send_to_server("login " + self.__account[0] + "," + self.__account[1])
			respond = self.receive_from_server()
			if respond == "O":  # Ok
				output = self.__input_font.render(LOGIN_WORKED, True, GREEN)
				legal_case = True
			elif respond == "B":  # Ban
				date = self.receive_from_server()
				output = self.__input_font.render(ACCOUNT_BANNED + date, True, RED)
			elif respond == "T":  # Taken
				output = self.__input_font.render(ALREADY_TAKEN, True, RED)
			elif respond == "F":  # Failed
				output = self.__input_font.render(LOGIN_FAILED, True, RED)
		else:
			self.send_to_server("Signup " + self.__account[0] + "," + self.__account[1])
			respond = self.receive_from_server()
			if respond == "Y":  # account is registered in server databases
				output = self.__input_font.render(REGISTER_WORKED, True, GREEN)
				legal_case = True
			elif respond == "N":  # account is invalid
				output = self.__input_font.render(INVALID_USERNAME, True, RED)
			elif respond == "P":
				output = self.__input_font.render(INVALID_ACCOUNT_INPUT, True, RED)
				
		self.__screen.blit(output, msg_pos)
		pygame.display.flip()
		time.sleep(TIME_TO_WAIT)
		return legal_case
	
	def menu_screen(self):
		"""manage the game - (color, start a fight etc'), but first need to connect to an account - (from home screen)"""
		self.home_screen()
		menu_screen = pygame.image.load(MENU_SCREEN).convert()
		self.__screen.blit(menu_screen, [0, 0])
		self.__screen.blit(self.__output_font.render("Hello " + self.__account[0], True, WHITE), [50, 130])
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.send_to_server("exit")
					self.__client.close()
					exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.send_to_server("exit")
						self.__client.close()
						exit()
					
					elif event.key == pygame.K_s:  # player looks for a match
						mode_code = self.choose_battle_mode()
						if mode_code is not None:
							self.battle_start(mode_code)
						self.__screen.blit(menu_screen, (0, 0))
						self.__screen.blit(self.__output_font.render("Hello " + self.__account[0],
						                                             True, WHITE), [50, 130])
						pygame.display.flip()
					
					elif event.key == pygame.K_i:  # introductions of the game
						self.instructions_screen()
						self.__screen.blit(menu_screen, (0, 0))
						self.__screen.blit(self.__output_font.render("Hello " + self.__account[0],
						                                             True, WHITE), [50, 130])
						pygame.display.flip()
					
					elif event.key == pygame.K_c:  # players want to change his tank's color
						self.colors_screen()
						self.__screen.blit(menu_screen, (0, 0))
						self.__screen.blit(self.__output_font.render("Hello " + self.__account[0],
						                                             True, WHITE), [50, 130])
						pygame.display.flip()
					
					elif event.key == pygame.K_r:  # player wants to get information about his rating
						self.rating_screen()
						self.__screen.blit(menu_screen, (0, 0))
						self.__screen.blit(self.__output_font.render("Hello " + self.__account[0],
						                                             True, WHITE), [50, 130])
						pygame.display.flip()
				
				pygame.event.clear()
	
	def colors_screen(self):
		"""Builds the new color of the player as list values of rgb (red, green, blue)
		stores the value inside the demo tan, In addition the user can re-build other color
		or go back to the last saved version
		"""
		self.ask_for_color()
		rainbow_screen = pygame.image.load(COLOR_SCREEN).convert()
		self.__screen.blit(rainbow_screen, [0, 0])
		my_color = ["0", "0", "0"]
		for i in range(len(my_color)):
			my_color[i] = ""
			is_need_refresh = True
			while True:
				self.keep_alive()
				if is_need_refresh:  # refresh the screen
					self.__screen.blit(rainbow_screen, [0, 0])
					for index in range(3):
						color_pos = RGB_VALUES_POS[index]
						self.__screen.blit(self.__input_font.render(my_color[index],
						                                            True, WHITE), color_pos)
					self.__screen.blit(self.__demo_player.get_image(), self.__demo_player.get_loc())
					pygame.display.flip()
				
				events = pygame.event.get()
				my_color[i], is_end_collecting, is_need_refresh = self.get_input_from_user(my_color[i],
				                                                                            events, 3, str.isdigit,
				                                                                            self.limit_color_value)
				if is_end_collecting is None:
					return
				if is_end_collecting:
					if my_color[i] == "":
						my_color[i] = "0"
					break
		self.__demo_player.change_player_color([int(x) for x in my_color])  # store the final color in demo tank
		self.__screen.blit(self.__demo_player.get_image(), self.__demo_player.get_loc())
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.send_to_server("exit")
					exit()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return
					if event.key == pygame.K_t:  # player want to re-select color
						return self.colors_screen()
					if event.key == pygame.K_d:
						my_new_color = "%02x%02x%02x" % tuple(self.__demo_player.get_color())
						self.send_to_server("SetColor " + my_new_color)
						return
	
	@staticmethod
	def limit_color_value(data):
		"""filter of max value for element in rgb - player's color"""
		return int(data) > 255
	
	def ask_for_color(self):
		"""Asks the server for the player's colors, set the color in the demo tank"""
		self.send_to_server("GetColor")
		color = findall("..?", self.receive_from_server())
		self.__demo_player.change_player_color([int(x, base=16) for x in color])
	
	def instructions_screen(self):
		"""Explanations about the game itself: keys, traps, special abilities etc'"""
		settings = pygame.image.load(SETTINGS_SCREEN).convert()
		self.__screen.blit(settings, [0, 0])
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.send_to_server("exit")
					self.__client.close()
					exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return
	
	def rating_screen(self):
		"""Gets the rating of the 3 current champions In addition to the rating of the
		 player himself (if he doesn't already in the top 3) from the server.
		 organize the data and display it for the user"""
		font = pygame.font.SysFont('arial', 30)
		rating_screen = pygame.image.load(SCORE_BOARD).convert()
		self.__screen.blit(rating_screen, [0, 0])
		self.send_to_server("rating")
		respond_length = int(self.receive_from_server())
		rating_packet = ""
		for _ in range(respond_length):  # rating packet arrives split, need to bind it back
			rating_packet += self.receive_from_server()
		
		information = rating_packet.split("\n")  # for be sure
		x_axis = {0: 115, 1: 325, 2: 505, 3: 685, 4: 870, 5: 1045}
		for i, element in enumerate(information):
			for j, value in enumerate(element.split(" ")):
				output = font.render(value, True, WHITE)
				self.__screen.blit(output, [x_axis[j], 120 + 40 * i])
		names = [x.split(" ")[0] for x in information]
		if names[0] == self.__account[0]:
			self.__screen.blit(font.render("Congratulations " + self.__account[0]
			                               + " you are #1", True, BLACK), [400, 300])
			self.__screen.blit(pygame.image.load(GOLD), [550, 400])
		elif len(names) >= 2 and names[1] == self.__account[0]:
			self.__screen.blit(font.render("Congratulations " + self.__account[0]
			                               + " you are #2", True, BLACK), [400, 300])
			self.__screen.blit(pygame.image.load(SILVER), [550, 400])
		elif len(names) >= 3 and names[2] == self.__account[0]:
			self.__screen.blit(font.render("Congratulations " + self.__account[0]
			                               + " you are #3", True, BLACK), [400, 300])
			self.__screen.blit(pygame.image.load(BRONZE), [550, 400])
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.send_to_server("exit")
					self.__client.close()
					exit()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return
	
	def choose_battle_mode(self):
		"""The player decides which mode he wants to play - life or time mode
		return the mode code - 0 for life mode, 1 for time mode"""
		modes_screen = pygame.image.load(CHOOSE_MODE_SCREEN).convert()
		self.__screen.blit(modes_screen, [0, 0])
		pygame.display.flip()
		while True:
			self.keep_alive()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.send_to_server("exit")
					self.__client.close()
					exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return None
					elif event.key == pygame.K_1:
						return LIFE_MODE
					elif event.key == pygame.K_2:
						return TIME_MODE
	
	def output_battle_result(self, is_win):
		"""display the result of the battle: win, lose or draw
		parameters:
			is_win: type boolean, represent the result to display:
			True for win, False for lose and None for draw"""
		if is_win:
			output = self.__output_font.render(PLAYER_WIN, True, GREEN)
		elif is_win is False:
			output = self.__output_font.render(PLAYER_LOSE, True, RED)
		else:
			output = self.__output_font.render(PLAYER_DRAW, True, BLUE)
		self.__screen.blit(output, [900, 350])
		pygame.display.flip()
	
	def major_player(self):
		"""prepare the battle's data in case the player is the major player (he is the one who started the connection)"""
		waiting = pygame.image.load(WAITING_SCREEN).convert()
		self.__screen.blit(waiting, [0, 0])
		pygame.display.flip()
		
		stream_socket = socket.socket()
		stream_socket.bind((self.__ip, STREAM_PORT))  # for voice stream
		stream_socket.listen(1)
		
		main_socket = socket.socket()
		main_socket.bind((self.__ip, GAME_PORT))  # for game communicate
		main_socket.listen(1)
		
		self.__player_start_pos, self.__enemy_start_pos = self.prepare_battle()
		if self.__player_start_pos is None or self.__player_start_pos is False:
			self.clean_fight_data()
			return
		main_socket.settimeout(3.5)
		try:
			self.__enemy_socket, address = main_socket.accept()
		except socket.timeout:  # other player isn't connecting
			self.send_to_server("Cancel")
			self.clean_fight_data()
			output = self.__output_font.render(ENEMY_GONE, True, NEON)
			self.__screen.blit(output, [900, 350])
			pygame.display.flip()
			time.sleep(TIME_TO_WAIT)
			return False
		self.__enemy_ip = address[0]  # only ip address
		
		self.__enemy_socket.send(("%02x%02x%02x" % tuple(self.__demo_player.get_color())).encode())
		enemy_color = [int(x, base=16) for x in findall("..?", self.__enemy_socket.recv(6).decode())]
		
		self.__player = Tank(self.__player_start_pos,
		                     direction=6, new_color=self.__demo_player.get_color())
		self.__enemy = Tank(self.__enemy_start_pos, direction=0, new_color=enemy_color)
		
		self.__voice_socket = stream_socket.accept()[0]
		main_socket.close()
		stream_socket.close()
		return True
	
	def minor_player(self):
		"""prepare the battle's data in case the player is the minor player (he is the connector)"""
		self.__enemy_ip = self.receive_from_server()
		self.__enemy_start_pos, self.__player_start_pos = self.prepare_battle()
		if self.__player_start_pos is None or self.__player_start_pos is False:
			self.clean_fight_data()
			return False
		self.__enemy_socket = socket.socket()
		self.__enemy_socket.connect((self.__enemy_ip, GAME_PORT))
		
		self.__enemy_socket.send(("%02x%02x%02x" % tuple(self.__demo_player.get_color())).encode())
		enemy_color = [int(x, base=16) for x in findall("..?", self.__enemy_socket.recv(6).decode())]
		
		self.__player = Tank(self.__player_start_pos,
		                     direction=0, new_color=self.__demo_player.get_color())
		self.__enemy = Tank(self.__enemy_start_pos, direction=6, new_color=enemy_color)
		
		self.__voice_socket = socket.socket()
		self.__voice_socket.connect((self.__enemy_ip, STREAM_PORT))
		return True
	
	def battle_start(self, mode_code):
		"""Runs the process of the battle after finish to get the relevant data from the server
		like map information, other player's ip (in case of the being the connecting player)
		during the battle, manages its objects (bullets trap and tanks)
		while communicate with the enemy: enemy tank's data and the voice chat
		parameters:
			mode_code: type int, the code of the asked mode to send to the server
		"""
		self.ask_for_color()
		self.send_to_server("game " + str(mode_code))
		respond = self.receive_from_server()
		if respond == "#":  # Battlefields are locked
			output = self.__output_font.render(BATTLES_LOCKED, True, BLACK)
			self.__screen.blit(output, [270, 280])
			pygame.display.flip()
			time.sleep(2)
			return
		player_point = pygame.image.load(PLAYER_POINTER).convert()
		clock = pygame.time.Clock()
		
		main_player = self.receive_from_server()
		main_player = (main_player == "T")
		if main_player:
			is_start_battle = self.major_player()
		else:  # player makes connection with main player
			is_start_battle = self.minor_player()
		if not is_start_battle:
			return
		self.__enemy_socket.send(self.__account[0].encode())
		self.__enemy_username = self.__enemy_socket.recv(10).decode()
		self.__enemy_socket.settimeout(0.5)
		self.__voice_socket.settimeout(1)
		self.__player.change_player_color(self.__player.get_color())
		self.__enemy.change_player_color(self.__enemy.get_color())
		self.__last_hp_sending_time = time.time()
		
		start_battle_from = time.time()  # for time battle mode
		
		last_trap_creation_time = time.time()
		random_time_for_trap = random.randint(3, 5)
		
		threading.Thread(target=self.channeling_with_the_enemy).start()
		threading.Thread(target=self.stream_in).start()
		threading.Thread(target=self.stream_out).start()
		while not self.__flags[0]:
			self.keep_alive()
			events = pygame.event.get()
			for event in events:
				if event.type == pygame.QUIT:
					self.__flags[0] = True
					pygame.mixer.music.load(DEFEAT)
					pygame.mixer.music.play()
					self.send_to_server("exit")
					self.output_battle_result(False)
					time.sleep(TIME_TO_WAIT)
					self.__client.close()
					exit()
				
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.__flags[0] = True
						self.send_to_server("Defeat")
						pygame.mixer.music.load(DEFEAT)
						self.output_battle_result(False)
						break
					
					elif event.key == pygame.K_BACKSPACE:
						self.__is_voice_chat_active = not self.__is_voice_chat_active
					
					is_shoot, self.__new_bullet = self.__player.shoot_bullet(event, self.__bullets, -1)
					if is_shoot:
						pygame.mixer.music.load(FIRE)
						pygame.mixer.music.play()
			
			if self.__flags[0]:
				break
			
			if self.__flags[1]:  # enemy quit or disconnect
				self.send_to_server("Victory")
				self.send_to_server(self.__enemy_username)
				self.output_battle_result(True)
				pygame.mixer.music.load(VICTORY)
				break
			
			if pygame.sprite.spritecollide(self.__player, [self.__enemy], False):
				# relocate to the starting locations
				self.__collide_signal = "C"
				self.__player.lost_health(2)
				self.__enemy.lost_health(2)
				self.__player.update_loc(self.__player_start_pos[0], self.__player_start_pos[1])
			
			if main_player and time.time() - last_trap_creation_time >= random_time_for_trap:
				last_trap_creation_time, random_time_for_trap = self.create_trap()
				self.__new_trap = self.__traps[-1]
			
			if len(self.__traps) > 5:  # up to 5 traps in the map
				self.__traps.remove(self.__traps[0])
			
			for bullet in self.__bullets:
				bullet.update_loc()
				
				if pygame.sprite.spritecollide(bullet, [self.__player], False):
					self.__bullets.remove(bullet)
					self.__player.lost_health(1)
				
				elif pygame.sprite.spritecollide(bullet, [self.__enemy], False):
					self.__bullets.remove(bullet)
					self.__enemy.lost_health(1)
				
				elif pygame.sprite.spritecollide(bullet, self.__walls, False):
					bullet.hit_wall()
					if bullet.get_ttl() == 0:
						self.__bullets.remove(bullet)
			
			for trap in self.__traps:
				if pygame.sprite.spritecollide(trap, [self.__player], False):
					if self.__player.trap_affect(trap):
						pygame.mixer.music.load(BOOST)
						pygame.mixer.music.play(1)
					self.__traps.remove(trap)
				
				elif pygame.sprite.spritecollide(trap, [self.__enemy], False):
					self.__traps.remove(trap)
			
			if self.__player.get_health() <= 0:
				# player lost
				self.send_to_server("Defeat")
				self.__player.tank_destroyed(self.__screen, self.__explodes)
				self.output_battle_result(False)
				pygame.mixer.music.load(DEFEAT)
				self.__flags[0] = True
				break
			
			elif self.__enemy.get_health() <= 0:
				# player won
				self.send_to_server("Victory")
				self.send_to_server(self.__enemy_username)
				self.__enemy.tank_destroyed(self.__screen, self.__explodes)
				self.output_battle_result(True)
				pygame.mixer.music.load(VICTORY)
				self.__flags[0] = True
				break
			
			self.__player.move_tank(self.__walls)
			self.__player.is_done_infinity_ammo()
			self.__player.is_done_ghost()
			if self.__player.reload_ammo():  # only makes sound of reload when the player reloads
				pygame.mixer.music.load(RELOAD)
				pygame.mixer.music.play(2)
			
			self.prepare_for_refresh_screen()
			if self.__player.is_need_pointing():
				self.__screen.blit(player_point, [self.__player.get_loc()[0], self.__player.get_loc()[1] - 50])
			if mode_code == TIME_MODE:
				if self.take_care_time_mode(start_battle_from):  # time is up
					break
			pygame.display.flip()
			
			clock.tick(FPS_RATE)
		pygame.mixer.music.play()
		time.sleep(TIME_TO_WAIT)
		self.clean_fight_data()
	
	def clean_fight_data(self):
		"""Resets the fight members"""
		self.__last_hp_sending_time = None
		self.__enemy_username = ""
		self.__enemy = None
		self.__player = None
		self.__enemy_socket = None
		self.__voice_socket = None
		self.__enemy_ip = ""
		self.__traps = []
		self.__bullets = []
		self.__walls = []
		self.__flags = [False, False]
		self.__is_voice_chat_active = True
	
	def prepare_for_refresh_screen(self):
		"""Make arrangements for display the general data of match during
		 the fighting: hp, number of bullets etc', but don't display it yet
		  (maybe there is time mode's clock to display)"""
		output_list = [["my health:", (850, 30)], ["my ammo:", (850, 90)],
		               ["enemy health:", (850, 150)], [str(self.__player.get_health()), (1000, 33)],
		               [str(self.__enemy.get_health()), (1050, 153)],
		               [str(self.__player.get_num_bullet()) + " X", (990, 90)],
		               ["Sound:", (850, 210)]]
		self.__screen.fill(BROWN, (800, 0, 400, 600))
		self.__screen.blit(BATTLEFIELD_BACKGROUND, [0, 0])
		self.__screen.blit(BULLET, (1060, 82))
		
		if self.__is_voice_chat_active:
			self.__screen.blit(SOUND_ON, (950, 205))
		else:
			self.__screen.blit(SOUND_OFF, (950, 205))
		
		if self.__player.is_ghost_mode():
			self.__screen.blit(GHOST, (850, 270))
		for player in [self.__player, self.__enemy]:
			self.__screen.blit(player.get_image(), player.get_loc())
		for i in self.__bullets:
			self.__screen.blit(i.get_image(), i.get_loc())
		for trap in self.__traps:
			self.__screen.blit(trap.get_image(), trap.get_loc())
		for wall in self.__walls:
			wall.draw_line()
		for element in output_list:
			if output_list.index(element) == 5 and self.__player.is_infinity_ammo():  # in case of endless ammo
				self.__screen.blit(ENDLESS_AMMO, element[1])
				continue
			self.__screen.blit(self.__input_font.render(element[0], True, WHITE), element[1])
	
	def channeling_with_the_enemy(self):
		"""Manages to communication with enemy player during the fight, build and packets with
		the relevant data to the enemy: direction, location, new bullet if has been shot etc'
		if enemy quit, sets its flag so the main thread of the game would know
		"""
		clock = pygame.time.Clock()
		while not self.__flags[0]:
			packet_to_send = \
				f"D{self.__player.get_direction()}\n" \
				f"L{self.__player.get_loc()[0]},{self.__player.get_loc()[1]}\n"
			if self.__new_trap is not None:  # new trap
				packet_to_send += f"T{self.__new_trap.get_attribute()}" \
				                  f"{self.__new_trap.get_loc()[0]}.{self.__new_trap.get_loc()[1]}\n"
				self.__new_trap = None
			if self.__new_bullet is not None:
				packet_to_send += f"B{self.__new_bullet.get_direct()}\n"
				self.__new_bullet = None
			if self.__collide_signal == "C":
				packet_to_send += "C\n"
				self.__collide_signal = "O"
			if time.time() - self.__last_hp_sending_time > 2:
				self.__last_hp_sending_time = time.time()
				packet_to_send += f"H{self.__player.get_health()}"
			
			try:
				self.__enemy_socket.send((chr(len(packet_to_send))).encode()
				                         + packet_to_send.encode())
			except socket.error:
				self.__flags[1] = True  # enemy quit
				break
			rlist, _, _ = select([self.__enemy_socket], [], [], 0)
			if self.__enemy_socket in rlist:
				try:
					length = self.__enemy_socket.recv(1)
					if length == b"":  # enemy quit
						self.__flags[1] = True
						break
					else:
						enemy_data = self.__enemy_socket.recv(ord(length)).decode().split()
						self.take_care_enemy_packet(enemy_data)
				except socket.error:
					self.__flags[1] = True
					break
			clock.tick(FPS_RATE)
		self.__enemy_socket.close()
		self.__voice_socket.close()
	
	def take_care_enemy_packet(self, enemy_packet):
		"""Analyze the enemy's packets and sets the data in player's side
		parameters:
			enemy_packet: type string, the enemy's packet"""
		for header in enemy_packet:
			if "D" in header:
				self.__enemy.update_direction(int(header[1]))
			if "L" in header:
				x_pos, y_pos = header[1:].split(",")
				self.__enemy.update_loc(int(x_pos), int(y_pos))
			if "T" in header:  # new trap
				trap_attribute = header[1]
				trap_pos_x, trap_pox_y = header[2:].split(".")
				self.__traps.append(Trap(int(trap_pos_x), int(trap_pox_y), int(trap_attribute)))
			if "B" in header:  # new bullet
				self.__enemy.shoot_bullet(pygame.K_f, self.__bullets, int(header[1]))
			if "H" in header:
				self.__enemy.update_health(int(header[1:]))
			if "C" in header and self.__collide_signal != "O":  # player didn't notice a collision
				self.__player.lost_health(2)
				self.__enemy.lost_health(2)
				self.__player.update_loc(self.__player_start_pos[0], self.__player_start_pos[1])
				self.__collide_signal = ""
	
	def stream_in(self):
		"""Record the player's voice and send it to the enemy"""
		try:
			microphone = self.__audio.open(format=FORMAT, channels=CHANNELS,
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
		"""Play the data from the voice chat socket (The enemy's voice)"""
		try:
			speaker = self.__audio.open(format=FORMAT, channels=CHANNELS,
			                            rate=RATE, output=True, frames_per_buffer=CHUNK)
			while not (self.__flags[0] or self.__flags[1]):
				try:
					data = self.__voice_socket.recv(CHUNK)
					if self.__is_voice_chat_active:  # if voice chat is turned on
						speaker.write(data)
				except (IOError, socket.error):
					break
			speaker.stop_stream()
			speaker.close()
		except OSError:
			pass
	
	def prepare_battle(self):
		"""Waits until an enemy if found so server will send map's information,
		if player doesn't want to wait anymore notifies server and go back to the menu screen
		Until one of those events is happening, displays waiting screen to the player
		"""
		connect_img = pygame.image.load(WAITING_SCREEN)
		self.__screen.blit(connect_img, [0, 0])
		output = self.__input_font.render(WAITING_TO_ANOTHER + "...", True, BLACK)
		self.__screen.blit(output, [75, 520])
		pygame.display.flip()
		while True:
			rlist, _, _ = select([self.__client], [], [], 0)
			if self.__client in rlist:
				length = self.__client.recv(2)
				if length == b"":
					self.server_down_protocol()
				if length == b"##":  # new battles are invalid now
					output = self.__output_font.render(BATTLES_LOCKED, True, WHITE)
					self.__screen.blit(output, [270, 280])
					pygame.display.flip()
					time.sleep(2)
					return False, False
				length = unpack("<H", length)[0]
				all_walls, rects = self.__encryption.decrypt_map_data(self.__client.recv(length).decode())
				break
			
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.send_to_server("exit")
					self.__client.close()
					exit()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:  # player stops waiting for match
						self.send_to_server("%")
						return None, None
			self.__screen.blit(connect_img, [0, 0])
			self.refresh_waiting_screen()
		# analyzes the data of the map that was send
		all_walls = all_walls.split("\n")
		rects = [int(x) for x in findall(r"\d+", rects)]
		rects = [[rects[0]] + [rects[1]], [rects[2]] + [rects[3]]]
		for wall in all_walls:
			s_pos, e_pos = wall.split(" ")
			s_pos, e_pos = [int(x) for x in s_pos.split(",")], [int(y) for y in e_pos.split(",")]
			self.__walls.append(Wall(self.__screen, s_pos, e_pos))
		return rects
	
	def refresh_waiting_screen(self):
		"""refreshes the waiting screen"""
		output = self.__input_font.render(WAITING_TO_ANOTHER, True, BLACK)
		self.__screen.blit(output, [75, 320])
		pygame.display.flip()
		for i in range(4):
			output = self.__input_font.render("." * i, True, BLACK)
			self.__screen.blit(output, [405, 320])
			pygame.display.flip()
			time.sleep(0.3)
	
	def take_care_time_mode(self, start_time):
		"""If player is fighting in time mode, updates the game clock,
		if time is up sends the result to the server, returns true if time is up indeed
		parameters:
			start_time: type float, the moment the battle started"""
		time_to_play = SECS_TO_PLAY - (time.time() - start_time)
		if time_to_play <= 0:
			if self.__player.get_health() > self.__enemy.get_health():
				self.send_to_server("Victory")
				self.send_to_server(self.__enemy_username)
				self.output_battle_result(True)
				pygame.mixer.music.load(VICTORY)
				self.__flags[0] = True
			elif self.__player.get_health() < self.__enemy.get_health():
				self.send_to_server("Defeat")
				self.output_battle_result(False)
				pygame.mixer.music.load(DEFEAT)
				self.__flags[0] = True
			else:
				self.send_to_server("Draw")
				self.output_battle_result(None)
				pygame.mixer.music.load(DRAW)
				self.__flags[0] = True
			return True
		else:
			time_to_play = time.strftime("%M:%S", time.gmtime(time_to_play))
			self.__screen.blit(self.__input_font.render("Battle ends in: " + time_to_play, True, WHITE), [850, 270])
	
	def create_trap(self):
		"""creates a new trap in a valid location on the map"""
		x_surprise_loc = random.randint(0, 759)
		y_surprise_loc = random.randint(0, 559)
		new_surprise = Trap(x_surprise_loc, y_surprise_loc)
		while pygame.sprite.spritecollide(new_surprise,
		                                  self.__walls + self.__traps + [self.__player, self.__enemy], False):
			x_surprise_loc = random.randint(0, 759)
			y_surprise_loc = random.randint(0, 559)
			new_surprise = Trap(x_surprise_loc, y_surprise_loc)
		self.__traps.append(new_surprise)
		return time.time(), random.randint(3, 5)


def main():
	pygame.init()
	pygame.mixer.init()
	pygame.mixer.music.set_volume(1)
	screen = pygame.display.set_mode(SIZE)
	pygame.display.set_caption("War Of Tanks")
	game = Game(screen)
	game.menu_screen()


if __name__ == '__main__':
	main()
