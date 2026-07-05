# Reranking

Retrieval optimises for speed across a large corpus, which means it uses cheap scoring that trades some accuracy for scale. Reranking is a second, more expensive pass over a small candidate set that reorders results by relevance before they reach the generator.

## Bi-encoders versus cross-encoders

The embedding models used in dense retrieval are bi-encoders: they encode the query and each document separately, so document vectors can be precomputed and searched quickly. The cost of that efficiency is that the query and document never interact during scoring.

A cross-encoder instead takes the query and a candidate document together as a single input and outputs a relevance score. Because the two texts attend to each other directly, cross-encoders are markedly more accurate at judging relevance. They are too slow to run over an entire corpus, but ideal for reranking a handful of candidates.

## The two-stage pattern

The standard pattern is retrieve-then-rerank. A fast hybrid retriever pulls a few dozen candidates, and a cross-encoder reranks them down to the top few that are actually sent to the generator. This combination captures most of the accuracy of an exhaustive cross-encoder search at a small fraction of the cost, because the expensive model only ever sees a short list.

## Why it matters for grounding

Reranking improves not just ordering but grounding. Passing fewer, higher-quality passages to the generator reduces distraction from loosely related chunks and lowers the chance that the model latches onto an irrelevant detail. Better context precision going in tends to produce more faithful answers coming out.
