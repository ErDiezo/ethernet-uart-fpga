# ===========================================================================================
# ***************************************** LICENSE *****************************************
# ===========================================================================================
# Copyright (c) 2024, CATIE
# SPDX-License-Identifier: Apache-2.0

# ===========================================================================================
# *************************************** DESCRIPTION ***************************************
# ===========================================================================================
# This file is used to define the server.
# It uses the TCP/IP protocol, and transfers data threw an ethernet connexion.


# ===========================================================================================
# **************************************** LIBRARIES ****************************************
# ===========================================================================================
# Libraries used for this application.
import logging
import threading
import socket
import os
from datetime import datetime

import time



# ===========================================================================================
# ***************************************** MODULES *****************************************
# ===========================================================================================
# Custom libraries created for this application

pass

# ===========================================================================================
# **************************************** VARIABLES ****************************************
# ===========================================================================================
# Variable declaration/definition

# Logs
logsFile = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
# logsFile = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day


# ===========================================================================================
# ****************************************** CLASS ******************************************
# ===========================================================================================
# Variable declaration/definition

class Server(threading.Thread):
	"""
    Represents a server-side socket.
    For the parameters not mentionned here, check the socket.socket parameters.
    
    :param address: the address of the socket, first the ipv4, second the port
    :type address: tuple[str, int]
    :param logger: the logger used by the server
    :type logger: logging.Logger
	"""
	def __init__(self,
				address,
				socketFamily=socket.AF_INET,
				socketType=socket.SOCK_STREAM,
				socketProto=-1,
				socketfileno=None,
				bufferSize = 1024,
				threadGroup=None,
				threadTarget=None,
				threadName=None,
				threadArgs=list(),
				threadKwargs=dict(),
				threadDaemon=None,
				logger=None) -> None:
		
		super().__init__(group=threadGroup, target=threadTarget, name=threadName, daemon=threadDaemon)

		self._address = address
		self._args = threadArgs
		self._kwargs = threadKwargs
		self._socketInfos = (socketFamily, socketType, socketProto, socketfileno)
		self._bufferSize = bufferSize
		try:
			self._socket = socket.socket(*self._socketInfos)
			self._socket.settimeout(1)
		except Exception as e:
			raise e
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._serverOpen = False
		self._connectedSocket = None # List : 0 is the socket, 1 the adress, 2 the ID
		self._logger = logger
		self._receivedData = list()
    

	def _open(self) -> None:
		"""
        Opens the socket's connexion on the address given in the initialization.
		"""

		self._logger.info("Opening the server connexion...")
		try:
			self._socket.bind(self._address)
			self._socket.listen(1)
		except Exception as e:
			self._logger.error("Error while opening the connexion on %s:%d: %s. Socket not opened.", self._address[0], self._address[1], e)
			raise e
		else:
			self._serverOpen = True
			self._logger.info("Server connexion opened. Listening on %s:%i", self._address[0], self._address[1])


	def _close(self) -> None:
		"""
        Closes the socket.
		"""

		if not self._serverOpen:
			self._logger.info("The server is already closed")
			return
		self._logger.info("Closing connexion...")
		self._socket.close()
		self._serverOpen = False
		self._socket = socket.socket(*self._socketInfos)
		self._logger.info("Server connexion closed")
    
    
	def _accept(self) -> None:
		"""
		Accepts a connexion.
		"""
		self._connectedSocket = None

		while self._serverOpen and self._connectedSocket == None:
			try:
				conn, addr = self._socket.accept()
				conn.setblocking(0)
				self._connectedSocket = [conn, addr]
				self._logger.info("Accepted connexion from %s:%d", addr[0], addr[1])
			except socket.timeout:
				if self._serverOpen:
					continue
				else:
					return
			except OSError:
				continue


	def _receiveData(self) -> bytes:
		"""
		Receives data from the client.
		The received data is stored in the _receivedData variable then returned.
		"""
		try:
			newData = self._connectedSocket[0].recv(self._bufferSize)
			allData = newData
			while len(newData) >= self._bufferSize:
				newData = self._connectedSocket[0].recv(self._bufferSize)
				allData += newData
		except BlockingIOError:
			return None
		
		if allData == b"\xff":
			# The connexion has been closed -> reset
			self._connectedSocket[0].close()
			self._logger.info("%s:%d disconnected", self._connectedSocket[1][0], self._connectedSocket[1][1])
			self._connectedSocket = None
		elif allData:
			self._receivedData.append(allData)
		return allData
	

	def sendCommand(self, hw: int, cmd: int, info: int=0) -> None:
		"""
		Sends a command to the client, then receive the response from it that is added to the variable and returned.
		hw is an integer between 0 and 1.
		cmd is an integer between 0 and 7.
		info is an integer between 0 and 15.
		"""

		# To send data use the sendData method
		if hw == 0 and cmd == 1:
			self._logger.warning("To send data use the sendData method")
			return

		self._sendCommand(hw, cmd, info)
	

	def _sendCommand(self, hw: int, cmd: int, info: int=0) -> None:
		"""
		Sends a command to the client.
		hw is an integer between 0 and 1.
		cmd is an integer between 0 and 7.
		info is an integer between 0 and 15.
		"""
		# Verifying a client is connected
		if not self._connectedSocket:
			raise socket.error("No client is connected")
		
		# Verifying the given parameters
		if not isinstance(hw, int) or (hw != 0 and hw != 1):
			self._logger.error("Error while sending command (%d %d %d) : hw has to be 0 or 1.", hw, cmd, info)
			raise socket.error("hw has to be 0 or 1")
			return
		if not isinstance(cmd, int) or cmd < 0 or cmd > 7:
			self._logger.error("Error while sending command (%d %d %d) : cmd has to be an integer between 0 and 7 included.", hw, cmd, info)
			raise socket.error("cmd has to be an integer between 0 and 7 included")
			return
		if not isinstance(info, int) or info < 0 or info > 15:
			self._logger.error("Error while sending command (%d %d %d) : info has to be an integer between 0 and 15 included.", hw, cmd, info)
			raise socket.error("info has to be an integer between 0 and 15 included")
			return
		
		# Setting the data to send
		toSend = bytes([(hw << 7) | (cmd << 4) | info])

		# Sending the data
		try:
			if __name__ != "__main__":
				self._connectedSocket[0].sendall(toSend)
		except Exception as e:
			self._logger.error("Error while sending command (%d %d %d): %s", hw, cmd, info, e)
			raise socket.error(e)
		else:
			self._logger.info("Command %s sent", "".join([format(byte, '08b') for byte in toSend]))
	

	def sendFile(self, path : str, info : int) -> None:
		"""
		Sends a whole file to the client.
		Path is the path to the file to send. It has to be binary.
		Info is the integer data to send with the command.
		"""
		
		# Verifying if the file is really a file
		if not os.path.isfile(path):
			self._logger.error("%s is not a file. Nothing was sent", path)
			raise FileNotFoundError("{} is not a file. Nothing was sent".format(path))
		
		self._logger.info("Sending file %s", path)

		# Sending the file
		amountOfDataSent = 0
		try:
			with open(path, "rb") as file:
				readData = file.read(self._bufferSize - 1) # -1 for the command part
				while readData:
					# Send the message with the command before.
					# The function bytes(...) converts the 1 (HW + CMD) for the higher 4 bits
					# and the info (0..7) for the lower 4 bits into a byte.
					# Then the data to send is concatenated, and all is sent.
					self._connectedSocket[0].sendall(bytes([(1 << 4) | info]) + readData)
					amountOfDataSent += len(readData)

					readData = file.read(self._bufferSize - 1) # -1 for the command part
		except Exception as e:
			self._logger.error("Error while sending data (still %do sent) : %s", amountOfDataSent, e)
			raise socket.error(e)
		else:
			self._logger.info("Data sent (%do)", amountOfDataSent)


	def run(self) -> None:
		self._open()
		
		# TODO : Maybe @await ?
		while self._serverOpen: # Server open
			
			if not self._connectedSocket:
				# Looking for a connexion
				self._logger.debug("Looking for a connexion")
				self._accept()
			
				# Asks the identification to the client
				if not self.askIdentification():
					self._connectedSocket[0].close()
					self._logger.info("The connexion with %s:%d was closed because the client did not match the identification", self._connectedSocket[1][0], self._connectedSocket[1][1])
					self._connectedSocket = None
					continue
			
			self._receiveData()
		
		self._logger.info("Server closed")


	def stop(self) -> None:
		"""
		Closes the server.
		"""

		if self._connectedSocket:
			self._logger.info("Closing connexion with %s:%i", self._connectedSocket[1][0], self._connectedSocket[1][1])
			self._connectedSocket[0].close()
			self._connectedSocket = None

		self._logger.info("Closing the server")
		self._close()


	def askIdentification(self) -> bool:
		"""
		Asks the identification to the client, then checks it. 
		"""

		self._sendCommand(0, 0, 0) # Identification
		identification = self._receiveData()
		
		# Checks the identification
		# TODO : Has to be defined, here just checks if some data has been added
		if identification:
			return True
		else:
			return False

	
	def getReceivedData(self) -> bytes:
		"""
		Returns the list of all the data that has been received.
		"""

		return self._receivedData


	def getAddress(self) -> tuple:
		"""
		Returns the address that the server listens to in the form (adrr, port)
		"""
		return self._address

	
	def isRunning(self):
		"""
		Returns True if the server is running.
		"""

		return self._serverOpen





if __name__ == "__main__":
	import time
	# logsFile = os.path.join("logs", "Server_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
	logsFile = os.path.join("logs", "Server_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

	handler = logging.FileHandler(logsFile)
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	handler.setLevel(logging.DEBUG)

	serverLogger = logging.Logger("Server")
	serverLogger.addHandler(handler)

	server = Server(("0.0.0.0", 16384), logger=serverLogger, threadName="ServerThread")
	server.start()

	time.sleep(2)
	server._sendCommand(hw = 0, cmd = 7, info = 7)

	server.join()
	if server.isRunning():
		server.stop()
