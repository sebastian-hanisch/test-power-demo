"""Konstanten: Vehikel, Regler-Grenzen, Farben, Presets. Das Vehikel (ein Standort-Fenster) ist das der ganzen Linie."""

# Vehikel: ein Standort, tägliche Nachbestellung (Order-up-to), Wiederbeschaffungszeit 2 Tage, Zentrallager unbegrenzt.
BASE_MEAN = 20.0          # mittlere Tagesnachfrage des Standorts (Stück)
DISP = 5                  # Dispersion der negativ-binomialen Tagesnachfrage (ganzzahlig: Gamma(5) = Summe von 5 Exponentialzahlen)
LEAD = 2                  # Wiederbeschaffungszeit in Tagen
BURN_DAYS = 28            # Einschwingtage vor dem Auswertefenster (gleiche Regel wie im Fenster)
WINDOW_DAYS = 28          # Auswertefenster: vier Wochen = ein "Standort-Fenster" = eine Einheit des Experiments
WINDOW_WEEKS = WINDOW_DAYS // 7
Z_A = 1.0                 # Sicherheitsfaktor der bestehenden Regel A

Z_MIN, Z_MAX, DEFAULT_Z = 1.0, 2.0, 1.4      # Regel B: Sicherheitsfaktor (1,0 = identisch mit A = A/A-Test)
Z_STEP = 0.1
Z_GRID = tuple(round(Z_MIN + i * Z_STEP, 1) for i in range(int(round((Z_MAX - Z_MIN) / Z_STEP)) + 1))
N_MIN, N_MAX, DEFAULT_N, N_STEP = 5, 200, 30, 5   # geplante Standort-Fenster je Arm der Hauptstudie
M_MIN, M_MAX, DEFAULT_M, M_STEP = 5, 100, 10, 5   # Fenster je Arm des Pilots
SITES_MIN, SITES_MAX, DEFAULT_SITES, SITES_STEP = 4, 60, 10, 2   # Standorte, die gleichzeitig mitmachen können
SEED_MAX, DEFAULT_SEED = 999999, 35
N_GRID = (5, 10, 20, 30, 50, 100, 200)
POOL_SIZE = 10000         # Einheiten je Pool (je Sicherheitsfaktor)
ALPHA = 0.05
POWER_GOAL = 0.8
LIVE_REPS = 1000          # Wiederholungen der Live-Auswertung (aus dem Pool gezogen)
PILOT_REPS = 2000         # Anzahl Piloten in der Planungsstudie
RELEVANCE_PP = 0.02       # kleinste Wirkung, die sich betrieblich lohnt (2 Prozentpunkte Servicegrad)

COLOR_A = "#4c78a8"
COLOR_B = "#2F6B65"
COLOR_TRUTH = "#d95f02"
COLOR_MISS = "#c0392b"
COLOR_OK = "rgba(120,120,120,0.55)"

PRESETS = {
    "Mittlerer Effekt, kleiner Pilot (Voreinstellung)": {"z": DEFAULT_Z, "n": DEFAULT_N, "m": DEFAULT_M, "sites": DEFAULT_SITES,
                                                         "seed": DEFAULT_SEED},
    "Zu knapp geplant": {"z": 1.2, "n": 10, "m": 5, "sites": DEFAULT_SITES, "seed": DEFAULT_SEED},
    "Kleiner Effekt, großer Aufwand": {"z": 1.1, "n": 100, "m": 20, "sites": DEFAULT_SITES, "seed": DEFAULT_SEED},
    "Großer Effekt, großer Pilot": {"z": 1.8, "n": 20, "m": 50, "sites": DEFAULT_SITES, "seed": DEFAULT_SEED},
}
PRESET_ORDER = tuple(PRESETS)
PRESET_HELP = {
    "Mittlerer Effekt, kleiner Pilot (Voreinstellung)": "Sicherheitsfaktor 1,4 gegen 1,0, Pilot mit 10 Fenstern je Arm, Hauptstudie mit 30.",
    "Zu knapp geplant": "Sicherheitsfaktor 1,2, nur 10 Fenster je Arm in der Hauptstudie und ein Pilot mit 5: der Test sieht den Effekt meist nicht.",
    "Kleiner Effekt, großer Aufwand": "Sicherheitsfaktor 1,1: die Wirkung ist klein, der Umfang für 80 % Teststärke groß.",
    "Großer Effekt, großer Pilot": "Sicherheitsfaktor 1,8 mit einem Pilot von 50 Fenstern je Arm: die Planung ist hier verlässlich.",
}


def fmt_pct(x, digits=1):
    """Anteil (0..1) als Prozentzahl mit Dezimalkomma, z. B. 0,934 -> '93,4 %'."""
    return f"{100 * x:.{digits}f}".replace(".", ",") + " %"


def fmt_pp(x, digits=2):
    """Differenz in Prozentpunkten (aus Anteilen 0..1) mit Vorzeichen und Dezimalkomma."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Prozentpunkte"


def fmt_pp_plain(x, digits=1):
    """Betrag in Prozentpunkten ohne Vorzeichen: '3,2 Prozentpunkte'."""
    return f"{100 * x:.{digits}f}".replace(".", ",") + " Prozentpunkte"


def fmt_num(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_int(x):
    """Ganzzahl mit Leerzeichen als Tausendertrenner."""
    return f"{int(x):,}".replace(",", " ")


def fmt_pkt(x, digits=1):
    """Kurzform für enge Kacheln: '+4,0 Pkt.' (Differenz in Prozentpunkten, aus Anteilen 0..1)."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Pkt."
