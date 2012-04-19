from batchq.core.library import Library
from batchq.pipelines.interpreters.python import PythonTerminal

Library.pipelines.register("python",PythonTerminal)
