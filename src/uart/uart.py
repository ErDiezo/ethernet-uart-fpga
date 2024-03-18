import serial
import os, sys, signal



FILE_NAME_WITHOUT_IDX = "uart"
FILE_EXT = ".bin"
FILE_OPEN_MODE = "wb"

class UARTReceiver:
	"""
	Allows to receive files through UART communication.
	"""

	def __init__(self, port="/dev/ttyUSB0", baudrate=115200, dirPath=".") -> None:

		self._running = False # used in the mainloop

		self._dirPath = dirPath
		self._file = None

		self._serialCom = serial.Serial()
		self._serialCom.baudrate = baudrate
		self._serialCom.port = port # not in the initialization to avoid opening the port instantly


	def start(self) -> None:
		"""
		Starts the receiver.
		"""

		print("Start of the receiver")

		# get the new file name
		files = os.listdir(self._dirPath)
		
		fileIndex = -1
		for fileName in files:
			if fileName.startswith(FILE_NAME_WITHOUT_IDX) and fileName.endswith(FILE_EXT):
				try:
					# extract the integer value of from the file name
					i = int(fileName.split("_")[1].split(".")[0])
					if  i > fileIndex: fileIndex = i
				# skip files with invalid values
				except ValueError:
					pass
				except IndexError:
					pass
		fileIndex += 1
		fileName = FILE_NAME_WITHOUT_IDX + str(fileIndex) + FILE_EXT

		self._file = open(os.path.join(self._dirPath, fileName), FILE_OPEN_MODE)
		print("File opened : ", fileName)

		self._running = True

		self._uartloop()


	def stop(self, signal=None, frame=None) -> None:
		"""
		Stops the receiver.
		"""
		self._running = False
		self._file.close()
		self._serialCom.close()
		print("File closed")


	def _uartloop(self) -> None:
		"""
		Infinite loop used to receive data from the UART serial port.
		"""
		self._serialCom.open()

		while self._running:
			try:
				received = self._serialCom.read()
				print(received)
				self._file.write(received)
			except OSError:
				pass




if __name__ == "__main__":
	port = "/dev/ttyUSB0"
	baudrate = 115200
	dirPath = "."
	if len(sys.argv) == 2:
		port = sys.argv[1]
	elif len(sys.argv) == 3:
		port = sys.argv[1]
		dirPath = sys.argv[2]
	elif len(sys.argv) >= 4:
		port = sys.argv[1]
		baudrate = sys.argv[2]
		dirPath = sys.argv[3]

	receiver = UARTReceiver(port, baudrate, dirPath)

	signal.signal(signal.SIGINT, receiver.stop)

	receiver.start()