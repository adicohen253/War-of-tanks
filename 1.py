from sqlite3 import *


def insert_data(curs):
    curs.execute("INSERT INTO Accounts VALUES('adic23445', '212928139', 0, 0, 0, 'ff0000')")


def main():
    """hello world"""
    conn = connect('my database.db')
    c = conn.cursor()
    insert_data(c)
    conn.commit()
    c.close()


if __name__ == '__main__':
    main()
