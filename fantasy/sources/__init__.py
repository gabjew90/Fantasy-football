"""Projection sources. Each module exposes NAME (its core/registry.py name) and
a `project(...) -> fantasy.contract.SourceResult`. A new source is a new module
here plus a registry entry with its evidence; tests/test_core_guardrails.py
fails on a projection source that is not registered."""
