"""
Reference color chart for common urine test strip parameters.
Each entry maps a parameter -> list of (level_label, RGB reference color)
These are approximate standard chart colors (calibrate against your actual strip brand).
"""

REFERENCE_CHART = {
    "Glucose": [
        ("Negative", (0, 128, 90)),
        ("Trace",    (60, 150, 90)),
        ("+1",       (120, 170, 70)),
        ("+2",       (180, 160, 50)),
        ("+3",       (200, 120, 40)),
        ("+4",       (180, 80, 40)),
    ],
    "Protein": [
        ("Negative", (240, 220, 60)),
        ("Trace",    (210, 220, 90)),
        ("+1",       (150, 210, 120)),
        ("+2",       (90, 200, 150)),
        ("+3",       (40, 170, 160)),
    ],
    "pH": [
        ("5.0", (240, 130, 60)),
        ("6.0", (240, 180, 60)),
        ("6.5", (220, 210, 70)),
        ("7.0", (150, 210, 90)),
        ("7.5", (90, 190, 120)),
        ("8.0", (50, 160, 150)),
    ],
    "Ketones": [
        ("Negative", (250, 230, 220)),
        ("Trace",    (240, 200, 210)),
        ("+1",       (220, 150, 190)),
        ("+2",       (190, 100, 170)),
        ("+3",       (150, 60, 150)),
    ],
    "Blood": [
        ("Negative", (250, 200, 60)),
        ("Trace",    (200, 190, 90)),
        ("+1",       (140, 180, 110)),
        ("+2",       (90, 160, 130)),
        ("+3",       (40, 140, 140)),
    ],
}

# Approximate normalized position of each pad on a standard 5-pad strip
# (x_fraction_of_width) — used to auto-slice the strip image
PAD_POSITIONS = {
    "Glucose": 0.15,
    "Protein": 0.35,
    "pH":      0.5,
    "Ketones": 0.65,
    "Blood":   0.85,
}