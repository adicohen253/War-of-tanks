from tkinter import *


def main():
    window = Tk()
    window.geometry('700x700')
    window.resizable(False, False)
    window.title('Server manager')
    lf = LabelFrame(window, text="User's data", fg='blue', width=700, height=300)
    lf.place(y=400)
    window.mainloop()


if __name__ == '__main__':
    main()
