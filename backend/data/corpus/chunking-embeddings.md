# Chunking and embeddings

Before retrieval can happen, documents must be split into chunks and each chunk turned into a vector. Both choices quietly shape the quality of everything downstream.

## Chunking

A chunk is the unit of retrieval. If chunks are too large, a single vector has to represent several ideas at once, which blurs its meaning and drags in irrelevant text alongside the relevant part. If chunks are too small, they lose the surrounding context needed to be understood on their own. A common starting point is a few hundred tokens per chunk with a small overlap between neighbours so that a sentence split across a boundary is not lost. Splitting on natural boundaries such as paragraphs or headings usually beats splitting on a fixed character count, because it keeps coherent ideas together.

## Overlap

Overlap means consecutive chunks share some text at their boundary. A modest overlap reduces the risk that the exact passage answering a question falls in the gap between two chunks. Too much overlap inflates the index and returns near-duplicate results, so it is a balance.

## Embeddings

An embedding model maps text to a vector such that texts with similar meaning land near each other in the vector space. Retrieval quality depends heavily on the embedding model matching the domain of the corpus. General-purpose models are a reasonable default and run locally on a CPU, which keeps cost at zero.

## Cosine similarity and normalisation

Similarity between two embeddings is measured by the cosine of the angle between them. If vectors are L2-normalised to unit length first, cosine similarity reduces to a simple dot product, which is fast to compute at scale. Normalising embeddings up front is a common optimisation that lets a plain matrix multiplication rank an entire corpus against a query in one step.
