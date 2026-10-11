"""Teststärke und Stichprobenumfang - wie viel Daten reichen? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zweites Stück der Konzepte-Linie "Experimente und Wirkungsmessung": Aufbauend auf dem A/B-Test des ersten Stücks (gleiches
Vehikel: Standort-Fenster, Servicegrad) geht es um die Frage vor dem Experiment: Wie viele Fenster braucht man, was findet
ein Test mit n Fenstern gerade noch, und was passiert, wenn man den Umfang aus einem kleinen Pilot plant? Siehe README.

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import pwr_constants as C
from pwr_evaluation import (Settings, achieved_power, detectable_effect, duration_weeks, load_power_tables, load_pools,
                            nearest_z, normal_formula_n, pilot_plans, plan_outcomes, run_pilot, summarize, true_effect)
from pwr_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from pwr_visualization import build_exaggeration, build_mde, build_plan_boxes, build_plan_power

st.set_page_config(page_title="Teststärke – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _pools():
    return load_pools()


@st.cache_data(show_spinner=False)
def _tables():
    return load_power_tables()


@st.cache_data(show_spinner=False)
def _pilot(z, n, m, sites, seed):
    return run_pilot(Settings(z, n, m, sites, seed))


@st.cache_data(show_spinner=False)
def _cells(z):
    pools = _pools()
    return [summarize(pools, z, n, reps=C.LIVE_REPS, tag=9) for n in C.N_GRID]


@st.cache_data(show_spinner=False)
def _plans(z, m):
    pools = _pools()
    return pilot_plans(pools, z, m, reps=C.PILOT_REPS, relevance=C.RELEVANCE_PP)


st.title("📏 Teststärke und Stichprobenumfang: wie viele Fenster reichen?")
st.markdown(
    """
Im ersten Stück war die Frage: **Ist ein gemessener Unterschied echt?** Hier kommt die Frage davor: **Wie viele
Standort-Fenster muss man messen, damit ein echter Vorteil überhaupt gefunden wird?** Die **Teststärke** ist die
Wahrscheinlichkeit, dass der Test einen echten Unterschied als signifikant meldet. Sie hängt an vier Dingen: der **Größe der
Wirkung**, der **Streuung** der Fenster, dem **Umfang** und der **Fehlalarm-Grenze** (5 %). Weil die wahre Wirkung im
Vehikel bekannt ist, lässt sich messen, **was ein Test mit n Fenstern gerade noch findet**, wie weit ein signifikantes Ergebnis
danebenliegen kann und **wie gut die Planung aus einem kleinen Pilot ist**.
"""
)
st.caption(
    "Zweites Stück der Linie „Experimente und Wirkungsmessung“, aufbauend auf "
    "[ab-test-demo](https://sebastianhanisch-ab-test-demo.streamlit.app/) (gleiches Vehikel: Standort-Fenster, Servicegrad, "
    "Regel A gegen Regel B). Jedes Folgestück hebt eine der Annahmen unter „Wo die Annahmen enden“ auf."
)

with st.expander("So hängen Teststärke und Umfang zusammen", expanded=True):
    st.markdown(
        """
- **Wirkung:** Wie viel besser Regel B wirklich ist (Prozentpunkte Servicegrad). Halbe Wirkung heißt vierfacher Umfang.
- **Streuung:** Wie unterschiedlich die Fenster sind. Weniger Streuung heißt weniger Fenster.
- **Umfang:** Fenster je Arm. Der nachweisbare Effekt schrumpft nur mit der Wurzel des Umfangs.
- **Normalformel:** n = (1,96 + 0,84)² · (σ_A² + σ_B²) / Wirkung² je Arm für 80 % Teststärke. Sie braucht Wirkung und
  Streuung, und beides kennt man vor dem Experiment nicht, sondern nur aus einem **Pilot**.
- **Dauer:** Jedes Fenster braucht vier Wochen Messung nach vier Wochen Einschwingen. Wie viele Standorte gleichzeitig
  mitmachen, bestimmt die Wochen bis zum Ergebnis.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{i}", width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])
