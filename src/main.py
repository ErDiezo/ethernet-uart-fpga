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


DEBUG = True # Change this to True if you want to see all the debug infos


# ===========================================================================================
# **************************************** LIBRARIES ****************************************
# ===========================================================================================
# Libraries used for this application.
import logging
import os
import sys
from datetime import datetime



# ===========================================================================================
# ***************************************** MODULES *****************************************
# ===========================================================================================
# Custom libraries created for this application

from programManager import ProgramManager, isValidIpv4


# ===========================================================================================
# **************************************** VARIABLES ****************************************
# ===========================================================================================
# Variable declaration/definition

# Logs
# logsFile = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
logsFile = os.path.join("logs", "main_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day

# Default IP address
DEFAULT_ADDR = "192.168.1.1"
DEFAULT_PORT = 16384

# if the user wants to create their own identificationFunction, this variable has to be set to the function
identificationFunction = None


# ===========================================================================================
# **************************************** FUNCTIONS ****************************************
# ===========================================================================================
# Functions declaration/definition

pass





if __name__ == "__main__":
	if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
		logsFile = sys.argv[1]

	if not os.path.exists(os.path.dirname(logsFile)): os.makedirs(os.path.dirname(logsFile))
	handler = logging.FileHandler(logsFile)
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)

	mainLogger = logging.Logger("main")
	mainLogger.addHandler(handler)
	serverLogger = logging.Logger("Server")
	serverLogger.addHandler(handler)
	filesManagerLogger = logging.Logger("FilesManager")
	filesManagerLogger.addHandler(handler)

	addr, port = DEFAULT_ADDR, DEFAULT_PORT
	if len(sys.argv) >= 3:
		tmpAddr = sys.argv[1]
		tmpPort = int(sys.argv[2])
		if isValidIpv4(tmpAddr) and port >= 0 and port < 65535:
			addr, port = tmpAddr, tmpPort
		else:
			mainLogger.warning("%s:%d is not a valid addres. Set to default : %s:%d", tmpAddr, tmpPort, addr, port)

	programManager = ProgramManager(
		address=(addr, port),
		mainLogger=mainLogger,
		serverLogger=serverLogger,
		filesManagerLogger=filesManagerLogger,
		identificationFunction=identificationFunction
	)

	programManager.start()

	with open(logsFile, "a") as f:
		f.write("\n")