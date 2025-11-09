
import re

# Compare 2 strings and return a similarity score /100
def compareStrings(left: str, right: str) -> int:

    specialChar = re.compile(r"[^a-zA-Z0-9]")
    spaces = re.compile(r"\s+")

    if left == right:
        return 100

    left = left.strip().lower()
    right = right.strip().lower()

    if left == right:
        return 98

    left = re.sub(specialChar, " ", left)
    left = re.sub(spaces, " ", left)

    right = re.sub(specialChar, " ", right)
    right = re.sub(spaces, " ", right)

    if left == right:
        return 95

    lWords = set(left.split())
    rWords = set(right.split())

    wordsInCommon = lWords & rWords
    totalWords = lWords | rWords

    similarity = len(wordsInCommon) / len(totalWords)
    return int(similarity * 100)
