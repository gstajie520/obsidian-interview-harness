#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""默认配置测试。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


yaml: Any = pytest.importorskip("yaml")


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_harness_config_template_defaults_to_sqlite() -> None:
    config_path = ROOT_DIR / ".harness" / "config" / "harness.yaml.example"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert config["database"]["type"] == "sqlite"
