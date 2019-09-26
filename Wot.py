import sys
import pygame
import time
import socket
import game_obj
import random
import threading
from re import findall

# --------------------------------
# author: Adi cohen
# Final project: WOT Online
# --------------------------------

# constants
pygame.init()
FONT = pygame.font.SysFont('exocet', 50)
TIME_TO_SLEEP = 1.8
TIME_TO_PREVENT_FLOW = 0.002
SIZE = (1200, 600)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
POINT_POS = ([180, 165], [180, 360])
COLOR_PACKET_LEN = 11
TICK = 60
SECS_TO_PLAY = 10  # 2:30 minutes
MAPS = "maps.txt"
BATTLE_TO_DEATH = "0"
BATTLE_ON_TIME = "1"

# screens and elements
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
SERVER_DENIED = "Server access denied, cant create a connection"
ILLEGAL_USERNAME = "username must start with character"
INVALID_USERNAME = "invalid account change username please"
REGISTER_WORKED = "Registration accepted"
LOGIN_WORKED = "Login successful"
ALREADY_TAKEN = "cant login, another player use this account"
LOGIN_FAILED = "Login failed"

# network
IP = "192.168.11.116"
PORT_S = 2020
PORT_G = 5120


def handle_enemy_packet(enemy_socket, counter, enemy, player, bullets, traps):
    try:
        msg_len = ord(enemy_socket.recv(1).decode())
        info = str(enemy_socket.recv(msg_len).decode())
        if info != "":
            if "D" in info:
                enemy.set_enemy_pointer(int(info[info.index("D") + 1]))
            if "X" in info and "Y" in info:
                x_pos, y_pos = info[info.index("X") + 1:info.index("S")].split("Y")
                enemy.update_enemy_loc(int(x_pos), int(y_pos))
            if info[info.index("S") + 1] == "1":
                enemy.shoot_bullet(pygame.K_f, bullets)
            if "T" in info:
                attr = int(info[info.index("T") + 1])
                poses = info[info.index("T") + 2:].split(",")
                x_loc_of_trap, y_loc_of_trap = [int(x) for x in poses]
                traps.append(game_obj.Surprise(x_loc_of_trap, y_loc_of_trap, attr))
            if "C" in info:
                enemy.lost_health(2)
                player.lost_health(2)
                player.hit_wall()
        counter = 0
        return False, counter
    except socket.error:
        return counter == 6, counter + 1


def channeling_with_the_enemy(enemy_socket, flags, my_packet, enemy, player, bullets, traps):
    counter = 0
    while flags[0] is False:
        is_collide = False
        if pygame.sprite.spritecollide(player, [enemy], False):
            player.lost_health(2)
            enemy.lost_health(2)
            player.hit_wall()
            is_collide = True

        try:
            packet_to_send = my_packet[0] + "S" + flags[2]
            if flags[3] is not False:
                packet_to_send += "T" + str(flags[3].get_attribute()) \
                                  + str(flags[3].get_loc()[0]) + "," + str(flags[3].get_loc()[1])
                flags[3] = False
            if is_collide:
                packet_to_send += "C"  # for enemy to change direct too
            enemy_socket.send((chr(len(packet_to_send))).encode())
            enemy_socket.send(packet_to_send.encode())
            flags[2] = "0"
            time.sleep(TIME_TO_PREVENT_FLOW)
        except socket.error:
            flags[1] = True
            enemy_socket.close()
            break

        flags[1], counter = handle_enemy_packet(enemy_socket, counter, enemy, player, bullets, traps)
        if flags[1]:
            if enemy.get_health() != 0:  # enemy disconnect because of losing the match
                print("The other play quit you win!")
            enemy_socket.close()
            break
    if flags[0]:  # if player disconnect
        enemy_socket.close()


