from firebase import firebase


def main():
    fire = firebase.FirebaseApplication("https://my-project-b9bb8.firebaseio.com/", None)
    data = {"Username": "adic212", "Password": "212928139",
            "Wins": 0, "Loses": 0, "Draws": 0,}
    fire.post("Accounts", data)


if __name__ == '__main__':
    main()
