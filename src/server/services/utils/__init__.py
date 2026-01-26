#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Provides utilities for service."""

from .affiliations import detect_affiliation, detect_affiliations
from .patch_operations import build_patch_operations, build_update_member_operations
from .roles import get_highest_role
from .search_queries import (
    GroupsCriteria,
    RepositoriesCriteria,
    UsersCriteria,
    build_search_query,
    make_criteria_object,
)
