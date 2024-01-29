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
import time

pass

# ===========================================================================================
# ***************************************** MODULES *****************************************
# ===========================================================================================
# Custom libraries created for this application

pass

# ===========================================================================================
# **************************************** VARIABLES ****************************************
# ===========================================================================================
# Variable declaration/definition
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))

logger = logging.Logger("Server")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


# ===========================================================================================
# ****************************************** CLASS ******************************************
# ===========================================================================================
# Variable declaration/definition
class Server(threading.Thread):
	"""Represents a server that can run and transfer data to connected clients."""
	def __init__(self, name: str = "Server", *args, **kwargs) -> None:
		super().__init__(name=name, daemon=False)
		self.values = None
	

	def run(self):
		logger.debug(self.values[0])
		time.sleep(2)
		logger.debug(self.values[1])


	def print(self, *values):
		self.values = values
		self.start()





if __name__ == "__main__":
	main = logging.Logger("main")
	main.setLevel(logging.INFO)
	main.addHandler(handler)

	main.info("before creating thread")

	server1 = Server("Server 1")
	server2 = Server("Server 2")

	main.info("before running thread")

	server1.print(10, 11)
	server2.print(20, 21)
	server1.join()
	server2.join()

	main.info("wait for the thread to finish")

	main.info("all done")