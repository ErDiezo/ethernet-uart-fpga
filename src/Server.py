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



# ===========================================================================================
# ***************************************** MODULES *****************************************
# ===========================================================================================
# Custom libraries created for this application

pass

# ===========================================================================================
# **************************************** VARIABLES ****************************************
# ===========================================================================================
# Variable declaration/definition



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
				address: [str, int],
				socketFamily=socket.AF_INET,
				socketType=socket.SOCK_STREAM,
				socketProto=-1,
				socketfileno=None,
				bufferSize = 128,
				threadGroup=None,
				threadTarget=None,
				threadName=None,
				threadArgs=list(),
				threadKwargs=dict(),
				threadDaemon=None,
				logger=None):
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
		self._socketOpen = False
		self._connectedSocket = None
		self._logger = logger
    

	def _open(self) -> None:
		"""
        Opens the socket's connexion on the address given in the initialization.
		"""
		self._logger.info("Opening the server connexion...")
		try:
			self._socket.bind(self._address)
			self._socket.listen(1)
		except Exception as e:
			self._logger.error("Error while opening the connexion: %s\nSocket not opened.", e)
		else:
			self._socketOpen = True
			self._logger.info("Server connexion opened. Listening on %s:%i", self._address[0], self._address[1])


	def _close(self) -> None:
		"""
        Closes the socket.
		"""
		if not self._open:
			self._logger.info("The server is already closed")
			return
		self._logger.info("Closing connexion...")
		self._socket.close()
		self._socketOpen = False
		self._socket = socket.socket(*self._socketInfos)
		self._logger.info("Server connexion closed")

	
	def isRunning(self):
		"""Returns True if the server is running."""
		return self._socketOpen
    
    
	def _accept(self) -> None:
		"""
		Accepts a connexion.
		"""
		while self._connectedSocket == None:
			try:
				conn, addr = self._socket.accept()
				self._connectedSocket = (conn, addr)
				self._logger.info("Accepted connexion from %s:%i", addr[0], addr[1])
			except socket.timeout:
				# self._logger.debug("Timeout")
				continue
			except Exception as e:
				raise e


	def _receiveData(self) -> bytes:
		"""
		Receives data from the client.
		"""
		self._logger.debug("Receiving data...")
		newData = self._connectedSocket[0].recv(self._bufferSize)
		self._logger.debug(" -> [{}] {}".format(len(newData), newData))
		allData = newData
		while len(newData) >= self._bufferSize:
			newData = self._connectedSocket[0].recv(self._bufferSize)
			self._logger.debug(" -> [{}] {}".format(newData))
			allData += newData
		self._logger.debug(f"All received data : {allData}")
		return allData
	

	def _sendData(self, data) -> None:
		"""
		Sends some data to the client.
		"""
		self._logger.debug("Sending data...")
		try:
			self._connectedSocket[0].sendall(data)
		except Exception as e:
			self._logger.error("Error while sending data : %s", e)
		else:
			self._logger.debug("Data successfully sent")
		


	def run(self) -> None:
		self._open()
		
		while self._connectedSocket == None: # TODO : Maybe @await ?
			self._logger.debug("Looking for a connexion")
			self._accept()
			continue


	def stop(self) -> None:
		"""
		Closes the server.
		"""
		if self._connectedSocket:
			self._logger.info("Closing connexion with %s:%i", self._connectedSocket[1][0], self._connectedSocket[1][1])
			self._connectedSocket[0].close()
			self._connectedSocket = None

		self._logger.info("Closing the server.")
		self._close()


	def sendCommand(self, command: str, *args, **kwargs) -> None:
		"""
		Sends a command to the board.
		"""
		pass





if __name__ == "__main__":
	handler = logging.StreamHandler()
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	serverLogger = logging.Logger("Server")
	serverLogger.setLevel(logging.DEBUG)
	serverLogger.addHandler(handler)

	server = Server(("192.168.1.1", 16384), logger=serverLogger, threadName="ServerThread")
	server.start()
	server.join()

	if server.isRunning():
		server.stop()