# the game
def game_start(screen, client, demo_player, mode_code=BATTLE_TO_DEATH):
    """all the process of the game
    argument:
        account: type list, the username and password
        client: type - socket - the connection to the server
        demo_player: type - tank, for the color of the player
        size_screen_before: type - tuple, when battle start the screen size back to normal (SIZE)
        (right now it's temporary)
    """
    clock = pygame.time.Clock()
    current_size = screen.get_size()
    screen = pygame.display.set_mode(SIZE)
    battlefield = pygame.image.load(FIELD)
    walls = my_walls(screen)
    client.send(b"game" + mode_code.encode())
    main_player = int(client.recv(1).decode())
    main_player = main_player == 1
    if main_player:
        player = game_obj.Tank(20, 200, demo_player)
        enemy = game_obj.Tank(420, 50)
        waiting = pygame.image.load(CONNECT)
        screen.blit(waiting, [0, 0])
        pygame.display.flip()
        main_socket = socket.socket()
        main_socket.bind((my_ip(), PORT_G))
        main_socket.listen(1)
        another, address = main_socket.accept()
        another.send((str(demo_player.get_color()).replace(" ", '').replace("[", "").replace("]", "")).encode())
        enemy_color = another.recv(COLOR_PACKET_LEN).decode().split(",")
        main_socket.close()
    # main player create the server
    # (waiting for another one to start the game)
    else:
        address = client.recv(15).decode(), PORT_G
        player = game_obj.Tank(420, 50, demo_player)
        enemy = game_obj.Tank(20, 200)
        another = socket.socket()
        another.connect(address)
        another.send((str(demo_player.get_color()).replace(" ", '').replace("[", "").replace("]", "")).encode())
        enemy_color = another.recv(COLOR_PACKET_LEN).decode().split(",")
    # player makes connection with main player
    another.settimeout(0.5)
    enemy.change_player_color(enemy_color)
    screen.blit(battlefield, [0, 0])
    screen.blit(player.get_image(), player.get_loc())
    screen.blit(enemy.get_image(), enemy.get_loc())
    pygame.display.flip()
    start_battle_from = time.time()
    bullets = []
    traps = []
    timy = time.time()
    rund_time = random.randint(3, 5)
    player_point = pygame.image.load(MY_PLAYER_POINT).convert()
    player_point.set_colorkey(WHITE)

    flags = [False, False, "0", False]
    my_packet = ["D" + str(player.get_pointer())
                 + "X" + str(player.get_loc()[0]) + "Y" + str(player.get_loc()[1])]
    my_thread = threading.Thread(target=channeling_with_the_enemy,
                                 args=(another, flags, my_packet, enemy, player, bullets, traps))
    my_thread.start()
    while not flags[0]:
        my_packet[0] = "D" + str(player.get_pointer()) \
                       + "X" + str(player.get_loc()[0]) + "Y" + str(player.get_loc()[1])
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                flags[0] = True
                pygame.mixer.music.load(DEFEAT)
                pygame.mixer.music.play()
                client.send(b"Situ")
                time.sleep(TIME_TO_SLEEP)
                client.close()
                sys.exit()
                # exit from the game

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    flags[0] = True
                    pygame.mixer.music.load(DEFEAT)
                    client.send(b"situD")

                player.update_direct(walls, event)
                if player.shoot_bullet(event, bullets):
                    pygame.mixer.music.load(FIRE)
                    pygame.mixer.music.play()
                    flags[2] = "1"

        if flags[0] or flags[0] is None:  # none for a draw in time mode
            break

        if flags[1]:
            client.send(b"situV")
            pygame.mixer.music.load(VICTORY)
            break

        if main_player and time.time() - timy >= rund_time:
            timy, rund_time = create_trap(traps, walls, [player, enemy])
            flags[3] = traps[-1]

        if len(traps) > 4:
            traps.remove(traps[0])

        for bullet in bullets:
            bullet.update_loc()

            if pygame.sprite.spritecollide(bullet, walls, False):
                bullet.hit_wall(walls)
                if bullet.get_ttl() == 0:
                    bullets.remove(bullet)

            elif pygame.sprite.spritecollide(bullet, [player], False):
                bullets.remove(bullet)
                player.lost_health(1)

            elif pygame.sprite.spritecollide(bullet, [enemy], False):
                bullets.remove(bullet)
                enemy.lost_health(1)

        for t in traps:
            if pygame.sprite.spritecollide(t, [player], False):
                trap_affect(player, t)
                traps.remove(t)

            elif pygame.sprite.spritecollide(t, [enemy], False):
                trap_affect(enemy, t)
                traps.remove(t)

        if player.get_health() <= 0:
            flags[0] = None
            client.send(b"situD")
            pygame.mixer.music.load(DEFEAT)
            break
        elif enemy.get_health() <= 0:
            flags[0] = None
            client.send(b"situV")
            pygame.mixer.music.load(VICTORY)
            break

        if player.move_tank(walls):
            pygame.mixer.music.load(BRAKE)
            pygame.mixer.music.play()

        player.is_done_eternal_ammo()
        player.is_done_ghost()

        flip_screen(screen, [player, enemy], battlefield, bullets, traps)
        if player.is_need_pointing():
            screen.blit(player_point, [player.get_loc()[0], player.get_loc()[1] - 50])
        if mode_code == BATTLE_ON_TIME:
            if take_care_timer_of_time_mode(screen, player, enemy, flags, start_battle_from, client):
                break
        for wall in walls:
            wall.draw_line()
        pygame.display.flip()
        clock.tick(TICK)
        if player.reload_ammo():  # only makes sound of reload when the player reloads
            pygame.mixer.music.load(RELOAD)
            pygame.mixer.music.play(2)
        enemy.reload_ammo()
    pygame.mixer.music.play()
    time.sleep(TIME_TO_SLEEP)
    pygame.display.set_mode(current_size, pygame.VIDEORESIZE)


