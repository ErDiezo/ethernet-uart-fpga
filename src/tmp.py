import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print("created")
s.bind(("192.168.1.1", 16384))
print("bind")
s.listen(1)
print("listening")
conn, addr = s.accept()
print("connected : {}".format(addr))

conn.sendall(b"test")
print("sent")
received = conn.recv(2048)
print(received)

try:
	conn.close()
	s.close()
except Exception:
	pass

