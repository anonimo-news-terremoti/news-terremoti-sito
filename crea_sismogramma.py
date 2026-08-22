from obspy import read
import matplotlib.pyplot as plt

stream = read("appi_ehz.mseed")

trace = stream[0]

print(trace)

plt.figure(figsize=(12, 3))
plt.plot(trace.times(), trace.data, linewidth=0.6)

plt.title("IV.APPI..EHZ - Ultimi 30 minuti")
plt.xlabel("Secondi")
plt.ylabel("Ampiezza")

plt.tight_layout()
plt.savefig("appi_ehz.png", dpi=150)
plt.close()

print("✅ Creato appi_ehz.png")
