program = open("bootload.hex", "r")

f = open("rom.hex", "w")

start = 0
for line in program.readlines():
    line = line.strip()
    if len(line) == 8:
        print(f"{line[4:8]} {line[0:4]}", file=f)
        start += 2

for i in range(start, 3072, 2):
    print(f"{i:04x} {i+60001:04x}", file=f)
