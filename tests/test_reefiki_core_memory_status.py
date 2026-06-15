from scripts.reefiki_core.memory_status import (
    compact_status_result,
    memory_status_has_open,
    memory_status_next_action,
)


def test_memory_status_has_open_detects_review_queues() -> None:
    result = {
        "project": "reefiki",
        "review_queues": {"total": 1},
        "promotion_inbox": {"active": 0},
    }

    assert memory_status_has_open(result) is True


def test_memory_status_next_action_prefers_review_queue_summary() -> None:
    result = {
        "project": "reefiki",
        "review_queues": {"total": 2},
        "promotion_inbox": {"active": 1},
    }

    assert memory_status_next_action(result) == "run review-queues --summary for project reefiki"


def test_memory_status_next_action_reports_all_projects_summary() -> None:
    result = {
        "project": "all",
        "totals": {"review_queues": 0, "promotion_active": 1},
        "projects": [],
    }

    assert memory_status_next_action(result) == "run memory status --all-projects --only-open --summary"


def test_compact_status_result_keeps_all_project_summary_shape() -> None:
    result = {
        "project": "all",
        "only_open": True,
        "total": 1,
        "totals": {"review_queues": 1, "promotion_active": 0},
        "projects": [
            {
                "project": "reefiki",
                "policy": {"outcome": "pass"},
                "graphify": {"status": "missing_report"},
                "review_queues": {"total": 1},
                "promotion_inbox": {"active": 0},
                "next_action": "run review-queues --summary for project reefiki",
            }
        ],
    }

    compact = compact_status_result(result)

    assert compact["summary"] is True
    assert compact["has_open"] is True
    assert compact["projects"][0]["policy"] == "pass"
    assert compact["projects"][0]["graphify"] == "missing_report"
