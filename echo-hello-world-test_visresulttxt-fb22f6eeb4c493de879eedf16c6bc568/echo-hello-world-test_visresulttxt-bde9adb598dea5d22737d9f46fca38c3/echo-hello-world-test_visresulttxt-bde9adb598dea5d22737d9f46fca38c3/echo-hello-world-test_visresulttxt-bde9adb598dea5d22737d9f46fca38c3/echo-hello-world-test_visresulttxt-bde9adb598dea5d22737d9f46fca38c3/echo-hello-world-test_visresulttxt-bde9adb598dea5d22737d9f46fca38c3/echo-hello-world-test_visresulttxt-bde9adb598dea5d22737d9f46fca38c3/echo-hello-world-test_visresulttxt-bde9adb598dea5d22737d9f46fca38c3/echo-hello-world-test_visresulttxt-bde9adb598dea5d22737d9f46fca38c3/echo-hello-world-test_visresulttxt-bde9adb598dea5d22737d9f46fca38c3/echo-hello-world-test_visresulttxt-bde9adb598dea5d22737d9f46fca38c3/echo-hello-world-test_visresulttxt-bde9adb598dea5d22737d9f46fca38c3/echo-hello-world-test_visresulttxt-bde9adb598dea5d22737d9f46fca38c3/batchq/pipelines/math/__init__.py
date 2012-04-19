from batchq.core.library import Library
from batchq.pipelines.math.maple import MaplePipeline

Library.pipelines.register("maple", MaplePipeline)

