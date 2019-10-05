import threading
import socket
import pandas as pd
from tkinter import *
from sqlite3 import *
from tkinter.font import *
from tkinter.ttk import Combobox

LABELS_TEXT = ["Username", "Password", "Wins", "Loses", "Draws", "Color", "Server status"]
COMMANDS = pd.DataFrame(columns=["command", "description"], data=[
    ["report", "show records of player's stats"], ["clean", "delete all data of the accounts"]])
FONT = ("Arial", 12, NORMAL)


class Account:
    SERVER_STATUSES = {False: "Off", True: "On"}

    def __init__(self, username, password, wins=0, loses=0, draws=0, favorite_color="ff0000"):
        self.__username = username
        self.__password = password
        self.__wins = wins
        self.__loses = loses
        self.__draws = draws
        self.__favorite_color = favorite_color
        self.__is_connect = False

    def player_connect(self):
        self.__is_connect = True

    def player_disconnect(self):
        self.__is_connect = False

    def get_is_connect(self):
        return self.__is_connect

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

    def clean_data(self):
        self.__wins = 0
        self.__loses = 0
        self.__draws = 0
        self.__favorite_color = "ff0000"

    def add_win(self):
        self.__wins += 1

    def add_lose(self):
        self.__loses += 1

    def add_draws(self):
        self.__draws += 1

    def change_color(self, newcolor):
        self.__favorite_color = newcolor

    def __str__(self):
        return f"{self.__username} {' ' * (22 -len(self.__username))} {self.__password}" \
               f" {' ' * (21-len(self.__password))} {self.__wins} {' ' * 20}{self.__loses} {' ' * 20}{self.__draws} " \
               f"{' ' * 12}{self.__favorite_color}{' '*13}{self.SERVER_STATUSES[self.__is_connect]}"


def clean_accounts_data(accounts_list):
    conn = connect('my database.db')
    curs = conn.cursor()
    curs.execute("UPDATE ACCOUNTS SET Wins = 0, Loses = 0, Draws = 0, Color = 'ff0000'")
    conn.commit()
    for acc in accounts_list:
        acc.clean_data()


def register_new_player(new_account_data, accounts_list):
    """add the new account the the list
    argument:
        username = type: string
        password = type: string
    """
    conn = connect("my database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Accounts VALUES(?, ?, ?, ?, ?, ?)",
                   (new_account_data[0], new_account_data[1], 0, 0, 0, "ff0000"))
    conn.commit()
    conn.close()
    new_account = Account(username=new_account_data[0], password=new_account_data[1],
                          wins=0, loses=0, draws=0, favorite_color="ff0000")
    new_account.player_connect()
    accounts_list.append(new_account)
    return new_account


def is_can_register(client, accounts_list):
    """return to the player if username is already exist in the accounts list
    argument:
        client: type - socket
        players_data: type - pandas.DataFrame, holds the data of the users
    """
    new_player_data = client.recv(41).decode().split(",")
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
    account_to_check = client.recv(41).decode().split(",")
    exist = False
    for account in accounts_list:
        if account.get_username() == account_to_check[0] and account.get_password() == account_to_check[1]:
            # found match
            exist = True
            if account.get_is_connect():  # another player connect to this account
                client.send(b"N")
            else:
                client.send(b"T")  # can use this account
                account.player_connect()
                return account
    if not exist:
        client.send(b"F")  # desired account does not exist


def update_users_data(new_data_list, finish):
    conn = connect('my database.db')
    curs = conn.cursor()
    while not finish[0]:
        for update in new_data_list:
            account, act = update[0], update[1]
            if act == "V":
                curs.execute("UPDATE Accounts SET Wins = (?) WHERE Username = (?)",
                             (account.get_win(), account.get_username()))
            elif act == "D":
                curs.execute("UPDATE Accounts SET Loses = (?) WHERE Username = (?)",
                             (account.get_loses(), account.get_username()))
            elif act == "E":
                curs.execute("UPDATE Accounts SET Draws = (?) WHERE Username = (?)",
                             (account.get_loses(), account.get_username()))
            elif act == "C":
                new_color = update[2]
                curs.execute("UPDATE Accounts SET Color = (?) WHERE Username = (?)",
                             (new_color, account.get_username()))
            new_data_list.remove(update)
        conn.commit()
    print("done")


