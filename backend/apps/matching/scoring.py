"""
Compatibility scoring engine.

Deliberately kept as a pure, stateless function of two users' data so it
can later be swapped for a machine-learning recommender without touching
any calling code (views, services) — callers only depend on the
`compatibility_score(user_a, user_b) -> int` contract.

Signal weights are configurable via settings.MATCHING_WEIGHTS.
"""
from django.conf import settings


def _location_score(user_a, user_b) -> float:
    loc_a = (user_a.location or "").strip().lower()
    loc_b = (user_b.location or "").strip().lower()
    if not loc_a or not loc_b:
        return 0.5  # neutral — insufficient data, don't penalize or reward
    return 1.0 if loc_a == loc_b else 0.0


def _interest_score(profile_a, profile_b) -> float:
    interests_a = set(profile_a.interests.values_list("id", flat=True)) if profile_a else set()
    interests_b = set(profile_b.interests.values_list("id", flat=True)) if profile_b else set()

    if not interests_a and not interests_b:
        return 0.5  # neutral — no data either way
    union = interests_a | interests_b
    if not union:
        return 0.0
    intersection = interests_a & interests_b
    return len(intersection) / len(union)  # Jaccard similarity


def _age_score(user_a, user_b) -> float:
    from apps.profiles.models import Profile

    age_a = Profile.objects.filter(user=user_a).first()
    age_b = Profile.objects.filter(user=user_b).first()
    age_a = age_a.age if age_a else None
    age_b = age_b.age if age_b else None

    if age_a is None or age_b is None:
        return 0.5  # neutral — no DOB on file
    max_diff = getattr(settings, "MATCHING_MAX_AGE_DIFF", 15)
    diff = abs(age_a - age_b)
    return max(0.0, 1 - (diff / max_diff))


def _community_score(user_a, user_b) -> float:
    """
    Community overlap. The `communities` app is scaffolded but not yet
    implemented (later phase), so this returns a neutral score for now.
    Once CommunityMembership exists, replace this with a Jaccard overlap
    of each user's community memberships — the weight is already
    reserved for it and no caller-side changes will be needed.
    """
    return 0.5


def compatibility_score(user_a, user_b, weights: dict | None = None) -> int:
    """
    Returns an integer 0-100 compatibility score between two users.
    """
    weights = weights or settings.MATCHING_WEIGHTS

    profile_a = getattr(user_a, "profile", None)
    profile_b = getattr(user_b, "profile", None)

    location = _location_score(user_a, user_b)
    interests = _interest_score(profile_a, profile_b)
    age = _age_score(user_a, user_b)
    community = _community_score(user_a, user_b)

    raw = (
        location * weights["location"]
        + interests * weights["interests"]
        + age * weights["age"]
        + community * weights["community"]
    )
    return round(max(0.0, min(1.0, raw)) * 100)
