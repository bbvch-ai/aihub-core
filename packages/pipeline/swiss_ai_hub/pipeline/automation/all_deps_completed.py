from dagster import AutomationCondition

"""Materialize asset when all upstream dependencies are either completed or have failed"""
all_deps_completed = (~AutomationCondition.any_deps_missing()) & (~AutomationCondition.any_deps_in_progress())
