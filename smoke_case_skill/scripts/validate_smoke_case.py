#!/usr/bin/env python3
import json
import sys
from pathlib import Path


ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
ALLOWED_OPS = {"eq", "ne", "gt", "lt", "exists", "contains"}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def require(condition, message):
    if not condition:
        fail(message)


def load_case(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid json: {exc}")
    except OSError as exc:
        fail(f"cannot read file: {exc}")


def validate_assertion(assertion, step_index, assertion_index):
    prefix = f"steps[{step_index}].assertions[{assertion_index}]"
    require(isinstance(assertion, dict), f"{prefix} must be an object")
    require(assertion.get("path"), f"{prefix}.path is required")
    require(isinstance(assertion.get("path"), str), f"{prefix}.path must be a string")
    op = assertion.get("op")
    require(op, f"{prefix}.op is required")
    require(op in ALLOWED_OPS, f"{prefix}.op unsupported: {op}")


def validate_extract(extract, step_index):
    prefix = f"steps[{step_index}].extract"
    require(isinstance(extract, dict), f"{prefix} must be an object")
    for key, value in extract.items():
        require(isinstance(key, str) and key, f"{prefix} key must be a non-empty string")
        require(isinstance(value, str) and value, f"{prefix}.{key} must be a JSONPath string")


def validate_step(step, index):
    prefix = f"steps[{index}]"
    require(isinstance(step, dict), f"{prefix} must be an object")
    require(step.get("name"), f"{prefix}.name is required")
    require(step.get("method"), f"{prefix}.method is required")
    require(step.get("path"), f"{prefix}.path is required")
    method = str(step["method"]).upper()
    require(method in ALLOWED_METHODS, f"{prefix}.method unsupported: {step['method']}")
    require("assert" not in step, f"{prefix} uses unsupported field 'assert'; use 'assertions'")

    assertions = step.get("assertions", [])
    require(isinstance(assertions, list), f"{prefix}.assertions must be an array")
    for assertion_index, assertion in enumerate(assertions):
        validate_assertion(assertion, index, assertion_index)

    validate_extract(step.get("extract", {}), index)


def validate_case(case):
    require(isinstance(case, dict), "case json must be an object")
    require(case.get("name"), "name is required")
    require(case.get("priority"), "priority is required")
    require("continueOnFail" in case, "continueOnFail is required")
    require(isinstance(case["continueOnFail"], bool), "continueOnFail must be boolean")
    steps = case.get("steps")
    require(isinstance(steps, list), "steps must be an array")
    require(len(steps) > 0, "steps must not be empty")
    for index, step in enumerate(steps):
        validate_step(step, index)


def main():
    if len(sys.argv) != 2:
        fail("usage: validate_smoke_case.py /path/to/case.json")
    case = load_case(sys.argv[1])
    validate_case(case)
    print("OK: smoke case json is valid")


if __name__ == "__main__":
    main()
