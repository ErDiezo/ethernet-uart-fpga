import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
print(1)
s.bind(("192.168.1.1", 16384))
print(2)
s.listen(1)
print(3)
connected = False
while not connected:
	print('-')
	try:
		addr, port = s.accept()
		connected = True
	except socket.timeout:
		continue
print(addr, port)
