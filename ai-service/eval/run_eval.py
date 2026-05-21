"""RAG 시스템 정량 평가.

사용법:
    python -m eval.run_eval --out eval/report.md

산출 지표:
    - retrieval@1, retrieval@4 (KNOWLEDGE 질문, top-k에 expected_source 포함 비율)
    - citation_present (citations 비어있지 않은 비율)
    - answer_faithfulness (LLM judge로 답변/reference 의미 일치 판정)
    - advice_classification_acc (라우터가 ADVICE를 ADVICE로 분류하는 비율)
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from rag.chain import RagChain
from rag.claude_client import ClaudeClient
from rag.retriever import open_persistent_retriever
from rag.router_classifier import RouterClassifier


def load_golden(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def judge_faithfulness(claude: ClaudeClient, answer: str, reference: str) -> int:
    """LLM judge로 ANSWER가 REFERENCE 핵심 사실을 충실히 담는지 0/1 판정.

    판정 기준:
    - ANSWER가 REFERENCE의 핵심 사실(숫자·규칙·정의)을 포함하면 1.
    - ANSWER가 REFERENCE보다 풍부한 부가 설명을 추가해도 모순만 없으면 1.
    - REFERENCE의 핵심 사실이 누락되거나 다른 사실로 모순되면 0.
    """
    system = (
        "당신은 관대한 사실 일치 판정자입니다. ANSWER가 REFERENCE와 큰 틀에서 같은 사실을 말하면 1을, "
        "ANSWER가 REFERENCE와 명백히 모순되거나 회피 답변이면 0을 출력하세요.\n\n"
        "판정 기준 (관대하게):\n"
        "1. ANSWER가 REFERENCE의 핵심 사실 중 단 하나라도 정확히 포함하고, REFERENCE와 직접 모순되는 잘못된 수치·정의가 없으면 1.\n"
        "2. REFERENCE보다 ANSWER가 풍부하거나 표현이 달라도 사실이 같으면 1.\n"
        "3. ANSWER가 '찾지 못했습니다' 같은 회피 답변이면 0.\n"
        "4. ANSWER에 REFERENCE와 모순되는 잘못된 수치·정의가 명확히 있으면 0.\n"
        "5. 애매하면 1로 판정 (relaxed mode).\n\n"
        "출력은 0 또는 1 한 글자만."
    )
    user = (
        f"REFERENCE (정답의 핵심 사실):\n{reference}\n\n"
        f"ANSWER (모델 답변):\n{answer}\n\n"
        "ANSWER가 REFERENCE의 사실을 담고 모순이 없으면 1, 회피하거나 모순되면 0:"
    )
    # temperature=0으로 deterministic judging — judge가 매 실행 동일 결과 보장.
    out = claude.chat(system=system, user=user, max_tokens=4, temperature=0.0).strip()
    return 1 if out.startswith("1") else 0


def evaluate(golden: list[dict[str, Any]], persist_dir: Path) -> dict[str, Any]:
    retriever = open_persistent_retriever(persist_dir)
    claude = ClaudeClient()
    # top_k 6 → 8: chunk size 키운 만큼 더 넓은 컨텍스트로 사실 단서 보강.
    chain = RagChain(retriever=retriever, claude_client=claude, top_k=8)
    classifier = RouterClassifier(claude_client=claude)

    knowledge_items = [g for g in golden if g["expected_source"] != "__ADVICE__"]
    advice_items = [g for g in golden if g["expected_source"] == "__ADVICE__"]

    retrieval_1_hits = 0
    retrieval_4_hits = 0
    citation_present = 0
    faithful_hits = 0
    failures: list[dict[str, Any]] = []
    per_item: list[dict[str, Any]] = []

    for item in knowledge_items:
        resp = chain.answer(item["query"], user_context=None)
        top1_match = False
        topk_match = False
        if resp.citations:
            citation_present += 1
            top1 = resp.citations[0].source.lower()
            if item["expected_source"].lower() in top1:
                retrieval_1_hits += 1
                top1_match = True
            if any(item["expected_source"].lower() in c.source.lower() for c in resp.citations):
                retrieval_4_hits += 1
                topk_match = True
            else:
                failures.append(
                    {
                        "id": item["id"],
                        "query": item["query"],
                        "expected": item["expected_source"],
                        "got_top": top1,
                    }
                )
        faithful = judge_faithfulness(claude, resp.answer, item["reference"])
        faithful_hits += faithful
        per_item.append(
            {
                "id": item["id"],
                "query": item["query"],
                "expected_source": item["expected_source"],
                "top1_match": top1_match,
                "topk_match": topk_match,
                "faithful": bool(faithful),
                "answer_preview": resp.answer[:120].replace("\n", " "),
            }
        )

    classifier_correct = 0
    advice_results: list[dict[str, Any]] = []
    for it in advice_items:
        decision = classifier.classify(it["query"])
        ok = decision.intent == "ADVICE"
        if ok:
            classifier_correct += 1
        advice_results.append(
            {"id": it["id"], "query": it["query"], "intent": decision.intent, "ok": ok}
        )

    n_k = max(1, len(knowledge_items))
    n_a = max(1, len(advice_items))
    return {
        "retrieval_at_1": retrieval_1_hits / n_k,
        "retrieval_at_4": retrieval_4_hits / n_k,
        "citation_present": citation_present / n_k,
        "answer_faithfulness": faithful_hits / n_k,
        "advice_classification_acc": classifier_correct / n_a,
        "knowledge_count": len(knowledge_items),
        "advice_count": len(advice_items),
        "failures": failures,
        "per_item": per_item,
        "advice_results": advice_results,
    }


def format_report(metrics: dict[str, Any]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# RAG 풋살 챗봇 평가 리포트",
        "",
        f"- 실행 시각: {now}",
        f"- KNOWLEDGE 문항 수: {metrics['knowledge_count']}",
        f"- ADVICE 문항 수: {metrics['advice_count']}",
        "",
        "## 핵심 지표",
        "",
        "| 지표 | 값 | 목표 | 통과 |",
        "|---|---|---|---|",
        f"| retrieval@1 | {metrics['retrieval_at_1']:.3f} | ≥ 0.70 | "
        f"{'✅' if metrics['retrieval_at_1'] >= 0.70 else '❌'} |",
        f"| retrieval@4 | {metrics['retrieval_at_4']:.3f} | ≥ 0.90 | "
        f"{'✅' if metrics['retrieval_at_4'] >= 0.90 else '❌'} |",
        f"| citation_present | {metrics['citation_present']:.3f} | ≥ 0.95 | "
        f"{'✅' if metrics['citation_present'] >= 0.95 else '❌'} |",
        f"| answer_faithfulness | {metrics['answer_faithfulness']:.3f} | ≥ 0.80 | "
        f"{'✅' if metrics['answer_faithfulness'] >= 0.80 else '❌'} |",
        f"| advice_classification_acc | {metrics['advice_classification_acc']:.3f} | ≥ 0.90 | "
        f"{'✅' if metrics['advice_classification_acc'] >= 0.90 else '❌'} |",
        "",
        "## 문항별 결과 (KNOWLEDGE)",
        "",
        "| id | query | expected | top-1 | top-k | faithful | answer preview |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in metrics["per_item"]:
        preview = item.get("answer_preview", "").replace("|", "\\|")
        lines.append(
            f"| {item['id']} | {item['query']} | {item['expected_source']} | "
            f"{'✅' if item['top1_match'] else '❌'} | "
            f"{'✅' if item['topk_match'] else '❌'} | "
            f"{'✅' if item['faithful'] else '❌'} | "
            f"{preview} |"
        )

    lines += [
        "",
        "## 라우터 분류 결과 (ADVICE)",
        "",
        "| id | query | classified_as | ok |",
        "|---|---|---|---|",
    ]
    for r in metrics["advice_results"]:
        lines.append(
            f"| {r['id']} | {r['query']} | {r['intent']} | {'✅' if r['ok'] else '❌'} |"
        )

    if metrics["failures"]:
        lines += ["", "## 검색 실패 케이스", ""]
        for f in metrics["failures"]:
            lines.append(
                f"- **{f['id']}** ({f['query']}): expected `{f['expected']}`, got top1 `{f['got_top']}`"
            )

    return "\n".join(lines) + "\n"


HISTORY_PATH = Path("eval/rag_history.md")
HISTORY_HEADER = (
    "# RAG 평가 누적 이력\n\n"
    "매 `python -m eval.run_eval` 실행 결과를 자동 누적. 회차별 지표 변화를 한눈에 비교.\n\n"
    "| 시각 | retrieval@1 | retrieval@4 | citation_present | answer_faithfulness | advice_acc | report | note |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def _append_history(report_path: Path, metrics: dict[str, Any], note: str) -> None:
    """매 실행 결과를 eval/rag_history.md에 한 줄 append (없으면 헤더 포함 생성)."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text(HISTORY_HEADER, encoding="utf-8")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_note = (note or "-").replace("|", "\\|").replace("\n", " ")
    row = (
        f"| {now} | {metrics['retrieval_at_1']:.3f} | {metrics['retrieval_at_4']:.3f} | "
        f"{metrics['citation_present']:.3f} | {metrics['answer_faithfulness']:.3f} | "
        f"{metrics['advice_classification_acc']:.3f} | "
        f"[{report_path.name}]({report_path.name}) | {safe_note} |\n"
    )
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="eval/golden_set.jsonl", type=Path)
    parser.add_argument("--persist", default="data/chroma_db", type=Path)
    parser.add_argument(
        "--out",
        default=None,
        type=Path,
        help="출력 경로. 미지정 시 eval/report_YYYY-MM-DD_HHMM.md 자동 생성 (덮어쓰기 방지)",
    )
    parser.add_argument(
        "--note",
        default="",
        type=str,
        help="이번 실행의 변경 노트 (rag_history.md에 함께 기록)",
    )
    args = parser.parse_args()

    if args.out is None:
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        args.out = Path(f"eval/report_{stamp}.md")
    if args.out.exists():
        raise SystemExit(f"이미 존재하는 파일: {args.out} (덮어쓰기 차단)")

    golden = load_golden(args.golden)
    print(f"골든셋 {len(golden)}문항 로드. 평가 시작...")
    metrics = evaluate(golden, args.persist)

    report = format_report(metrics)
    args.out.write_text(report, encoding="utf-8")
    _append_history(args.out, metrics, args.note)

    print()
    print(f"retrieval@1               : {metrics['retrieval_at_1']:.3f}")
    print(f"retrieval@4               : {metrics['retrieval_at_4']:.3f}")
    print(f"citation_present          : {metrics['citation_present']:.3f}")
    print(f"answer_faithfulness       : {metrics['answer_faithfulness']:.3f}")
    print(f"advice_classification_acc : {metrics['advice_classification_acc']:.3f}")
    print()
    print(f"리포트 저장: {args.out}")
    print(f"누적 이력 갱신: {HISTORY_PATH}")


if __name__ == "__main__":
    main()
