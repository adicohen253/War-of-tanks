import time
from sqlite3 import *
from server import Account


def build_my_accounts(db_cursor):
    db_cursor.execute("SELECT * FROM Accounts")
    data = [list(x) for x in db_cursor.fetchall()]
    accounts_list = []
    for acc in data:
        accounts_list.append(Account(username=acc[0], password=acc[1], wins=acc[2],
                                     loses=acc[3], draws=acc[4], favorite_color=acc[5], ban_until=acc[6]))
    accounts_list.sort(key=lambda x: x.get_username())
    return accounts_list


def main():
    a = time.struct_time((0, 0, 0, 0, 0, 0, 0, 0, 0))
    a = time.mktime(a)




if __name__ == '__main__':
    main()
