#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一入口 main.py 测试。"""

from __future__ import annotations

from argparse import Namespace
from typing import Any

import main


def test_dispatch_defaults_to_serve(monkeypatch: Any) -> None:
    called: dict[str, Any] = {}

    def fake_run_serve(host: str, port: int, reload_enabled: bool) -> None:
        called["host"] = host
        called["port"] = port
        called["reload_enabled"] = reload_enabled

    monkeypatch.setattr(main, "run_serve", fake_run_serve)

    main.dispatch(Namespace(command=None))

    assert called == {
        "host": "127.0.0.1",
        "port": 8000,
        "reload_enabled": False,
    }


def test_dispatch_import_questions_forwards_arguments(monkeypatch: Any) -> None:
    called: dict[str, Any] = {}

    def fake_run_import_questions(
        knowledge_base: str | None,
        module: str | None,
    ) -> int:
        called["knowledge_base"] = knowledge_base
        called["module"] = module
        return 3

    monkeypatch.setattr(main, "run_import_questions", fake_run_import_questions)

    main.dispatch(
        Namespace(
            command="import-questions",
            knowledge_base="java_interview",
            module="Redis",
        )
    )

    assert called == {
        "knowledge_base": "java_interview",
        "module": "Redis",
    }
