import threading
import socket
import time
from firebase import firebase
from os import listdir
from tkinter import *
from sqlite3 import *
from tkinter.font import *
from tkinter.ttk import Combobox, Treeview
from requests.exceptions import ConnectionError

FONT = ("Arial", 10, NORMAL)
API_SIZE = '1050x600'

INSTALLER_FILE = "game installer.exe"
HTTP_RESPONSE_OK = b"""HTTP/1.1 200 OK
Content-Type: zip; charset=utf-8
Content-Disposition: attachment; filename=War of tanks.exe
Connection: keep-alive

"""
HTTP_RESPONSE_NOT_FOUND = b"""HTTP/1.1 404 NOT FOUND
"""
HTTP_RESPONSE_FORBIDDEN = b"""HTTP/1.1 403 FORBIDDEN
"""
MAX_NUM_DAY_IN_MONTHS = {"01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30,
                         "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31}

FIREBASE_URL = "https://my-project-b9bb8.firebaseio.com/"


class Account:
    def __init__(self, username, password, wins, loses, draws, color,
                 bandate, firebase_token):
        self.__username = username
        self.__password = password
        self.__wins = wins
        self.__loses = loses
        self.__draws = draws
        self.__favorite_color = color
        self.__arena_number = 0
        self.__ban_string = bandate
        self.__ban_struct = None
        self.__firebase_token = firebase_token
        self.set_ban_until_struct()
        if self.__ban_string != "00/00/0000 00:00":
            self.__client_status = "Ban"
        else:
            self.__client_status = "Off"

    def set_ban_until_struct(self):
        date, hour = self.__ban_string.split(" ")
        day, month, year = [int(element) for element in date.split("/")]
        hour = int(hour[:2])
        self.__ban_struct = time.struct_time((year, month, day, hour, 0, 0, 0, 0, 0))

    def player_online(self):
        self.__client_status = "On"

    def player_offline(self):
        self.__client_status = "Off"

    def get_client_status(self):
        return self.__client_status

    def get_username(self):
        return self.__username

    def get_password(self):
        return self.__password

    def get_win(self):
        return self.__wins

    def get_loses(self):
        return self.__loses

    def get_draws(self):
        return self.__draws

    def get_color(self):
        return self.__favorite_color

    def get_arena_number(self):
        return self.__arena_number

    def get_ban_string(self):
        return self.__ban_string

    def get_ban_struct(self):
        return self.__ban_struct

    def get_firebase_token(self):
        return self.__firebase_token

    def set_arena_number(self, new_arena_number):
        self.__arena_number = new_arena_number

    def clean_data(self):
        self.__wins = 0
        self.__loses = 0
        self.__draws = 0
        self.__favorite_color = "ff0000"
        self.__ban_string = "00/00/0000 00:00"
        self.__ban_struct = time.struct_time((0, 0, 0, 0, 0, 0, 0, 0, 0))
        if self.__client_status == "Ban":
            self.__client_status = "Off"

    def set_ban_until(self, new_date):
        self.__ban_string = new_date
        self.set_ban_until_struct()
        self.__client_status = "Ban"

    def erase_ban(self):
        self.__ban_string = "00/00/0000 00:00"
        self.__ban_struct = time.struct_time((0, 0, 0, 0, 0, 0, 0, 0, 0))
        self.__client_status = "Off"

    def add_win(self):
        self.__wins += 1

    def add_lose(self):
        self.__loses += 1

    def add_draws(self):
        self.__draws += 1

    def change_color(self, newcolor):
        self.__favorite_color = newcolor

    def __str__(self):
        return f"{self.__username} {self.__password} " \
               f"{self.__wins} {self.__loses} {self.__draws} " \
               f"{self.__favorite_color} {self.__client_status} " \
               f"{self.__ban_string} {self.__arena_number}"


class Server:
    DEATH_MODE = 0
    TIME_MODE = 1

    def __init__(self):
        self.__ip = my_ip()
        self.__server_socket = socket.socket()
        self.__server_socket.bind((self.__ip, 2020))
        self.__server_socket.listen(1)
        self.__server_socket.settimeout(0.2)
        self.__fire = firebase.FirebaseApplication(FIREBASE_URL, None)
        self.__is_online_database = False
        self.__accounts_list = []
        self.build_my_accounts()
        self.__accounts_updates_to_table = []
        self.__stop_running = False

        self.__death_battle_ip = ""
        self.__death_battle_arena = 0
        self.__death_battle_creator = None

        self.__time_battle_ip = ""
        self.__time_battle_arena = 0
        self.__time_battle_creator = None

    def build_my_accounts(self):
        try:
            data = [x for x in self.__fire.get('/Accounts', '').items()]
            for element in data:
                firebase_token = element[0]
                username, password = element[1]['Username'], element[1]['Password']
                wins, loses, draws = element[1]['Wins'], element[1]['Loses'], element[1]['Draws']
                color, bandate = element[1]['Color'], element[1]['Bandate']
                self.__accounts_list.append(Account(username, password, wins, loses,
                                                    draws, color, bandate, firebase_token))
            self.__is_online_database = True
            return
        except ConnectionError:
            pass
        conn = connect("my database.db")
        curs = conn.cursor()
        curs.execute("UPDATE Flags set 'Offline update' = 1")
        conn.commit()
        curs.execute("SELECT * FROM Accounts")
        data = [list(x) for x in curs.fetchall()]
        accounts_list = []
        for acc in data:
            accounts_list.append(Account(acc[0], acc[1], acc[2],
                                         acc[3], acc[4], acc[5], acc[6], acc[7]))
        accounts_list.sort(key=lambda x: x.get_username())
        return accounts_list

    def active(self):
        for index in range(10):
            threading.Thread(target=self.help_player, args=([index])).start()
        threading.Thread(target=self.update_users_data).start()
        threading.Thread(target=self.is_ban_date_passed).start()
        self.create_server_screen()
        self.__stop_running = True
        self.__server_socket.close()

    def create_server_screen(self):
        window = Tk()
        window.geometry(API_SIZE)
        window.title("My server")
        window.resizable(OFF, OFF)
        window.configure(background='azure')
        Label(window, text="My IP is: " + self.__ip, fg='blue',
              bg='white', borderwidth=5, relief=SUNKEN).place(x=850, y=30)

        # Admin options's widgets
        lf = LabelFrame(window, font=FONT, text="Admin interface:")
        lf.place(x=0, y=0, width=750, height=200)

        user, password = StringVar(), StringVar()
        day, month = StringVar(value="day"), StringVar(value="month")
        year, hour = StringVar(value="year"), StringVar(value="hour")
        Label(lf, text="Username:", font=FONT).place(x=20, y=10)
        Entry(lf, textvariable=user).place(x=125, y=15)

        Label(lf, text="Password:", font=FONT).place(x=20, y=50)
        Entry(lf, textvariable=password).place(x=125, y=55)

        Label(lf, text="Date:", font=FONT).place(x=300, y=10)
        Label(lf, text='Hour:', font=FONT).place(x=300, y=45)
        Combobox(lf, state='readonly', takefocus=OFF, width=4, textvariable=day,
                 values=["day"] + [f"0{x}" if x < 10 else x for x in range(1, 32)]).place(x=360, y=10)
        Combobox(lf, state='readonly', takefocus=OFF, width=6, textvariable=month,
                 values=["month"] + [f"0{x}" if x < 10 else x for x in range(1, 13)]).place(x=430, y=10)
        Combobox(lf, state='readonly', takefocus=OFF, width=4, textvariable=year,
                 values=["year"] + [str(x) for x in range(2019, 3000)]).place(x=515, y=10)
        Combobox(lf, state='readonly', width=6, textvariable=hour,
                 values=["hour"] + [f"0{x}:00" if x < 10 else f"{x}:00" for x in range(0, 24)]).place(x=360, y=45)

        Button(lf, command=lambda: self.admin_register(user, password, tree),
               text='Register', borderwidth=3, width=10, bg='green').place(x=20, y=140)
        Button(lf, command=lambda: self.admin_ban(user, password, [day, month, year, hour], tree),
               text='Ban', borderwidth=3, width=10, bg='yellow').place(x=120, y=140)
        Button(lf, command=lambda: self.admin_free_ban(user, password, tree),
               text="Free", borderwidth=3, width=10, bg='azure').place(x=220, y=140)
        Button(lf, command=lambda: self.admin_delete(user, password, tree),
               text='Delete', borderwidth=3, width=10, bg='red').place(x=320, y=140)

        # Clients data's widgets
        headers = ('Username', 'Password', 'Wins',
                   'Loses', 'Draws', 'Color', 'Status', 'Ban date', 'Arena')
        scroll = Scrollbar(window, orient=VERTICAL)
        tree = Treeview(window, columns=headers, show='headings', yscrollcommand=scroll.set)
        for elem in headers:
            tree.heading(elem, text=elem)
            tree.column(elem, width=114, anchor='center')
        tree.place(y=375)
        scroll.config(command=tree.yview)
        scroll.place(x=1029, y=375, height=225)
        Button(window, text='Clean data', bg='dodger blue', height=3, width=15,
               command=lambda: self.clean_accounts_data(tree)).place(x=20, y=250)
        Button(window, text='exit', bg='dodger blue', width=15, height=3,
               command=lambda: window.destroy()).place(x=160, y=250)
        window.bind("<FocusIn>", lambda event: self.show_account_data(tree))
        window.bind("<Enter>", lambda event: self.show_account_data(tree))
        window.mainloop()

    def admin_register(self, new_username, new_password, window):
        if is_valid_admin_buffers(new_username.get(), new_password.get()):
            if new_username.get() not in [element.get_username() for element in self.__accounts_list]:
                self.register_new_player([new_username.get(), new_password.get()], is_online=False)
                window.focus_set()
                window.master.focus_set()
        new_password.set("")
        new_username.set("")

    def admin_ban(self, username_to_ban, user_password, ban_until, window):
        if is_valid_admin_buffers(username_to_ban.get(), user_password.get()) and is_valid_ban_date(ban_until):
            for account in self.__accounts_list:
                if account.get_username() == username_to_ban.get() and account.get_password() == user_password.get():
                    ban_player_until = "/".join(element.get() for element in ban_until[0:3]) + " " + ban_until[3].get()
                    set_ban_in_table(username_to_ban.get(), ban_player_until)
                    account.set_ban_until(ban_player_until)
                    break
        window.focus_set()
        window.master.focus_set()
        username_to_ban.set("")
        user_password.set("")
        ban_until[0].set("day")
        ban_until[1].set("month")
        ban_until[2].set("year")
        ban_until[3].set("hour")

    def admin_delete(self, username_to_delete, user_password, window):
        if is_valid_admin_buffers(username_to_delete.get(), user_password.get()):
            for acc in self.__accounts_list:
                if acc.get_username() == username_to_delete.get() and acc.get_password() == user_password.get():
                    self.__accounts_list.remove(acc)
                    delete_from_account_table(username_to_delete.get())
                    window.focus_set()
                    window.master.focus_set()
                    break
        username_to_delete.set("")
        user_password.set("")

    def admin_free_ban(self, username_to_free, user_password, window):
        if is_valid_admin_buffers(username_to_free.get(), user_password.get()):
            for acc in self.__accounts_list:
                if acc.get_username() == username_to_free.get() and acc.get_password() == user_password.get():
                    acc.erase_ban()
                    set_ban_in_table(username_to_free.get(), "00/00/0000 00:00")
                    window.focus_set()
                    window.master.focus_set()
                    break
        username_to_free.set("")
        user_password.set("")

    def clean_accounts_data(self, window):
        conn = connect('my database.db')
        curs = conn.cursor()
        curs.execute(f"UPDATE ACCOUNTS SET Wins = 0, Loses = 0, Draws = 0, Color = 'ff0000', Ban = (?)",
                     ("00/00/0000 00:00",))
        conn.commit()
        for acc in self.__accounts_list:
            acc.clean_data()
        window.focus_set()
        window.master.focus_set()

    def show_account_data(self, tree):
        for i in tree.get_children():
            tree.delete(i)
        for account in self.__accounts_list:
            tree.insert("", END, values=str(account).split(' '))

    def uploader(self):
        print("uploader start...")
        server = socket.socket()
        server.bind((self.__ip, 50000))
        server.listen(1)
        server.settimeout(3)
        with open(INSTALLER_FILE, 'rb') as my_file:
            data = my_file.read()
        my_files = listdir(".")
        while self.__stop_running is False:
            try:
                client, address = server.accept()
                client.settimeout(3)
                request = client.recv(1024).decode().split("\r\n")
                if request == ['']:
                    client.close()
                    raise socket.error
                if is_installer_req(request[0]):
                    client.send(HTTP_RESPONSE_OK + data)
                elif request[0].split("/")[1].split(" ")[0] in my_files:
                    client.send(HTTP_RESPONSE_FORBIDDEN)
                else:
                    client.send(HTTP_RESPONSE_NOT_FOUND)
                client.close()
            except socket.error:
                continue
        print("uploader shut down...")
        server.close()

    def update_users_data(self):
        print("Accounts updater start...")
        conn = connect('my database.db')
        curs = conn.cursor()
        while self.__stop_running is False:
            for update in self.__accounts_updates_to_table:
                account, act = update[0], update[1]
                if act == "W":
                    curs.execute("UPDATE Accounts SET Wins = (?) WHERE Username = (?)",
                                 (account.get_win(), account.get_username()))
                elif act == "L":
                    curs.execute("UPDATE Accounts SET Loses = (?) WHERE Username = (?)",
                                 (account.get_loses(), account.get_username()))
                elif act == "E":
                    curs.execute("UPDATE Accounts SET Draws = (?) WHERE Username = (?)",
                                 (account.get_loses(), account.get_username()))
                elif act == "C":
                    new_color = update[2]
                    curs.execute("UPDATE Accounts SET Color = (?) WHERE Username = (?)",
                                 (new_color, account.get_username()))
                self.__accounts_updates_to_table.remove(update)
            conn.commit()
            time.sleep(5)
        print("Accounts updater shut down...")

    def is_ban_date_passed(self):
        print("Bans check start...")
        conn = connect("my database.db")
        curs = conn.cursor()
        while self.__stop_running is False:
            banned_list = list(filter(lambda x: x.get_client_status() == "Ban", self.__accounts_list))
            current_time = time.mktime(time.localtime())
            for acc in banned_list:
                if time.mktime(acc.get_ban_struct()) < current_time:
                    acc.player_offline()
                    acc.erase_ban()
                    curs.execute("UPDATE Accounts SET Ban = '00/00/0000 00:00'"
                                 " WHERE Username = (?)", (acc.get_username(),))
            conn.commit()
            time.sleep(3)
        print("Bans Check shut down...")

    def help_player(self, index):
        """all the account need to be in accounts_list, if the one that needed isn't there admin erased it:
            the char '@' sign to client that his user has been deleted while he was connected
            the chr '!' sign to client that the update succeeded
            """
        print(f"client thread number {index + 1} start")
        while self.__stop_running is False:
            account = None
            try:
                player, address = self.__server_socket.accept()
            except socket.error:
                continue
            while self.__stop_running is False:
                try:
                    request = player.recv(5).decode()
                    if self.__stop_running:
                        sys.exit()
                    if request == "exit ":
                        player.close()
                        account.player_offline()
                        break
                    elif request == "Exit ":
                        player.close()
                        break

                    #  only cases when account doesn't known yet
                    elif request == "info ":
                        account = self.is_can_register(player)
                    elif request == "login":
                        account = self.player_login(player)

                    elif request == "color":
                        if account not in self.__accounts_list:
                            player.send(b"@")  # account deleted
                            break
                        player.send(account.get_color().encode())

                    elif request == "Color":
                        new_color = player.recv(6).decode()
                        if account not in self.__accounts_list:
                            player.send(b"@")  # account deleted
                            break
                        account.change_color(new_color)
                        self.__accounts_updates_to_table.append([account, "C", new_color])
                        player.send(b"!")

                    elif request[:4] == "game":
                        mode_code = int(request[4])
                        if account not in self.__accounts_list:
                            player.send(b"@")  # account deleted
                            break
                        if self.handle_battle_request(mode_code, address, player, account):
                            break
                        asked_map = find_asked_map(player.recv(30).decode())
                        player.send(asked_map.encode())
                        try:
                            request = player.recv(4).decode()
                            account.set_arena_number(0)
                            if account not in self.__accounts_list:
                                player.send(b"@")  # account deleted
                                break
                            if request == "situ":
                                act = player.recv(1).decode()
                                if act == "W":
                                    account.add_win()
                                elif act == "L":
                                    account.add_lose()
                                elif act == "E":
                                    account.add_draws()
                                self.__accounts_updates_to_table.append([account, act])
                                player.send(b"!")
                            elif request == "Situ":  # client exit the game
                                player.close()
                                self.__accounts_updates_to_table.append([account, "L"])
                                account.add_lose()
                                account.player_offline()
                                break

                        except socket.error:
                            account.set_arena_number(0)
                            print(account.get_username() + " illegal exit from battle count as losing")
                            self.__accounts_updates_to_table.append([account, "L"])
                            player.close()
                            account.add_lose()
                            account.player_offline()
                            break

                except socket.error:
                    player.close()
                    if account is not None:
                        account.player_offline()
                    break

            player.close()

    def handle_battle_request(self, mode_code, address, client_socket, account):
        if mode_code == self.DEATH_MODE:
            if self.__death_battle_ip == "":  # player create connection
                client_socket.send(b"T")
                self.__death_battle_ip = address[0]
                self.__death_battle_arena = self.find_next_arena(self.DEATH_MODE)
                account.set_arena_number(self.__death_battle_arena)
                self.__death_battle_creator = client_socket
                try:
                    client_socket.recv(2)
                except socket.error:
                    account.set_arena_number(0)
                    account.player_offline()
                    client_socket.close()
                    return True
            else:
                try:
                    self.__death_battle_creator.send(b"found an enemy")
                    self.__death_battle_creator = None
                except socket.error:
                    self.__death_battle_ip = ""
                    return self.handle_battle_request(mode_code, address, client_socket, account)

                client_socket.send(b"F" + self.__death_battle_ip.encode())
                self.__death_battle_ip = ""
                account.set_arena_number(self.__death_battle_arena)

        elif mode_code == self.TIME_MODE:
            if self.__time_battle_ip == "":  # player create connection
                client_socket.send(b"T")
                self.__time_battle_ip = address[0]
                self.__time_battle_arena = self.find_next_arena(self.TIME_MODE)
                account.set_arena_number(self.__time_battle_arena)
                self.__time_battle_creator = client_socket
                try:
                    client_socket.recv(2)
                except socket.error:
                    account.set_arena_number(0)
                    account.player_offline()
                    client_socket.close()
                    return True
            else:
                try:
                    self.__time_battle_creator.send(b"found an enemy")
                    self.__time_battle_creator = None
                except socket.error:
                    self.__time_battle_ip = ""
                    return self.handle_battle_request(mode_code, address, client_socket, account)

                client_socket.send(b"F" + self.__time_battle_ip.encode())
                self.__time_battle_ip = ""
                account.set_arena_number(self.__time_battle_arena)

    def is_can_register(self, client):
        """return to the player if username is already exist in the accounts list
        argument:
            client: type - socket
        """
        new_player_data = client.recv(21).decode().split(",")
        exist = False
        for acc in self.__accounts_list:
            if acc.get_username() == new_player_data[0]:
                exist = True
        if exist:
            client.send(b"N")
        else:
            client.send(b"Y")
            new_account = self.register_new_player(new_player_data)
            print("A new player signed up, is username is: " + new_player_data[0])
            return new_account

    def register_new_player(self, new_account_data, is_online=True):
        """add the new account the the list
        argument:
            username = type: string
            password = type: string
        """
        firebase_token = ""
        if self.__is_online_database:
            data = {"Username": new_account_data[0], "Password": new_account_data[1],
                    "Wins": 0, "Loses": 0, "Draws": 0, "Color": "ff0000", "Bandate": "00/00/0000 00:00"}
            firebase_token = self.__fire.post("Accounts", data)['name']

        conn = connect("my database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Accounts VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                       (new_account_data[0], new_account_data[1], 0, 0, 0,
                        "ff0000", "00/00/0000 00:00", firebase_token))
        conn.commit()
        conn.close()
        new_account = Account(new_account_data[0], new_account_data[1],
                              0, 0, 0, "ff0000", "00/00/0000 00:00", firebase_token)
        if is_online:
            new_account.player_online()
        self.__accounts_list.append(new_account)
        self.__accounts_list.sort(key=lambda x: x.get_username())
        return new_account

    def player_login(self, client):
        account_to_check = client.recv(21).decode().split(",")
        exist = False
        for account in self.__accounts_list:
            if account.get_username() == account_to_check[0] and account.get_password() == account_to_check[1]:
                # found match
                exist = True
                if account.get_client_status() == "On":  # this account is already taken
                    client.send(b"T")
                elif account.get_client_status() == "Ban":
                    client.send(b"B")
                    client.send(account.get_ban_string().encode())
                else:
                    client.send(b"O")  # can use this account
                    account.player_online()
                    return account
        if not exist:
            client.send(b"F")  # desired account does not exist

    def find_next_arena(self, mode_code):
        if mode_code == self.DEATH_MODE:
            my_arenas = [x.get_arena_number() for x in self.__accounts_list if x.get_arena_number() >= 1
                         and x.get_arena_number() % 2]
            if my_arenas:  # not empty list
                min_arena = min(my_arenas)
                if min_arena == 1:
                    return max(my_arenas) + 2
                else:
                    return min_arena - 2
            else:
                return 1
        else:
            my_arenas = [x.get_arena_number() for x in self.__accounts_list if x.get_arena_number() >= 1
                         and not (x.get_arena_number() % 2)]
            if my_arenas:  # not empty list
                min_arena = min(my_arenas)
                if min_arena == 2:
                    return max(my_arenas) + 2
                else:
                    return min_arena - 2
            else:
                return 2


