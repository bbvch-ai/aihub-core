import math
import re

from swiss_ai_hub.core.generative_ai import IngestedNode

QUERY_TERM = re.compile(r"[\w-]+")
MIN_TERM_LENGTH = 2
K1 = 1.2
B = 0.75


class AttachedFileLexicalRanking:
    """The sections of a file that share words with the query, best first, scored with BM25.

    Embeddings see a row of a large table as much like every other row, so an identifier such as `ORD-145678` is
    lost to them; counting the query's words finds it. Terms are counted as substrings of the lowercased section and
    no index is built, which keeps memory flat for a sheet of millions of characters.
    """

    @staticmethod
    def rank(sections: list[IngestedNode], query: str) -> list[IngestedNode]:
        terms = AttachedFileLexicalRanking.terms(query)
        if not terms or not sections:
            return []
        texts = [section.content.lower() for section in sections]
        counts = [[text.count(term) for term in terms] for text in texts]
        lengths = [len(text) for text in texts]
        average_length = sum(lengths) / len(lengths) or 1
        idf = [
            AttachedFileLexicalRanking.idf(len(sections), sum(1 for row in counts if row[i])) for i in range(len(terms))
        ]
        scores = [
            sum(
                weight * count * (K1 + 1) / (count + K1 * (1 - B + B * length / average_length))
                for weight, count in zip(idf, row, strict=True)
                if count
            )
            for row, length in zip(counts, lengths, strict=True)
        ]
        ranked = sorted(
            (index for index, score in enumerate(scores) if score > 0), key=lambda index: scores[index], reverse=True
        )
        return [sections[index] for index in ranked]

    @staticmethod
    def terms(query: str) -> list[str]:
        """The query's words and the parts of its hyphenated ones, so `ORD-145678` also matches `145678`."""
        found: list[str] = []
        for token in QUERY_TERM.findall(query.lower()):
            found.append(token)
            if "-" in token:
                found.extend(part for part in token.split("-") if part)
        return list(dict.fromkeys(term for term in found if len(term) >= MIN_TERM_LENGTH))

    @staticmethod
    def idf(total: int, containing: int) -> float:
        """Never negative: classic BM25 penalises a term found in more than half the sections, which with substring
        counting is nearly every short word, and a section would then score lower for containing `is`."""
        return math.log(1 + (total - containing + 0.5) / (containing + 0.5))
