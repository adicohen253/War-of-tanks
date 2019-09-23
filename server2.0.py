import threading
import socket
from tkinter import *
import pandas as pd

LABELS_TEXT = ["Username", "Password", "Wins", "Loses", "Draws", "Color", "Server status"]
ACCOUNTS_FILE = "accounts.txt"
COMMANDS = pd.DataFrame(columns=["command", "description"], data=[
    ["report", "show records of player's stats"], ["clean", "delete all data of the accounts"]])


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
        return f"{self.__username} {' '*5} {self.__password} {' '*5} {self.__wins} {' '*5} {self.__loses} {' '*5}" \
               f"{self.SERVER_STATUSES[self.__is_connect]}"


def clean_accounts_data(accounts_list, view):
    restart_accounts = []
    with open(ACCOUNTS_FILE, "r") as acc:
        for line in acc:
            parts = line.split(" ")
            parts[5], parts[7], parts[9] = "0", "0", "0"
            parts[11] = "ff0000"
            parts = " ".join(parts) + "\n"
            restart_accounts.append(parts)
    with open(ACCOUNTS_FILE, "w") as new_acc:
        for account in restart_accounts:
            new_acc.write(account)
    view.delete(0, END)
    for acc in accounts_list:
        acc.clean_data()
        view.insert(END, str(acc))


def is_exist(user, is_login=False):
    """checks in accounts list if account name like this is already exist"""
    with open(ACCOUNTS_FILE, 'r') as accounts:
        accounts = accounts.read().split("\n")[:-1]  # last var is empty line
        for account in accounts:
            data = account.split(" ")
            if data[1] == user[0]:
                if not is_login:
                    return True
                else:
                    if data[3] == user[1]:
                        return True
    return False


def register_new_player(new_account_data, accounts_list):
    """add the new account the the list
    argument:
        username = type: string
        password = type: string
    """
    with open(ACCOUNTS_FILE, 'a') as accounts:
        accounts.write("Username: " + new_account_data[0]
                       + " password: " + new_account_data[1] + " victory: 0 defeat: 0 draws: 0 color: ff0000\n")
    new_account = Account(username=new_account_data[0], password=new_account_data[1],
                          wins=0, loses=0, draws=0, favorite_color="ff0000")
    new_account.player_connect()
    accounts_list.append(new_account)


def register_player(client, accounts_list):
    """return to the player if username is already exist in the accounts list
    argument:
        client: type - socket
        players_data: type - pandas.DataFrame, holds the data of the users
    """
    new_player_data = client.recv(41).decode().split(",")
    already_exist = is_exist(new_player_data)
    if already_exist:
        client.send(b"N")
    else:
        client.send(b"Y")
        register_new_player(new_player_data, accounts_list)
        print("A new player signed up, is username is: " + new_player_data[0])
        return new_player_data[0]


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
                client.send(b"T")
                account.player_connect()
                return account_to_check[0]
    if not exist:
        client.send(b"F")


def update_user_wins_or_loses(players_to_update):
    while True:
        for var in players_to_update:
            username, act = var[0], var[1]
            with open(ACCOUNTS_FILE, "r") as my_file:
                accounts = []
                for line in my_file:
                    parts = line.split(" ")
                    if parts[1] == username:
                        if act == "V":
                            parts[5] = str(int(parts[5]) + 1)
                        elif act == "D":
                            parts[7] = str(int(parts[7]) + 1)
                        elif act == "E":
                            parts[9] = str(int(parts[9]) + 1)
                        elif act == "C":
                            parts[11] = var[2]
                            parts.append(" \n")
                        accounts.append(" ".join(parts))
                    else:
                        accounts.append(line)
            with open(ACCOUNTS_FILE, "w") as my_file:
                for a in accounts:
                    my_file.write(a)
            players_to_update.remove(var)


# when get ip from first player append it to the list and not replace the current ip
def help_client(server, codes, update_users, accounts_list):
    while True:
        server.listen(1)
        player1, address1 = server.accept()
        username = ""
        while True:
            try:
                request = player1.recv(5).decode()
                if request == "exit ":
                    player1.close()
                    for account in accounts_list:
                        if account.get_username() == username:
                            account.player_disconnect()
                    break
                elif request == "Exit ":
                    player1.close()
                    break

                elif request == "info ":
                    username = register_player(player1, accounts_list)
                elif request == "login":
                    username = player_login(player1, accounts_list)

                elif request == "color":
                    send_color(player1, username, accounts_list)

                elif request == "Color":  # change the player's color in the data base - need to turn to function...
                    new_color = player1.recv(6).decode()
                    update_users.append([username, "C", new_color])
                    for account in accounts_list:
                        if account.get_username() == username:
                            account.change_color(new_color)

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
                            update_users.append([username, act])
                            for account in accounts_list:
                                if account.get_username() == username:
                                    if act == "V":
                                        account.add_win()
                                    elif act == "D":
                                        account.add_lose()
                                    elif act == "E":
                                        account.add_draws()
                        elif request == "Situ":  # client exit the game
                            player1.close()
                            update_users.append([username, "D"])
                            for account in accounts_list:
                                if account.get_username() == username:
                                    account.add_lose()
                                    account.player_disconnect()
                            break

                    except socket.error:
                        print(username + " illegal exit from battle count as losing")
                        update_users.append([username, "D"])
                        player1.close()
                        for account in accounts_list:
                            if account.get_username() == username:
                                account.add_lose()
                                account.player_disconnect()
                        break
            except socket.error:
                player1.close()
                if username != "":
                    for account in accounts_list:
                        if account.get_username() == username:
                            account.player_disconnect()
                    print(username + " disconnect at unrecognized way")
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


def build_my_account_list():
    accounts_list = []
    with open(ACCOUNTS_FILE, "r") as my_file:
        for line in my_file:
            data = line.split(" ")
            accounts_list.append(Account(data[1], data[3], int(data[5]), int(data[7]), int(data[9]), data[11]))
    return accounts_list


def create_server_screen(accounts_list):
    window = Tk()
    window.geometry('1200x800')
    window.title("My server")
    # window.resizable(OFF, OFF)
    scroll = Scrollbar(window, orient=VERTICAL)
    view_accounts = Listbox(window, width=107, height=16, bg='gray', fg='blue', yscrollcommand=scroll.set, font=0)
    scroll.config(command=view_accounts.yview)
    clean_button = Button(window, text='Clean accounts data', height=3,
                          command=lambda: clean_accounts_data(accounts_list, view_accounts))
    for index, value in enumerate(LABELS_TEXT):
        Label(window, text=value, font=0, fg='red', bg='black').place(x=index*170, y=370)
    for account in accounts_list:
        view_accounts.insert(END, str(account))
    view_accounts.place(y=415)
    scroll.place(x=1185, y=400, height=400)
    clean_button.place(x=1000, y=270)
    window.mainloop()
    return window


def main():
    print("wait to connect between players\nmy ip is: " + my_ip())
    server = socket.socket()
    server.bind((my_ip(), 2020))
    mediation_variables = [[True, None], [True, None]]
    updates = []
    accounts_list = build_my_account_list()
    for _ in range(10):
        element = threading.Thread(target=help_client, args=(server, mediation_variables, updates, accounts_list))
        element.start()
    threading.Thread(target=update_user_wins_or_loses, args=([updates])).start()
    create_server_screen(accounts_list)


if __name__ == '__main__':
    main()
