REGISTRY = {}

from .episode_runner import EpisodeRunner
REGISTRY["episode"] = EpisodeRunner

from .parallel_runner import ParallelRunner
REGISTRY["parallel"] = ParallelRunner

from .bayes_parallel_runner import BayesParallelRunner
REGISTRY["bayes"] = BayesParallelRunner
