# ethernet-uart-fpga
Réalisation d'un serveur PC permettant de transmettre des fichiers binaires à une carte FPGA par un lien ethernet.

Ce binôme est chargé de mettre en œuvre un script permettant l’analyse de fichiers binaires, puis leur émission sur un lien Ethernet en TCP/IP en tant que serveur. Ce script
permettra également le pilotage du logiciel applicatif de la Zedboard (reset des pointeurs mémoires). Ce script pourra être rédigé en langage Python, C ou C++, mais l’usage du langage Python est fortement recommandé ici.

## Lancement du programme
Pour lancer le programme, il suffit d'exéctuer le main avec Python (version > 3.8). Pour préciser une adresse IP et un port d'écoute, il suffit des les indiquer à la suite (par défaut **192.168.1.1:16384**). Pour spécifier un fichier utilisé pour les *logs*, indiquer le chemin à la suite.  
__Attention :__ il n'est pas possible de ne préciser uniquement l'adresse IP sans le port.  
__Attention 2 :__ le fichier de *logs* doit déjà exister.

Exemples :
- `python3.8 main.py`
- `python3.8 main.py /path/to/logs`
- `python3.8 main.py 0.0.0.0 1234`
- `python3.8 main.py 0.0.0.0 1234 /path/to/logs`

## Fonctions disponbiles et utilisation
- `exit` : quitte le programme.
- `id` : demande l'identification du client.
- `load ptr` : ouvre un sélectionneur de fichiers et envoie celui sélectionné au pointeur `ptr`.
- `rstptr ptr` : reset le pointeur `ptr`. Si `ptr` vaut `all`, reset tous les pointeurs.
- `status` : demande des informations sur la FPGA.
- `route ptr` : commande `route` appliquée au pointeur `ptr`.
- `rstfifo` : reset la FIFO.
- `rstfpga` : reset la FPGA.
- `custom ...` : envoie tout ce qui est passé en paramètres. L'option `-b` permet d'indiquer que ce qui est envoyé est une phrase binaire. Exemple : `custom -b 01101001`.

## Autres informations
- Les données reçues sont données en temps réel dans le terminal. 
- Les logs sont écrits dans le fichier daté au jour.
- Pour obtenir des infos de debug, changer la variable `DEBUG` à `True` dans le fichier `main.py`.
- Le client doit envoyer `0xff` à la déconnexion.