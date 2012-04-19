from tutorial3_nohup1 import *

class NoHUPStartSSH(NoHUPStart):
    username = batch.Property()
    password = batch.Property()
    server = batch.Property()

    terminal = batch.Controller(SSHTerminal, username, password, server)
