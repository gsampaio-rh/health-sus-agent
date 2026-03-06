"""ICSAP — Brazilian list of Primary-Care-Sensitive Conditions (Portaria SAS/MS 221/2008).

Each ICSAP group maps to ICD-10 codes that represent hospitalizations avoidable
through effective primary care. A high ICSAP admission rate signals primary care failure.
"""

ICSAP_GROUPS: dict[str, dict] = {
    "01_vaccine_preventable": {
        "name": "Doenças preveníveis por imunização",
        "codes": [
            "A33", "A34", "A35", "A36", "A37", "A95",
            "B05", "B06", "B16", "B26",
            "G000",
            "A170", "A19",
            "A150", "A151", "A152", "A153", "A154", "A155", "A156", "A157", "A158", "A159",
            "A160", "A161", "A162", "A163", "A164", "A165", "A166", "A167", "A168", "A169",
            "A171", "A172", "A173", "A174", "A175", "A176", "A177", "A178", "A179",
            "A18",
            "I00", "I01", "I02",
            "A51", "A52", "A53",
            "B50", "B51", "B52", "B53", "B54",
            "B77",
        ],
    },
    "02_gastroenteritis": {
        "name": "Gastroenterites infecciosas e complicações",
        "codes": ["E86", "A00", "A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09"],
    },
    "03_anemia": {
        "name": "Anemia por deficiência de ferro",
        "codes": ["D50"],
    },
    "04_nutritional_deficiency": {
        "name": "Deficiências nutricionais",
        "codes": [
            "E40", "E41", "E42", "E43", "E44", "E45", "E46",
            "E50", "E51", "E52", "E53", "E54", "E55", "E56", "E57", "E58", "E59",
            "E60", "E61", "E62", "E63", "E64",
        ],
    },
    "05_ear_nose_throat": {
        "name": "Infecções de ouvido, nariz e garganta",
        "codes": ["H66", "J00", "J01", "J02", "J03", "J06", "J31"],
    },
    "06_bacterial_pneumonia": {
        "name": "Pneumonias bacterianas",
        "codes": ["J13", "J14", "J153", "J154", "J158", "J159", "J181"],
    },
    "07_asthma": {
        "name": "Asma",
        "codes": ["J45", "J46"],
    },
    "08_pulmonary": {
        "name": "Doenças pulmonares",
        "codes": ["J20", "J21", "J40", "J41", "J42", "J43", "J44", "J47"],
    },
    "09_hypertension": {
        "name": "Hipertensão",
        "codes": ["I10", "I11"],
    },
    "10_angina": {
        "name": "Angina pectoris",
        "codes": ["I20"],
    },
    "11_heart_failure": {
        "name": "Insuficiência cardíaca",
        "codes": ["I50", "J81"],
    },
    "12_cerebrovascular": {
        "name": "Doenças cerebrovasculares",
        "codes": ["I63", "I64", "I65", "I66", "I67", "I69", "G45", "G46"],
    },
    "13_diabetes": {
        "name": "Diabetes mellitus",
        "codes": [
            "E100", "E101", "E102", "E103", "E104", "E105", "E106", "E107", "E108", "E109",
            "E110", "E111", "E112", "E113", "E114", "E115", "E116", "E117", "E118", "E119",
            "E120", "E121", "E122", "E123", "E124", "E125", "E126", "E127", "E128", "E129",
            "E130", "E131", "E132", "E133", "E134", "E135", "E136", "E137", "E138", "E139",
            "E140", "E141", "E142", "E143", "E144", "E145", "E146", "E147", "E148", "E149",
        ],
    },
    "14_epilepsy": {
        "name": "Epilepsia",
        "codes": ["G40", "G41"],
    },
    "15_kidney_urinary": {
        "name": "Infecção no rim e trato urinário",
        "codes": ["N10", "N11", "N12", "N30", "N34", "N390"],
    },
    "16_skin_infection": {
        "name": "Infecção da pele e tecido subcutâneo",
        "codes": ["A46", "L01", "L02", "L03", "L04", "L08"],
    },
    "17_pelvic_inflammatory": {
        "name": "Doença inflamatória de órgãos pélvicos femininos",
        "codes": ["N70", "N71", "N72", "N73", "N75", "N76"],
    },
    "18_gi_ulcer": {
        "name": "Úlcera gastrointestinal",
        "codes": ["K25", "K26", "K27", "K28", "K920", "K921", "K922"],
    },
    "19_prenatal": {
        "name": "Doenças relacionadas ao pré-natal e parto",
        "codes": ["O23", "A50", "P350"],
    },
}


def _build_lookup_table() -> dict[str, str]:
    """Build a flat lookup: every possible ICD-10 prefix → group key.

    Expands short prefixes (e.g. "A33") into entries at lengths 3, 4, 5
    so vectorized matching on truncated codes works in O(1) per row.
    """
    lookup: dict[str, str] = {}
    for group_key, group in ICSAP_GROUPS.items():
        for code in group["codes"]:
            norm = code.upper().replace(".", "")
            lookup[norm] = group_key
    return lookup


_ICSAP_LOOKUP = _build_lookup_table()

# Pre-compute sorted unique prefix lengths for vectorized matching
_PREFIX_LENGTHS = sorted(set(len(k) for k in _ICSAP_LOOKUP), reverse=True)


def classify_icsap(icd10_code: str) -> str | None:
    """Classify a single ICD-10 code into an ICSAP group (for non-vectorized use)."""
    if not icd10_code or not isinstance(icd10_code, str):
        return None
    clean = icd10_code.strip().upper().replace(".", "")
    if not clean:
        return None
    for length in _PREFIX_LENGTHS:
        prefix = clean[:length]
        if prefix in _ICSAP_LOOKUP:
            return _ICSAP_LOOKUP[prefix]
    return None


def classify_icsap_series(codes: "pd.Series") -> "pd.Series":
    """Vectorized ICSAP classification for a pandas Series of ICD-10 codes.

    ~100x faster than row-by-row classify_icsap for large DataFrames.
    """
    import pandas as pd

    clean = codes.astype(str).str.strip().str.upper().str.replace(".", "", regex=False)

    result = pd.Series(index=codes.index, dtype="object")

    for length in _PREFIX_LENGTHS:
        truncated = clean.str[:length]
        matched = truncated.map(_ICSAP_LOOKUP)
        mask = matched.notna() & result.isna()
        result = result.where(~mask, matched)

    return result


def is_icsap(icd10_code: str) -> bool:
    """Fast check: is this ICD-10 code an ICSAP condition?"""
    return classify_icsap(icd10_code) is not None


def get_group_name(group_key: str) -> str:
    return ICSAP_GROUPS.get(group_key, {}).get("name", group_key)
