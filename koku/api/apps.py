#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""API application configuration module."""
import os

from django.apps import AppConfig

from koku.feature_flags import UNLEASH_CLIENT


class ApiConfig(AppConfig):
    """API application configuration."""

    name = "api"

    def ready(self):
        UNLEASH_CLIENT.unleash_instance_id += f"-{os.getpid()}"
        UNLEASH_CLIENT.initialize_client()
