"""
title: AI Hub runtime mods
description: Runs the enabled tenant's published backend mods through native chat hooks.
required_open_webui_version: 0.11.4
"""

from aihub_mods.native_filter import NativeFilter


class Filter(NativeFilter):
    pass
