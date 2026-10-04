# deadfish.py

INPUT_FILE = "encoding"


def run_deadfish(code):
    acc = 0
    output = []

    for ch in code:
        if ch.isspace():
            continue

        if ch == "i":
            acc += 1

        elif ch == "d":
            acc -= 1

        elif ch == "s":
            acc *= acc

        elif ch == "o":
            output.append(acc)
            print(acc)

        else:
            print(f"Unknown instruction: {ch!r}")

        # Classic Deadfish reset rule
        if acc == -1 or acc == 256:
            acc = 0

    return output


with open(INPUT_FILE, "r") as f:
    code = f.read()

result = run_deadfish(code)

print("\nNumeric output:")
print(result)

print("\nASCII interpretation:")

text = "".join(
    chr(x) if 32 <= x <= 126 else f"<{x}>"
    for x in result
)

print(text)