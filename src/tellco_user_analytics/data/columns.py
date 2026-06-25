"""Canonical xDR column names matching the PostgreSQL schema."""

USER_ID = "MSISDN/Number"
BEARER_ID = "Bearer Id"
DURATION_MS = "Dur. (ms)"
HANDSET_MANUFACTURER = "Handset Manufacturer"
HANDSET_TYPE = "Handset Type"
TOTAL_DL = "Total DL (Bytes)"
TOTAL_UL = "Total UL (Bytes)"

# Application traffic columns (download, upload) per xDR session
APPLICATIONS: dict[str, tuple[str, str]] = {
    "Social Media": ("Social Media DL (Bytes)", "Social Media UL (Bytes)"),
    "Google": ("Google DL (Bytes)", "Google UL (Bytes)"),
    "Email": ("Email DL (Bytes)", "Email UL (Bytes)"),
    "Youtube": ("Youtube DL (Bytes)", "Youtube UL (Bytes)"),
    "Netflix": ("Netflix DL (Bytes)", "Netflix UL (Bytes)"),
    "Gaming": ("Gaming DL (Bytes)", "Gaming UL (Bytes)"),
    "Other": ("Other DL (Bytes)", "Other UL (Bytes)"),
}