st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Wahrheit**")
    z = st.slider("Sicherheitsfaktor z von Regel B", *bounds("z_slider"), step=C.Z_STEP, key="z_slider", format="%.1f",
                  help="Regel A fährt z = 1,0. Je größer z, desto größer die wahre Wirkung. Bei z = 1,0 gibt es keine Wirkung.")
    st.markdown("**Planung**")
    n = st.slider("Fenster je Arm in der Hauptstudie", *bounds("n_slider"), step=C.N_STEP, key="n_slider",
                  help="So viele unabhängige Standort-Fenster bekommt jede Regel in der Hauptstudie.")
    m = st.slider("Fenster je Arm im Pilot", *bounds("m_slider"), step=C.M_STEP, key="m_slider",
                  help="Der Pilot liefert die Schätzungen für Wirkung und Streuung, aus denen der Umfang geplant wird.")
    sites = st.slider("Standorte, die gleichzeitig messen", *bounds("sites_slider"), step=C.SITES_STEP, key="sites_slider",
                      help="Jeder Standort misst ein Fenster nach dem anderen; je mehr Standorte, desto schneller das Ergebnis.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1,
                           key="seed_input", help="Bestimmt die Nachfragen des einen Pilots unten.")
    st.button("🎲 Neuen Pilot würfeln", on_click=randomize_seed)

z, n, m, sites, seed = nearest_z(float(z)), int(n), int(m), int(sites), int(seed)
sync_query_params({"z_slider": z, "n_slider": n, "m_slider": m, "sites_slider": sites, "seed_input": seed})

pools = _pools()
tables = _tables()
truth = true_effect(pools, z)
sd_a = float(pools[nearest_z(C.Z_A)].std(ddof=1))
sd_b = float(pools[z].std(ddof=1))
table = tables[z]
power_now = float(achieved_power(table, n))
has_effect = z > C.Z_A
n_need = normal_formula_n(pools, z) if has_effect else None

# --- Was sieht ein Test mit n Fenstern? ------------------------------------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 🔭 Was findet ein Test mit n Fenstern?")
mde_now = detectable_effect(sd_a, sd_b, n)
weeks = duration_weeks(n, sites)
row1, row2 = st.columns(2), st.columns(2)
c1, c2, c3, c4 = row1[0], row1[1], row2[0], row2[1]
c1.metric("Teststärke" if has_effect else "Fehlalarmrate", C.fmt_pct(power_now),
          help="Anteil der Experimente, die bei dieser Wirkung und diesem Umfang signifikant werden (gemessen).")
c2.metric("Nachweisbar (80 %)", C.fmt_pkt(mde_now).replace("+", ""),
          help="Kleinste wahre Wirkung, die der Test bei diesem Umfang mit 80 % Teststärke findet (Normalformel).")
c3.metric("Nötig für 80 %", str(n_need) if n_need is not None else "–",
          help="Fenster je Arm. Normalformel mit der wahren Wirkung und den gemessenen Streuungen; bei z = 1,0 gibt es keine Wirkung.")
c4.metric("Dauer", f"{weeks} Wochen",
          help=f"2 × {n} Fenster auf {sites} Standorten; eine Runde dauert {C.WINDOW_WEEKS + C.BURN_DAYS // 7} Wochen.")
ns_curve = np.array(list(range(5, 61)) + list(range(65, 201, 5)) + list(range(225, 1001, 25)), dtype=float)
st.plotly_chart(build_mde(ns_curve, [detectable_effect(sd_a, sd_b, k) for k in ns_curve], truth, n, n_need),
                width="stretch", key=f"mde_{z}_{n}")
if has_effect:
    if power_now >= 0.8:
        verdict = f"Mit {n} Fenstern je Arm findet der Test diese Wirkung in {C.fmt_pct(power_now, 0)} der Fälle."
    else:
        verdict = (f"Mit {n} Fenstern je Arm findet der Test diese Wirkung nur in {C.fmt_pct(power_now, 0)} der Fälle. "
                   f"Er könnte erst eine Wirkung ab etwa {C.fmt_pp_plain(mde_now)} sicher sehen; die wahre Wirkung ist "
                   f"{C.fmt_pp_plain(truth)}.")
    st.info(
        verdict + f" **Halbiert man die nachweisbare Wirkung, braucht man vier Mal so viele Fenster:** der Gewinn an "
        f"Genauigkeit wächst nur mit der Wurzel des Umfangs. Die Hauptstudie dauert bei {sites} Standorten {weeks} Wochen."
    )
else:
    st.info(
        "Bei z = 1,0 gibt es nichts zu finden: die Teststärke ist die Fehlalarmrate und bleibt um 5 %, egal wie groß die "
        "Stichprobe ist. Die Kurve zeigt trotzdem, welche Wirkung ein Test mit n Fenstern gerade noch fände."
    )

