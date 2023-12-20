CMD_FIELD_LENGTH = 16	# Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4   # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10**LENGTH_FIELD_LENGTH-1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

PROTOCOL_CLIENT = {
"login_msg" : "LOGIN",
"logout_msg" : "LOGOUT"
}

PROTOCOL_SERVER = {
"login_ok_msg" : "LOGIN_OK",
"login_failed_msg" : "ERROR"
}

ERROR_RETURN = None  # What is returned in case of an error

def zero_elimination(value):
	var = ""
	length = len(var)
	for x in value:
		if x == "0" and length == 0:
			pass
		else:
			var += x
		length = len(var)
	if len(var) == 0:
		var = 0
	return var


def build_message(cmd, data):
	"""
	Gets command name (str) and data field (str) and creates a valid protocol message
	Returns: str, or None if error occurred
	"""
	if not type(cmd) == str or not type(data) == str:
		return ERROR_RETURN
	cmd_length = len(cmd)
	data_length = len(data)
	length_field_zeros = ""
	if data_length < 10:
		length_field_zeros = "000"
	elif data_length < 100:
		length_field_zeros = "00"
	elif data_length < 1000:
		length_field_zeros = "0"
	elif data_length >= 10000:
		return ERROR_RETURN
	if cmd_length > CMD_FIELD_LENGTH:
		return ERROR_RETURN
	remained_cmd_field_length = CMD_FIELD_LENGTH - cmd_length
	cmd_space = ""
	num = 0
	while not num == remained_cmd_field_length:
		cmd_space += " "
		num += 1
	full_msg = cmd + cmd_space + DELIMITER + length_field_zeros + str(data_length) + DELIMITER + data
	return full_msg


def parse_message(data):
	"""
	Parses protocol message and returns command name and data field
	Returns: cmd (str), data (str). If some error occured, returns None, None
	"""
	cmd = ""
	msg = ""
	delimiter_num = 0
	num = 0
	for x in data:
		if not x == " " and not x == DELIMITER:
			cmd += x
			num += 1
		elif x == DELIMITER:
			break
		else:
			num += 1
	for x in data:
		if x == DELIMITER:
			delimiter_num += 1
		elif delimiter_num == 2:
			msg += x
	cmd_length = len(cmd)
	msg_length = len(msg)
	var = data[17:21]
	new_var = zero_elimination(var)
	try:
		new_var = int(new_var)
	except:
		return (None, None)
	if not cmd_length <= CMD_FIELD_LENGTH or not num == CMD_FIELD_LENGTH:
		return (None, None)
	elif not msg_length <= MAX_DATA_LENGTH or not delimiter_num == 2 or not new_var == msg_length:
		return (None, None)
	else:
		return (cmd, msg)


def split_data(data, expected_fields):
	"""
	Helper method. gets a string and number of expected fields in it. Splits the string
	using protocol's data field delimiter (|#) and validates that there are correct number of fields.
	Returns: list of fields if all ok. If some error occured, returns None
	"""
	data_list = []
	word = ""
	length_of_data = len(data)
	data_delimiters = data.count(DATA_DELIMITER)
	fields = data_delimiters + 1
	if length_of_data == 0 and expected_fields == 0:
		return data_list
	elif length_of_data > 0 and expected_fields == 0:
		return ERROR_RETURN
	elif length_of_data == 0 and expected_fields > 0:
		return ERROR_RETURN
	elif not fields == expected_fields or data[0] == DATA_DELIMITER or data[-1] == DATA_DELIMITER:
		return ERROR_RETURN
	else:
		for x in data:
			if not x == DATA_DELIMITER:
				word += x
			else:
				data_list.append(word)
				word = ""
		data_list.append(word)
	return data_list


def join_data(msg_fields):
	"""
	Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter.
	Returns: string that looks like cell1#cell2#cell3
	"""
	new_list = []
	for x in msg_fields:
		new_list.append(str(x))
	string = "#".join(new_list)
	return string


def main():
	string1 = ""
	list1 = ["apples", 2, "lemons", "dragons"]
	data1 = split_data(string1, 0)
	data2 = join_data(list1)
	data3 = build_message("LOGIN", "")
	data4 = parse_message("LOGIN           |0009|user#pass")
	print(data1)
	print(data2)
	print(list1)
	print(data3)
	print(data4)
	print("a")

if __name__ == "__main__":
	main()
