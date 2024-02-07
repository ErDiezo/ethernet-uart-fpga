# ===========================================================================================
# ***************************************** LICENSE *****************************************
# ===========================================================================================
# Copyright (c) 2024, CATIE
# SPDX-License-Identifier: Apache-2.0

# ===========================================================================================
# *************************************** DESCRIPTION ***************************************
# ===========================================================================================
# This file is used to define the files manager.
# It uses the curses module to develop a terminal integrated files manager.


# ===========================================================================================
# **************************************** LIBRARIES ****************************************
# ===========================================================================================
# Libraries used for this application.
import logging
import threading
import curses
import os
from datetime import datetime



# ===========================================================================================
# ***************************************** MODULES *****************************************
# ===========================================================================================
# Custom libraries created for this application

pass

# ===========================================================================================
# **************************************** VARIABLES ****************************************
# ===========================================================================================
# Variable declaration/definition

# Color indexes
COLORS = {
	"index" : {
		"file" : 0,
		"dir" : 1,
		"link" : 2,
	},
	"curses" : {
		"file" : None,
		"dir" : None,
		"link" : None,
	},
}

# ===========================================================================================
# ****************************************** CLASS ******************************************
# ===========================================================================================
# Variable declaration/definition

class FilesManager(threading.Thread):
	"""
    Represents a server-side socket.
    For the parameters not mentionned here, check the socket.socket parameters.
    
    :param address: the address of the socket, first the ipv4, second the port
    :type address: tuple[str, int]
    :param logger: the logger used by the server
    :type logger: logging.Logger
	"""
	def __init__(self,
			  	stdscr,
				threadGroup=None,
				threadTarget=None,
				threadName=None,
				threadArgs=list(),
				threadKwargs=dict(),
				threadDaemon=None,
				logger=None):
		super().__init__(group=threadGroup, target=threadTarget, name=threadName, daemon=threadDaemon)
		self._args = threadArgs
		self._kwargs = threadKwargs
		self._logger = logger

		self._stdscr = stdscr
		self._currentDir = os.getcwd()
		self._files = [".", ".."] + sorted(os.listdir(self._currentDir))
		self._selectedIndex = 0

		curses.curs_set(0)


	def run(self) -> None:
		self._logger.info("Starting files manager")
		self._display()

		while True:
			key = self._stdscr.getch()

			if key == ord('q'):
				break
			elif key == ord('a'):
				self._alert("test")
			elif key == curses.KEY_UP and self._selectedIndex > 0:
				self._selectedIndex -= 1
			elif key == curses.KEY_DOWN and self._selectedIndex < len(self._files) - 1:
				self._selectedIndex += 1
			elif key == curses.KEY_ENTER or key == 10 or key == 13: # ENTER or \n or \r
				self._onEnterPress()

			self._display()

		self._logger.info("Ending files manager")


	def _display(self) -> None:
		self._stdscr.clear()
		height, width = self._stdscr.getmaxyx()

		for idx, file in enumerate(self._files):
			current_file = os.path.join(self._currentDir, file)
			if os.path.isdir(current_file):
				self._stdscr.addstr(idx, 0, file, COLORS["curses"]["dir"] | curses.A_BOLD | curses.A_REVERSE*(idx==self._selectedIndex))
			elif os.path.islink(current_file):
				self._stdscr.addstr(idx, 0, file, COLORS["curses"]["link"] | curses.A_BOLD | curses.A_REVERSE*(idx==self._selectedIndex))
			else:
				self._stdscr.addstr(idx, 0, file, COLORS["curses"]["file"] | curses.A_REVERSE*(idx==self._selectedIndex))

		self._stdscr.refresh()
	

	def _alert(self, text):
		"""
		This function is used to display an alert in the center of the screen
		"""
		self._logger.warning(text)
		nLines = 6
		nCols = 30
		oldHeight, oldWidth = self._stdscr.getmaxyx()

		alertWin = curses.newwin(nLines, nCols, (oldHeight-nLines)//2, (oldWidth-nCols)//2)
		
		while True:

			alertWin.clear()

			for i in range(nLines):
				alertWin.addstr(i, 0, " "*(nCols-1), curses.A_REVERSE)

			alertWin.refresh()

			key = self._stdscr.getch()

			if key == ord('q'):
				break

		
	def _onEnterPress(self) -> None:
		"""
		Defines what happens when the user press the ENTER key.
		"""
		if self._files[self._selectedIndex] == ".":
			self._files = [".", ".."] + sorted(os.listdir(self._currentDir))
		elif self._files[self._selectedIndex] == "..":
			self._changeDir(os.path.dirname(self._currentDir))
		else:
			current_file = os.path.join(self._currentDir, self._files[self._selectedIndex])
			if os.path.isdir(current_file):
				self._changeDir(current_file)
			
	

	def _changeDir(self, dirPath) -> None:
		"""
		Changes the working directory.
		"""
		self._currentDir = dirPath
		self._selectedIndex = 0
		self._files = [".", ".."] + sorted(os.listdir(self._currentDir))
		




def main(stdscr):
	# logsFiles = os.path.join("logs", "FilesManager_{}.log".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S'))) # Day + time
	logsFiles = os.path.join("logs", "FilesManager_{}.log".format(datetime.now().strftime('%d-%m-%Y'))) # Only day
	handler = logging.FileHandler(logsFiles)
	handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	
	filesManagerLogger = logging.Logger("FilesManager")
	filesManagerLogger.setLevel(logging.DEBUG)
	filesManagerLogger.addHandler(handler)
	
	filesManager = FilesManager(stdscr, logger=filesManagerLogger)

	# Basic colors
	curses.init_pair(COLORS["index"]["dir"], curses.COLOR_CYAN, curses.COLOR_BLACK) # Directory
	curses.init_pair(COLORS["index"]["link"], curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Link
	COLORS["curses"]["file"] = curses.color_pair(COLORS["index"]["file"])
	COLORS["curses"]["dir"] = curses.color_pair(COLORS["index"]["dir"])
	COLORS["curses"]["link"] = curses.color_pair(COLORS["index"]["link"])

	filesManager.start()
	filesManager.join()




if __name__ == "__main__":
	# logsFiles = os.path.join("logs", "FilesManager_{}".format(datetime.now().strftime('%d-%m-%Y_%H:%m:%S')))
	# handler = logging.FileHandler(logsFiles)
	# handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s (%(name)s): %(message)s", datefmt="%H:%M:%S"))
	
	# logging.basicConfig(filename=logsFiles,
	# 					filemode='w',
	# 					format='[%(asctime)s] %(levelname)s (%(name)s): %(message)s',
	# 					datefmt='%H:%M:%S',
	# 					level=logging.DEBUG)
	
	# filesManagerLogger = logging.Logger("FilesManager")
	# filesManagerLogger.setLevel(logging.DEBUG)
	# filesManagerLogger.addHandler(handler)

	curses.wrapper(main)