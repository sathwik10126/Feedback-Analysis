"""
College email validation and automatic role detection.

Domain policy:  every account must use the official college domain.
Role detection is derived strictly from the local-part of the email
(the part before the @) — the user never self-selects a role at signup.

  Student : local-part is a roll number      e.g. 21CS045@college.edu
            Pattern: starts with digits, contains letters, ends with digits
            (standard university roll-number format: <year><branch><number>)

  Faculty : local-part is alphabetic only     e.g. johnpaul@college.edu
            (first name + last name, no digits, no separators)

  Admin   : NOT derivable from email pattern. Admin access is never granted
            automatically — an existing admin must explicitly promote an
            account from the Admin Panel. This prevents privilege escalation
            through email-format spoofing.
"""

import re

COLLEGE_DOMAIN = "college.edu"

# 21CS045 / 22IT102 / 23ME9  → digits, then letters, then digits
ROLL_NUMBER_PATTERN = re.compile(r"^\d{2}[a-zA-Z]{2,4}\d{1,4}$")

# johnpaul / sarahkhan → letters only, reasonable name length
FACULTY_NAME_PATTERN = re.compile(r"^[a-zA-Z]{4,40}$")

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9]+@([a-zA-Z0-9.-]+)$")


class EmailValidationError(Exception):
    """Raised when a college email fails domain or format validation."""
    pass


def validate_and_detect_role(email: str) -> str:
    """
    Validate a college email and deterministically derive the account role.

    Returns:
        "student" | "faculty"

    Raises:
        EmailValidationError with a user-facing message on any failure.

    Note: "admin" is intentionally never returned here — admin accounts
    are provisioned separately (see promote_to_admin in database layer).
    """
    if not email or "@" not in email:
        raise EmailValidationError("Please enter a valid email address.")

    email = email.strip().lower()
    match = EMAIL_PATTERN.match(email)
    if not match:
        raise EmailValidationError("Email format is invalid.")

    local_part, domain = email.split("@", 1)

    if domain != COLLEGE_DOMAIN:
        raise EmailValidationError(
            f"Only official college email addresses (@{COLLEGE_DOMAIN}) are permitted."
        )

    if ROLL_NUMBER_PATTERN.match(local_part):
        return "student"

    if FACULTY_NAME_PATTERN.match(local_part):
        return "faculty"

    raise EmailValidationError(
        "Email does not match a recognized student roll-number or faculty "
        "name format. Contact the system administrator if you believe this "
        "is an error."
    )


def is_valid_college_domain(email: str) -> bool:
    """Quick domain-only check, used for admin promotion eligibility."""
    if not email or "@" not in email:
        return False
    domain = email.strip().lower().split("@", 1)[1]
    return domain == COLLEGE_DOMAIN