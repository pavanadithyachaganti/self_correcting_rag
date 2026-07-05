# Corrective and self-correcting RAG

A naive RAG pipeline retrieves a fixed number of chunks and passes them straight to the generator, with no check on whether those chunks are actually useful or whether the answer is grounded. Self-correcting approaches add feedback loops that inspect intermediate results and take action when quality is low.

## Relevance grading

After retrieval, a grading step asks a language model to judge whether the retrieved passages actually help answer the question. If the grade is high, the pipeline proceeds to generation. If the grade is low, the pipeline can react: rewrite the query, retrieve again, or fall back to an external source such as web search. This prevents the generator from being handed weak context that it will either ignore or hallucinate around.

## Query rewriting

When retrieval returns weak context, the original phrasing is often the problem. Query rewriting uses the model to produce an alternative query with better keywords or synonyms, then retrieves again. A small number of rewrite attempts usually recovers relevant passages that the first query missed.

## Corrective RAG

Corrective RAG (CRAG) formalises this idea. A lightweight evaluator labels retrieved documents as correct, ambiguous, or incorrect. Correct documents are refined into focused knowledge strips. When documents are ambiguous or incorrect, the system supplements or replaces them, commonly with a web search, before generating. The goal is to make the generator robust to imperfect retrieval.

## Self-RAG

Self-RAG trains a model to decide when to retrieve and to critique its own output using reflection tokens. The model can assess whether a statement is supported by the retrieved evidence and whether the response is useful, then revise accordingly. The shared theme across CRAG and Self-RAG is the same: do not trust the first retrieval or the first draft blindly. Check, and correct.

## Faithfulness verification

A final self-correction step checks the generated answer against the retrieved context for unsupported claims. If the answer asserts something the context does not support, the system can regenerate under stricter instructions to use only the provided evidence. This directly targets hallucination, the failure mode that most damages user trust.
