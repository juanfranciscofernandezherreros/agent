"""OWASP security knowledge used to enrich static-analysis findings.

Mappings are intentionally conservative and versioned; they classify candidates but
do not prove exploitability.
"""

OWASP_SQL_INJECTION = {
    "owasp_top10": {
        "version": "2025",
        "id": "A05:2025",
        "name": "Injection",
        "url": "https://top10.owasp.org/2025/A05_2025-Injection/",
    },
    "cwe": {
        "id": "CWE-89",
        "name": "Improper Neutralization of Special Elements used in an SQL Command",
        "url": "https://cwe.mitre.org/data/definitions/89.html",
    },
    "asvs_area": "V5 - Validation, Sanitization and Encoding",
    "guidance": [
        "Prefer parameterized queries/prepared statements so data remains separate from SQL syntax.",
        "Do not concatenate untrusted values into SQL query strings.",
        "For structural SQL elements that cannot be parameterized (such as identifiers or sort direction), use strict allow-lists of application-owned values.",
        "Do not treat manual escaping as the primary defense.",
    ],
    "references": [
        "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
        "https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html",
        "https://owasp.org/Top10/2025/A05_2025-Injection/",
    ],
}
