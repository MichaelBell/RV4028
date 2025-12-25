f = open("rom.hex", "w")

for i in range(0, 2048, 2):
    print(f"{i:04x} {i+1:04x}", file=f)
