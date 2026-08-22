import os
import requests
from datetime import datetime, timedelta, timezone

from obspy import read
import matplotlib.pyplot as plt

STAZIONI = [
    # CAMPI FLEGREI
    {"station": "CSFT", "channel": "HHZ", "title": "Solfatara"},
    {"station": "CPIS", "channel": "HHZ", "title": "Pisciarelli"},
    {"station": "CBAG", "channel": "HHZ", "title": "Bagnoli"},
    {"station": "CNIS", "channel": "HHZ", "title": "Nisida"},
    {"station": "CFMN", "channel": "HHZ", "title": "Monte Nuovo"},

    # VESUVIO
    {"station": "OVO", "channel": "HHZ", "title": "Osservatorio Vesuviano"}
]

def scarica_waveform(station, channel):
    fine = datetime.now(timezone.utc)
    inizio = fine - timedelta(minutes=30)

    start = inizio.strftime("%Y-%m-%dT%H:%M:%S")
    end = fine.strftime("%Y-%m-%dT%H:%M:%S")

    url = (
        "https://webservices.ingv.it/fdsnws/dataselect/1/query"
        f"?net=IV"
        f"&sta={station}"
        f"&loc=--"
        f"&cha={channel}"
        f"&starttime={start}"
        f"&endtime={end}"
        f"&nodata=404"
    )

    nome_file = f"{station}_{channel}.mseed"

    risposta = requests.get(
        url,
        timeout=60
    )

    if risposta.status_code != 200 or not risposta.content:
        raise RuntimeError(
            f"Nessun dato per {station}.{channel} "
            f"(HTTP {risposta.status_code})"
        )

    with open(nome_file, "wb") as f:
        f.write(risposta.content)

    return nome_file


def genera_png(file_mseed, station, channel, title):
    stream = read(file_mseed)

    stream.merge(
        method=1,
        fill_value="interpolate"
    )

    trace = stream[0]
    trace.detrend("demean")

    nome_png = f"{station}_{channel}.png"

    fig = plt.figure(figsize=(14, 0.65))
    ax = fig.add_subplot(111)

    ax.plot(
        trace.times(),
        trace.data,
        linewidth=0.35
    )

    # Solo il tracciato: niente assi, titoli o bordi
    ax.set_axis_off()

    fig.subplots_adjust(
        left=0,
        right=1,
        top=1,
        bottom=0
    )

    fig.savefig(
        nome_png,
        dpi=120,
        bbox_inches="tight",
        pad_inches=0
    )

    plt.close(fig)

    return nome_png

def main():
    print("📡 AGGIORNAMENTO SISMOGRAFI REALI")

    for stazione in STAZIONI:
        station = stazione["station"]
        channel = stazione["channel"]
        title = stazione["title"]

        try:
            print(
                f"\n⬇️ Scarico IV.{station}..{channel}"
            )

            file_mseed = scarica_waveform(
                station,
                channel
            )

            file_png = genera_png(
                file_mseed,
                station,
                channel,
                title
            )

            print(
                f"✅ Creato {file_png}"
            )

        except Exception as errore:
            print(
                f"❌ {station}: {errore}"
            )

    print("\n✅ Aggiornamento terminato.")


if __name__ == "__main__":
    main()
