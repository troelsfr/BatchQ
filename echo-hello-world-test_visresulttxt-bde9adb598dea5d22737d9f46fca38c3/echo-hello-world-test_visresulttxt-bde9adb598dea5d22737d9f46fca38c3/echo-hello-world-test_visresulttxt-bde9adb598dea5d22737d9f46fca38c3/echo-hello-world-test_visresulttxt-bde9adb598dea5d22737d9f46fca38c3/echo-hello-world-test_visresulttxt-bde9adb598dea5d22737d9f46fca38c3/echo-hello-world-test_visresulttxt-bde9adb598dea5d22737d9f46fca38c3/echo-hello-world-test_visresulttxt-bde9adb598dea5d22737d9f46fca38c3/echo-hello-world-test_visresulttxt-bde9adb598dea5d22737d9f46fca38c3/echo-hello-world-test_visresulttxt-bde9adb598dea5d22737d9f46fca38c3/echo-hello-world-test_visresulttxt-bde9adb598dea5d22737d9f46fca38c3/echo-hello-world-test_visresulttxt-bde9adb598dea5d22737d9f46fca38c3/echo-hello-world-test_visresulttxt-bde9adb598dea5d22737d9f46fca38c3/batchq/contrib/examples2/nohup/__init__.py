from batchq.core.library import Library
from nohup import NoHUP

Library.queues.register("local-module",NoHUP)

