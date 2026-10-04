# custom_deadfish.py

INPUT_FILE = "encoding"

START_VALUE = 0

# Rules:
# d = decrement current cell
# i = increment current cell
# s = square current cell
# r = move pointer right
# y = move pointer left
# > = print current cell, then reset machine

ALLOW_NEGATIVE_POINTERS = True
MAX_STEPS = 10_000_000
MAX_ABS_VALUE = 10**1000

TRACE = False


class VM:
    def __init__(self, code):
        self.code = code
        self.cells = {0: START_VALUE}
        self.ptr = 0
        self.ip = 0
        self.steps = 0
        self.output = []

    def get(self):
        return self.cells.get(self.ptr, START_VALUE)

    def set(self, value):
        self.cells[self.ptr] = value

    def reset(self):
        self.cells = {0: START_VALUE}
        self.ptr = 0

    def move_right(self):
        self.ptr += 1

        if self.ptr not in self.cells:
            self.cells[self.ptr] = START_VALUE

    def move_left(self):
        if not ALLOW_NEGATIVE_POINTERS and self.ptr == 0:
            raise RuntimeError(
                "Pointer tried to move left of cell 0"
            )

        self.ptr -= 1

        if self.ptr not in self.cells:
            self.cells[self.ptr] = START_VALUE

    def emit_current(self):
        value = self.get()
        self.output.append(value)

        if 32 <= value <= 126:
            display = repr(chr(value))
        else:
            display = f"<{value}>"

        print(
            f"[OUT] ip={self.ip:6} "
            f"ptr={self.ptr:4} "
            f"value={value!r} "
            f"ascii={display}"
        )

    def trace(self, op, before, after):
        if TRACE:
            print(
                f"ip={self.ip:6} "
                f"op={op!r:3} "
                f"ptr={self.ptr:4} "
                f"before={before!r} "
                f"after={after!r}"
            )

    def run(self):
        while self.ip < len(self.code):

            self.steps += 1

            if self.steps > MAX_STEPS:
                print("\n[!] Step limit reached")
                break

            op = self.code[self.ip]

            if op.isspace():
                self.ip += 1
                continue

            before = self.get()

            # d = decrement
            if op == "d":
                self.set(
                    self.get() - 1
                )

            # i = increment
            elif op == "i":
                self.set(
                    self.get() + 1
                )

            # s = square
            elif op == "s":
                value = self.get()

                if abs(value) > MAX_ABS_VALUE:
                    print(
                        f"\n[!] Refusing huge square "
                        f"at ip={self.ip}"
                    )
                    break

                self.set(
                    value * value
                )

            # r = move pointer right
            elif op == "r":
                self.move_right()

            # y = move pointer left
            elif op == "y":
                self.move_left()

            # > = output current cell, then reset
            elif op == ">":
                self.emit_current()
                self.reset()

            else:
                print(
                    f"\n[?] Unknown symbol "
                    f"{op!r} at position {self.ip}"
                )

            after = self.get()

            self.trace(
                op,
                before,
                after
            )

            self.ip += 1

        print("\nNumeric output:")
        print(self.output)

        print("\nASCII output:")

        text = ""

        for value in self.output:
            if 32 <= value <= 126:
                text += chr(value)
            elif value == 10:
                text += "\n"
            elif value == 13:
                text += "\r"
            elif value == 9:
                text += "\t"
            else:
                text += f"<{value}>"

        print(text)


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:
        code = f.read()

    symbols = sorted(
        set(
            c for c in code
            if not c.isspace()
        )
    )

    print(
        f"Loaded {len(code)} characters "
        f"from {INPUT_FILE!r}"
    )

    print("Symbols present:")
    print(
        " ".join(
            repr(x)
            for x in symbols
        )
    )

    print()

    vm = VM(code)
    vm.run()


if __name__ == "__main__":
    main()