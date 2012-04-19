from batchq.core import batch

def home_create_dir(directory, wildcard, verbose = False, inherits = None):
    if inherits is None:
        return batch.Function(verbose=verbose) \
            .home().chdir(wildcard) \
            .exists(directory).Qdon(1).mkdir(directory, True) \
            .chdir(directory)
    else:
        return batch.Function(inherits,verbose=verbose) \
            .home().chdir(wildcard) \
            .exists(directory).Qdon(1).mkdir(directory, True) \
            .chdir(directory)
    
def send_command(command, verbose = False, inherits = None):
    if inherits is None:
        return batch.Function(verbose=verbose) \
            .send_command(command)
    else:
        return batch.Function(inherits,verbose=verbose) \
            .send_command(command)