# filters and sub-functions for Server class
def is_installer_req(request):
    return request.startswith("GET") and "/Game.exe" in request and "HTTP/1.1" in request


def is_valid_admin_buffers(username, password):
    return (0 < len(username) <= 10) and (0 < len(password) <= 10) \
           and ((0x61 <= ord(username[0]) <= 0x7a) or (0x41 <= ord(username[0]) <= 0x5a))\
           and all([((0x61 <= ord(letter) <= 0x7a) or (0x41 <= ord(letter) <= 0x5a) or letter.isdigit())
                    for letter in username[1:]]) \
           and all([((0x61 <= ord(letter) <= 0x7a) or (0x41 <= ord(letter) <= 0x5a)  # a-z or A-Z or digit
                     or letter.isdigit()) for letter in password])


def is_valid_ban_date(date_values_list):
    return all(True if element.get().isdigit() else False for element in date_values_list[:2]) \
           and date_values_list[3].get()[2] == ":" and\
           MAX_NUM_DAY_IN_MONTHS[date_values_list[1].get()] >= int(date_values_list[0].get())


def delete_from_account_table(username):
    conn = connect("my database.db")
    curs = conn.cursor()
    curs.execute("DELETE FROM Accounts WHERE Username = ?", (username, ))
    conn.commit()


def set_ban_in_table(username, ban_player_until):
    conn = connect("my database.db")
    curs = conn.cursor()
    curs.execute("UPDATE Accounts SET Ban = (?) WHERE Username = (?)", (ban_player_until, username))
    conn.commit()


def find_asked_map(map_code):
    conn = connect("my database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT Walls FROM Maps WHERE MapCode = (?)", (map_code, ))
    walls_of_asked_map = cursor.fetchall()[0][0]
    return walls_of_asked_map


def my_ip():
    """return my local current ip in string"""
    return socket.gethostbyname(socket.gethostname())


def main():
    server = Server()
    server.active()


if __name__ == '__main__':
    main()
