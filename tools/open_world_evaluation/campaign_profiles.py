"""Resource-bounded campaign profiles for continuous OW evaluation."""

from __future__ import annotations

import argparse
import os
from typing import Any

SCHEDULE_PROFILES = {
    "15 2 * * *": ("daily", 20),
    "30 3 * * 1": ("weekly", 100),
}
RELEASE_PROMPT_COUNT = 250
MANUAL_DEFAULT = 100
MANUAL_MAX = 2000
TARGETS_PER_PROMPT = 3
CONTROLLED_DIAGNOSTIC_COUNT = 106


def resolve_campaign_profile(
    event_name: str,
    *,
    schedule: str = "",
    prompt_count: str | int | None = None,
) -> dict[str, Any]:
    """Return a validated profile for schedule, release, or manual campaigns."""
    if event_name == "schedule":
        if schedule not in SCHEDULE_PROFILES:
            raise ValueError(f"unsupported OW schedule: {schedule!r}")
        cadence, count = SCHEDULE_PROFILES[schedule]
    elif event_name == "release":
        cadence, count = "release", RELEASE_PROMPT_COUNT
    elif event_name == "workflow_dispatch":
        cadence = "manual"
        raw = MANUAL_DEFAULT if prompt_count in (None, "") else prompt_count
        try:
            count = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("manual prompt_count must be an integer") from exc
        if isinstance(raw, bool) or not 1 <= count <= MANUAL_MAX:
            raise ValueError(f"manual prompt_count must be between 1 and {MANUAL_MAX}")
    else:
        raise ValueError(f"unsupported campaign event: {event_name!r}")

    random_case_count = count * TARGETS_PER_PROMPT
    total_case_count = random_case_count + CONTROLLED_DIAGNOSTIC_COUNT
    return {
        "cadence": cadence,
        "prompt_count": count,
        "random_target_case_count": random_case_count,
        "controlled_diagnostic_case_count": CONTROLLED_DIAGNOSTIC_COUNT,
        "total_case_count": total_case_count,
        "target_count": TARGETS_PER_PROMPT,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a safe OW continuous-campaign profile.")
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    parser.add_argument("--schedule", default=os.environ.get("GITHUB_EVENT_SCHEDULE", ""))
    parser.add_argument("--prompt-count", default=os.environ.get("MANUAL_PROMPT_COUNT", ""))
    args = parser.parse_args()
    try:
        profile = resolve_campaign_profile(
            args.event, schedule=args.schedule, prompt_count=args.prompt_count
        )
    except ValueError as exc:
        parser.error(str(exc))

    for key, value in profile.items():
        print(f"{key}={value}")
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as stream:
            stream.write(f"OW_CADENCE={profile['cadence']}\n")
            stream.write(f"PROMPT_COUNT={profile['prompt_count']}\n")
            stream.write(f"OW_EXPECTED_CASE_COUNT={profile['total_case_count']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