# --- Signifikant und trotzdem zu groß -------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔬 Signifikant und trotzdem zu groß")
if has_effect:
    cells = _cells(z)
    points = [(c["reject"], c["exaggeration"], c["n"]) for c in cells if np.isfinite(c["exaggeration"])]
    here = summarize(pools, z, n, reps=C.LIVE_REPS, tag=9)   # gleiche Ziehung wie die Teststärke-Tabelle
    current = (here["reject"], here["exaggeration"]) if np.isfinite(here["exaggeration"]) else None
    st.markdown(
        "Ein Test schlägt bei kleiner Teststärke nur an, wenn der Zufall die Schätzung nach oben getrieben hat. Wer nur "
        "die **signifikanten** Ergebnisse berichtet, berichtet deshalb zu große Wirkungen."
    )
    st.plotly_chart(build_exaggeration(points, current), width="stretch", key=f"exag_{z}_{n}")
    if current is not None:
        st.info(
            f"Bei {n} Fenstern je Arm und einer Teststärke von {C.fmt_pct(here['reject'], 0)} ist ein signifikantes Ergebnis "
            f"im Mittel das **{C.fmt_num(here['exaggeration'])}-Fache** der wahren Wirkung. Bei 80 % Teststärke ist die "
            "Überschätzung klein; darunter wächst sie schnell."
        )
    else:
        st.info("Bei diesem Umfang meldet der Test praktisch nie etwas als signifikant; es gibt nichts zu überschätzen.")
else:
    st.info("Bei z = 1,0 gibt es keine wahre Wirkung; jedes signifikante Ergebnis ist ein Fehlalarm und damit unendlich "
            "zu groß. Wählen Sie einen Sicherheitsfaktor über 1,0.")

# --- Planung aus einem Pilot ------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🧭 Den Umfang aus einem kleinen Pilot planen")
st.markdown(
    f"Vor der Hauptstudie macht man einen Pilot mit {m} Fenstern je Arm und setzt dessen Wirkung und Streuung in die "
    "Normalformel ein. Das ist die übliche Praxis, und sie hat ihre Tücken."
)
with st.spinner("Pilot simulieren …"):
    pilot = _pilot(z, n, m, sites, seed)
pw = pilot["welch"]
planned_power = float(achieved_power(table, pilot["plan_n"]))
prow1, prow2 = st.columns(2), st.columns(2)
p1, p2, p3, p4 = prow1[0], prow1[1], prow2[0], prow2[1]
p1.metric("Wirkung im Pilot", C.fmt_pkt(pw["diff"]), delta="signifikant" if pilot["significant"] else "nicht signifikant",
          delta_color="off", delta_arrow="off", help=f"Die wahre Wirkung ist {C.fmt_pp(truth)}.")
p2.metric("Daraus geplant", f"{int(pilot['plan_n'])} Fenster",
          help="Je Arm. Normalformel mit der Wirkung und den Streuungen des Pilots; Obergrenze 1 000.")
p3.metric("Eigentlich nötig", str(n_need) if n_need is not None else "–", help="Fenster je Arm, Normalformel mit der wahren Wirkung.")
p4.metric("Teststärke Plan", C.fmt_pct(planned_power),
          help="Wie oft die so geplante Hauptstudie den echten Effekt findet (bei der wahren Wirkung).")
plans = _plans(z, m)
outcomes = plan_outcomes(plans, table)
left, right = st.columns(2)
with left:
    st.plotly_chart(build_plan_boxes(plans, n_need), width="stretch", key=f"planbox_{z}_{m}")
with right:
    st.plotly_chart(build_plan_power(outcomes), width="stretch", key=f"planpow_{z}_{m}")
plug = outcomes["plugin"]
if has_effect:
    st.info(
        f"**Plant man mit der Pilot-Wirkung, erreicht die Hauptstudie im Mittel {C.fmt_pct(plug['power_mean'], 0)} Teststärke, "
        f"nicht 80 %; {C.fmt_pct(plug['share_below_70'], 0)} der Studien liegen unter 70 %.** Der Pilot streut: der "
        f"geplante Umfang reicht von {int(plug['n_q10'])} bis {int(plug['n_q90'])} Fenstern je Arm (10 bis 90 %)."
    )
    sig = outcomes["signif"]
    if sig["share_planned"] > 0 and not np.isnan(sig["power_mean"]):
        st.warning(
            f"**Plant man erst, wenn der Pilot signifikant war, wird es schlechter:** nur {C.fmt_pct(sig['share_planned'], 0)} "
            f"der Piloten sind signifikant, und deren Wirkung ist zu groß geschätzt. Die geplante Hauptstudie erreicht im "
            f"Mittel {C.fmt_pct(sig['power_mean'], 0)} Teststärke."
        )
    rel, con = outcomes["relevanz"], outcomes["konserv"]
    st.success(
        f"Zwei Auswege: die **kleinste lohnende Wirkung** ({C.fmt_pp_plain(C.RELEVANCE_PP, 0)}) fest vorgeben und nur die "
        f"Streuung aus dem Pilot nehmen ({C.fmt_pct(rel['power_mean'], 0)} mittlere Teststärke, Umfang im Median "
        f"{int(rel['n_median'])}), oder die **untere Grenze** der Pilot-Wirkung einsetzen ({C.fmt_pct(con['power_mean'], 0)}, "
        f"aber im Median {int(con['n_median'])} Fenster je Arm). Beides kostet mehr Fenster, dafür stimmt die Teststärke."
    )
