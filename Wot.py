import sys
import pygame
import time
import socket
import game_obj
import random
import threading
import pyaudio
import string
from re import findall

# --------------------------------
# author: Adi cohen
# Final project: WOT Online
# --------------------------------

# constants
pygame.init()
TIME_TO_WAIT = 1.3
SIZE = (1200, 600)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
POINT_POS = ([180, 165], [180, 360])
ASKED_IP_LEN_PACKET = 15
FPS_RATE = 50
PACKET_SENDING_RATE = 60
SECS_TO_PLAY = 150  # 2:30 minutes
BATTLE_TO_DEATH = 0
BATTLE_ON_TIME = 1

# screens and widgets
POINTER = "project images/pointer.png"
REGISTER_SCREEN = "project images/register.png"
LOGIN_SCREEN = "project images/login.png"
COLOR_SCREEN = "project images/colors.jpg"
SETTINGS_SCREEN = "project images/settings.jpg"
SETTINGS_SCREEN_PART_2 = "project images/settings1.jpg"
MAIN_SCREEN = "project images/Main.jpg"
MENU_SCREEN = "project images/menu.jpg"
CHOOSE_MODE_SCREEN = "project images/modes.png"
CONNECT = "project images/connect.jpg"
FIELD = "project images/zone.png"
GHOST = "project images/ghost.png"
ENDLESS_AMMO = "project images/Endless_Ammo.png"
MY_PLAYER_POINT = "project images/player_point.png"

# sounds
DRAW = "project sounds/draw.mp3"
BOOST = "project sounds/boost.mp3"
ERROR_INPUT = "project sounds/error.mp3"
DEFEAT = "project sounds/losing.mp3"
VICTORY = "project sounds/wining.mp3"
FIRE = "project sounds/shot.mp3"
BRAKE = "project sounds/brake.mp3"
RELOAD = "project sounds/reload.mp3"

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
SERVER_PORT = 2020
GAME_PORT = 5120
STREAM_PORT = 32000

# voice stream
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WIDTH = 2


