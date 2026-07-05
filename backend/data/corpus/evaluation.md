# Evaluating RAG systems

Because a RAG system has separate retrieval and generation stages, a single accuracy number hides where it fails. Useful evaluation measures each stage and the relationship between them. Three metrics are widely used and can be computed with a language model acting as a judge.

## Faithfulness

Faithfulness measures whether the generated answer is grounded in the retrieved context, that is, whether every claim it makes is supported by the provided passages. Low faithfulness signals hallucination: the model is asserting things the evidence does not back up. This is usually the most important metric for trust, because a confident but unsupported answer is worse than an honest "not enough information".

## Context precision

Context precision measures the quality of retrieval: what fraction of the retrieved passages are actually relevant to the question. Low context precision means the retriever is returning noise, which both wastes the context window and increases the chance of a distracted or unfaithful answer. It is the metric that improves most directly from better hybrid retrieval and reranking.

## Answer relevancy

Answer relevancy measures whether the answer actually addresses the question that was asked, independent of whether it is grounded. An answer can be perfectly faithful to the context yet fail to answer the user's question, for example by summarising a tangent. This metric catches evasive or off-topic responses.

## LLM as a judge

Computing these metrics without human-labelled data relies on using a language model as an evaluator. The judge is given the question, the context, and the answer, and asked to return a calibrated score with a short justification. This is cheap and fast, but the judge is itself imperfect, so scores are best read as directional signals and tracked over time rather than treated as ground truth. Frameworks such as RAGAS standardise these metrics.

## Offline evaluation harness

Running the same fixed set of questions through the system after every change turns evaluation into a regression test. Aggregate scores across the set reveal whether a change to chunking, retrieval, or the prompt actually improved quality or merely moved it around. This is what separates a system that is being engineered from one that is being guessed at.
