import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.retrieval import Index
from app.agent import SelfCorrectingAgent


def main():
    eval_path = os.path.join(os.path.dirname(__file__), "..", "data", "eval_set.json")
    with open(eval_path) as f:
        questions = [q["question"] for q in json.load(f)]

    idx = Index()
    idx.build(settings.corpus_dir)
    agent = SelfCorrectingAgent(idx)

    agg = {"faithfulness": 0.0, "context_precision": 0.0, "answer_relevancy": 0.0}
    print(f"\nRunning eval on {len(questions)} questions (provider={agent.llm.name})\n")
    print(f"{'faith':>7} {'ctxP':>7} {'ansR':>7}  question")
    print("-" * 72)
    for q in questions:
        r = agent.run(q)
        s = r["scores"]
        for k in agg:
            agg[k] += s[k]
        print(f"{s['faithfulness']:>7.2f} {s['context_precision']:>7.2f} "
              f"{s['answer_relevancy']:>7.2f}  {q[:44]}")
    n = len(questions)
    print("-" * 72)
    print(f"{agg['faithfulness']/n:>7.2f} {agg['context_precision']/n:>7.2f} "
          f"{agg['answer_relevancy']/n:>7.2f}  AVERAGE\n")


if __name__ == "__main__":
    main()
