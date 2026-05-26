"""LangGraph 에이전트 정량 평가.

사용법:
    python -m eval.run_agent_eval                    # 자동 타임스탬프 파일
    python -m eval.run_agent_eval --out eval/x.md    # 명시 경로

산출 지표:
    - intent_acc           : 의도 분류 정확도
    - tool_correctness     : 기대 Tool 호출 흔적 (LLM judge)
    - proposal_validity    : 시나리오별 최소 제안 수 충족 여부
    - e2e_success          : 시나리오 전체 통과
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from agent.graph import build_agent_graph
from agent.springboot_client import SpringbootClient
from agent.state import make_initial_state
from agent.tools import Tools
from rag.claude_client import ClaudeClient


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def judge_tool_correctness(
    claude: ClaudeClient, expected_tools: list[str], actual_signals: list[str]
) -> int:
    if not expected_tools:
        return 1
    system = (
        "당신은 LangGraph 에이전트의 Tool 호출 검증자입니다. "
        "EXPECTED_TOOLS에 포함된 도구들이 모두 호출된 흔적이 ACTUAL_SIGNALS에 보이면 1, "
        "누락이 있으면 0을 출력하세요. 출력은 0 또는 1만."
    )
    user = (
        f"EXPECTED_TOOLS: {expected_tools}\n\n"
        f"ACTUAL_SIGNALS: {actual_signals}\n\n0 또는 1만:"
    )
    # temperature=0으로 deterministic judging.
    out = claude.chat(system=system, user=user, max_tokens=4, temperature=0.0).strip()
    return 1 if out.startswith("1") else 0


def run_one(scenario: dict, graph, claude: ClaudeClient) -> dict:
    import re

    state = make_initial_state(scenario["user_input"], user_id=1)
    # "3팀" / "4팀" / "8팀" 등을 정규식으로 추출 (인식 못하면 4팀 기본)
    m = re.search(r"(\d+)\s*팀", scenario["user_input"])
    team_count = int(m.group(1)) if m else 4
    team_count = max(1, min(team_count, 16))  # 안전 가드
    state["team_info"] = {
        "team_ids": list(range(1, team_count + 1)),
        "team_names": {i: f"T{i}" for i in range(1, team_count + 1)},
        "team_id": min(team_count, 5),
        "team_name": f"T{min(team_count, 5)}",
    }
    final = graph.invoke(state)

    intent_ok = 1 if final["intent"] == scenario["expected_intent"] else 0
    proposal_ok = (
        1 if len(final.get("proposals", [])) >= scenario["min_proposals"] else 0
    )
    # tool_calls가 명시적으로 잡혀 있으면 LLM judge 없이 결정적으로 검증
    actual_tools = final.get("tool_calls", [])
    expected_tools = scenario.get("expected_tools", [])
    if expected_tools:
        tool_ok = 1 if all(t in actual_tools for t in expected_tools) else 0
    else:
        tool_ok = 1
    signals = final.get("warnings", []) + final.get("errors", [])
    signals.append(f"proposals_count={len(final.get('proposals', []))}")
    signals.append(f"tool_calls={actual_tools}")

    if scenario.get("expect_warning") and not final.get("warnings"):
        proposal_ok = 0

    e2e_ok = 1 if (intent_ok and proposal_ok and tool_ok) else 0

    return {
        "id": scenario["id"],
        "user_input": scenario["user_input"],
        "expected_intent": scenario["expected_intent"],
        "actual_intent": final["intent"],
        "intent_ok": bool(intent_ok),
        "proposal_ok": bool(proposal_ok),
        "tool_ok": bool(tool_ok),
        "e2e_ok": bool(e2e_ok),
        "actual_proposals": len(final.get("proposals", [])),
        "warnings_count": len(final.get("warnings", [])),
    }


def evaluate(scenarios: list[dict]) -> dict:
    claude = ClaudeClient()
    spring = SpringbootClient()
    tools = Tools(client=spring)
    graph = build_agent_graph(claude_client=claude, tools=tools)

    results = [run_one(s, graph, claude) for s in scenarios]
    n = max(1, len(results))
    return {
        "intent_acc": sum(r["intent_ok"] for r in results) / n,
        "tool_correctness": sum(r["tool_ok"] for r in results) / n,
        "proposal_validity": sum(r["proposal_ok"] for r in results) / n,
        "e2e_success": sum(r["e2e_ok"] for r in results) / n,
        "results": results,
    }


def format_report(metrics: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# LangGraph 에이전트 평가 리포트",
        "",
        f"- 실행 시각: {now}",
        f"- 시나리오 수: {len(metrics['results'])}",
        "",
        "## 핵심 지표",
        "",
        "| 지표 | 값 | 목표 | 통과 |",
        "|---|---|---|---|",
        f"| intent_acc | {metrics['intent_acc']:.3f} | ≥ 0.90 | "
        f"{'✅' if metrics['intent_acc'] >= 0.90 else '❌'} |",
        f"| tool_correctness | {metrics['tool_correctness']:.3f} | ≥ 0.85 | "
        f"{'✅' if metrics['tool_correctness'] >= 0.85 else '❌'} |",
        f"| proposal_validity | {metrics['proposal_validity']:.3f} | ≥ 0.90 | "
        f"{'✅' if metrics['proposal_validity'] >= 0.90 else '❌'} |",
        f"| e2e_success | {metrics['e2e_success']:.3f} | ≥ 0.75 | "
        f"{'✅' if metrics['e2e_success'] >= 0.75 else '❌'} |",
        "",
        "## 시나리오별 결과",
        "",
        "| id | input | intent | proposal | tool | e2e |",
        "|---|---|---|---|---|---|",
    ]
    for r in metrics["results"]:
        lines.append(
            f"| {r['id']} | {r['user_input']} | "
            f"{'✅' if r['intent_ok'] else '❌'} ({r['actual_intent']}) | "
            f"{'✅' if r['proposal_ok'] else '❌'} ({r['actual_proposals']}) | "
            f"{'✅' if r['tool_ok'] else '❌'} | "
            f"{'✅' if r['e2e_ok'] else '❌'} |"
        )
    return "\n".join(lines) + "\n"


HISTORY_PATH = Path("eval/agent_history.md")
HISTORY_HEADER = (
    "# LangGraph 에이전트 평가 누적 이력\n\n"
    "매 `python -m eval.run_agent_eval` 실행 결과를 자동 누적. 회차별 지표 변화를 한눈에 비교.\n\n"
    "| 시각 | intent_acc | tool_correctness | proposal_validity | e2e_success | report | note |\n"
    "|---|---|---|---|---|---|---|\n"
)


def _append_history(report_path: Path, metrics: dict, note: str) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text(HISTORY_HEADER, encoding="utf-8")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_note = (note or "-").replace("|", "\\|").replace("\n", " ")
    row = (
        f"| {now} | {metrics['intent_acc']:.3f} | {metrics['tool_correctness']:.3f} | "
        f"{metrics['proposal_validity']:.3f} | {metrics['e2e_success']:.3f} | "
        f"[{report_path.name}]({report_path.name}) | {safe_note} |\n"
    )
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(row)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenarios", default="eval/agent_scenarios.jsonl", type=Path)
    p.add_argument(
        "--out",
        default=None,
        type=Path,
        help="출력 경로. 미지정 시 eval/agent_report_<timestamp>.md 자동 생성 (덮어쓰기 방지)",
    )
    p.add_argument(
        "--note",
        default="",
        type=str,
        help="이번 실행의 변경 노트 (agent_history.md에 함께 기록)",
    )
    args = p.parse_args()

    if args.out is None:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        args.out = Path(f"eval/agent_report_{stamp}.md")
    if args.out.exists():
        raise SystemExit(f"이미 존재하는 파일: {args.out} (덮어쓰기 차단)")

    scenarios = load_scenarios(args.scenarios)
    print(f"시나리오 {len(scenarios)}개 로드. 평가 시작 (LLM judge 호출됨)...")
    metrics = evaluate(scenarios)
    report = format_report(metrics)
    args.out.write_text(report, encoding="utf-8")
    _append_history(args.out, metrics, args.note)

    print()
    print(f"intent_acc        : {metrics['intent_acc']:.3f}")
    print(f"tool_correctness  : {metrics['tool_correctness']:.3f}")
    print(f"proposal_validity : {metrics['proposal_validity']:.3f}")
    print(f"e2e_success       : {metrics['e2e_success']:.3f}")
    print()
    print(f"리포트 저장: {args.out}")
    print(f"누적 이력 갱신: {HISTORY_PATH}")


if __name__ == "__main__":
    main()
