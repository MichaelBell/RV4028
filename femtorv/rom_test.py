program = """
00000517
03850513
90000637
f0060613
00054583
00058863
00b60023
00150513
ff1ff06f
0007a537
12050513
fff50513
fc0508e3
ff9ff06f
6c6c6548
77202c6f
646c726f
000a0d21
"""

f = open("rom.hex", "w")

start = 0
for line in program.splitlines():
    if len(line) == 8:
        print(f"{line[4:8]} {line[0:4]}", file=f)
        start += 2

for i in range(start, 3072, 2):
    print(f"{i:04x} {i+60001:04x}", file=f)
