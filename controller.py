import cmd
import pandas as pd
import argparse
import os
import requests
from datetime import datetime

# URL of the Flask API
URL = "http://wot_server:5000/"

# The token for authentication
token = "63894cwflanedfognk35ffik2"

# The headers with the Bearer token
headers = {
    "Authorization": f"Admin {token}"
}

# Check the response status code and print the result
class Contorller(cmd.Cmd):
    """"""
    prompt = '> '
        
    
    def do_print(self, line):
        """Print account data. Usage: print account [<username>] or print account -A"""
        parser = argparse.ArgumentParser(prog='print account')
        parser.add_argument('username', type=str, help='Username of the account to print')
        parser.add_argument('-A', '--all', action='store_true', help='Print all accounts')

        try:
            args = line.split()
            if '--help' in args or '-h' in args:
                parser.print_help()
                return
            if args[0].lower() == 'account':
                if len(args) == 1:
                    print("Please specify a username or use -A to print all accounts.")
                    return
                elif args[1] == '-A':
                    response = requests.get(URL + "accounts", headers=headers, json={})
                    if response.status_code == 200:
                        print(self.json_to_df(response))
                    else:
                        print("Status code: ", response.status_code,  response.json().get("message"))
                # Otherwise, assume the second argument is the username and print the account
                else:
                    response = requests.get(URL + "accounts", headers=headers, json={"username": args[1]})
                    if response.status_code == 200:
                        print(self.json_to_df(response))
                    else:
                        print("Status code: " + str(response.status_code) + ",",  response.json().get("message"))

            else:
                print("Unknown command. Please use 'print account [<username>] or print account -A'")
        except IndexError:
            parser.print_help()
            
    def do_create(self, line):
        """Create a new account. Usage: create account <username> <password>
        conditions for a valid account:
            -> username and password both need to be between 0-10 characters
            -> username have to start with a letter
        """
        parser = argparse.ArgumentParser(prog='create account')
        parser.add_argument('username', type=str, help='Username of the account to create')
        parser.add_argument('password', type=str, help='Password of the account to create')
        try:
            args = line.split()
            if '--help' in args or '-h' in args:
                parser.print_help()
                return
            if args[0].lower() == 'account':
                response = requests.post(URL + "accounts", headers=headers, json={"username": args[1], "password": args[2]})
                print("Status code:" + str(response.status_code) + ",",  response.json().get("message"))
            else:
                print("Unknown command. Please use 'create account <username> <password>'")
        except IndexError:
            parser.print_help()
            
    def do_reset(self, line):
        """Reset an existing account. Usage: reset account <username>"""
        parser = argparse.ArgumentParser(prog='reset account')
        parser.add_argument('username', type=str, help='Username of the account to reset')
        try:
            args = line.split()
            if '--help' in args or '-h' in args:
                parser.print_help()
                return
            if args[0].lower() == 'account':
                if args[1] == "-A":
                    response = requests.put(URL + "accounts", headers=headers, json={})
                    if response.status_code == 204:
                        print("All accounts have been reset successfully.")
                        return
                    print("Status code:" + str(response.status_code) + ",",  response.json().get("message"))
                else:
                    response = requests.put(URL + "accounts", headers=headers, json={"username": args[1]})
                    if response.status_code == 204:
                        print(f"Account {args[1]} has been reset successfully.")
                        return
                    print("Status code:" + str(response.status_code) + ",",  response.json().get("message"))
            else:
                print("Unknown command. Please use 'reset account <username>")
        except IndexError:
            parser.print_help()
    
    def do_delete(self, line):
        """Delete an existing account. Usage: delete account <username>"""
        parser = argparse.ArgumentParser(prog='delete account')
        parser.add_argument('username', type=str, help='Username of the account to delete')
        try:
            args = line.split()
            if '--help' in args or '-h' in args:
                parser.print_help()
                return
            if args[0].lower() == 'account':
                response = requests.delete(URL + "accounts", headers=headers, json={"username": args[1]})
                if response.status_code == 204:
                    print(f"Account {args[1]} has been deleted successfully.")
                    return
                print("Status code:" + str(response.status_code) + ",",  response.json().get("message"))
            else:
                print("Unknown command. Please use 'delete account <username>'")
        except IndexError:
            parser.print_help()
            
            
    def do_free(self, line):
        """Free an existing account from suspension. Usage: free account <username>"""
        parser = argparse.ArgumentParser(prog='free account')
        parser.add_argument('username', type=str, help='Username of the account to free from suspension')
        try:
            args = line.split()
            if '--help' in args or '-h' in args:
                parser.print_help()
                return
            if args[0].lower() == 'account':
                response = requests.put(URL + "suspensions", headers=headers, json={"username": args[1]})
                if response.status_code == 204:
                    print(f"Account {args[1]} has been freed from suspension successfully.")
                    return
                print("Status code:" + str(response.status_code) + ",",  response.json().get("message"))
            else:
                print("Unknown command. Please use 'free account <username>'")
        except IndexError:
            parser.print_help()
            
    def do_ban(self, line):
        """Ban an existing account. Usage: ban account <username> <date>"""
        parser = argparse.ArgumentParser(prog='ban an account')
        parser.add_argument('username', type=str, help='Username of the account to ban')
        parser.add_argument('date', type=str, help='Date to ban the account')
        try:
            args = line.split()
            if '--help' in args or '-h' in args:
                parser.print_help()
                return
            if args[0].lower() == 'account':
                is_valid_data = self.is_valid_future_date(args[2])
                if is_valid_data is True:
                    response = requests.post(URL + "suspensions", headers=headers, json={"username": args[1], "ban_date": args[2]})
                    if response.status_code == 204:
                        print(f"Account {args[1]} has been banned successfully until {args[2]}.")
                        return
                    print("Status code:" + str(response.status_code) + ",",  response.json().get("message"))
                elif is_valid_data is None:
                    print("Date is already in the past. Please use a future date.")
                else:
                    print("Invalid date format. Please use DD/MM/YYYY.")
            else:
                print("Unknown command. Please use 'ban account <username>'")
        except IndexError:
            parser.print_help()
    
    def do_online(self, line):
        """"Check how many players are online"""
        response = requests.get(URL + "online", headers=headers)
        print("Status code:" + str(response.status_code) + ",",  response.json().get("message"))
        
    def do_set(self, line):
        """Set server options - allowing connections to server and allowing the server to make new battles"""
        parser = argparse.ArgumentParser(prog='set server options - new connections and new battles')
        parser.add_argument('option', type=str, help='Option to set (connections/battles)')
        parser.add_argument('value', type=str, help='Value to set (true/false)')
        try:
            args = line.split()
            if '--help' in args or '-h' in args:
                parser.print_help()
                return
            if args[0].lower() in ["connections", "battles"]:
                if args[1].lower() in ['true', 'false']:
                    response = requests.put(URL + "options", headers=headers, json={'option': args[0].lower(), 'value': args[1].lower()})
                    if response.status_code == 204:
                        print(f"Option {args[0].lower()} set to {args[1].lower()}.")
                        return
                else:
                    print("Invalid value. Please use 'true' or 'false'.")
            else:
                print("Invalid option. Please use 'connections' or 'battles'.")
        except IndexError:
            parser.print_help()
        

    def do_shutdown(self, line):
        """close terminal"""
        return True
    
    def emptyline(self):
        """Handle empty line input."""
        pass
    
    def do_clear(self,line):
        """clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def json_to_df(self,response):
        """convert json to dataframe to display accounts"""
        accounts_json = response.json()
        accounts_df = pd.DataFrame(accounts_json).transpose()
        return accounts_df[["Username", "Password", "Wins", "Losses", "Draws", "Points", "Color", "Status", "Ban date", "Battle ID"]]
    
    def is_valid_future_date(self, date_string):
        """Check if the date is in valid format of dd/mm/yyyy and hansn't passed yet"""
        try:
            date_obj = datetime.strptime(date_string, f'%d/%m/%Y')
            current_date = datetime.now()
            if date_obj.date() >= current_date.date():
                return True
            else:
                return None # date already passed
        except ValueError:
            # If parsing fails, the format is incorrect
            return False
    
if __name__ == '__main__':
    Contorller().cmdloop()