def take_care_timer_of_time_mode(screen, player, enemy, flags, start_time, client):
    time_to_play = SECS_TO_PLAY - (time.time() - start_time)
    if time_to_play <= 0:
        if player.get_health() > enemy.get_health():
            client.send(b"situV")
            pygame.mixer.music.load(VICTORY)
            flags[0] = True
            return True
        elif player.get_health() < enemy.get_health():
            client.send(b"situD")
            pygame.mixer.music.load(DEFEAT)
            flags[1] = True
            return True
        else:
            client.send(b"situE")
            pygame.mixer.music.load(DRAW)
            flags[0] = None
            return True
    else:
        time_to_play = time.strftime("%M:%S", time.gmtime(time_to_play))
        screen.blit(FONT.render(time_to_play, True, WHITE), [900, 420])


def my_walls(screen, map_code="default"):
    """build the walls of the battlefield
    argument:
        screen: pygame.surface, the battlefield
        code: type - int,
        code: type - str,
    """
    walls = []
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
                walls.append(game_obj.Wall(screen, s_pos, e_pos))
    return walls


def trap_affect(player, trap):
    """active the trap attribute on the player"""
    if trap.get_attribute() == 1:
        player.lost_health(1)
    if trap.get_attribute() == 2:
        if player.get_health() <= 29:
            player.heal_health()
    if trap.get_attribute() == 3:
        player.active_eternal_ammo_mode()
        pygame.mixer.music.load(BOOST)
        pygame.mixer.music.play(1)
    if trap.get_attribute() == 4:
        player.active_ghost_mode()
        pygame.mixer.music.load(BOOST)
        pygame.mixer.music.play(1)


def create_trap(traps, walls, players):
    """create a new mine (location is safe)
    argument:
        surprise: type - list, the all traps in the battlefield
        walls_and_players: type - list of all objects that's can block location for a new mine
    """
    x_surprise_loc = random.randint(0, 759)
    y_surprise_loc = random.randint(0, 559)
    new_surprise = game_obj.Surprise(x_surprise_loc, y_surprise_loc)
    while pygame.sprite.spritecollide(new_surprise, walls + traps + players, False):
        x_surprise_loc = random.randint(0, 759)
        y_surprise_loc = random.randint(0, 559)
        new_surprise = game_obj.Surprise(x_surprise_loc, y_surprise_loc)
    traps.append(new_surprise)
    return time.time(), random.randint(7, 12)


# screen functions - account data color etc
def legal_chars_for_username(data):
    """filter for username data in account"""
    return data.isalpha() or data.isdigit()


def register_and_login_screen(screen, account, client, is_login_now, size_screen=SIZE):
    """get the data of from the user, (username and password)
    argument:
        account: type - list, the username and password
        is_login_now: type - boolean, flag of if player try to login or register
        size_screen: type - tuple, the current size of the screen
    """
    size = size_screen
    pointer_to_bar = pygame.image.load(POINTER)
    pointer_to_bar.set_colorkey(WHITE)
    if is_login_now:
        enrollment_screen = pygame.image.load(LOGIN_SCREEN)
        photos_to_resize = [pointer_to_bar, LOGIN_SCREEN]
    else:
        enrollment_screen = pygame.image.load(REGISTER_SCREEN)
        photos_to_resize = [pointer_to_bar, REGISTER_SCREEN]
    enrollment_screen = pygame.transform.scale(enrollment_screen, size_screen)
    screen.blit(enrollment_screen, [0, 0])
    pygame.display.flip()
    for i in range(len(account)):
        point_pos = POINT_POS[i]
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode(event.dict['size'], pygame.VIDEORESIZE)
                    point_pos = calculate_new_pos(screen.get_size(), size, point_pos[0], point_pos[1])
                    enrollment_screen = pygame.transform.scale(pygame.image.load
                                                               (photos_to_resize[1]), screen.get_size())
                    size = screen.get_size()
            account[i], end_collecting = get_input_from_user(account[i], events, 20, client,
                                                             legal_chars_for_username, lambda x: False)
            if end_collecting is None:
                account = ["", ""]
                return account, size
            if end_collecting:
                break
            screen.blit(enrollment_screen, [0, 0])
            screen.blit(pointer_to_bar, point_pos)
            for index in range(len(account)):
                if account[index] != "":
                    account_pos = calculate_new_pos(size, SIZE, 300, 202 * (index + 1))
                    print_username = FONT.render(account[index], True, BLUE)
                    screen.blit(print_username, account_pos)
            pygame.display.flip()
    if not is_register_or_login(screen, account, client, size, is_login_now):
        account, size = register_and_login_screen(screen, account, client, is_login_now, size)
    return account, size


