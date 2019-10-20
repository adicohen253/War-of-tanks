import threading
import socket
import time
from os import listdir
from tkinter import *
from sqlite3 import *
from tkinter.font import *
from tkinter.ttk import Combobox

LABELS_TEXT = [["Username", 0], ["Password", 120], ["Wins", 230], ["Loses", 300],
               ["Draws", 370], ["Color", 450], ["Server status", 530], ["Ban until", 680], ["Arena", 820]]
FONT = ("Arial", 12, NORMAL)

INSTALLER_FILE = "Wot installer.zip"
HTTP_RESPONSE_OK = b"""HTTP/1.1 200 OK
Content-Type: zip; charset=utf-8
Content-Disposition: attachment; filename=installer.zip
Connection: keep-alive

"""
HTTP_RESPONSE_NOT_FOUND = b"""HTTP/1.1 404 NOT FOUND
"""
HTTP_RESPONSE_FORBIDDEN = b"""HTTP/1.1 403 FORBIDDEN
"""
MAX_NUM_DAY_IN_MONTHS = {"01": 31, "02": 28, "03": 31, "04": 30, "05": 31, "06": 30,
                         "07": 31, "08": 31, "09": 30, "10": 31, "11": 30, "12": 31}


class Account:
    def __init__(self, username, password, wins=0, loses=0, draws=0, favorite_color="ff0000", client_status="Off",
                 ban_til="00/00/0000 00:00"):
        self.__username = username
        self.__password = password
        self.__wins = wins
        self.__loses = loses
        self.__draws = draws
        self.__favorite_color = favorite_color
        self.__client_status = client_status
        self.__arena_number = 0
        self.__ban_until = string_to_time_struct(ban_til)

    def time_struct_to_string(self):
        date = "/".join([f"0{element}" if element < 10 else str(element) for element in self.__ban_until[2:0:-1]])
        year = f"/{'0' * 4 if self.__ban_until[0] == 0 else self.__ban_until[0]}"
        hour = str(self.__ban_until[3]) + ":00"
        return f"{date+year} {hour}"

    def player_connect(self):
        self.__client_status = "On"

    def player_disconnect(self):
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

    def get_ban_until(self):
        return self.__ban_until

    def set_arena_number(self, new_arena_number):
        self.__arena_number = new_arena_number

    def clean_data(self):
        self.__wins = 0
        self.__loses = 0
        self.__draws = 0
        self.__favorite_color = "ff0000"
        self.__ban_until = string_to_time_struct("00/00/0000 00:00")

    def set_ban_until(self, new_date):
        self.__ban_until = string_to_time_struct(new_date)

    def erase_ban_until(self):
        self.__ban_until = time.struct_time((0, 0, 0, 0, 0, 0, 0, 0, 0))

    def add_win(self):
        self.__wins += 1

    def add_lose(self):
        self.__loses += 1

    def add_draws(self):
        self.__draws += 1

    def change_color(self, newcolor):
        self.__favorite_color = newcolor

    def __str__(self):
        return f"{self.__username}{' ' * round(20.5 - len(self.__username))}{self.__password}" \
               f"{' ' * (21 - len(self.__password))} {self.__wins} {' ' * 15}{self.__loses} {' ' * 15}{self.__draws}" \
               f"{' ' * 12}{self.__favorite_color}{' ' * 13}{self.__client_status}{' ' * 24}" \
               f"{self.time_struct_to_string()}{' '* (30-(len(self.time_struct_to_string())))}{self.__arena_number}"


def string_to_time_struct(ban_string):
    date, hour = ban_string.split(" ")
    day, month, year = [int(element) for element in date.split("/")]
    hour = hour[:2]
    return time.struct_time((year, month, day, hour, 0, 0, 0, 0, 0))


def find_first_taken_arena(accounts_list):
    my_arenas = [x.get_arena_number() for x in accounts_list if x.get_arena_number() >= 1]
    if my_arenas:  # not empty list
        min_arena = min(my_arenas)
        if min_arena == 1:
            return max(my_arenas) + 1
        else:
            return min_arena - 1
    else:
        return 1


