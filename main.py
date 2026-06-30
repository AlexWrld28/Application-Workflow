from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator


DEFAULT_COMPLETED_APPLICATIONS_PATH = Path(__file__).with_name("completed_applications.json")


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    required: bool = False
    default_factory: Callable[[], str] | None = None


def _timestamp_now() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


FIELD_SPECS: tuple[FieldSpec, ...] = (
    FieldSpec("company", "Company name", required=True),
    FieldSpec("title", "Job title", required=True),
    FieldSpec("url", "Application URL", required=True),
    FieldSpec("location", "Location"),
    FieldSpec("status", "Status", default_factory=lambda: "submitted"),
    FieldSpec("submitted_at", "Submitted at", default_factory=_timestamp_now),
    FieldSpec("notes", "Notes"),
)


def _coerce_application_number(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < 1:
        return None
    return number


def _next_application_number(applications: list[dict[str, Any]]) -> int:
    existing_numbers = [
        number
        for application in applications
        if isinstance(application, dict)
        for number in [_coerce_application_number(application.get("application_number"))]
        if number is not None
    ]
    if existing_numbers:
        return max(existing_numbers) + 1
    return len(applications) + 1


def _load_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON: {exc}") from exc

    if not isinstance(payload, list):
        raise SystemExit(f"{path} must contain a JSON array.")

    return payload


def _save_json_array(path: Path, payload: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(payload, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _default_value(spec: FieldSpec) -> str | None:
    if spec.default_factory is None:
        return None
    return spec.default_factory()


def _prompt_interactive(spec: FieldSpec, value: str | None) -> str:
    if value is not None and value != "":
        return value

    default_value = _default_value(spec)
    print(spec.label)
    prompt = "> " if default_value is None else f"[{default_value}] > "
    response = input(prompt).strip()
    if response:
        return response
    if default_value is not None:
        return default_value
    if spec.required:
        raise SystemExit(f"{spec.label} is required.")
    return ""


def _read_stdin_values() -> Iterator[str]:
    first_line = True
    for line in sys.stdin.read().splitlines():
        if first_line:
            line = line.lstrip("\ufeff").lstrip("\u00ef\u00bb\u00bf")
            first_line = False
        yield line


def _resolve_field(spec: FieldSpec, value: str | None, stdin_values: Iterator[str] | None) -> str:
    if value is not None and value != "":
        return value

    if stdin_values is not None:
        try:
            stdin_value = next(stdin_values)
        except StopIteration:
            stdin_value = None
        else:
            if stdin_value != "":
                return stdin_value
            default_value = _default_value(spec)
            if default_value is not None:
                return default_value
            if spec.required:
                raise SystemExit(f"{spec.label} is required.")
            return ""

    if sys.stdin.isatty():
        return _prompt_interactive(spec, value)

    default_value = _default_value(spec)
    if default_value is not None:
        return default_value
    if spec.required:
        raise SystemExit(f"{spec.label} is required.")
    return ""


def add_application(args: argparse.Namespace) -> int:
    completed_path = Path(args.file).expanduser()
    applications = _load_json_array(completed_path)
    stdin_values = _read_stdin_values() if args.stdin or not sys.stdin.isatty() else None

    record = {"application_number": _next_application_number(applications)}
    record.update(
        {
            spec.key: _resolve_field(spec, getattr(args, spec.key), stdin_values)
            for spec in FIELD_SPECS
        }
    )

    applications.insert(0, record)
    _save_json_array(completed_path, applications)

    print(f"Added application #{record['application_number']}: {record['company']} - {record['title']}")
    print(f"Saved to: {completed_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Application Workflow",
        description="Personal application tracking.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    applications_parser = subparsers.add_parser("applications", help="Application tracking commands")
    applications_subparsers = applications_parser.add_subparsers(dest="applications_command", required=True)

    add_parser = applications_subparsers.add_parser("add", help="Add a completed application")
    add_parser.add_argument("--company", help="Company name")
    add_parser.add_argument("--title", help="Job title")
    add_parser.add_argument("--url", help="Application URL")
    add_parser.add_argument("--location", help="Role location", default=None)
    add_parser.add_argument("--status", help="Application status", default=None)
    add_parser.add_argument("--submitted-at", help="Submission timestamp (ISO 8601)", default=None)
    add_parser.add_argument("--notes", help="Optional notes", default=None)
    add_parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read one field per line from standard input in the fixed field order",
    )
    add_parser.add_argument(
        "--file",
        help="Path to completed_applications.json",
        default=str(DEFAULT_COMPLETED_APPLICATIONS_PATH),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, extras = parser.parse_known_args(argv)

    ignored_extras = [item for item in extras if item in {"/", "\\"}]
    unexpected_extras = [item for item in extras if item not in ignored_extras]
    if unexpected_extras:
        parser.error(f"unrecognized arguments: {' '.join(unexpected_extras)}")

    if args.command == "applications" and args.applications_command == "add":
        return add_application(args)

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
