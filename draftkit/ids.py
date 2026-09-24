"""Moved to core.ids on 2026-09-24 (docs/plans/2026-09-24-consolidation-plan.md).

Re-exported so existing imports keep working. New code imports core.ids. To
change a setting such as CACHE_TTL, set it on core.ids -- assigning it here
would not reach the functions that read it.
"""

from core.ids import (CACHE_TTL, PLAYERIDS_URL, NameIndex, SleeperIndex,  # noqa: F401
                      invert, load_id_map, normalize_name, sleeper_gsis)
