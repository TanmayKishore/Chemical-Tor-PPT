"""Constants and standard vocabulary across chemical presentation slides."""

NOT_AVAILABLE = "Not Available"      # Unsupplied record
NOT_APPLICABLE = "Not Applicable"    # Does not apply to this project
TO_BE_VERIFIED = "To be verified"    # Data variance detected
TO_BE_FINALISED = "To be finalised"  # Pending ToR appraisal value
CALCULATED = "(Calculated)"          # Derived by arithmetic

CHEMICAL_TOR_DECK = "chemical_tor"
SECTOR_5F = "5(f)"


def is_tor_stage(options) -> bool:
    """Terms of Reference stage: estimates and proposed plans."""
    return True

