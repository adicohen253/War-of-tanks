import sys
import pygame
import time
import socket
import game_obj
import random
import threading
import pyaudio
from re import findall

# --------------------------------
# author: Adi cohen
# Final project: WOT Online
# --------------------------------

# constants
pygame.init()
TIME_TO_WAIT = 1.8
TIME_TO_PREVENT_FLOW = 0.002
SIZE = (1200, 600)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
POINT_POS = ([180, 165], [180, 360])
COLOR_PACKET_LEN = 11
ASKED_IP_LEN_PACKET = 15
TICK = 60
SECS_TO_PLAY = 150  # 2:30 minutes
MAPS = "maps.txt"
BATTLE_TO_DEATH = "0"
BATTLE_ON_TIME = "1"

# screens and widgets
POINTER = "pointer.png"
REGISTER_SCREEN = "register.png"
LOGIN_SCREEN = "login.png"
COLOR_SCREEN = "colors.jpg"
SETTINGS_SCREEN = "settings.jpg"
SETTINGS_SCREEN_PART_2 = "settings1.jpg"
MAIN_SCREEN = "Main.png"
MENU_SCREEN = "menu.jpg"
CHOOSE_MODE_SCREEN = "modes.png"
CONNECT = "connect.jpg"
FIELD = "zone.png"
GHOST = "ghost.png"
ENDLESS_AMMO = "Endless_Ammo.png"
MY_PLAYER_POINT = "player_point.png"

# sounds
DRAW = 'draw.mp3'
BOOST = "boost.mp3"
ERROR_INPUT = "error.mp3"
DEFEAT = "losing.mp3"
VICTORY = 'wining.mp3'
FIRE = 'shot.mp3'
BRAKE = 'brake.mp3'
RELOAD = 'reload.mp3'

# messages
ACCOUNT_BANNED = "This account banned until: "
SERVER_DENIED = "Server access denied, cant create a connection"
ILLEGAL_USERNAME = "username must start with character"
INVALID_USERNAME = "invalid account change username please"
REGISTER_WORKED = "Registration accepted"
LOGIN_WORKED = "Login successful"
ALREADY_TAKEN = "cant login, another player use this account"
LOGIN_FAILED = "Login failed"

# network
IP = "192.168.1.20"
SERVER_PORT = 2020
GAME_PORT = 5120
STREAM_OUTPUT_PORT = 32000

# voice stream
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WIDTH = 2