def is_register_or_login(screen, account, client, size, is_login_now=False):
    """take care of every case of registering or login to username
    argument:
        account: type - list, the username and password
        is_login_now: type - boolean, flag of if player tries to login or register
    """
    msg_pos = calculate_new_pos(size, SIZE, 300, 500)
    if not account[0][0].isalpha():
        output = FONT.render(ILLEGAL_USERNAME, True, BLUE)
        screen.blit(output, msg_pos)
        pygame.display.flip()
        time.sleep(TIME_TO_SLEEP)
        return False

    legal_case = False
    if is_login_now:
        client.send(b"login")
        client.send((account[0] + "," + account[1]).encode())
        respond = client.recv(1).decode()
        if respond == "T":
            output = FONT.render(LOGIN_WORKED, True, BLUE)
            legal_case = True
        elif respond == "N":
            output = FONT.render(ALREADY_TAKEN, True, BLUE)
        else:
            output = FONT.render(LOGIN_FAILED, True, BLUE)
    else:
        client.send(("info " + account[0] + "," + account[1]).encode())
        answer = client.recv(1).decode()
        if answer == "Y":
            output = FONT.render(REGISTER_WORKED, True, BLUE)
            legal_case = True
        else:
            output = FONT.render(INVALID_USERNAME, True, BLUE)
    screen.blit(output, msg_pos)
    pygame.display.flip()
    time.sleep(TIME_TO_SLEEP)
    return legal_case


def calculate_new_pos(size_screen, old_size, x, y):
    """Calculates the new location for output
    argument:
        size_screen: type - tuple, the current size of the screen
        x: type - int, the new rate of the x output
        y: type - int, the new rate of the y output
    """
    new_loc_x = int(round(float(x * size_screen[0] / old_size[0])))
    new_loc_y = int(round(float(y * size_screen[1] / old_size[1])))
    return new_loc_x, new_loc_y


def choose_battle_mode(screen, client):
    modes_screen = pygame.image.load(CHOOSE_MODE_SCREEN)
    screen.blit(modes_screen, [0, 0])
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.send(b"exit ")
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_1:
                    return BATTLE_TO_DEATH
                elif event.key == pygame.K_2:
                    return BATTLE_ON_TIME


def settings_screen(screen, size, client):
    """Explains the game keys, plus a way to changing player's color option"""
    settings = [pygame.transform.scale(pygame.image.load(SETTINGS_SCREEN), size),
                pygame.transform.scale(pygame.image.load(SETTINGS_SCREEN_PART_2), size)]
    time_to_exchange = time.time()
    screens = [SETTINGS_SCREEN, SETTINGS_SCREEN_PART_2]
    screen.blit(settings[0], [0, 0])
    settings[0], settings[1] = settings[1], settings[0]
    pygame.display.flip()
    while True:
        if time.time() - time_to_exchange >= 0.8:
            screen.blit(settings[0], [0, 0])
            settings[0], settings[1] = settings[1], settings[0]
            pygame.display.flip()
            time_to_exchange = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.send(b"exit ")
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.dict['size'], pygame.VIDEORESIZE)
                size = screen.get_size()
                for i in range(len(settings)):
                    settings[i] = pygame.transform.scale(pygame.image.load(screens[i]), size)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    return size


