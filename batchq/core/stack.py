MACHINE_STACK = []
import os
import shutil
bin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bin"))


def select_machine(machine):
    global MACHINE_STACK
    MACHINE_STACK.append(machine)
    
    rh = machine.remote.home()
    rbh = machine.remote.path.join(rh, ".batchq/bin")
    if not machine.remote.isdir(rbh):
        machine.remote.mkdir(rbh, True)

    machine.sync(bin_path, rbh, mode = machine.MODE_LOCAL_REMOTE)    
    machine.remote.send_command("export PATH=$PATH:%s"%rbh)

    rh = machine.local.home()
    lbh = machine.local.path.join(rh, ".batchq/bin")
    if not machine.local.isdir(lbh):
        machine.local.mkdir(lbh, True)

    for f in os.listdir(bin_path):
        src =os.path.join(bin_path, f)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(lbh, f))
    machine.local.send_command("export PATH=$PATH:%s"%lbh)

def end_machine():
    global MACHINE_STACK
    MACHINE_STACK = MACHINE_STACK[:-1]

def current_machine():
    global MACHINE_STACK
    if len(MACHINE_STACK) == 0:
        return None
    return MACHINE_STACK[-1]



    
