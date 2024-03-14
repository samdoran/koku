#
# Copyright 2021 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
"""API application configuration module."""
import logging
import os

from django.apps import AppConfig

from koku.feature_flags import UNLEASH_CLIENT


LOG = logging.getLogger(__name__)


class ApiConfig(AppConfig):
    """API application configuration."""

    name = "api"
    _unleash_initialized = False

    def ready(self):
        if not ApiConfig._unleash_initialized:
            UNLEASH_CLIENT.unleash_instance_id += f"-{os.getpid()}"
            LOG.info(f"{LOG.name} Iniliatizing unleash client {UNLEASH_CLIENT.unleash_instance_id}")
            UNLEASH_CLIENT.initialize_client()
            ApiConfig._unleash_initialized = True