def color_choose_screen(screen, size_screen, demo_player, client):
    """build the new color of the player as list values of rgb (red, green, blue)
    argument:
        size_screen: type - tuple, the size of the screen
        demo_player: type - tank, for showing the player his tank's color"""
    size = size_screen
    rainbow_screen = pygame.transform.scale(pygame.image.load(COLOR_SCREEN), size)
    demo_player_pos = calculate_new_pos(size, SIZE, demo_player.get_loc()[0], demo_player.get_loc()[1])
    demo_player.update_enemy_loc(demo_player_pos[0], demo_player_pos[1])
    screen.blit(rainbow_screen, [0, 0])
    my_color = ["", "", ""]
    for i in range(len(my_color)):
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode(event.dict['size'], pygame.VIDEORESIZE)
                    rainbow_screen = pygame.transform.scale(pygame.image.load(COLOR_SCREEN), screen.get_size())
                    demo_player_pos = calculate_new_pos(screen.get_size(),
                                                        size, demo_player.get_loc()[0], demo_player.get_loc()[1])
                    demo_player.update_enemy_loc(demo_player_pos[0], demo_player_pos[1])
                    size = screen.get_size()
            my_color[i], end_collecting = get_input_from_user(my_color[i], events,
                                                              3, client, str.isdigit, limit_color_value)
            if end_collecting is None:
                return size
            if end_collecting:
                break
            screen.blit(rainbow_screen, [0, 0])
            for element in range(len(my_color)):
                color_pos = calculate_new_pos(size, SIZE, 200 + 300 * element, 310)
                show_color = FONT.render(my_color[element], True, WHITE)
                screen.blit(show_color, color_pos)
            screen.blit(demo_player.get_image(), demo_player.get_loc())
            pygame.display.flip()
        if my_color[i] == "":
            my_color[i] = "0"
    # in case that not value has been received
    color_pos = calculate_new_pos(size, SIZE, 200 + 300 * 2, 310)
    show_color = FONT.render(my_color[2], True, WHITE)
    screen.blit(show_color, color_pos)
    demo_player.change_player_color(my_color)
    screen.blit(demo_player.get_image(), demo_player.get_loc())
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.send(b"exit ")
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.dict['size'], pygame.VIDEORESIZE)
                rainbow_screen = pygame.transform.scale(rainbow_screen, screen.get_size())
                screen.blit(rainbow_screen, [0, 0])
                demo_player_pos = calculate_new_pos(screen.get_size(), size,
                                                    demo_player.get_loc()[0], demo_player.get_loc()[1])
                demo_player.update_enemy_loc(demo_player_pos[0], demo_player_pos[1])
                screen.blit(demo_player.get_image(), demo_player.get_loc())
                for i in range(len(my_color)):
                    color_pos = calculate_new_pos(screen.get_size(), SIZE, 200 + 300 * i, 310)
                    show_color = FONT.render(str(my_color[i]), True, WHITE)
                    screen.blit(show_color, color_pos)
                size = screen.get_size()
                pygame.display.flip()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    return color_choose_screen(screen, size, demo_player, client)
                if event.key == pygame.K_d:
                    client.send(b"Color")
                    my_new_color = "%02x%02x%02x" % tuple(demo_player.get_color())
                    client.send(str("".join(my_new_color)).encode())
                    return size


def limit_color_value(data):
    """filter of max value for element in rgb - player's color"""
    return int(data) > 255


def get_input_from_user(previous_data, events, limit_data, client, filter1, filter2):
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
            if limit_data == 3:
                client.send(b"exit ")
            else:
                client.send(b"Exit ")
            sys.exit()
        if event.type == pygame.KEYDOWN:
            try:
                if event.key == pygame.K_ESCAPE:
                    return previous_data, None
                if filter1(event.unicode):
                    if len(previous_data) < limit_data:
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
            except UnicodeEncodeError:
                pygame.mixer.music.load(ERROR_INPUT)
                pygame.mixer.music.play()
                pygame.event.clear()
    return previous_data, False


