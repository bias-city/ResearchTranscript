# Spike: eingebettetes Python (PyO3) — Phase 0 von docs/appstore-plan.md

Entstanden am 17. September 2026 in einem Multi-Agenten-Lauf, hier gesichert,
weil der Plan darauf aufbaut. Ein eigenständiges Rust-Programm, KEIN Teil der
App: es startet die gebündelte CPython-3.13-Laufzeit aus
`frontend/src-tauri/resources/python-runtime` isoliert im eigenen Prozess
(`PyConfig_InitIsolatedConfig`, eigener `sys.path`, kein site-Import, kein
Schreiben von .pyc), importiert `researchtranscript`, `pydantic_core` und
`enrich_core`, lässt die Job-Threads aus `jobs.py` neben Rust laufen und
bricht einen Job ab. Gemessen wurde mit Hardened Runtime und ohne
Sonder-Entitlements: Start 4–22 ms, Import ~50 ms.

Bauen und laufen lassen (nach `node scripts/bundle-resources.mjs`, damit die
Laufzeit und das venv unter `frontend/src-tauri/resources` liegen):

    cd spike/pyo3
    PYO3_CONFIG_FILE=$PWD/pyo3-config.txt cargo run --release

`pyo3-config.txt` zeigt auf die gebündelte Laufzeit; `build.rs` setzt den
rpath so, wie er später im App-Bundle liegt. Die im Scratchpad benutzten
Probe-Konfigurationen und Audiodateien sind nicht mitgenommen.
