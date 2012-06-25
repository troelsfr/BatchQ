MACHINE_STACK = []
def select_machine(machine):
    global MACHINE_STACK
    MACHINE_STACK.append(machine)

def end_machine():
    global MACHINE_STACK
    MACHINE_STACK = MACHINE_STACK[:-1]

def current_machine():
    global MACHINE_STACK
    if len(MACHINE_STACK) == 0:
        return None
    return MACHINE_STACK[-1]



    
