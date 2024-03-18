# Notes
Here are some notes about the UART communication. Files are only rececived, not sent.

## Parameters
- Port : depends on the context. Maybe list them all then choose ? Or specify in the script call.
- Baudrate : 115200.
- Parity : should be able to do both.

## Other infos
No end-file character. Write indefinitely, maybe wait for a key to be pressed to escape. **Warning :** be careful to close the file when escaping the script.  

