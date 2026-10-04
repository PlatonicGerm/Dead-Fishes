# brute_all.py

from itertools import product
import math

INPUT_FILE = "encoding"

TOP_RESULTS = 50

MAX_STEPS = 2_000_000
MAX_VALUE = 10**50
MAX_TAPE_WIDTH = 1000


# ============================================================
# POSSIBLE BEHAVIORS
# ============================================================

VALUE_OPS_D = [
    "dec",
    "inc",
    "double",
    "half",
    "negate",
    "zero",
    "noop",
]

VALUE_OPS_I = [
    "inc",
    "dec",
    "double",
    "half",
    "negate",
    "zero",
    "noop",
]

VALUE_OPS_S = [
    "square",
    "double",
    "half",
    "negate",
    "zero",
    "noop",
]

POINTER_OPS_R = [
    "right",
    "left",
    "home",
    "zero_cell",
    "noop",
]

POINTER_OPS_Y = [
    "left",
    "right",
    "home",
    "zero_cell",
    "noop",
]

GT_MODES = [
    "current_reset",
    "current_noreset",
    "tape_reset",
    "tape_noreset",
]

CELL_MODES = [
    "unbounded",
    "8bit",
    "16bit",
]


# ============================================================
# VM
# ============================================================

class VM:

    def __init__(
        self,
        code,
        d_mode,
        i_mode,
        s_mode,
        r_mode,
        y_mode,
        gt_mode,
        cell_mode,
    ):

        self.code = code

        self.d_mode = d_mode
        self.i_mode = i_mode
        self.s_mode = s_mode

        self.r_mode = r_mode
        self.y_mode = y_mode

        self.gt_mode = gt_mode
        self.cell_mode = cell_mode

        self.cells = {0: 0}
        self.ptr = 0

        self.output = []

        self.failed = False
        self.steps = 0


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    def normalize(self, value):

        if self.cell_mode == "8bit":
            return value & 0xff

        if self.cell_mode == "16bit":
            return value & 0xffff

        return value


    def get(self):

        return self.cells.get(
            self.ptr,
            0
        )


    def set(self, value):

        value = self.normalize(value)

        if (
            self.cell_mode == "unbounded"
            and abs(value) > MAX_VALUE
        ):
            self.failed = True
            return

        self.cells[self.ptr] = value


    def reset(self):

        self.cells = {0: 0}
        self.ptr = 0


    # --------------------------------------------------------
    # VALUE OPS
    # --------------------------------------------------------

    def value_op(self, mode):

        x = self.get()

        if mode == "inc":
            self.set(x + 1)

        elif mode == "dec":
            self.set(x - 1)

        elif mode == "double":
            self.set(x * 2)

        elif mode == "half":
            self.set(x // 2)

        elif mode == "negate":
            self.set(-x)

        elif mode == "square":

            if (
                self.cell_mode == "unbounded"
                and abs(x) > 10**20
            ):
                self.failed = True
                return

            self.set(x * x)

        elif mode == "zero":
            self.set(0)

        elif mode == "noop":
            pass


    # --------------------------------------------------------
    # POINTER OPS
    # --------------------------------------------------------

    def pointer_op(self, mode):

        if mode == "right":

            self.ptr += 1

        elif mode == "left":

            self.ptr -= 1

        elif mode == "home":

            self.ptr = 0

        elif mode == "zero_cell":

            self.set(0)

        elif mode == "noop":

            pass

        if abs(self.ptr) > MAX_TAPE_WIDTH:
            self.failed = True


    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    def emit_current(self):

        self.output.append(
            self.get()
        )


    def emit_tape(self):

        if not self.cells:
            return

        lo = min(self.cells)
        hi = max(self.cells)

        if hi - lo > MAX_TAPE_WIDTH:
            self.failed = True
            return

        for address in range(
            lo,
            hi + 1
        ):

            self.output.append(
                self.cells.get(
                    address,
                    0
                )
            )


    def do_gt(self):

        if self.gt_mode == "current_reset":

            self.emit_current()
            self.reset()

        elif self.gt_mode == "current_noreset":

            self.emit_current()

        elif self.gt_mode == "tape_reset":

            self.emit_tape()
            self.reset()

        elif self.gt_mode == "tape_noreset":

            self.emit_tape()


    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    def run(self):

        for op in self.code:

            if op.isspace():
                continue

            self.steps += 1

            if self.steps > MAX_STEPS:
                self.failed = True
                break

            if op == "d":

                self.value_op(
                    self.d_mode
                )

            elif op == "i":

                self.value_op(
                    self.i_mode
                )

            elif op == "s":

                self.value_op(
                    self.s_mode
                )

            elif op == "r":

                self.pointer_op(
                    self.r_mode
                )

            elif op == "y":

                self.pointer_op(
                    self.y_mode
                )

            elif op == ">":

                self.do_gt()

            else:

                # Unknown chars ignored
                continue

            if self.failed:
                break

        return self.output


# ============================================================
# DISPLAY / SCORING
# ============================================================

def render(values):

    out = ""

    for x in values:

        if 32 <= x <= 126:

            out += chr(x)

        elif x == 10:

            out += "\\n"

        elif x == 13:

            out += "\\r"

        elif x == 9:

            out += "\\t"

        else:

            out += "."

    return out


def score(values):

    if not values:
        return -999999

    result = 0

    printable = 0

    for x in values:

        if 32 <= x <= 126:

            printable += 1
            result += 6

        else:

            result -= 2

        if (
            ord("a") <= x <= ord("z")
            or ord("A") <= x <= ord("Z")
        ):
            result += 3

        if ord("0") <= x <= ord("9"):
            result += 2

        if x in map(
            ord,
            "{}_-!@#$%^&*()[]"
        ):
            result += 2


    # percentage printable bonus

    ratio = printable / len(values)

    result += int(
        ratio * 100
    )


    text = render(
        values
    ).lower()


    # common English / CTF patterns

    bonuses = {
        "tribe": 100,
        "ctf": 80,
        "flag": 80,
        "{": 30,
        "}": 30,
        "the": 20,
        "this": 20,
        "you": 15,
        "key": 20,
        "code": 20,
        "pass": 20,
    }


    for word, bonus in bonuses.items():

        if word in text:
            result += bonus


    return result


# ============================================================
# MAIN SEARCH
# ============================================================

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
            c
            for c in code
            if not c.isspace()
        )
    )


    print(
        f"Loaded {len(code)} characters"
    )

    print(
        "Symbols:",
        symbols
    )


    total = (
        len(VALUE_OPS_D)
        * len(VALUE_OPS_I)
        * len(VALUE_OPS_S)
        * len(POINTER_OPS_R)
        * len(POINTER_OPS_Y)
        * len(GT_MODES)
        * len(CELL_MODES)
    )


    print(
        f"Testing {total:,} combinations..."
    )

    print()


    best = []

    tested = 0


    combos = product(
        VALUE_OPS_D,
        VALUE_OPS_I,
        VALUE_OPS_S,
        POINTER_OPS_R,
        POINTER_OPS_Y,
        GT_MODES,
        CELL_MODES,
    )


    for (
        d_mode,
        i_mode,
        s_mode,
        r_mode,
        y_mode,
        gt_mode,
        cell_mode,
    ) in combos:


        vm = VM(
            code,
            d_mode,
            i_mode,
            s_mode,
            r_mode,
            y_mode,
            gt_mode,
            cell_mode,
        )


        values = vm.run()

        tested += 1


        if vm.failed:
            continue


        result_score = score(
            values
        )


        text = render(
            values
        )


        entry = (
            result_score,
            d_mode,
            i_mode,
            s_mode,
            r_mode,
            y_mode,
            gt_mode,
            cell_mode,
            values,
            text,
        )


        best.append(
            entry
        )


        # Keep list from growing forever

        if len(best) > 500:

            best.sort(
                key=lambda x: x[0],
                reverse=True
            )

            best = best[
                :TOP_RESULTS
            ]


    best.sort(
        key=lambda x: x[0],
        reverse=True
    )


    best = best[
        :TOP_RESULTS
    ]


    print()
    print(
        f"Completed {tested:,} combinations."
    )

    print()


    for rank, result in enumerate(
        best,
        1
    ):

        (
            result_score,
            d_mode,
            i_mode,
            s_mode,
            r_mode,
            y_mode,
            gt_mode,
            cell_mode,
            values,
            text,
        ) = result


        print(
            "=" * 80
        )

        print(
            f"#{rank} SCORE={result_score}"
        )

        print(
            f"d = {d_mode}"
        )

        print(
            f"i = {i_mode}"
        )

        print(
            f"s = {s_mode}"
        )

        print(
            f"r = {r_mode}"
        )

        print(
            f"y = {y_mode}"
        )

        print(
            f"> = {gt_mode}"
        )

        print(# brute_all.py

from itertools import product
import math

INPUT_FILE = "encoding"

TOP_RESULTS = 50

MAX_STEPS = 2_000_000
MAX_VALUE = 10**50
MAX_TAPE_WIDTH = 1000


# ============================================================
# POSSIBLE BEHAVIORS
# ============================================================

VALUE_OPS_D = [
    "dec",
    "inc",
    "double",
    "half",
    "negate",
    "zero",
    "noop",
]

VALUE_OPS_I = [
    "inc",
    "dec",
    "double",
    "half",
    "negate",
    "zero",
    "noop",
]

VALUE_OPS_S = [
    "square",
    "double",
    "half",
    "negate",
    "zero",
    "noop",
]

POINTER_OPS_R = [
    "right",
    "left",
    "home",
    "zero_cell",
    "noop",
]

POINTER_OPS_Y = [
    "left",
    "right",
    "home",
    "zero_cell",
    "noop",
]

GT_MODES = [
    "current_reset",
    "current_noreset",
    "tape_reset",
    "tape_noreset",
]

CELL_MODES = [
    "unbounded",
    "8bit",
    "16bit",
]


# ============================================================
# VM
# ============================================================

class VM:

    def __init__(
        self,
        code,
        d_mode,
        i_mode,
        s_mode,
        r_mode,
        y_mode,
        gt_mode,
        cell_mode,
    ):

        self.code = code

        self.d_mode = d_mode
        self.i_mode = i_mode
        self.s_mode = s_mode

        self.r_mode = r_mode
        self.y_mode = y_mode

        self.gt_mode = gt_mode
        self.cell_mode = cell_mode

        self.cells = {0: 0}
        self.ptr = 0

        self.output = []

        self.failed = False
        self.steps = 0


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    def normalize(self, value):

        if self.cell_mode == "8bit":
            return value & 0xff

        if self.cell_mode == "16bit":
            return value & 0xffff

        return value


    def get(self):

        return self.cells.get(
            self.ptr,
            0
        )


    def set(self, value):

        value = self.normalize(value)

        if (
            self.cell_mode == "unbounded"
            and abs(value) > MAX_VALUE
        ):
            self.failed = True
            return

        self.cells[self.ptr] = value


    def reset(self):

        self.cells = {0: 0}
        self.ptr = 0


    # --------------------------------------------------------
    # VALUE OPS
    # --------------------------------------------------------

    def value_op(self, mode):

        x = self.get()

        if mode == "inc":
            self.set(x + 1)

        elif mode == "dec":
            self.set(x - 1)

        elif mode == "double":
            self.set(x * 2)

        elif mode == "half":
            self.set(x // 2)

        elif mode == "negate":
            self.set(-x)

        elif mode == "square":

            if (
                self.cell_mode == "unbounded"
                and abs(x) > 10**20
            ):
                self.failed = True
                return

            self.set(x * x)

        elif mode == "zero":
            self.set(0)

        elif mode == "noop":
            pass


    # --------------------------------------------------------
    # POINTER OPS
    # --------------------------------------------------------

    def pointer_op(self, mode):

        if mode == "right":

            self.ptr += 1

        elif mode == "left":

            self.ptr -= 1

        elif mode == "home":

            self.ptr = 0

        elif mode == "zero_cell":

            self.set(0)

        elif mode == "noop":

            pass

        if abs(self.ptr) > MAX_TAPE_WIDTH:
            self.failed = True


    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    def emit_current(self):

        self.output.append(
            self.get()
        )


    def emit_tape(self):

        if not self.cells:
            return

        lo = min(self.cells)
        hi = max(self.cells)

        if hi - lo > MAX_TAPE_WIDTH:
            self.failed = True
            return

        for address in range(
            lo,
            hi + 1
        ):

            self.output.append(
                self.cells.get(
                    address,
                    0
                )
            )


    def do_gt(self):

        if self.gt_mode == "current_reset":

            self.emit_current()
            self.reset()

        elif self.gt_mode == "current_noreset":

            self.emit_current()

        elif self.gt_mode == "tape_reset":

            self.emit_tape()
            self.reset()

        elif self.gt_mode == "tape_noreset":

            self.emit_tape()


    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    def run(self):

        for op in self.code:

            if op.isspace():
                continue

            self.steps += 1

            if self.steps > MAX_STEPS:
                self.failed = True
                break

            if op == "d":

                self.value_op(
                    self.d_mode
                )

            elif op == "i":

                self.value_op(
                    self.i_mode
                )

            elif op == "s":

                self.value_op(
                    self.s_mode
                )

            elif op == "r":

                self.pointer_op(
                    self.r_mode
                )

            elif op == "y":

                self.pointer_op(
                    self.y_mode
                )

            elif op == ">":

                self.do_gt()

            else:

                # Unknown chars ignored
                continue

            if self.failed:
                break

        return self.output


# ============================================================
# DISPLAY / SCORING
# ============================================================

def render(values):

    out = ""

    for x in values:

        if 32 <= x <= 126:

            out += chr(x)

        elif x == 10:

            out += "\\n"

        elif x == 13:

            out += "\\r"

        elif x == 9:

            out += "\\t"

        else:

            out += "."

    return out


def score(values):

    if not values:
        return -999999

    result = 0

    printable = 0

    for x in values:

        if 32 <= x <= 126:

            printable += 1
            result += 6

        else:

            result -= 2

        if (
            ord("a") <= x <= ord("z")
            or ord("A") <= x <= ord("Z")
        ):
            result += 3

        if ord("0") <= x <= ord("9"):
            result += 2

        if x in map(
            ord,
            "{}_-!@#$%^&*()[]"
        ):
            result += 2


    # percentage printable bonus

    ratio = printable / len(values)

    result += int(
        ratio * 100
    )


    text = render(
        values
    ).lower()


    # common English / CTF patterns

    bonuses = {
        "tribe": 100,
        "ctf": 80,
        "flag": 80,
        "{": 30,
        "}": 30,
        "the": 20,
        "this": 20,
        "you": 15,
        "key": 20,
        "code": 20,
        "pass": 20,
    }


    for word, bonus in bonuses.items():

        if word in text:
            result += bonus


    return result


# ============================================================
# MAIN SEARCH
# ============================================================

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
            c
            for c in code
            if not c.isspace()
        )
    )


    print(
        f"Loaded {len(code)} characters"
    )

    print(
        "Symbols:",
        symbols
    )


    total = (
        len(VALUE_OPS_D)
        * len(VALUE_OPS_I)
        * len(VALUE_OPS_S)
        * len(POINTER_OPS_R)
        * len(POINTER_OPS_Y)
        * len(GT_MODES)
        * len(CELL_MODES)
    )


    print(
        f"Testing {total:,} combinations..."
    )

    print()


    best = []

    tested = 0


    combos = product(
        VALUE_OPS_D,
        VALUE_OPS_I,
        VALUE_OPS_S,
        POINTER_OPS_R,
        POINTER_OPS_Y,
        GT_MODES,
        CELL_MODES,
    )


    for (
        d_mode,
        i_mode,
        s_mode,
        r_mode,
        y_mode,
        gt_mode,
        cell_mode,
    ) in combos:


        vm = VM(
            code,
            d_mode,
            i_mode,
            s_mode,
            r_mode,
            y_mode,
            gt_mode,
            cell_mode,
        )


        values = vm.run()

        tested += 1


        if vm.failed:
            continue


        result_score = score(
            values
        )


        text = render(
            values
        )


        entry = (
            result_score,
            d_mode,
            i_mode,
            s_mode,
            r_mode,
            y_mode,
            gt_mode,
            cell_mode,
            values,
            text,
        )


        best.append(
            entry
        )


        # Keep list from growing forever

        if len(best) > 500:

            best.sort(
                key=lambda x: x[0],
                reverse=True
            )

            best = best[
                :TOP_RESULTS
            ]


    best.sort(
        key=lambda x: x[0],
        reverse=True
    )


    best = best[
        :TOP_RESULTS
    ]


    print()
    print(
        f"Completed {tested:,} combinations."
    )

    print()


    for rank, result in enumerate(
        best,
        1
    ):

        (
            result_score,
            d_mode,
            i_mode,
            s_mode,
            r_mode,
            y_mode,
            gt_mode,
            cell_mode,
            values,
            text,
        ) = result


        print(
            "=" * 80
        )

        print(
            f"#{rank} SCORE={result_score}"
        )

        print(
            f"d = {d_mode}"
        )

        print(
            f"i = {i_mode}"
        )

        print(
            f"s = {s_mode}"
        )

        print(
            f"r = {r_mode}"
        )

        print(
            f"y = {y_mode}"
        )

        print(
            f"> = {gt_mode}"
        )

        print(
            f"cells = {cell_mode}"
        )

        print()

        print(
            "ASCII:"
        )

        print(
            text
        )

        print()

        print(
            "NUMBERS:"
        )

        print(
            values[:200]
        )

        print()


if __name__ == "__main__":
    main()
            f"cells = {cell_mode}"
        )

        print()

        print(
            "ASCII:"
        )

        print(
            text
        )

        print()

        print(
            "NUMBERS:"
        )

        print(
            values[:200]
        )

        print()


if __name__ == "__main__":
    main()