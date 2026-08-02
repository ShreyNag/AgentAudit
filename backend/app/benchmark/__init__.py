"""Benchmark framework: task/environment registries, loading, and validation.

Loads environments and generates deterministic tasks; never communicates directly with the
Evaluation Engine (PROJECT_SPEC_2 SS51/SS75).
"""

from app.benchmark.models import BenchmarkEnvironmentMeta, Task
from app.benchmark.registry import BenchmarkRegistry
from app.benchmark.task_loader import TaskLoader
from app.benchmark.validator import BenchmarkValidator

__all__ = [
    "BenchmarkEnvironmentMeta",
    "Task",
    "BenchmarkRegistry",
    "TaskLoader",
    "BenchmarkValidator",
]