def help_client(server, codes, update_users, accounts_list, finish, index):
    print(f"client thread number {index} active")
    while not finish[0]:
        account = None
        try:
            player1, address1 = server.accept()
        except socket.error:
            continue
        while not finish[0]:
            try:
                request = player1.recv(5).decode()
                if request == "exit ":
                    player1.close()
                    account.player_disconnect()
                    break
                elif request == "Exit ":
                    player1.close()
                    break

                elif request == "info ":
                    account = is_can_register(player1, accounts_list)
                elif request == "login":
                    account = player_login(player1, accounts_list)

                elif request == "color":
                    player1.send(account.get_color().encode())

                elif request == "Color":  # change the player's color in the data base - need to turn to function...
                    new_color = player1.recv(6).decode()
                    account.change_color(new_color)
                    update_users.append([account, "C", new_color])

                elif request[:4] == "game":
                    mode_code = int(request[4])
                    player1.send(str(int(codes[mode_code][0])).encode())
                    if not codes[mode_code][0]:  # player connects
                        player1.send(str(codes[mode_code][1]).encode())
                    else:
                        codes[mode_code][1] = address1[0]  # player makes connection
                    codes[mode_code][0] = not codes[mode_code][0]
                    try:
                        request = player1.recv(4).decode()
                        if request == "situ":
                            act = player1.recv(1).decode()
                            if act == "V":
                                account.add_win()
                            elif act == "D":
                                account.add_lose()
                            elif act == "E":
                                account.add_draws()
                            update_users.append([account, act])
                        elif request == "Situ":  # client exit the game
                            player1.close()
                            update_users.append([account, "D"])
                            account.add_lose()
                            account.player_disconnect()
                            break

                    except socket.error:
                        print(account.get_username() + " illegal exit from battle count as losing")
                        update_users.append([account, "D"])
                        player1.close()
                        account.add_lose()
                        account.player_disconnect()
                        break
            except socket.error:
                player1.close()
                if account is not None:
                    account.player_disconnect()
                break


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


def create_server_screen(accounts_list):
    window = Tk()
    window.geometry('1000x600')
    window.title("My server")
    window.resizable(OFF, OFF)
    scroll = Scrollbar(window, orient=VERTICAL)
    view_accounts = Listbox(window, width=88, height=8, fg='blue', yscrollcommand=scroll.set, font=FONT)
    view_accounts.place(y=410)
    scroll.config(command=view_accounts.yview)
    scroll.place(x=800, y=400, height=200)
    Button(window, text='Clean accounts data', height=3, width=20,
           command=lambda: clean_accounts_data(accounts_list)).place(x=830, y=430)
    Button(window, text='exit', width=20, height=3, command=lambda: window.destroy()).place(x=830, y=500)
    for index, value in enumerate(LABELS_TEXT):
        Label(window, text=value, font=FONT, fg='red', bg='yellow').place(x=index * 140, y=370)
    Label(window, text="My IP is: " + my_ip(), fg='blue',
          bg='white', borderwidth=5, relief=SUNKEN).place(x=850, y=30)
    username, admit_act = StringVar(), StringVar()
    Label(window, text='Options').place(x=100, y=80)
    Label(window, text='Admin updates:', font=FONT, fg='blue', bg='white').place(x=100, y=20)
    Combobox(window, values=("Wins", "Loses", "Draws"), textvariable=admit_act).place(x=200, y=80)
    Entry(window, textvariable=username).place(x=220, y=20)
    window.bind("<FocusIn>", lambda event: show_account_data(view_accounts, accounts_list))
    window.bind("<Enter>", lambda event: show_account_data(view_accounts, accounts_list))
    window.mainloop()


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
                                     loses=acc[3], draws=acc[4], favorite_color=acc[5]))
    return accounts_list


def main():
    server = socket.socket()
    server.bind((my_ip(), 2020))
    print("good")
    server.listen(1)
    server.settimeout(0.2)
    mediation_variables = [[True, None], [True, None]]
    updates = []
    conn = connect("my database.db")
    curs = conn.cursor()
    accounts_list = build_my_accounts(curs)
    finish = [False]  # flag for all the threads
    for index in range(10):
        element = threading.Thread(target=help_client,
                                   args=(server, mediation_variables, updates, accounts_list, finish, index))
        element.start()
    threading.Thread(target=update_users_data, args=(updates, finish)).start()
    create_server_screen(accounts_list)
    finish[0] = True


if __name__ == '__main__':
    main()
