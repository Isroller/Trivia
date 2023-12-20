import socket
import chatlib

SERVER_IP = "127.0.0.1"  # server will run on same computer as client
SERVER_PORT = 5678
TIMEOUT_IN_SECONDS = 3

def build_and_send_message(conn, code, data):
    msg = chatlib.build_message(code, data)
    if msg == None:
        raise Exception("Problem with either code or data")
    else:
        try:
            conn.send(msg.encode())
        except:
            print("host disconnected unexpectedly")
            exit()


def recv_message_and_parse(conn):
    full_msg = conn.recv(1024).decode()
    cmd, data = chatlib.parse_message(full_msg)
    return cmd, data


def connect():
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect((SERVER_IP, SERVER_PORT))
    return my_socket


def login(conn):
    cmd = "ERROR"
    while cmd == "ERROR":
        username = input("Please enter your username:\n")
        password = input("Please enter your password:\n")
        list1 = []
        list1.append(username)
        list1.append(password)
        data = chatlib.join_data(list1)
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], data)
        cmd, data = recv_message_and_parse(conn)
        if cmd == "ERROR":
            print(cmd, " ", data, "\n")
    if cmd == None:
        print("We apologize but we are experiencing a problem with the server, please try to log in again later")
        return None
    else:
        return cmd


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")


def build_send_recv_parse(conn, cmd, data):
    build_and_send_message(conn, cmd, data)
    try:
        cmd, returned_data = recv_message_and_parse(conn)
    except:
        return None, None
    else:
        return cmd, returned_data


def get_score(conn):
    msg, data = build_send_recv_parse(conn, "MY_SCORE", "")
    if msg == None:
        exit()
    else:
        print("Your score is: " + data)


def get_allscores(conn):
    msg, data = build_send_recv_parse(conn, "HIGHSCORE", "")
    if msg == None:
        exit()
    else:
        print(data)


def play_question(conn):
    msg, data = build_send_recv_parse(conn, "GET_QUESTION", "")
    try:
        expected_fields = data.count("#") + 1
    except:
        print("Sorry. A problem occured with the server. Goodbye")
        exit()
    else:
        string_list = chatlib.split_data(data, expected_fields)
        if not msg == "NO_QUESTIONS":
            num = 0
            for x in string_list:
                if num == 0:
                    print('question number '+ x + ":")
                    num += 1
                elif num == 1:
                    print(x)
                    num += 1
                elif num < 6:
                    print('(' + str(num - 1) + ') ' + x)
                    num += 1
            answer = input("Please choose an answer[1, 2, 3, 4]:\n")
            while not answer == "1" and not answer == "2" and not answer == "3" and not answer == "4":
                answer = input("Please choose a valid answer[1, 2, 3, 4]:\n")
            complete_answer = string_list[0] + "#" + answer
            msg, data = build_send_recv_parse(conn, "SEND_ANSWER", complete_answer)
            if msg == "CORRECT_ANSWER":
                print("Correct. Well done!")
            elif msg == "WRONG_ANSWER":
                print("Incorrect answer. Sorry!\nThe correct answer is number " + data)
        elif msg == "NO_QUESTION":
            print("No more questions. Goodbye!")


def get_logged_users(conn):
    msg, data = build_send_recv_parse(conn, "LOGGED", "")
    print("The users that are currently logged are: " + data)


def main():
    conn = connect()
    result = login(conn)
    if not result == None:
        answer = input("Please choose which action you'd like to take:\n(A) play a question\n(B) get logged users\n(C) get your score\n(D) get all the scores\n(E) log out\n").upper()
        while not answer == "E":
            while not answer == "A" and not answer == "B" and not answer == "C" and not answer == "D" and not answer == "E":
                answer = input("Please enter a valid answer [A, B, C, D, E]:\nWhich action you'd like to take:\n(A) play a question\n(B) get logged users\n(C) get your score\n(D) get all the scores\n(E) log out\n").upper()
            if answer == "C":
                get_score(conn)
                answer = input("Please choose which action you'd like to take:\n(A) play a question\n(B) get logged users\n(C) get your score\n(D) get all the scores\n(E) log out\n").upper()
            elif answer == "D":
                get_allscores(conn)
                answer = input("Please choose which action you'd like to take:\n(A) play a question\n(B) get logged users\n(C) get your score\n(D) get all the scores\n(E) log out\n").upper()
            elif answer == "B":
                get_logged_users(conn)
                answer = input("Please choose which action you'd like to take:\n(A) play a question\n(B) get logged users\n(C) get your score\n(D) get all the scores\n(E) log out\n").upper()
            elif answer == "A":
                play_question(conn)
                answer = input("Please choose which action you'd like to take:\n(A) play a question\n(B) get logged users\n(C) get your score\n(D) get all the scores\n(E) log out\n").upper()
    print("Logging out! Goodbye!:)")
    logout(conn)
    conn.close()

main()
