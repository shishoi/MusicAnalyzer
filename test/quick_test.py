from rapidfuzz import fuzz

title1 = 'יאללה תרקדי'
title2 = 'תיק קטן'

sim = fuzz.token_set_ratio(title1, title2) / 100.0

print(f"Title 1: {title1}")
print(f"Title 2: {title2}")
print(f"Similarity: {sim:.2%}")
print(f"Minimum required: 70%")
print(f"\nResult: {'SKIPPED - will not be compared' if sim < 0.70 else 'PASSED - will continue comparison'}")
