"""Canonical xDR column names matching the PostgreSQL schema."""

USER_ID = "MSISDN/Number"
BEARER_ID = "Bearer Id"
DURATION_MS = "Dur. (ms)"
HANDSET_MANUFACTURER = "Handset Manufacturer"
HANDSET_TYPE = "Handset Type"
TOTAL_DL = "Total DL (Bytes)"
TOTAL_UL = "Total UL (Bytes)"

# Network / experience columns (per xDR session)
RTT_DL = "Avg RTT DL (ms)"
RTT_UL = "Avg RTT UL (ms)"
THROUGHPUT_DL = "Avg Bearer TP DL (kbps)"
THROUGHPUT_UL = "Avg Bearer TP UL (kbps)"
TCP_RETRANS_DL = "TCP DL Retrans. Vol (Bytes)"
TCP_RETRANS_UL = "TCP UL Retrans. Vol (Bytes)"

EXPERIENCE_SESSION_COLUMNS = [
    RTT_DL,
    RTT_UL,
    THROUGHPUT_DL,
    THROUGHPUT_UL,
    TCP_RETRANS_DL,
    TCP_RETRANS_UL,
    HANDSET_TYPE,
]

# Aggregated per-user experience metric names
AVG_TCP_RETRANS = "avg_tcp_retrans_bytes"
AVG_RTT_MS = "avg_rtt_ms"
AVG_THROUGHPUT_KBPS = "avg_throughput_kbps"
EXPERIENCE_FEATURES = [AVG_TCP_RETRANS, AVG_RTT_MS, AVG_THROUGHPUT_KBPS]

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
