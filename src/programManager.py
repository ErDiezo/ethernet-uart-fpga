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
		try:
			additionnalData = receivedData[1:].decode()
		except UnicodeDecodeError:
			additionnalData = receivedData[1:]
	else:
		additionnalData = ""

	error = int(additionnalData)
		
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
	if error: print(" ERROR", error, "\n> ", end="")
	else: print("\n\n> ", end="")


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
				filesManagerLogger=None
			) -> None:
		
		super().__init__(group=threadGroup, target=threadTarget, name=threadName, daemon=threadDaemon)

		self._address = address
		self._args = threadArgs
		self._kwargs = threadKwargs
		
		self._logger = mainLogger
		
		self._server = Server(address=address, bufferSize=512, logger=serverLogger)
		if identificationFunction: self._server.identificationFunction = identificationFunction
		self._filesManager = FilesManager(logger=filesManagerLogger, threaded=False)

		self._displayDataRunning = False # The loop for displaying data
		self._displayDataThread = threading.Thread(target = self._displayData)

		self._running = False # The main loop
   

	def run(self) -> None:
		self._server.start()
		self._displayDataThread.start()

		self._logger.info("Data manager started")
		self._running = True

		while self._running:
			userInput = input("> ")

			try:
				command, *args = userInput.split()
			except ValueError:
				continue

			try:
				# Runs the function depending on the command
				if command == "exit":
					self.stop()
					continue
				elif command == "id":
					self._server.askIdentification()
				elif command == "load":
					if len(args) == 0:
						raise AttributeError("not enough parameter was given")
					info = int(args[0])
					if info < 0 or info > 7: raise Exception("info has to be in range 0 to 7")
					path = self._filesManager.start()
					self._server.sendFile(path, info)
				elif command == "rstptr":
					if len(args) == 0: raise AttributeError("no parameter was given")
					info = 8 if args[0] == "all" else int(args[0])
					if info < 0 or info > 8: raise Exception("info has to be in range 0 to 8")
					self._server.sendCommand(0, 2, info)
				elif command == "status":
					self._server.sendCommand(1, 0)
				elif command == "route":
					if len(args) == 0: raise AttributeError("no parameter was given")
					info = int(args[0])
					if info < 0 or info > 7: raise Exception("info has to be in range 0 to 7")
					self._server.sendCommand(1, 1, info)
				elif command == "rstfifo":
					self._server.sendCommand(1, 2, 0)
				elif command == "rstfpga":
					self._server.sendCommand(1, 2, 1)
				elif command == "custom":
					# Sends whatever is specified in parameters
					if len(args) > 0 and args[0] == "-b":
						if len(args) > 2:
							print(f"Warning : ignoring the parameters after {args[1]} because sending bits")

						# Pad the bit string with zeros to make its length a multiple of 8
						paddedBitString = args[1].ljust((len(args[1]) + 7) // 8 * 8, '0')
						# Convert the padded bit string to bytes
						byteArray = bytearray(int(paddedBitString[i:i+8], 2) for i in range(0, len(paddedBitString), 8))
						
						self._server._connectedSocket[0].sendall(bytes(byteArray).ljust(self._server._bufferSize, b'\x00')) # adjust the size to the buffer size
					else:
						self._server._connectedSocket[0].sendall(" ".join(args).encode())
				else:
					print(f"Command \"{command}\" unknown")
					continue
			except socketError as e:
				print(f"Could not send the command {command} : {e}")
			except Exception as e:
				print(f"Could not send the command {command} : {e}")
				self._logger.warning("Could not send the command %s %s : %s", command, " ".join(args), e)
			else:
				self._logger.debug("%s %s command executed", command, " ".join(args))
		
		self._logger.info("Program manager closed")


	def stop(self) -> None:
		"""
		Closes the program manager.
		"""
		self._logger.info("Closing the program manager")

		self._running = False
		self._displayDataRunning = False
		self._filesManager.stop()
		self._server.stop()


	def _displayData(self, displayFunction = displayErrors) -> list:
		"""
		Decodes the data and displays it, in an infinite loop.
		"""
		self._displayDataRunning = True

		# Infinite loop
		while self._displayDataRunning:
			try:
				receivedData = self._server.getReceivedData().pop(0) # Take the oldest received data
			except IndexError: # No data received
				time.sleep(1)
				continue

			# Decode the command
			if len(receivedData) == 0: continue
			cmd = receivedData[0] # Take the first byte
			info = cmd & 0b1111
			hw = cmd >> 7
			cmd = (cmd >> 4) & 0b111
			
			if displayFunction == print:
				# To choose which format for displaying, uncomment the wanted section

				# With decode
				if len(receivedData) > 1:
					try:
						additionnalData = receivedData[1:].decode()
					except UnicodeDecodeError:
						additionnalData = receivedData[1:]
				else:
					additionnalData = ""
					
				displayFunction("\nreceived : ", end="")
				# Display the command
				if hw:
					if cmd == 0:
						displayFunction("status", repr(additionnalData))
					elif cmd == 1:
						displayFunction("route", info, repr(additionnalData))
					elif cmd == 2:
						if info :
							displayFunction("rstfpga", repr(additionnalData))
						else:
							displayFunction("rstfifo", repr(additionnalData))
					else:
						self._logger.warning("The command hw:{} cmd:{} could not be found.".format(hw, cmd))
				else:
					if cmd == 0:
						displayFunction("id", repr(additionnalData))
					elif cmd == 1:
						displayFunction("load", info, repr(additionnalData))
					elif cmd == 2:
						displayFunction("rstptr", info, repr(additionnalData))
					else:
						self._logger.warning("The command hw:{} cmd:{} could not be found.".format(hw, cmd))
				
				# # Without decode
				# displayFunction("\nreceived : ", receivedData)

				# End
				displayFunction("\n> ", end="")
			else:
				displayFunction(receivedData)
			continue



if __name__ == "__main__":
	import time
	# logsFile = os.path.join("logs", "Server_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
	logsFile = os.path.join("logs", "Server_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

	handler = logging.FileHandler(logsFile)
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	handler.setLevel(logging.DEBUG)

	serverLogger = logging.Logger("Server")
	serverLogger.addHandler(handler)

