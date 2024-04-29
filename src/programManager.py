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
import os
import time
import re
from datetime import datetime
from socket import error as socketError



# ===========================================================================================
# ***************************************** MODULES *****************************************
# ===========================================================================================
# Custom libraries created for this application

from server import Server
from filesManager import FilesManager
import terminal
from terminal import Terminal

# ===========================================================================================
# **************************************** VARIABLES ****************************************
# ===========================================================================================
# Variable declaration/definition

# Logs
logsFile = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
# logsFile = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day


# ===========================================================================================
# **************************************** FUNCTIONS ****************************************
# ===========================================================================================
# Functions declaration/definition

def isValidIpv4(ip: str) -> bool:
	if not isinstance(ip, str): return False

	# Regular expression pattern for IPv4 address
	ipv4_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"

	# Check if the string matches the pattern
	match = re.match(ipv4_pattern, ip)

	if match:
		# Check if each octet is within the valid range (0-255)
		for octet in match.groups():
			if not (0 <= int(octet) <= 255): return False
		return True
	else:
		return False
	

def displayErrors(receivedData, logger) -> None:
	"""
	Display errors on the terminal
	"""
	# Decode the command
	if len(receivedData) == 0: return
	cmd = receivedData[0] # Take the first byte
	info = cmd & 0b1111
	hw = cmd >> 7
	cmd = (cmd >> 4) & 0b111

	if len(receivedData) > 1:
		additionnalData = receivedData[1:]
	else:
		additionnalData = ""

	try:
		error = int.from_bytes(additionnalData, byteorder="big")
	except ValueError:
		error = additionnalData
		
	print("\nreceived : ", end="")
	# Display the command
	if hw:
		if cmd == 0:
			print("status", end="")
		elif cmd == 1:
			print("route", info, end="")
		elif cmd == 2:
			if info :
				print("rstfpga", end="")
			else:
				print("rstfifo", end="")
		else:
			logger.warning("The command hw:{} cmd:{} could not be found.".format(hw, cmd))
	else:
		if cmd == 0:
			print("id", repr(additionnalData))
		elif cmd == 1:
			print("load", info, end="")
		elif cmd == 2:
			print("rstptr", info, end="")
		else:
			logger.warning("The command hw:{} cmd:{} could not be found.".format(hw, cmd))


	# End
	if (hw or cmd) and error: print(" ERROR", error, "\n> ", end="")
	else: print(" ok\n\n> ", end="")


# ===========================================================================================
# ****************************************** CLASS ******************************************
# ===========================================================================================
# Variable declaration/definition

