import itertools
from typing import List, Optional
from urllib.parse import urlparse

from app.schemas.corporate_entity import AccountNode, AccountSuggestion, RecommendationType


def normalize_string(val: Optional[str]) -> str:
    if not val:
        return ""
    return " ".join(val.lower().strip().split())


def normalize_domain(url: Optional[str]) -> str:
    if not url:
        return ""
    cleaned = url.strip().lower()
    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned
    try:
        netloc = urlparse(cleaned).netloc
        return netloc.removeprefix("www.")
    except Exception:
        return ""


def evaluate_merge_candidates(accounts: List[AccountNode]) -> List[AccountSuggestion]:
    suggestions: List[AccountSuggestion] = []

    for acc1, acc2 in itertools.combinations(accounts, 2):
        if acc1.account_type != acc2.account_type:
            continue

        matched_criteria: List[str] = []

        # 1. Same Name
        n1, n2 = normalize_string(acc1.name), normalize_string(acc2.name)
        if n1 and n2 and n1 == n2:
            matched_criteria.append("SAME_NAME")

        # 2. Same URL
        u1, u2 = normalize_domain(acc1.official_url), normalize_domain(acc2.official_url)
        if u1 and u2 and u1 == u2:
            matched_criteria.append("SAME_URL")

        # 3. Same Address
        if acc1.address and acc2.address:
            if acc1.address.canonical_key() == acc2.address.canonical_key():
                matched_criteria.append("SAME_ADDRESS")

        if matched_criteria:
            confidence_weights = {1: 0.80, 2: 0.92, 3: 0.99}
            score = confidence_weights.get(len(matched_criteria), 0.75)

            criteria_str = ", ".join(matched_criteria)
            rationale = (
                f"Accounts '{acc1.name}' (ID: {acc1.id}) and '{acc2.name}' (ID: {acc2.id}) "
                f"exist at the same tier [{acc1.account_type.value}] and matched on criteria: [{criteria_str}]. "
                f"Recommended action: Review records for duplicate consolidation."
            )

            suggestions.append(
                AccountSuggestion(
                    recommendation_type=RecommendationType.SUGGEST_MERGE,
                    primary_account_id=acc1.id,
                    target_account_id=acc2.id,
                    confidence_score=score,
                    match_criteria=matched_criteria,
                    rationale=rationale,
                )
            )

    return suggestions