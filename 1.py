import time


def main():
    # a = "14/10/2019"
    # b = a.split("-")
    # a = b[0].split("/") + b[1].split(":")
    # a = [int(value) for value in a]
    # c = time.struct_time((a[2], a[1], a[0], a[3], a[4], 0, 0, 0, 0))
    a = time.struct_time((0, 0, 0, 0, 0, 0,0,0,0))
    print(a)


if __name__ == '__main__':
    main()