class ProgramManager(threading.Thread):
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
				identificationFunction=None,
				threadGroup=None,
				threadTarget=None,
				threadName=None,
				threadArgs=list(),
				threadKwargs=dict(),
				threadDaemon=None,
				mainLogger=None,
				serverLogger=None,
				filesManagerLogger=None,
				terminalLogger=None
			) -> None:
		
		super().__init__(group=threadGroup, target=threadTarget, name=threadName, daemon=threadDaemon)

		self._address = address
		self._args = threadArgs
		self._kwargs = threadKwargs
		
		self._logger = mainLogger
		
		self._server = Server(address=address, bufferSize=512, logger=serverLogger)
		if identificationFunction: self._server.identificationFunction = identificationFunction
		self._filesManager = FilesManager(logger=filesManagerLogger, threaded=False)
		self._terminal = Terminal(logger=terminalLogger, executeCommandFunction=self._handleCommand)

		self._handleReceivedDataRunning = False # The loop for handling received data

		self._running = False # The main loop
   

	def run(self) -> None:
		self._server.start()
		self._terminal.start()

		self._logger.info("Data manager started")
		self._running = True
		
		self._logger.info("Program manager closed")

		self._handleReceivedData()

		self._terminal.join()


	def stop(self) -> None:
		"""
		Closes the program manager.
		"""
		self._logger.info("Closing the program manager")

		self._running = False
		self._handleReceivedDataRunning = False
		self._filesManager.stop()
		self._server.stop()
		self._terminal.stop()


	def _handleReceivedData(self) -> None:
		"""
		Decodes the data and displays it, in an infinite loop.
		"""
		self._handleReceivedDataRunning = True

		# Infinite loop
		while self._handleReceivedDataRunning:
			try:
				receivedData = self._server.getReceivedData().pop(0) # Take the oldest received data
			except IndexError: # No data received
				time.sleep(0.5)
				continue

			# Decode the command
			if len(receivedData) == 0: continue
			cmd = receivedData[0] # Take the first byte
			info = cmd & 0b1111
			hw = cmd >> 7
			cmd = (cmd >> 4) & 0b111
			
			# To choose which format for displaying, uncomment the wanted section

			# With decode
			if len(receivedData) > 1:
				try:
					additionnalData = receivedData[1:].decode()
				except UnicodeDecodeError:
					additionnalData = receivedData[1:]
			else:
				additionnalData = ""

			# Display the command
			if hw:
				if cmd == 0:
					self._terminal.addEntry("status", repr(additionnalData), flags=terminal.RECEIVED)
				elif cmd == 1:
					self._terminal.addEntry("route", repr(info) + repr(additionnalData), flags=terminal.RECEIVED)
				elif cmd == 2:
					if info :
						self._terminal.addEntry("rstfpga", repr(additionnalData), flags=terminal.RECEIVED)
					else:
						self._terminal.addEntry("rstfifo", repr(additionnalData), flags=terminal.RECEIVED)
				else:
					self._terminal.addEntry("received data", "the command hw:{} cmd:{} could not be found.".format(hw, cmd), flags=terminal.ALERT)
					self._logger.warning("The command hw:{} cmd:{} could not be found.".format(hw, cmd))
			else:
				if cmd == 0:
					self._terminal.addEntry("id", repr(additionnalData), flags=terminal.RECEIVED)
					self._terminal.connectedClient = repr(additionnalData)
				elif cmd == 1:
					self._terminal.addEntry("load", repr(info) + repr(additionnalData), flags=terminal.RECEIVED)
				elif cmd == 2:
					self._terminal.addEntry("rstptr", repr(info) + repr(additionnalData), flags=terminal.RECEIVED)
				else:
					self._terminal.addEntry("received data", "the command hw:{} cmd:{} could not be found.".format(hw, cmd), flags=terminal.ALERT)
					self._logger.warning("The command hw:{} cmd:{} could not be found.".format(hw, cmd))
			
			# # Without decode
			# self._terminal.addEntry("received (plain)", receivedData, flags=terminal.RECEIVED)


	def _handleCommand(self, command: str, *data) -> None:
		"""
		Handle a new command entry
		"""
		try:
			# Runs the function depending on the command
			if command == "exit":
				self.stop()
				return
			elif command == "id":
				self._server.askIdentification()
			elif command == "load":
				if len(data) == 0:
					raise AttributeError("not enough parameter was given")
				info = int(data[0])
				if info < 0 or info > 7: raise Exception("info has to be in range 0 to 7")
				path = self._filesManager.start()
				self._server.sendFile(path, info)
			elif command == "rstptr":
				if len(data) == 0: raise AttributeError("no parameter was given")
				info = 8 if data[0] == "all" else int(data[0])
				if info < 0 or info > 8: raise Exception("info has to be in range 0 to 8")
				self._server.sendCommand(0, 2, info)
			elif command == "status":
				self._server.sendCommand(1, 0)
			elif command == "route":
				if len(data) == 0: raise AttributeError("no parameter was given")
				info = int(data[0])
				if info < 0 or info > 7: raise Exception("info has to be in range 0 to 7")
				self._server.sendCommand(1, 1, info)
			elif command == "rstfifo":
				self._server.sendCommand(1, 2, 0)
			elif command == "rstfpga":
				self._server.sendCommand(1, 2, 1)
			elif command == "custom":
				# Sends whatever is specified in parameters
				if len(data) > 0 and data[0] == "-b":
					if len(data) > 2:
						self._terminal.addEntry(command, f"warning : ignoring the parameters after {data[1]} because sending bits", flags=terminal.BOLD)

					# Pad the bit string with zeros to make its length a multiple of 8
					paddedBitString = data[1].ljust((len(data[1]) + 7) // 8 * 8, '0')
					# Convert the padded bit string to bytes
					byteArray = bytearray(int(paddedBitString[i:i+8], 2) for i in range(0, len(paddedBitString), 8))
					
					self._server._connectedSocket[0].sendall(bytes(byteArray).ljust(self._server._bufferSize, b'\x00')) # adjust the size to the buffer size
				else:
					self._server._connectedSocket[0].sendall(" ".join(data).encode())
			else:
				self._terminal.addEntry(command, "command unknown", flags=terminal.ALERT)
				return
		except Exception as e:
			self._terminal.addEntry(command, "could not send the command: {}".format(e), flags=terminal.ALERT)
			self._logger.warning("Could not send the command %s %s : %s", command, " ".join(data), e)
		else:
			self._terminal.addEntry(command, "executed" + '' if not len(data) else " with data: " + " ".join(data), flags=terminal.SENT)
			self._logger.debug("%s %s command executed", command, " ".join(data))





if __name__ == "__main__":
	import time
	# logsFile = os.path.join("logs", "Server_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
	logsFile = os.path.join("logs", "Server_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

	handler = logging.FileHandler(logsFile)
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	handler.setLevel(logging.DEBUG)

	serverLogger = logging.Logger("Server")
	serverLogger.addHandler(handler)

