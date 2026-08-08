from dataclasses import dataclass, field
from threading import Lock


@dataclass
class MetricsStore:
    total_queries: int = 0
    blocked_queries: int = 0
    confidence_scores: list = field(default_factory=list)
    flagged_issue_count: int = 0
    _lock: Lock = field(default_factory=Lock)

    def record_query(self, blocked: bool, confidence: float | None, had_flags: bool):
        with self._lock:
            self.total_queries += 1
            if blocked:
                self.blocked_queries += 1
            if confidence is not None:
                self.confidence_scores.append(confidence)
            if had_flags:
                self.flagged_issue_count += 1

    def summary(self) -> dict:
        with self._lock:
            avg_confidence = (
                sum(self.confidence_scores) / len(self.confidence_scores)
                if self.confidence_scores else None
            )
            return {
                "total_queries": self.total_queries,
                "blocked_queries": self.blocked_queries,
                "block_rate": round(self.blocked_queries / self.total_queries, 3) if self.total_queries else None,
                "avg_confidence": round(avg_confidence, 3) if avg_confidence is not None else None,
                "flagged_issue_rate": round(self.flagged_issue_count / self.total_queries, 3) if self.total_queries else None,
            }


metrics_store = MetricsStore()