else:
    st.info("Bei z = 1,0 gibt es keine Wirkung: die Pilot-Wirkung ist reines Rauschen, und der geplante Umfang springt "
            "zwischen winzig und der Obergrenze. Genau das passiert in kleiner Form auch bei echten kleinen Effekten.")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Umfang steht vorher fest** | Wer zwischendurch hinsieht und früh stoppt, ändert Fehlalarmrate und Teststärke; der feste Umfang gilt dann nicht mehr. | Zwischenblicke und dauerndes Hinsehen |
| **Streuung und Wirkung sind aus dem Pilot schätzbar** | Ein kleiner Pilot streut stark (siehe oben); die Planung ist so unsicher wie der Pilot. | Varianzreduktion (kleinere Streuung, weniger Fenster) |
| **Ein Test, eine Kennzahl** | Mehrere Kennzahlen oder Varianten brauchen einen strengeren Schwellenwert und damit mehr Fenster. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Einheiten unabhängig und gleichartig** | Verhältniskennzahlen, Cluster und Serienkorrelation vergrößern die nötige Zahl der Fenster. | Verhältniskennzahlen und Cluster |
| **Die Zuteilung lief wie geplant** | Verlust von Fenstern verkleinert den Umfang und kann verzerren. | Gültigkeit der Zuteilung (A/A, Sample-Ratio-Mismatch) |
| **Die Verteilung ist harmlos** | Hier schief, aber harmlos; mit Ausreißern verliert der Test Teststärke. | Schiefe Daten und Ausreißer |
"""
)
st.caption(
    "Die Zahlen stammen aus dem erfundenen Vehikel dieses Stücks; die Aussagen gelten für unabhängige Fenster und einen "
    "Test je Experiment."
)

st.markdown("---")
with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Teststärke.** Für den Welch-Test von $\bar x_B - \bar x_A$ bei wahrer Wirkung $\Delta$ ist die Teststärke
$1-\beta = P(|t| > t_{1-\alpha/2,\nu})$ mit nichtzentraler Verteilung. Gemessen wird sie hier als Anteil signifikanter
Experimente aus den Pools (je 10 000 Fenster, SplitMix64).

**Normalformel.** Für zweiseitig $\alpha$ und Teststärke $1-\beta$:
$n = (z_{1-\alpha/2} + z_{1-\beta})^2 \,(\sigma_A^2 + \sigma_B^2)/\Delta^2$ Fenster je Arm. Umgekehrt findet der Test bei $n$
Fenstern eine Wirkung $\Delta_{\min} = (z_{1-\alpha/2} + z_{1-\beta})\sqrt{(\sigma_A^2 + \sigma_B^2)/n}$.

**Überschätzung (Typ M).** Unter den signifikanten Ergebnissen ist der Betrag der Schätzung im Mittel
$E[|\hat\Delta| \mid \text{signifikant}] / \Delta$ mal die wahre Wirkung; bei kleiner Teststärke wird fast nur signifikant,
was der Zufall nach oben getrieben hat.

**Planung aus einem Pilot.** Aus $m$ Fenstern je Arm: $\hat n = (z_{1-\alpha/2}+z_{1-\beta})^2(\hat\sigma_A^2 +
\hat\sigma_B^2)/\hat\Delta^2$ (begrenzt auf 1 000). Weil $\hat n$ mit $1/\hat\Delta^2$ geht, ist es bei kleinem $m$ extrem
verteilt. **Vorsichtig:** $\hat\Delta$ durch die untere 80-%-Grenze ersetzen. **Relevanz:** $\hat\Delta$ durch die kleinste
lohnende Wirkung ersetzen.

Implementiert in `pwr_evaluation.py` (Teststärke, nachweisbarer Effekt, Pilot-Planung), `pwr_stats.py` (Welch,
Normalformel), `pwr_vehicle.py` (Standort-Fenster), `generate_precomputed.py` (Pools, Teststärke-Tabellen).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html)."
)
