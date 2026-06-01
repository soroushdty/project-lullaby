"""Public API for the seeded synthetic longitudinal cohort simulator.

Use :func:`generate_synthetic` for the clone-to-run workflow and
:func:`generate_cohort_tables` when tests or downstream tools need in-memory tables.
All generated records are synthetic and deterministic for a fixed effective config.
"""

from src.simulation.cohort import SimulationTables, generate_cohort_tables
from src.simulation.config import SimulationConfig, load_simulation_config
from src.simulation.export import SimulationRunResult, generate_synthetic

__all__ = [
    "SimulationConfig",
    "SimulationRunResult",
    "SimulationTables",
    "generate_cohort_tables",
    "generate_synthetic",
    "load_simulation_config",
]
