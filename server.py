import chatlib
import socket
import random
import select
import json
import requests

"""
users = {"test": {"password": "test", "score": 300, "questions_asked": []}, "yossi": {"password": "123", "score": 500, "questions_asked": []},
		   "master": {"password": "master", "score": 200, "questions_asked": []}}
questions = {2313: {"question": "How much is 2+2?", "answers": ["3","4","2","1"], "correct": 2},
		   4122: {"question": "What is the capital of France?","answers": ["Lion", "Marseille", "Paris", "Montpellier"], "correct": 3}} 
"""
users = {}
questions = {}
logged_clients = {} # a dictionary of client hostnames to usernames
ERROR_MSG = "ERROR"
SERVER_PORT = 5678
SERVER_IP = "0.0.0.0"
messages_to_send = []
client_sockets = []

def setup_socket():
	"""
	Creates new listening socket and returns it
	Recieves: -
	Returns: the socket object
	"""
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind((SERVER_IP, SERVER_PORT))
	server_socket.listen()
	return server_socket


def build_and_send_message(conn, cmd, data):
	global messages_to_send
	message = chatlib.build_message(cmd, data)
	if message == None:
		raise AssertionError("Problem with either code or data")
	else:
		print("[SERVER] ", conn.getpeername(), "msg: ", message)
		messages_to_send.append((conn, message))


def print_client_sockets():
	global logged_clients
	for x in logged_clients:
		print(x)


def recv_message_and_parse(conn):
	full_msg = conn.recv(1024).decode()
	cmd, data = chatlib.parse_message(full_msg)
	if cmd == None:
		print("Client disconnected unexpectedly")
		return cmd, data
	else:
		print("[CLIENT] ", conn.getpeername(), " msg: ", full_msg, " ")
		return cmd, data


def load_questions():
	"""
	Loads questions bank from file
	Recieves: -
	Returns: -
	"""
	global questions
	f = open("questions.txt", "r")
	questions = json.loads(f.read())
	f.close()


def load_user_database():
	"""
	Loads users list from file
	Recieves: -
	Returns: -
	"""
	global users
	f = open("users.txt", "r")
	users = json.loads(f.read())
	f.close()

		
def send_error(conn, error_msg):
	"""
	Sends error message with given message
	Recieves: socket, message error string from called function
	Returns: None
	"""
	global ERROR_MSG
	build_and_send_message(conn, ERROR_MSG, error_msg)


def handle_getscore_message(conn, username):
	global users
	build_and_send_message(conn, "YOUR_SCORE", str(users[username]["score"]))


def func(e):
	return e["score"]


def handle_highscore_message(conn):
	global users
	users_list = []
	users_dic = {}
	for x in users:
		users_dic["name"] = x
		users_dic["score"] = users[x]["score"]
		users_list.append(users_dic)
		users_dic = {}
	users_list.sort(key = func, reverse = True)
	message = ""
	for x in users_list:
		message += x["name"] + ": " + str(x["score"]) + "\n"
	build_and_send_message(conn, "ALL_SCORE", message)


def handle_logout_message(conn):
	"""
	Closes the given socket. Also removes user from logged_users dictionary
	Recieves: socket
	Returns: None
	"""
	global logged_clients
	global client_sockets
	if conn.getpeername() in logged_clients:
		logged_clients.pop(conn.getpeername())
	print("{} has disconnected".format(conn.getpeername()))
	client_sockets.remove(conn)
	conn.close()


def handle_logged_message(conn):
	global logged_clients
	message = ""
	length = len(logged_clients)
	num = 1
	for client in logged_clients:
		if not num == length:
			message += logged_clients[client] + ", "
			num += 1
		else:
			message += logged_clients[client]
	build_and_send_message(conn, "LOGGED_ANSWER", message)


def handle_login_message(conn, data):
	"""
	Gets socket and message data of login message. Checks if user and password exist and match
	If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
	Recieves: socket and data
	Returns: None (sends answer to client)
	"""
	global users
	global logged_clients
	msg_data_list = chatlib.split_data(data, 2)
	if msg_data_list == None:
		send_error(conn, "Something wrong with your username or password. Please try again")
	else:
		username = msg_data_list[0]
		pasword = msg_data_list[1]
		if username in users:
			if users[username]["password"] == pasword:
				logged_clients[conn.getpeername()] = username
				build_and_send_message(conn, "LOGIN_OK", "")
			else:
				send_error(conn, "Error! Password does not match!")
		else:
			send_error(conn, "Error! Username does not exist!")


