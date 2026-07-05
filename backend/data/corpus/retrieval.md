# Retrieval in RAG systems

Retrieval-augmented generation grounds a language model in an external corpus so that answers reflect specific source material rather than only the model's parametric memory. The quality of the retrieval step sets a ceiling on the quality of the final answer: if the right passage never reaches the model, no amount of clever prompting will recover it.

## Dense retrieval

Dense retrieval encodes both the query and each document chunk into fixed-length vectors using an embedding model, then finds the nearest chunks by cosine similarity. Dense methods capture semantic similarity, so a query about "cutting energy costs" can match a passage about "reducing power consumption" even with no shared words. Their weakness is exact terms: rare identifiers, product codes, and proper nouns can be under-weighted.

## Sparse retrieval and BM25

Sparse retrieval scores documents on term overlap. BM25 is the standard lexical ranking function. It rewards query terms that appear in a document, dampens the effect of very frequent terms, and normalises for document length. BM25 is strong exactly where dense retrieval is weak: exact keywords, codes, and names. It has no notion of synonyms, so paraphrased queries can miss.

## Hybrid retrieval

Because dense and sparse retrieval fail in different ways, combining them is more robust than either alone. A hybrid retriever runs both and merges the two ranked lists. The merge should not simply add raw scores, because dense cosine scores and BM25 scores live on different scales. Rank-based fusion avoids this problem.

## Reciprocal rank fusion

Reciprocal rank fusion (RRF) combines ranked lists using only the position of each item, not its raw score. Each document receives a score of one divided by a constant k plus its rank in a list, summed across all lists. A common value of k is 60. Because it uses rank rather than score, RRF is insensitive to the different score scales of dense and sparse retrievers, which makes it a simple and reliable default for hybrid search.