class Game:
    def __init__(self, screen, ip):
        self.__screen = screen
        self.__ip = my_ip()
        self.server_ip = ip
        self.__font = pygame.font.SysFont('arial', 35)
        self.__demo_player = game_obj.Tank(500, 400)
        self.__demo_player.set_demo_tank_image(pygame.transform.scale(self.__demo_player.get_image(), [100, 100]))
        self.__client = socket.socket()
        self.__account = ["", ""]
        self._get_account()

        # game start and it's functions manage these attributes
        self.__flags = [False, False]
        self.__p = pyaudio.PyAudio()
        self.__is_collide_happened = False
        self.__new_bullet = None
        self.__new_trap = None
        self.__enemy = None
        self.__player = None
        self.__stream_socket = None
        self.__enemy_socket = None
        self.__enemy_ip = ""
        self.__traps = []
        self.__bullets = []
        self.__walls = []

    def _try_connect_to_server(self):
        """return if client success to connect the game server
            argument:
                client - type: socket
        """
        self.__client.settimeout(2)
        while True:
            try:
                self.__client.connect((self.server_ip, SERVER_PORT))
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
            if "@" in message:  # the account deleted from the server
                self.__client.close()
                print("your account deleted from server...")
                time.sleep(TIME_TO_WAIT)
                sys.exit()
            return message
        except socket.error:
            print("server shut down...")
            self.__client.close()
            time.sleep(TIME_TO_WAIT)
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
            pygame.event.clear()
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
            elif respond == "B":  # Ban
                date, hour = self._receive_from_server(16).split(" ")
                output = self.__font.render(ACCOUNT_BANNED + date + "  in " + hour, True, BLUE)
            elif respond == "T":  # Taken
                output = self.__font.render(ALREADY_TAKEN, True, BLUE)
            else:  # Failed
                output = self.__font.render(LOGIN_FAILED, True, BLUE)
        else:
            self._send_to_server(("regis" + self.__account[0] + "," + self.__account[1]).encode())
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
        self.__flags = [False, False]
        self._get_my_color()
        battlefield = pygame.image.load(FIELD)
        self._send_to_server(b"game" + str(mode_code).encode())
        player_point = pygame.image.load(MY_PLAYER_POINT).convert()
        player_point.set_colorkey(WHITE)
        clock = pygame.time.Clock()
        main_player = self._receive_from_server(1)
        main_player = (main_player == "T")
        if main_player:
            waiting = pygame.image.load(CONNECT)
            self.__screen.blit(waiting, [0, 0])
            pygame.display.flip()

            stream_socket = socket.socket()
            stream_socket.bind((self.__ip, STREAM_PORT))  # for voice stream
            stream_socket.listen(1)

            main_socket = socket.socket()
            main_socket.bind((self.__ip, GAME_PORT))  # for game communicate
            main_socket.listen(1)

            self._receive_from_server(15)  # server found an enemy
            self._send_to_server(b"Ok")
            self.__enemy_socket, address = main_socket.accept()
            self.__enemy_ip = address[0]  # only ip address
            self.__enemy_socket.send(("%02x%02x%02x" % tuple(self.__demo_player.get_color())).encode())
            enemy_color = [int(x, base=16) for x in findall("..?", self.__enemy_socket.recv(6).decode())]
            self.__player = game_obj.Tank(20, 200, direct=6, new_color=self.__demo_player.get_color())
            self.__enemy = game_obj.Tank(420, 50, direct=2, new_color=enemy_color)

            self.__stream_socket = stream_socket.accept()[0]
            main_socket.close()
            stream_socket.close()
        # main player create the server
        # (waiting for another one for starting the game)

        else:  # player makes connection with main player
            self.__enemy_ip = self._receive_from_server(ASKED_IP_LEN_PACKET)
            self.__enemy_socket = socket.socket()
            self.__enemy_socket.connect((self.__enemy_ip, GAME_PORT))
            self.__enemy_socket.send(("%02x%02x%02x" % tuple(self.__demo_player.get_color())).encode())
            enemy_color = [int(x, base=16) for x in findall("..?", self.__enemy_socket.recv(6).decode())]
            self.__player = game_obj.Tank(420, 50, direct=2, new_color=self.__demo_player.get_color())
            self.__enemy = game_obj.Tank(20, 200, direct=6, new_color=enemy_color)

            self.__stream_socket = socket.socket()
            self.__stream_socket.connect((self.__enemy_ip, STREAM_PORT))

        self.__enemy_socket.settimeout(0.5)
        self.__enemy.change_player_color(enemy_color)
        self.__screen.blit(battlefield, [0, 0])
        self.__screen.blit(self.__player.get_image(), self.__player.get_loc())
        self.__screen.blit(self.__enemy.get_image(), self.__enemy.get_loc())
        pygame.display.flip()
        self._my_walls()

        start_battle_from = time.time()  # for time battle mode

        last_trap_moment = time.time()
        random_time_for_trap = random.randint(3, 5)

        threading.Thread(target=self._channeling_with_the_enemy).start()
        threading.Thread(target=self.stream_in).start()
        threading.Thread(target=self.stream_out).start()

        while not self.__flags[0]:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.__flags[0] = True
                    pygame.mixer.music.load(DEFEAT)
                    pygame.mixer.music.play()
                    self._send_to_server(b"Situ")
                    time.sleep(TIME_TO_WAIT)
                    self.__client.close()
                    sys.exit()
                    # exit from the game

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.__flags[0] = True
                        pygame.mixer.music.load(DEFEAT)
                        self._send_to_server(b"situL")
                        self._receive_from_server(1)

                    self.__player.update_direct(self.__walls, event)
                    is_shoot, self.__new_bullet = self.__player.shoot_bullet(event, self.__bullets)
                    if is_shoot:
                        pygame.mixer.music.load(FIRE)
                        pygame.mixer.music.play()

            if self.__flags[0]:
                break

            if self.__flags[1]:
                pygame.mixer.music.load(VICTORY)
                break

            if pygame.sprite.spritecollide(self.__player, [self.__enemy], False):
                self.__is_collide_happened = True
                self._send_to_server(b"situE")
                self._receive_from_server(1)
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
                self.__flags[0] = True
                self._send_to_server(b"situL")
                self._receive_from_server(1)
                pygame.mixer.music.load(DEFEAT)
                break

            elif self.__enemy.get_health() <= 0:
                self.__flags[0] = True
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
                self._take_care_time_mode(start_battle_from)
            for wall in self.__walls:
                wall.draw_line()
            pygame.display.flip()
            if self.__player.reload_ammo():  # only makes sound of reload when the player reloads
                pygame.mixer.music.load(RELOAD)
                pygame.mixer.music.play(2)

            clock.tick(FPS_RATE)

        pygame.mixer.music.play()
        time.sleep(TIME_TO_WAIT)

        self.__enemy = None
        self.__player = None
        self.__times_of_collapse = 0
        self.__enemy_socket.close()
        self.__enemy_socket = None
        self.__stream_socket.close()
        self.__stream_socket = None
        self.__enemy_ip = ""
        self.__traps = []
        self.__bullets = []
        self.__walls = []
        self.is_collide_happened = False

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

    def _channeling_with_the_enemy(self):
        clock = pygame.time.Clock()
        counter = 0
        while not self.__flags[0]:
            clock.tick(PACKET_SENDING_RATE)
            packet_to_send = \
                f"D{self.__player.get_pointer()}\n" \
                f"L{self.__player.get_loc()[0]},{self.__player.get_loc()[1]}\n"
            if self.__new_trap is not None:  # new trap
                packet_to_send += f"T{self.__new_trap.get_attribute()}" \
                                  f"{self.__new_trap.get_loc()[0]}.{self.__new_trap.get_loc()[1]}\n"
                self.__new_trap = None
            if self.__new_bullet is not None:
                packet_to_send += f"B{self.__new_bullet.get_first_lunch_direct()}\n"
                self.__new_bullet = None
            if self.__is_collide_happened:
                packet_to_send += "C\n"
                self.__flags[0] = True
            try:
                self.__enemy_socket.send((chr(len(packet_to_send))).encode())
                self.__enemy_socket.send(packet_to_send.encode())
            except socket.error:  # enemy player quit
                self.__flags[1] = True
                self._send_to_server(b"situW")
                self._receive_from_server(1)
                break

            self.__flags[1], counter = self._take_care_enemy_packet(counter)
            if self.__flags[1]:  # enemy player doesn't responding
                self._send_to_server(b"situW")
                self._receive_from_server(1)
                break
            time.sleep(0.02)
        self.__enemy_socket.close()

    def _take_care_enemy_packet(self, counter):
        try:
            msg_len = self.__enemy_socket.recv(1).decode()
            if msg_len == "":
                raise socket.error  # other player quit
            msg_len = ord(msg_len)
            info = str(self.__enemy_socket.recv(msg_len).decode()).split()
            for header in info:
                if "D" in header:
                    self.__enemy.set_enemy_pointer(int(header[1]))
                if "L" in header:
                    x_pos, y_pos = header[1:].split(",")
                    self.__enemy.update_enemy_loc(int(x_pos), int(y_pos))
                if "T" in header:
                    trap_attribute = header[1]
                    trap_pos_x, trap_pox_y = header[2:].split(".")
                    self.__traps.append(game_obj.Trap(int(trap_pos_x), int(trap_pox_y), int(trap_attribute)))
                if "B" in header:
                    first_direct_after_collapse_wall = header[1]
                    self.__enemy.shoot_bullet(pygame.K_f, self.__bullets, first_direct_after_collapse_wall)
                if ("C" in header) and not self.__is_collide_happened:
                    self._send_to_server(b"situE")
                    self._receive_from_server(1)
                    pygame.mixer.music.load(DRAW)
                    self.__flags[0] = True
            return False, 0
        except socket.error:
            return counter == 6, counter + 1

    def stream_in(self):
        try:
            microphone = self.__p.open(format=FORMAT, channels=CHANNELS,
                                       rate=RATE, input=True, frames_per_buffer=CHUNK)
            while not (self.__flags[0] or self.__flags[1]):
                try:
                    self.__stream_socket.send(microphone.read(CHUNK))
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
                    speaker.write(self.__stream_socket.recv(CHUNK))
                except (IOError, socket.error):
                    break
            speaker.stop_stream()
            speaker.close()
        except OSError:
            pass

    def _my_walls(self, map_code="<>-default"):
        self._send_to_server(map_code.encode())
        all_walls = self._receive_from_server(1024).split("\n")
        for wall in all_walls:
            s_pos, e_pos = wall.split(" ")
            s_pos, e_pos = [int(x) for x in s_pos.split(",")], [int(y) for y in e_pos.split(",")]
            self.__walls.append(game_obj.Wall(self.__screen, s_pos, e_pos))

    def _take_care_time_mode(self, start_time):
        time_to_play = SECS_TO_PLAY - (time.time() - start_time)
        if time_to_play <= 0:
            if self.__player.get_health() > self.__enemy.get_health():
                self._send_to_server(b"situW")
                self._receive_from_server(1)
                pygame.mixer.music.load(VICTORY)
                self.__flags[0] = True
            elif self.__player.get_health() < self.__enemy.get_health():
                self._send_to_server(b"situL")
                self._receive_from_server(1)
                pygame.mixer.music.load(DEFEAT)
                self.__flags[1] = True
            else:
                self._send_to_server(b"situE")
                self._receive_from_server(1)
                pygame.mixer.music.load(DRAW)
                self.__flags[0] = True
        else:
            time_to_play = time.strftime("%M:%S", time.gmtime(time_to_play))
            self.__screen.blit(self.__font.render(time_to_play, True, WHITE), [900, 420])

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
        new_surprise = game_obj.Trap(x_surprise_loc, y_surprise_loc)
        while pygame.sprite.spritecollide(new_surprise,
                                          self.__walls + self.__traps + [self.__player, self.__enemy], False):
            x_surprise_loc = random.randint(0, 759)
            y_surprise_loc = random.randint(0, 559)
            new_surprise = game_obj.Trap(x_surprise_loc, y_surprise_loc)
        self.__traps.append(new_surprise)
        return time.time(), random.randint(3, 5)


# filter for getting input from user in color and connect screens
def legal_chars_for_username_and_password(data):
    """filter for username data in account"""
    return data.isdigit() or (data in string.ascii_letters)


def limit_color_value(data):
    """filter of max value for element in rgb - player's color"""
    return int(data) > 255


def my_ip():
    """return my local current ip in string"""
    return socket.gethostbyname(socket.gethostname())


def main():
    pygame.mixer.init()
    pygame.mixer.music.set_volume(1)
    ip = input("enter server ip: ")
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("War Of Tanks")
    game = Game(screen, ip)
    game.game_manager()


if __name__ == '__main__':
    main()
