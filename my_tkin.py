from tkinter import *

ACCOUNTS_FILE = 'accounts.txt'
LABELS_TEXT = ["Username", "Password", "Wins", "Loses", "Draws", "Color", "Server status"]


def create_server_screen():
    window = Tk()
    window.geometry('1200x800')
    window.title("My server")
    # window.resizable(OFF, OFF)
    clean_button = Button(window, text='Clean accounts data', height=3, command=lambda: clean_accounts_data())
    scroll = Scrollbar(window, orient=VERTICAL)
    view_accounts = Listbox(window, width=107, height=16, bg='gray', fg='blue', yscrollcommand=scroll.set, font=0)
    scroll.config(command=view_accounts.yview)
    for index, value in enumerate(LABELS_TEXT):
        Label(window, text=value, font=0, fg='red', bg='black').place(x=index*170, y=370)
    view_accounts.place(y=415)
    scroll.place(x=1185, y=400, height=400)
    clean_button.place(x=1000, y=270)
    return window


def clean_accounts_data():
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


def main():
    window = create_server_screen()
    window.mainloop()


if __name__ == '__main__':
    main()
