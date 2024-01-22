# ===========================================================================================
# ***************************************** LICENSE *****************************************
# ===========================================================================================
# Copyright (c) 2024, CATIE
# SPDX-License-Identifier: Apache-2.0

# ===========================================================================================
# *************************************** DESCRIPTION ***************************************
# ===========================================================================================
# This unit provides a TCP/IP server interface ETH link for the Zynq board.
# Data are sent through ETH as long as there is client connected and ready.
# A list of command is available to choose for sending data or other instruction to the Zynq
# board.


# ===========================================================================================
# **************************************** LIBRARIES ****************************************
# ===========================================================================================
# Libraries used for this application.
# Example code:
#   > import lib # Lib Librarie used for ...
#   > from lib import module # Module from Lib used in ...

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

'''
    TCP/IP specific variables to create and run server on specific ip/port
'''
pass

'''
    Binaries specific variables to read files and send then on ETH link
        [ TARGET | COMMAND | INFORMATION || ---- DATA ---- ]
        [ 1 bit  | 3 bits  |   4 bits    ||    TBD bits    ]
        [          8 bits                ||    TBD bits    ]
    TBD bits is to be chosen in colaboration with cortex A9 group
'''
pass

# ===========================================================================================
# **************************************** FUNCTIONS ****************************************
# ===========================================================================================
# Function declaration/definition

# ====[ Parsing function: to send correct instruction ]======================================
def Send_Instruction():
    # ====[ START: Parsing instruction ]=====================================================
    pass
    # ====[ END: Parsed instruction ]========================================================

    # ====[ START: Send instruction ]========================================================
    pass
    # ====[ END: Instruction sended ]========================================================

# ===========================================================================================
# **************************************** STRUCTURE ****************************************
# ===========================================================================================
# Main code to execute the application

if __name__ == '__main__':
    # ====[ START: TCP/IP Server creation and execution ]====================================
    pass
    # ====[ END: TCP/IP Server running ]=====================================================

    # ====[ START: Waiting for client to connect ]===========================================
    pass
    # ====[ END: Client connected ]==========================================================

    # ====[ START: Run main Loop for sending instruction to Zynq board ]=====================
    while ...:
        # ====[ START: Waiting for Client to be ready ]======================================
        '''
            CLI to choose the instruction to send
            > Choose instruction to send:
            >    [1] Load        : Load a binary file
            >    [2] Rewind      : Reset CPU ptr index
            >    [3] Route       : Configure FGPA Data block output
            >    [4] Status      : Querry FPGA status
            >    [5] Clear       : Clear FPGA fifo
            >    [6] Reset PL    : Reset FPGA
            > Instruction to send: []
        '''
        pass
        # ====[ END: Client ready ]==========================================================
            
        # ====[ START: Let user choose an instruction to send ]==============================
        pass
        # ====[ END: Instruction chosen ]====================================================

        # ====[ START: Parse the asked instrucion and send it on ETH link ]==================
        Send_Instruction(...)
        # ====[ END: Instruction sended ]====================================================
    # ====[ END: Running Loop (Never reached) ]==============================================