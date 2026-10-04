# brute_y.py

INPUT_FILE = "encoding"

START_VALUE = 0
MAX_ABS_VALUE = 10**100
MAX_STEPS = 5_000_000


Y_MODES = [
    "left",
    "reset_cell",
    "home",
    "double",
    "half",
    "negate",
    "copy_right",
    "copy_left",
    "swap_right",
    "swap_left",
    "noop",
]


class VM:
    def __init__(self, code, y_mode):
        self.code = code
        self.y_mode = y_mode

        self.cells = {0: START_VALUE}
        self.ptr = 0

        self.output = []
        self.steps = 0
        self.failed = False

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
        self.ptr -= 1

        if self.ptr not in self.cells:
            self.cells[self.ptr] = START_VALUE

    def do_y(self):

        if self.y_mode == "left":
            self.move_left()

        elif self.y_mode == "reset_cell":
            self.set(0)

        elif self.y_mode == "home":
            self.ptr = 0

        elif self.y_mode == "double":
            self.set(self.get() * 2)

        elif self.y_mode == "half":
            self.set(self.get() // 2)

        elif self.y_mode == "negate":
            self.set(-self.get())

        elif self.y_mode == "copy_right":
            self.cells[self.ptr + 1] = self.get()

        elif self.y_mode == "copy_left":
            self.cells[self.ptr - 1] = self.get()

        elif self.y_mode == "swap_right":
            a = self.get()
            b = self.cells.get(self.ptr + 1, START_VALUE)

            self.cells[self.ptr] = b
            self.cells[self.ptr + 1] = a

        elif self.y_mode == "swap_left":
            a = self.get()
            b = self.cells.get(self.ptr - 1, START_VALUE)

            self.cells[self.ptr] = b
            self.cells[self.ptr - 1] = a

        elif self.y_mode == "noop":
            pass

        else:
            raise RuntimeError(
                f"Unknown y mode: {self.y_mode}"
            )

    def run(self):

        for op in self.code:

            if op.isspace():
                continue

            self.steps += 1

            if self.steps > MAX_STEPS:
                self.failed = True
                break

            if op == "i":
                self.set(self.get() + 1)

            elif op == "d":
                self.set(self.get() - 1)

            elif op == "s":
                value = self.get()

                if abs(value) > MAX_ABS_VALUE:
                    self.failed = True
                    break

                self.set(value * value)

            elif op == "r":
                self.move_right()

            elif op == "y":
                self.do_y()

            elif op == ">":
                self.output.append(self.get())
                self.reset()

            else:
                # Ignore unknown characters for now
                pass

        return self.output


def render(values):
    text = ""

    for value in values:

        if 32 <= value <= 126:
            text += chr(value)

        elif value == 10:
            text += "\\n"

        elif value == 13:
            text += "\\r"

        elif value == 9:
            text += "\\t"

        else:
            text += "."

    return text


def score(values):
    if not values:
        return -999999

    points = 0

    for value in values:

        # printable ASCII
        if 32 <= value <= 126:
            points += 5

        # common flag characters
        if value in map(ord, "abcdefghijklmnopqrstuvwxyz"):
            points += 2

        if value in map(ord, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            points += 2

        if value in map(ord, "0123456789"):
            points += 1

        if value in map(ord, "{}_-"):
            points += 3

        # strongly penalize ridiculous output
        if value < -1000 or value > 10000:
            points -= 10

        elif value < 0 or value > 255:
            points -= 3

    text = render(values).lower()

    # CTF-ish bonus
    for marker in [
        "flag",
        "ctf",
        "tribe",
        "{",
        "}",
    ]:
        if marker in text:
            points += 20

    return points


def main():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as f:
        code = f.read()

    print(
        f"Loaded {len(code)} characters "
        f"from {INPUT_FILE!r}"
    )

    print()

    results = []

    for mode in Y_MODES:

        vm = VM(code, mode)

        try:
            values = vm.run()

            results.append(
                (
                    score(values),
                    mode,
                    values,
                    render(values),
                    vm.failed,
                )
            )

        except Exception as e:

            results.append(
                (
                    -999999,
                    mode,
                    [],
                    f"ERROR: {e}",
                    True,
                )
            )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    for rank, result in enumerate(results, 1):

        score_value, mode, values, text, failed = result

        print("=" * 70)
        print(
            f"#{rank}  y={mode}  "
            f"score={score_value}  "
            f"failed={failed}"
        )

        print()

        print("ASCII:")
        print(text)

        print()

        print("Numbers:")
        print(values)

        print()


if __name__ == "__main__":
    main()