def flip_screen(screen, players, zone, ammo, traps):
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
                   ["enemy health:", (850, 245)], [str(players[0].get_health()), (1000, 70)],
                   [str(players[1].get_health()), (1000, 285)], [str(players[0].get_num_bullet()) + " X", (950, 170)]]
    screen.fill(BLUE)
    screen.blit(zone, [0, 0])
    screen.blit(bullet, (1030, 160))
    if players[0].get_is_ghost_mode():
        ghost_icon = pygame.image.load(GHOST).convert()
        ghost_icon.set_colorkey(WHITE)
        screen.blit(ghost_icon, (900, 350))
    for player in players:
        screen.blit(player.get_image(), player.get_loc())
    for i in ammo:
        screen.blit(i.get_image(), i.get_loc())
    for trap in traps:
        screen.blit(trap.get_image(), trap.get_loc())
    for element in output_list:
        if output_list.index(element) == 5 and players[0].get_is_eternal_ammo_mode():  # in case of endless ammo
            endless_ammo = pygame.image.load(ENDLESS_AMMO).convert()
            endless_ammo.set_colorkey(WHITE)
            screen.blit(endless_ammo, element[1])
            continue
        screen.blit(FONT.render(element[0], True, WHITE), element[1])


def my_ip():
    """return my current ip in string"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.0.0.8', 1027))
    except socket.error:
        return None
    return s.getsockname()[0]


def try_connect_to_server(client):
    """return if client success to connect the game server
        argument:
            client - type: socket
    """
    client.settimeout(2)
    while True:
        try:
            client.connect((IP, PORT_S))
            return True
        except socket.error:
            return False
        finally:
            client.settimeout(None)


def get_account(screen, account):
    size = SIZE
    main_s = pygame.image.load(MAIN_SCREEN)
    client = socket.socket()
    is_connect = False
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                if is_connect:
                    client.send(b"Exit ")
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.dict['size'], pygame.VIDEORESIZE)
                size = screen.get_size()
                main_s = pygame.transform.scale(pygame.image.load(MAIN_SCREEN), size)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if is_connect:
                        client.send(b"Exit ")
                    sys.exit()
                elif event.key == pygame.K_l or event.key == pygame.K_r:
                    if not is_connect:
                        if try_connect_to_server(client):
                            is_connect = True
                            if event.key == pygame.K_l:
                                account, size = register_and_login_screen(screen, account, client, True, size)
                                main_s = pygame.transform.scale(pygame.image.load(MAIN_SCREEN), size)

                            else:
                                account, size = register_and_login_screen(screen, account, client, False, size)
                                main_s = pygame.transform.scale(pygame.image.load(MAIN_SCREEN), size)
                        else:
                            failed_output = FONT.render(SERVER_DENIED, True, RED)
                            output_pos = calculate_new_pos(size, SIZE, 100, 500)
                            screen.blit(failed_output, output_pos)
                            pygame.display.flip()
                            time.sleep(TIME_TO_SLEEP)
                            pygame.event.clear()
                    else:
                        if event.key == pygame.K_l:
                            account, size = register_and_login_screen(screen, account, client, True, size)
                            main_s = pygame.transform.scale(pygame.image.load(MAIN_SCREEN), size)

                        else:
                            account, size = register_and_login_screen(screen, account, client, False, size)

        if account != ["", ""]:
            return size, account, client
        screen.blit(main_s, [0, 0])
        pygame.display.flip()


def main():
    """the main screen and management of all the game"""
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode(SIZE, pygame.VIDEORESIZE)
    pygame.display.set_caption("War Of Tanks")
    demo_player = game_obj.Tank(500, 400)
    demo_player.set_demo_tank_image(pygame.transform.scale(demo_player.get_image(), [100, 100]))
    size, account, client = get_account(screen, ["", ""])
    menu_screen = pygame.image.load(MENU_SCREEN)
    client.send(b"color")
    saved_color = findall("..?", client.recv(6).decode())
    demo_player.change_player_color([int(x, base=16) for x in saved_color])
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.send(b"exit ")
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode(event.dict['size'], pygame.VIDEORESIZE)
                size = screen.get_size()
                menu_screen = pygame.transform.scale(pygame.image.load(MENU_SCREEN), size)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    mode_code = choose_battle_mode(screen, client)
                    if mode_code is not None:
                        game_start(screen, client, demo_player, mode_code)

                elif event.key == pygame.K_ESCAPE:
                    client.send(b"exit ")
                    sys.exit()

                elif event.key == pygame.K_i:
                    size = settings_screen(screen, size, client)
                    menu_screen = pygame.transform.scale(pygame.image.load(MENU_SCREEN), size)

                elif event.key == pygame.K_c:
                    size = color_choose_screen(screen, size, demo_player, client)
                    menu_screen = pygame.transform.scale(pygame.image.load(MENU_SCREEN), size)
            pygame.event.clear()
        screen.blit(menu_screen, (0, 0))
        pygame.display.flip()


if __name__ == '__main__':
    main()
