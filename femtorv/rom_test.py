f = open("rom.hex", "w")

print("0067 0000", file=f) # Jump to addr 0
for i in range(2, 2048, 2):
    print(f"{i:04x} {i+60001:04x}", file=f)