def handle_client_message(conn, cmd, data):
	"""
	Gets message code and data and calls the right function to handle command
	Recieves: socket, message code and data
	Returns: None
	"""
	global logged_clients
	if cmd == "LOGIN":
		handle_login_message(conn, data)
	elif cmd == "LOGOUT":
		handle_logout_message(conn)
	elif cmd == "MY_SCORE":
		handle_getscore_message(conn, logged_clients[conn.getpeername()])
	elif cmd == "LOGGED":
		handle_logged_message(conn)
	elif cmd == "HIGHSCORE":
		handle_highscore_message(conn)
	elif cmd == "GET_QUESTION":
		handle_question_message(conn, logged_clients[conn.getpeername()])
	elif cmd == "SEND_ANSWER":
		handle_answer_message(conn, logged_clients[conn.getpeername()], data)
	else:
		send_error(conn, "Command is not known")


def load_questions_from_web(username):
	global questions
	global users
	condition1 = False
	condition2 = False
	try:
		f = open("questions.txt", "r")
		questions = json.loads(f.read())
	except:
		print("file does not exist yet")
		r = requests.get('https://opentdb.com/api.php?amount=50&type=multiple')
		web_question = json.loads(r.text)['results'][random.randint(1, 49)]
		answers = web_question['incorrect_answers'] + [web_question['correct_answer']]
		random.shuffle(answers)
		correct_answer_index = answers.index(web_question['correct_answer']) + 1
		modified_web_question = {}
		modified_web_question['question'] = web_question['question']
		modified_web_question['answers'] = answers
		modified_web_question['correct'] = correct_answer_index
	else:
		while condition1 == False:
			r = requests.get('https://opentdb.com/api.php?amount=50&type=multiple')
			web_question = json.loads(r.text)['results'][random.randint(1, 49)]
			answers = web_question['incorrect_answers'] + [web_question['correct_answer']]
			random.shuffle(answers)
			correct_answer_index = answers.index(web_question['correct_answer']) + 1
			modified_web_question = {}
			modified_web_question['question'] = web_question['question']
			modified_web_question['answers'] = answers
			modified_web_question['correct'] = correct_answer_index
			for question_number in questions:
				if questions[question_number]['question'] == modified_web_question['question']:
					if int(question_number) in users[username]['questions_asked']:
						condition1 = False
						condition2 = False
						break
					else:
						condition1 = True
						condition2 = True
						break
				else:
					condition1 = True
	if condition2 == True:
		users[username]['questions_asked'] = users[username]['questions_asked'] + [int(question_number)]
		update_users_file()
		return question_number + '#' + questions[question_number]['question'] + '#' + '#'.join(questions[question_number]['answers'])
	else:
		length = len(questions) + 1
		questions[str(length)] = modified_web_question
		update_questions_file()
		users[username]['questions_asked'] = users[username]['questions_asked'] + [length]
		update_users_file()
		return str(length) + '#' + questions[str(length)]['question'] + '#' + '#'.join(questions[str(length)]['answers'])


def handle_question_message(conn, username):
	global logged_clients
	random_question = load_questions_from_web(username)
	if random_question == None:
		build_and_send_message(conn, "NO_QUESTIONS", "")
	else:
		build_and_send_message(conn, "YOUR_QUESTION", random_question)


def update_users_file():
	global users
	f = open("users.txt", "w")
	f.write(json.dumps(users))
	f.close()


def update_questions_file():
	global questions
	f = open("questions.txt", "w")
	f.write(json.dumps(questions))
	f.close()


def handle_answer_message(conn, username, data):
	global users
	global questions
	question_answer = chatlib.split_data(data, 2)
	if int(question_answer[1]) == questions[question_answer[0]]["correct"]:
		users[username]["score"] += 5
		update_users_file()
		build_and_send_message(conn, "CORRECT_ANSWER", "")
	else:
		build_and_send_message(conn, "WRONG_ANSWER", str(questions[question_answer[0]]["correct"]))


def main():
	global users
	global logged_clients
	global messages_to_send
	global client_sockets
	print("Welcome to Trivia Server!")
	server_socket = setup_socket()
	while True:
		load_user_database()
		try:
			ready_to_read, ready_to_write, in_errors = select.select([server_socket] + client_sockets, client_sockets, [])
		except:
			print("ready_to_read is empty")
		else:
			for current_socket in ready_to_read:
				if current_socket == server_socket:
					client_socket, client_address = server_socket.accept()
					print("New Client Joined! ", client_address)
					client_sockets.append(client_socket)
				else:
					(cmd, data) = recv_message_and_parse(current_socket)
					if cmd == None:
						if current_socket.getpeername() in logged_clients:
							logged_clients.pop(current_socket.getpeername())
						print("{} has disconncted".format(current_socket.getpeername()))
						client_sockets.remove(current_socket)
						current_socket.close()
					else:
						handle_client_message(current_socket, cmd, data)
			for socket_message in messages_to_send:
				(client_socket, message) = socket_message
				client_socket.send(message.encode())
			messages_to_send = []


if __name__ == '__main__':
	main()
	