def my_ip():
    """return my current ip in string"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.0.0.8', 1027))
    except socket.error:
        return None
    return s.getsockname()[0]


def send_color(client, username, accounts_list):
    for account in accounts_list:
        if account.get_username() == username:
            client.send(account.get_color().encode())


def register_new_player(new_account_data, accounts_list, is_online=True):
    """add the new account the the list
    argument:
        username = type: string
        password = type: string
    """
    conn = connect("my database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Accounts VALUES(?, ?, ?, ?, ?, ?, ?)",
                   (new_account_data[0], new_account_data[1], 0, 0, 0, "ff0000", "00/00/0000 00:00"))
    conn.commit()
    conn.close()
    new_account = Account(username=new_account_data[0], password=new_account_data[1],
                          wins=0, loses=0, draws=0, favorite_color="ff0000")
    if is_online:
        new_account.player_connect()
    accounts_list.append(new_account)
    accounts_list.sort(key=lambda x: x.get_username())
    return new_account


def is_can_register(client, accounts_list):
    """return to the player if username is already exist in the accounts list
    argument:
        client: type - socket
        players_data: type - pandas.DataFrame, holds the data of the users
    """
    new_player_data = client.recv(21).decode().split(",")
    exist = False
    for acc in accounts_list:
        if acc.get_username() == new_player_data[0]:
            exist = True
    if exist:
        client.send(b"N")
    else:
        client.send(b"Y")
        new_account = register_new_player(new_player_data, accounts_list)
        print("A new player signed up, is username is: " + new_player_data[0])
        return new_account


def player_login(client, accounts_list):
    account_to_check = client.recv(21).decode().split(",")
    exist = False
    for account in accounts_list:
        if account.get_username() == account_to_check[0] and account.get_password() == account_to_check[1]:
            # found match
            exist = True
            if account.get_client_status() == "On":  # another player connect to this account
                client.send(b"N")
            else:
                client.send(b"T")  # can use this account
                account.player_connect()
                return account
    if not exist:
        client.send(b"F")  # desired account does not exist


def update_users_data(new_updates_list, finish):
    print("Accounts updater start...")
    conn = connect('my database.db')
    curs = conn.cursor()
    while not finish[0]:
        for update in new_updates_list:
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
            new_updates_list.remove(update)
        conn.commit()
    print("Accounts updater shut down...")


def help_player(server, codes, update_users, accounts_list, finish, index, available_arena):
    """all the account need to be in accounts_list, if the one that needed isn't there admin erased it:
        the char '@" sign to client that his user has been deleted while he was connected
        the chr '!' sign to client that the update succeeded
        """
    print(f"client thread number {index + 1} start")
    while not finish[0]:
        account = None
        try:
            player1, address1 = server.accept()
        except socket.error:
            continue
        while not finish[0]:
            try:
                request = player1.recv(5).decode()
                if finish[0]:
                    sys.exit()
                if request == "exit ":
                    player1.close()
                    account.player_disconnect()
                    break
                elif request == "Exit ":
                    player1.close()
                    break

                #  only cases when account doesn't known yet
                elif request == "info ":
                    account = is_can_register(player1, accounts_list)
                elif request == "login":
                    account = player_login(player1, accounts_list)

                elif request == "color":
                    if account not in accounts_list:
                        player1.send(b"@")
                        break
                    player1.send(account.get_color().encode())

                elif request == "Color":
                    new_color = player1.recv(6).decode()
                    if account not in accounts_list:
                        player1.send(b"@")
                        break
                    account.change_color(new_color)
                    update_users.append([account, "C", new_color])
                    player1.send(b"!")

                elif request[:4] == "game":
                    mode_code = int(request[4])
                    if account not in accounts_list:
                        player1.send(b"@")
                        break
                    player1.send(str(codes[mode_code][0]).encode())
                    if not codes[mode_code][0]:
                        # player connects, send ip of client who made connection
                        player1.send(str(codes[mode_code][1]).encode())
                        account.set_arena_number(available_arena[0])
                        available_arena[0] = find_first_taken_arena(accounts_list)
                    else:
                        codes[mode_code][1] = address1[0]  # player makes connection
                        account.set_arena_number(available_arena[0])
                    codes[mode_code][0] = not codes[mode_code][0]
                    try:
                        request = player1.recv(4).decode()
                        if account not in accounts_list:
                            player1.send(b"@")
                            break
                        account.set_arena_number(0)
                        if request == "situ":
                            act = player1.recv(1).decode()
                            if act == "W":
                                account.add_win()
                                available_arena[0] = find_first_taken_arena(accounts_list)
                            elif act == "L":
                                account.add_lose()
                            elif act == "E":
                                account.add_draws()
                            update_users.append([account, act])
                            player1.send(b"!")
                        elif request == "Situ":  # client exit the game
                            player1.close()
                            update_users.append([account, "L"])
                            account.add_lose()
                            account.player_disconnect()
                            break

                    except socket.error:
                        print(account.get_username() + " illegal exit from battle count as losing")
                        update_users.append([account, "L"])
                        player1.close()
                        account.add_lose()
                        account.player_disconnect()
                        break

            except socket.error:
                player1.close()
                if account is not None:
                    account.player_disconnect()
                break
        player1.close()


def is_installer_req(request):
    return request.startswith("GET") and "/installer.zip" in request and "HTTP/1.1" in request


def uploader(finish):
    print("uploader start...")
    server = socket.socket()
    server.bind((my_ip(), 50000))
    server.listen(1)
    server.settimeout(3)
    with open(INSTALLER_FILE, 'rb') as my_file:
        data = my_file.read()
    my_files = listdir(".")
    while not finish[0]:
        try:
            client, address = server.accept()
            client.settimeout(3)
            request = client.recv(1024).decode().split("\r\n")
            if request == ['']:
                raise socket.error
            if is_installer_req(request[0]):
                client.send(HTTP_RESPONSE_OK + data)
            elif request[0].split("/")[1].split(" ")[0] in my_files:
                client.send(HTTP_RESPONSE_FORBIDDEN)
            else:
                client.send(HTTP_RESPONSE_NOT_FOUND)
            client.close()
        except socket.error:
            pass
    print("uploader shut down...")
    server.close()


def create_server_screen(accounts_list):
    window = Tk()
    window.geometry('950x600')
    window.title("My server")
    window.resizable(OFF, OFF)
    Label(window, text="My IP is: " + my_ip(), fg='blue',
          bg='white', borderwidth=5, relief=SUNKEN).place(x=800, y=30)

    # Admin options's widgets
    lf = LabelFrame(window, font=FONT, text="Admin interface:")
    lf.place(x=0, y=10, width=600, height=200)

    user, password = StringVar(), StringVar()
    day, month = StringVar(value="day"), StringVar(value="month")
    year, hour = StringVar(value="year"), StringVar(value="hour")
    Label(lf, text="Username:", font=FONT).place(x=20, y=10)
    Entry(lf, textvariable=user).place(x=110, y=15)

    Label(lf, text="Password:", font=FONT).place(x=20, y=50)
    Entry(lf, textvariable=password).place(x=110, y=55)

    Label(lf, text="Date:", font=FONT).place(x=280, y=10)
    Label(lf, text='Hour:', font=FONT).place(x=280, y=45)
    Combobox(lf, state='readonly', takefocus=OFF, width=6, textvariable=day,
             values=[f"0{x}" if x < 10 else x for x in range(1, 32)]).place(x=330, y=10)
    Combobox(lf, state='readonly', takefocus=OFF, width=6, textvariable=month,
             values=[f"0{x}" if x < 10 else x for x in range(1, 13)]).place(x=400, y=10)
    Combobox(lf, state='readonly', takefocus=OFF, width=6, textvariable=year,
             values=[x for x in range(2019, 3000)]).place(x=470, y=10)
    Combobox(lf, state='readonly', width=6, textvariable=hour,
             values=[f"0{x}:00" if x < 10 else f"{x}:00" for x in range(0, 24)]).place(x=330, y=45)

    Button(lf, command=lambda: admin_register(accounts_list, user, password, view_accounts),
           text='Register', borderwidth=3, width=10, bg='green').place(x=20, y=140)
    Button(lf, command=lambda: admin_ban(accounts_list, user, password, [day, month, year, hour], view_accounts),
           text='Ban', borderwidth=3, width=10, bg='yellow').place(x=110, y=140)
    Button(lf, command=lambda: admin_delete(accounts_list, user, password, view_accounts),
           text='Delete', borderwidth=3, width=10, bg='red').place(x=290, y=140)
    Button(lf, command=lambda: admin_free_ban(accounts_list, user, password, view_accounts),
           text="Free", borderwidth=3, width=10, bg='azure').place(x=200, y=140)

    # Clients data's widgets
    scroll = Scrollbar(window, orient=VERTICAL)
    view_accounts = Listbox(window, width=100, height=10, fg='blue', yscrollcommand=scroll.set, font=FONT)
    view_accounts.place(y=410)
    scroll.config(command=view_accounts.yview)
    scroll.place(x=905, y=400, height=200)
    Button(window, text='Clean accounts data', height=3, width=20,
           command=lambda: clean_accounts_data(accounts_list, view_accounts)).place(x=750, y=180)
    Button(window, text='exit', width=20, height=3, command=lambda: window.destroy()).place(x=750, y=250)
    for labe in LABELS_TEXT:
        Label(window, text=labe[0], font=FONT, fg='red', bg='yellow').place(x=labe[1], y=370)

    window.bind("<FocusIn>", lambda event: show_account_data(view_accounts, accounts_list))
    window.bind("<Enter>", lambda event: show_account_data(view_accounts, accounts_list))
    window.mainloop()


def clean_accounts_data(accounts_list, window):
    conn = connect('my database.db')
    curs = conn.cursor()
    curs.execute(f"UPDATE ACCOUNTS SET Wins = 0, Loses = 0, Draws = 0, Color = 'ff0000', Ban = (?)",
                 ("00/00/0000 00:00", ))
    conn.commit()
    for acc in accounts_list:
        acc.clean_data()
    window.focus_set()
    window.master.focus_set()


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


def admin_register(accounts_list, new_username, new_password, window):
    if is_valid_admin_buffers(new_username.get(), new_password.get()):
        if new_username.get() not in [element.get_username() for element in accounts_list]:
            register_new_player([new_username.get(), new_password.get()], accounts_list, is_online=False)
            window.focus_set()
            window.master.focus_set()
    new_password.set("")
    new_username.set("")


def admin_delete(accounts_list, username_to_delete, user_password, window):
    if is_valid_admin_buffers(username_to_delete.get(), user_password.get()):
        for acc in accounts_list:
            if acc.get_username() == username_to_delete.get() and acc.get_password() == user_password.get():
                accounts_list.remove(acc)
                delete_from_account_table(username_to_delete.get())
                window.focus_set()
                window.master.focus_set()
                break
    username_to_delete.set("")
    user_password.set("")


def delete_from_account_table(username):
    conn = connect("my database.db")
    curs = conn.cursor()
    curs.execute("DELETE FROM Accounts WHERE Username = ?", (username, ))
    conn.commit()


def admin_ban(accounts_list, username_to_ban, user_password, ban_until, window):
    if is_valid_admin_buffers(username_to_ban.get(), user_password.get()) and is_valid_ban_date(ban_until):
        for account in accounts_list:
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


def admin_free_ban(accounts_list, username_to_free, user_password, window):
    if is_valid_admin_buffers(username_to_free.get(), user_password.get()):
        for acc in accounts_list:
            if acc.get_username() == username_to_free.get() and acc.get_password() == user_password.get():
                acc.set_ban_until("00/00/0000 00:00")
                set_ban_in_table(username_to_free.get(), "00/00/0000 00:00")
                window.focus_set()
                window.master.focus_set()
                break
    username_to_free.set("")
    user_password.set("")


def set_ban_in_table(username, ban_player_until):
    conn = connect("my database.db")
    curs = conn.cursor()
    curs.execute("UPDATE Accounts SET Ban = (?) WHERE Username = (?)", (ban_player_until, username))
    conn.commit()


def show_account_data(account_box, account_list):
    account_box.delete(0, END)
    for account in account_list:
        account_box.insert(END, str(account))


def build_my_accounts(db_cursor):
    db_cursor.execute("SELECT * FROM Accounts")
    data = [list(x) for x in db_cursor.fetchall()]
    accounts_list = []
    for acc in data:
        accounts_list.append(Account(username=acc[0], password=acc[1], wins=acc[2],
                                     loses=acc[3], draws=acc[4], favorite_color=acc[5], ban_til=acc[6]))
    accounts_list.sort(key=lambda x: x.get_username())
    return accounts_list


def main():
    server = socket.socket()
    server.bind((my_ip(), 2020))
    server.listen(1)
    server.settimeout(0.2)
    conn = connect("my database.db")
    curs = conn.cursor()
    accounts_list = build_my_accounts(curs)

    available_arena = [1]
    channels_for_matches = [[True, None], [True, None]]
    account_updates_to_table = []
    finish = [False]  # flag for all the threads
    for index in range(10):
        element = threading.Thread(target=help_player, args=(server, channels_for_matches, account_updates_to_table,
                                                             accounts_list, finish, index, available_arena))
        element.start()
    threading.Thread(target=update_users_data, args=(account_updates_to_table, finish)).start()
    threading.Thread(target=uploader, args=([finish])).start()
    create_server_screen(accounts_list)
    finish[0] = True


if __name__ == '__main__':
    main()