class Game:
    def __init__(self, screen):
        self.__screen = screen
        self.__ip = ""
        self.__font = pygame.font.SysFont('arial', 35)
        self._my_ip()
        self.__demo_player = game_obj.Tank(500, 400)
        self.__demo_player.set_demo_tank_image(pygame.transform.scale(self.__demo_player.get_image(), [100, 100]))
        self.__client = socket.socket()
        self.__account = ["", ""]
        self._get_account()

        # game start and it's functions manage these attributes
        self.__enemy = None
        self.__player = None
        self.__enemy_socket = None
        self.__enemy_ip = ""
        self.__traps = []
        self.__bullets = []
        self.__walls = []

    def _my_ip(self):
        """return my current ip in string"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('192.0.0.8', 1027))
        except socket.error:
            return None
        self.__ip = s.getsockname()[0]

    def _try_connect_to_server(self):
        """return if client success to connect the game server
            argument:
                client - type: socket
        """
        self.__client.settimeout(2)
        while True:
            try:
                self.__client.connect((IP, SERVER_PORT))
                return True
            except socket.error:
                return False
            finally:
                self.__client.settimeout(None)

    def _send_to_server(self, message_to_send):
        try:
            self.__client.send(message_to_send)
        except socket.error:
            sys.exit()

    def _receive_from_server(self, buffersize):
        try:
            message = self.__client.recv(buffersize).decode()
            if message == "":
                raise socket.error
            if "@" in message:
                self.__client.close()
                sys.exit()
            return message
        except socket.error:
            self.__client.close()
            sys.exit()

    def _get_my_color(self):
        self._send_to_server(b"color")
        saved_color = findall("..?", self._receive_from_server(6))
        self.__demo_player.change_player_color([int(x, base=16) for x in saved_color])

    def _get_account(self):
        main_s = pygame.image.load(MAIN_SCREEN)
        is_connect = False
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    if is_connect:
                        self._send_to_server(b"Exit ")  # already has connection with server
                    self.__client.close()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if is_connect:
                            self._send_to_server(b"Exit ")
                        self.__client.close()
                        sys.exit()
                    elif event.key == pygame.K_l or event.key == pygame.K_r:
                        if not is_connect:
                            if self._try_connect_to_server():
                                is_connect = True
                                if event.key == pygame.K_l:
                                    self.__account = self._register_and_login_screen(True)

                                else:
                                    self.__account = self._register_and_login_screen(False)
                            else:
                                failed_output = self.__font.render(SERVER_DENIED, True, RED)
                                self.__screen.blit(failed_output, [100, 500])
                                pygame.display.flip()
                                time.sleep(TIME_TO_WAIT)
                                pygame.event.clear()
                        else:
                            if event.key == pygame.K_l:
                                self.__account = self._register_and_login_screen(True)

                            else:
                                self.__account = self._register_and_login_screen(False)
            if self.__account != ["", ""]:
                return
            self.__screen.blit(main_s, [0, 0])
            pygame.display.flip()

    def _register_and_login_screen(self, is_login_now):
        """get the data of from the user, (username and password)
        argument:
            account: type - list, the username and password
            is_login_now: type - boolean, flag of if player try to login or register
            size_screen: type - tuple, the current size of the screen
        """
        pointer_to_bar = pygame.image.load(POINTER)
        pointer_to_bar.set_colorkey(WHITE)
        if is_login_now:
            enrollment_screen = pygame.image.load(LOGIN_SCREEN)
        else:
            enrollment_screen = pygame.image.load(REGISTER_SCREEN)
        self.__screen.blit(enrollment_screen, [0, 0])
        pygame.display.flip()
        for i in range(len(self.__account)):
            point_pos = POINT_POS[i]
            while True:
                events = pygame.event.get()
                self.__account[i], end_collecting = \
                    self._get_input_from_user(self.__account[i], events, 10,
                                              legal_chars_for_username_and_password)
                if end_collecting is None:
                    self.__account = ["", ""]
                    return self.__account
                if end_collecting:
                    break
                self.__screen.blit(enrollment_screen, [0, 0])
                self.__screen.blit(pointer_to_bar, point_pos)
                for index in range(len(self.__account)):
                    if self.__account[index] != "":
                        account_pos = 300, 202 * (index + 1)
                        print_username = self.__font.render(self.__account[index], True, BLUE)
                        self.__screen.blit(print_username, account_pos)
                pygame.display.flip()
        if not self._take_care_connection_cases(is_login_now):
            self.__account = self._register_and_login_screen(is_login_now)
            return self.__account

    def _take_care_connection_cases(self, is_login_now=False):
        """take care of every case of registering or login to username
        argument:
            account: type - list, the username and password
            is_login_now: type - boolean, flag of if player tries to login or register
        """
        msg_pos = 100, 500
        if not self.__account[0][0].isalpha():  # username must start with alphabetical letter
            output = self.__font.render(ILLEGAL_USERNAME, True, BLUE)
            self.__screen.blit(output, msg_pos)
            pygame.display.flip()
            time.sleep(TIME_TO_WAIT)
            return False

        legal_case = False
        if is_login_now:
            self._send_to_server(("login" + self.__account[0] + "," + self.__account[1]).encode())
            respond = self._receive_from_server(1)
            if respond == "O":  # Ok
                output = self.__font.render(LOGIN_WORKED, True, BLUE)
                legal_case = True
            elif respond == "B":
                date, hour = self._receive_from_server(16).split(" ")
                output = self.__font.render(ACCOUNT_BANNED + date + "  in " + hour, True, BLUE)
            elif respond == "T":  # Taken
                output = self.__font.render(ALREADY_TAKEN, True, BLUE)
            else:  # Failed
                output = self.__font.render(LOGIN_FAILED, True, BLUE)
        else:
            self._send_to_server(("info " + self.__account[0] + "," + self.__account[1]).encode())
            answer = self._receive_from_server(1)
            if answer == "Y":
                output = self.__font.render(REGISTER_WORKED, True, BLUE)
                legal_case = True
            else:
                output = self.__font.render(INVALID_USERNAME, True, BLUE)
        self.__screen.blit(output, msg_pos)
        pygame.display.flip()
        time.sleep(TIME_TO_WAIT)
        return legal_case

    def _color_choose_screen(self):
        """build the new color of the player as list values of rgb (red, green, blue)
        argument:
            size_screen: type - tuple, the size of the screen
            demo_player: type - tank, for showing the player his tank's color"""
        self._get_my_color()
        rainbow_screen = pygame.image.load(COLOR_SCREEN)
        self.__screen.blit(rainbow_screen, [0, 0])
        my_color = ["0", "0", "0"]
        for i in range(len(my_color)):
            my_color[i] = ""
            finish = False
            while not finish:
                events = pygame.event.get()
                my_color[i], end_collecting = self._get_input_from_user(my_color[i], events,
                                                                        3, str.isdigit, limit_color_value)
                if end_collecting is None:
                    return
                if end_collecting:
                    if my_color[i] == "":
                        my_color[i] = "0"
                    finish = True
                self.__screen.blit(rainbow_screen, [0, 0])
                for element in range(len(my_color)):
                    color_pos = 200 + 300 * element, 310
                    show_color = self.__font.render(my_color[element], True, WHITE)
                    self.__screen.blit(show_color, color_pos)
                self.__screen.blit(self.__demo_player.get_image(), self.__demo_player.get_loc())
                pygame.display.flip()
        self.__demo_player.change_player_color(my_color)
        self.__screen.blit(self.__demo_player.get_image(), self.__demo_player.get_loc())
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._send_to_server(b"exit ")
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        return self._color_choose_screen()
                    if event.key == pygame.K_d:
                        self._send_to_server(b"Color")
                        my_new_color = "%02x%02x%02x" % tuple(self.__demo_player.get_color())
                        self._send_to_server(str("".join(my_new_color)).encode())
                        self._receive_from_server(1)
                        return

    def _get_input_from_user(self, previous_data, events, limit_data_len, filter1, filter2=lambda x: False):
        """add the input from the player to the current data status - (account color etc),
        plus change the size of the screen.
        argument:
            screen_image: string, the name of the image file of the current screen image
            previous_data: type -  str, the current data
            events: type - pygame.event, all the input from the user
            limit_data: type - str, the limit length that data can be
            filter1: type - function, if can add that char to previous_data
            filter2: type - function, if there is need to remove last char from previous_data from some reason
        """
        for event in events:
            if event.type == pygame.QUIT:
                if self.__account != ["", ""]:
                    # in color choose screen, there is already account to disconnect from
                    self._send_to_server(b"exit ")
                else:
                    self._send_to_server(b"Exit ")
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

    def _settings_screen(self):
        """Explains the game keys, plus a way to changing player's color option"""
        settings = [pygame.image.load(SETTINGS_SCREEN),
                    pygame.image.load(SETTINGS_SCREEN_PART_2)]
        time_to_exchange = time.time()
        self.__screen.blit(settings[0], [0, 0])
        settings[0], settings[1] = settings[1], settings[0]
        pygame.display.flip()
        finish = False
        while not finish:
            if time.time() - time_to_exchange >= 0.8:
                self.__screen.blit(settings[0], [0, 0])
                settings[0], settings[1] = settings[1], settings[0]
                pygame.display.flip()
                time_to_exchange = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._send_to_server(b"exit ")
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        finish = True

    def game_manager(self):
        """after connect to a user, this function manage the game - (color, introductions etc)"""
        menu_screen = pygame.image.load(MENU_SCREEN)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._send_to_server(b"exit ")
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:  # player look for a match
                        mode_code = self._choose_battle_mode()
                        if mode_code is not None:
                            self._battle_start(mode_code)

                    elif event.key == pygame.K_ESCAPE:
                        self._send_to_server(b"exit ")
                        sys.exit()

                    elif event.key == pygame.K_i:  # introductions of game's buttons
                        self._settings_screen()

                    elif event.key == pygame.K_c:  # player want to change his tank's color
                        self._color_choose_screen()
                pygame.event.clear()
            self.__screen.blit(menu_screen, (0, 0))
            pygame.display.flip()

    def _choose_battle_mode(self):
        modes_screen = pygame.image.load(CHOOSE_MODE_SCREEN)
        self.__screen.blit(modes_screen, [0, 0])
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._send_to_server(b"exit ")
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_1:
                        return BATTLE_TO_DEATH
                    elif event.key == pygame.K_2:
                        return BATTLE_ON_TIME

    def _battle_start(self, mode_code=BATTLE_TO_DEATH):
        """all the process of the game
        argument:
            account: type list, the username and password
            client: type - socket - the connection to the server
            demo_player: type - tank, for the color of the player
            size_screen_before: type - tuple, when battle start the screen size back to normal (SIZE)
            (right now it's temporary)
        """
        self._get_my_color()
        clock = pygame.time.Clock()
        battlefield = pygame.image.load(FIELD)
        self._my_walls()
        self._send_to_server(b"game" + mode_code.encode())
        finish_stream = [False]
        player_point = pygame.image.load(MY_PLAYER_POINT).convert()
        player_point.set_colorkey(WHITE)

        main_player = self._receive_from_server(5)
        main_player = (main_player == "True")
        if main_player:
            self.__player = game_obj.Tank(20, 200, self.__demo_player)
            self.__enemy = game_obj.Tank(420, 50)
            waiting = pygame.image.load(CONNECT)
            self.__screen.blit(waiting, [0, 0])
            pygame.display.flip()
            main_socket = socket.socket()
            main_socket.bind((self.__ip, GAME_PORT))
            main_socket.listen(1)
            self.__enemy_socket, address = main_socket.accept()
            self.__enemy_ip = address[0]  # only ip address
            self.__enemy_socket.send((str(self.__demo_player.get_color())
                                      .replace(" ", '').replace("[", "").replace("]", "")).encode())
            enemy_color = self.__enemy_socket.recv(COLOR_PACKET_LEN).decode().split(",")
            main_socket.close()
            threading.Thread(target=self.voice_stream_creator, args=([finish_stream])).start()
        # main player create the server
        # (waiting for another one to start the game)
        else:
            self.__enemy_ip = self._receive_from_server(ASKED_IP_LEN_PACKET)
            self.__player = game_obj.Tank(420, 50, self.__demo_player)
            self.__enemy = game_obj.Tank(20, 200)
            self.__enemy_socket = socket.socket()
            self.__enemy_socket.connect((self.__enemy_ip, GAME_PORT))
            self.__enemy_socket.send((str(self.__demo_player.get_color())
                                      .replace(" ", '').replace("[", "").replace("]", "")).encode())
            enemy_color = self.__enemy_socket.recv(COLOR_PACKET_LEN).decode().split(",")
            threading.Thread(target=self.voice_stream_connector, args=([finish_stream])).start()
        # player makes connection with main player
        self.__enemy_socket.settimeout(0.5)
        self.__enemy.change_player_color(enemy_color)
        self.__screen.blit(battlefield, [0, 0])
        self.__screen.blit(self.__player.get_image(), self.__player.get_loc())
        self.__screen.blit(self.__enemy.get_image(), self.__enemy.get_loc())
        pygame.display.flip()

        start_battle_from = time.time()
        last_trap_moment = time.time()
        random_time_for_trap = random.randint(3, 5)
        flags = [False, False, False, "0"]
        my_packet = ["D" + str(self.__player.get_pointer())
                     + "X" + str(self.__player.get_loc()[0]) + "Y" + str(self.__player.get_loc()[1])]
        threading.Thread(target=self._channeling_with_the_enemy,
                         args=(flags, my_packet)).start()
        while not flags[0]:
            my_packet[0] = "D" + str(self.__player.get_pointer()) \
                           + "X" + str(self.__player.get_loc()[0]) + "Y" + str(self.__player.get_loc()[1])
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    flags[0] = True
                    pygame.mixer.music.load(DEFEAT)
                    pygame.mixer.music.play()
                    self._send_to_server(b"Situ")
                    time.sleep(TIME_TO_WAIT)
                    self.__client.close()
                    sys.exit()
                    # exit from the game

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        flags[0] = True
                        pygame.mixer.music.load(DEFEAT)
                        self._send_to_server(b"situL")
                        self._receive_from_server(1)

                    self.__player.update_direct(self.__walls, event)
                    if self.__player.shoot_bullet(event, self.__bullets):
                        pygame.mixer.music.load(FIRE)
                        pygame.mixer.music.play()
                        flags[3] = "1"

            if flags[0] or flags[0] is None:  # already send to server the result of match
                # None when battle ends as well
                break

            if flags[1]:
                self._send_to_server(b"situW")
                self._receive_from_server(1)
                pygame.mixer.music.load(VICTORY)
                break

            if main_player and time.time() - last_trap_moment >= random_time_for_trap:
                last_trap_moment, random_time_for_trap = self._create_trap()
                flags[2] = self.__traps[-1]

            if len(self.__traps) > 4:
                self.__traps.remove(self.__traps[0])

            for bullet in self.__bullets:
                bullet.update_loc()

                if pygame.sprite.spritecollide(bullet, self.__walls, False):
                    bullet.hit_wall(self.__walls)
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
                flags[0] = None
                self._send_to_server(b"situL")
                self._receive_from_server(1)
                pygame.mixer.music.load(DEFEAT)
                break
            elif self.__enemy.get_health() <= 0:
                flags[0] = None
                self._send_to_server(b"situW")
                self._receive_from_server(1)
                pygame.mixer.music.load(VICTORY)
                break

            if self.__player.move_tank(self.__walls):
                pygame.mixer.music.load(BRAKE)
                pygame.mixer.music.play()

            self.__player.is_done_eternal_ammo()
            self.__player.is_done_ghost()

            self._flip_screen(battlefield)
            if self.__player.is_need_pointing():
                self.__screen.blit(player_point, [self.__player.get_loc()[0], self.__player.get_loc()[1] - 50])
            if mode_code == BATTLE_ON_TIME:
                if self._take_care_timer_of_time_mode(flags, start_battle_from):
                    break
            for wall in self.__walls:
                wall.draw_line()
            pygame.display.flip()
            clock.tick(TICK)
            if self.__player.reload_ammo():  # only makes sound of reload when the player reloads
                pygame.mixer.music.load(RELOAD)
                pygame.mixer.music.play(2)
        pygame.mixer.music.play()
        time.sleep(TIME_TO_WAIT)
        finish_stream[0] = True  # end of stream
        self.__enemy = None
        self.__player = None
        self.__enemy_socket.close()
        self.__enemy_socket = None
        self.__enemy_ip = ""
        self.__traps = []
        self.__bullets = []
        self.__walls = []

    def _flip_screen(self, zone):
        """shows all the data of the surface (pixels) plus the data of the players
        argument:
            players: type - list of tanks,(player and enemy)
            zone: type - surface, the image of the field
            ammo: type - list of bullets, all the bullets in the field
            traps: all the mines in the battlefield
        """
        bullet = pygame.image.load(game_obj.BULLET).convert()
        bullet.set_colorkey(WHITE)
        bullet = pygame.transform.scale(bullet, (50, 50))
        # constants of UI to battle screen":
        output_list = [["my health:", (850, 30)], ["my ammo:", (850, 120)],
                       ["enemy health:", (850, 245)], [str(self.__player.get_health()), (1000, 70)],
                       [str(self.__enemy.get_health()), (1000, 285)],
                       [str(self.__player.get_num_bullet()) + " X", (950, 170)]]
        self.__screen.fill(BLUE)
        self.__screen.blit(zone, [0, 0])
        self.__screen.blit(bullet, (1030, 160))
        if self.__player.get_is_ghost_mode():
            ghost_icon = pygame.image.load(GHOST).convert()
            ghost_icon.set_colorkey(WHITE)
            self.__screen.blit(ghost_icon, (900, 350))
        for player in [self.__player, self.__enemy]:
            self.__screen.blit(player.get_image(), player.get_loc())
        for i in self.__bullets:
            self.__screen.blit(i.get_image(), i.get_loc())
        for trap in self.__traps:
            self.__screen.blit(trap.get_image(), trap.get_loc())
        for element in output_list:
            if output_list.index(element) == 5 and self.__player.get_is_eternal_ammo_mode():  # in case of endless ammo
                endless_ammo = pygame.image.load(ENDLESS_AMMO).convert()
                endless_ammo.set_colorkey(WHITE)
                self.__screen.blit(endless_ammo, element[1])
                continue
            self.__screen.blit(self.__font.render(element[0], True, WHITE), element[1])

    def _channeling_with_the_enemy(self, flags, my_packet):
        counter = 0
        while flags[0] is False:
            is_collide = False
            if pygame.sprite.spritecollide(self.__player, [self.__enemy], False):
                self.__player.lost_health(2)
                self.__enemy.lost_health(2)
                self.__player.hit_wall()
                is_collide = True

            try:
                packet_to_send = my_packet[0] + "S" + flags[3]
                if flags[2] is not False:  # run if there is a new trap
                    packet_to_send += "T" + str(flags[2].get_attribute()) \
                                      + str(flags[2].get_loc()[0]) + "," + str(flags[2].get_loc()[1])
                    flags[2] = False
                if is_collide:
                    packet_to_send += "C"  # flag to enemy if there was a collapse
                self.__enemy_socket.send((chr(len(packet_to_send))).encode())
                self.__enemy_socket.send(packet_to_send.encode())
                flags[3] = "0"
                time.sleep(TIME_TO_PREVENT_FLOW)
            except socket.error:
                flags[1] = True
                self.__enemy_socket.close()
                break

            flags[1], counter = self._take_care_enemy_packet(counter)
            if flags[1]:
                self.__enemy_socket.close()
                break
        if flags[0]:  # if player disconnect
            self.__enemy_socket.close()

    def _take_care_enemy_packet(self, counter):
        try:
            msg_len = ord(self.__enemy_socket.recv(1).decode())
            info = str(self.__enemy_socket.recv(msg_len).decode())
            if info != "":
                if "D" in info:
                    self.__enemy.set_enemy_pointer(int(info[info.index("D") + 1]))
                if "X" in info and "Y" in info:
                    x_pos, y_pos = info[info.index("X") + 1:info.index("S")].split("Y")
                    self.__enemy.update_enemy_loc(int(x_pos), int(y_pos))
                if info[info.index("S") + 1] == "1":
                    self.__enemy.shoot_bullet(pygame.K_f, self.__bullets)
                if "T" in info:
                    attr = int(info[info.index("T") + 1])
                    poses = info[info.index("T") + 2:].split(",")
                    x_loc_of_trap, y_loc_of_trap = [int(x) for x in poses]
                    self.__traps.append(game_obj.Surprise(x_loc_of_trap, y_loc_of_trap, attr))
                if "C" in info:
                    self.__enemy.lost_health(2)
                    self.__player.lost_health(2)
                    self.__player.hit_wall()
            counter = 0
            return False, counter
        except socket.error:
            return counter == 6, counter + 1
        except TypeError:  #
            return True, 0

    def voice_stream_connector(self, finish_game):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.__enemy_ip, STREAM_OUTPUT_PORT))
        p = pyaudio.PyAudio()
        while not finish_game[0]:
            try:
                stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
                while not finish_game[0]:
                    try:
                        data = stream.read(CHUNK)
                        s.sendall(data)
                    except IOError:
                        break
                stream.stop_stream()
                stream.close()
                p.terminate()
            except OSError:
                time.sleep(3)
        s.close()

    def voice_stream_creator(self, finish_game):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.__ip, STREAM_OUTPUT_PORT))
        s.listen(1)
        p = pyaudio.PyAudio()
        client, address = s.accept()
        while not finish_game[0]:
            try:
                stream = p.open(format=p.get_format_from_width(WIDTH), channels=CHANNELS,
                                rate=RATE, output=True, frames_per_buffer=CHUNK)
                while not finish_game[0]:
                    try:
                        stream.write(client.recv(CHUNK))
                    except IOError:
                        break

                stream.stop_stream()
                stream.close()
                p.terminate()
                client.close()
            except OSError:
                time.sleep(3)
        s.close()

    def _my_walls(self, map_code="default"):
        """build the walls of the battlefield
        argument:
            screen: pygame.surface, the battlefield
            screen: pygame.surface, the battlefield
            code: type - int,
            code: type - str,
        """
        found = False
        with open(MAPS, "r") as my_maps:
            all_maps = [m.split("\n" * 2) for m in my_maps.read().split("\n" * 3)[:-1]]
            for element in all_maps:
                if element[0] == map_code:
                    all_walls = element[1].split("\n")
                    found = True
            if found:
                for wall in all_walls:
                    s_pos, e_pos = wall.split(" ")
                    s_pos, e_pos = [int(x) for x in s_pos.split(",")], [int(y) for y in e_pos.split(",")]
                    self.__walls.append(game_obj.Wall(self.__screen, s_pos, e_pos))

    def _take_care_timer_of_time_mode(self, flags, start_time):
        time_to_play = SECS_TO_PLAY - (time.time() - start_time)
        if time_to_play <= 0:
            if self.__player.get_health() > self.__enemy.get_health():
                self._send_to_server(b"situW")
                self._receive_from_server(1)
                pygame.mixer.music.load(VICTORY)
                flags[0] = True
                return True
            elif self.__player.get_health() < self.__enemy.get_health():
                self._send_to_server(b"situL")
                self._receive_from_server(1)
                pygame.mixer.music.load(DEFEAT)
                flags[1] = True
                return True
            else:
                self._send_to_server(b"situE")
                self._receive_from_server(1)
                pygame.mixer.music.load(DRAW)
                flags[0] = None
                return True
        else:
            time_to_play = time.strftime("%M:%S", time.gmtime(time_to_play))
            self.__screen.blit(self.__font.render(time_to_play, True, WHITE), [900, 420])

    def _trap_affect(self, trap, myself):
        """active the trap attribute on the player"""
        if myself:
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
        new_surprise = game_obj.Surprise(x_surprise_loc, y_surprise_loc)
        while pygame.sprite.spritecollide(new_surprise,
                                          self.__walls + self.__traps + [self.__player, self.__enemy], False):
            x_surprise_loc = random.randint(0, 759)
            y_surprise_loc = random.randint(0, 559)
            new_surprise = game_obj.Surprise(x_surprise_loc, y_surprise_loc)
        self.__traps.append(new_surprise)
        return time.time(), random.randint(3, 5)


# filter for getting input from user in color and connect screens
def legal_chars_for_username_and_password(data):
    """filter for username data in account"""
    return data.isdigit() or (data.isalpha() and ((0x61 <= ord(data) <= 0x7a) or (0x41 <= ord(data) <= 0x5a)))


def limit_color_value(data):
    """filter of max value for element in rgb - player's color"""
    return int(data) > 255


def main():
    pygame.mixer.init()
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("War Of Tanks")
    game = Game(screen)
    game.game_manager()


if __name__ == '__main__':
    main()
