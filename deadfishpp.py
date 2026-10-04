#!/usr/bin/env python3

import sys
import re

class DeadfishPP:
    def __init__(self, code):
        self.code = code
        self.ip = 0
        self.ptr = 0
        self.mem = {0: 0}
        self.vars = {}

    # -------------------------
    # Memory
    # -------------------------

    def get(self):
        return self.mem.get(self.ptr, 0)

    def set(self, value):
        self.mem[self.ptr] = value

    def cell_range(self):
        if not self.mem:
            return [0]

        lo = min(self.mem)
        hi = max(self.mem)

        return range(lo, hi + 1)

    # -------------------------
    # Matching helpers
    # -------------------------

    def find_forward(self, start, op, cl):
        depth = 1

        for i in range(start + 1, len(self.code)):
            if self.code[i] == op:
                depth += 1
            elif self.code[i] == cl:
                depth -= 1
                if depth == 0:
                    return i

        raise SyntaxError(f"Unmatched {op!r} at {start}")

    def find_backward(self, start, op, cl):
        depth = 1

        for i in range(start - 1, -1, -1):
            if self.code[i] == cl:
                depth += 1
            elif self.code[i] == op:
                depth -= 1
                if depth == 0:
                    return i

        raise SyntaxError(f"Unmatched {cl!r} at {start}")

    # -------------------------
    # Parsing
    # -------------------------

    def parse_string(self, pos):
        assert self.code[pos] == '"'

        out = []
        i = pos + 1

        escapes = {
            "n": "\n",
            "t": "\t",
            "r": "\r",
            "b": "\b",
            "f": "\f",
            "v": "\v",
            "0": "\0",
            '"': '"',
            "\\": "\\",
            "?": "\ufffd",
            "o": "\ufffc",
        }

        while i < len(self.code):
            ch = self.code[i]

            if ch == '"':
                return "".join(out), i + 1

            if ch == "\\":
                i += 1

                if i >= len(self.code):
                    raise SyntaxError("Dangling escape")

                esc = self.code[i]

                if esc in escapes:
                    out.append(escapes[esc])
                    i += 1
                    continue

                # Try decimal or hexadecimal Unicode escape.
                m = re.match(r"[0-9a-fA-F]+", self.code[i:])
                if m:
                    token = m.group(0)
                    try:
                        out.append(chr(int(token, 16)))
                        i += len(token)
                        continue
                    except ValueError:
                        pass

                out.append(esc)
                i += 1
                continue

            out.append(ch)
            i += 1

        raise SyntaxError("Unterminated string")

    def parse_number(self, pos):
        m = re.match(r"-?\d+", self.code[pos:])

        if not m:
            return None, pos

        token = m.group(0)
        return int(token), pos + len(token)

    def parse_value(self, pos):
        while pos < len(self.code) and self.code[pos].isspace():
            pos += 1

        if pos >= len(self.code):
            raise SyntaxError("Expected value")

        if self.code[pos] == '"':
            return self.parse_string(pos)

        if self.code[pos] == "m":
            if pos + 1 >= len(self.code):
                raise SyntaxError("Expected variable after m")

            name = self.code[pos + 1]

            if name not in self.vars:
                raise NameError(f"Unknown variable {name!r}")

            return self.vars[name], pos + 2

        if self.code[pos] == "[":
            end = self.code.find("]", pos + 1)

            if end == -1:
                raise SyntaxError("Unclosed memory reference")

            addr = int(self.code[pos + 1:end])
            return self.mem.get(addr, 0), end + 1

        num, end = self.parse_number(pos)

        if num is not None:
            return num, end

        raise SyntaxError(
            f"Cannot parse value at position {pos}: "
            f"{self.code[pos:pos+20]!r}"
        )

    # -------------------------
    # Output
    # -------------------------

    def output_char(self, value):
        if isinstance(value, str):
            raise TypeError("Unicode output requires a number")

        if value < 0 or value > 0x10FFFF:
            raise ValueError(f"Unicode value out of range: {value}")

        print(chr(value), end="", flush=True)

    def output_all_chars(self):
        for addr in self.cell_range():
            value = self.mem.get(addr, 0)

            if isinstance(value, str):
                print(value, end="")
            else:
                self.output_char(value)

        sys.stdout.flush()

    def output_all_numbers(self):
        vals = []

        for addr in self.cell_range():
            vals.append(str(self.mem.get(addr, 0)))

        print(" ".join(vals))

    # -------------------------
    # Interpreter
    # -------------------------

    def run(self):
        while self.ip < len(self.code):
            ch = self.code[self.ip]

            if ch.isspace():
                self.ip += 1
                continue

            # Comments
            if ch == "{":
                end = self.code.find("}", self.ip + 1)

                if end == -1:
                    raise SyntaxError("Unclosed comment")

                self.ip = end + 1
                continue

            # String literal assignment:
            # "hello"~x;
            if ch == '"':
                value, pos = self.parse_string(self.ip)

                while pos < len(self.code) and self.code[pos].isspace():
                    pos += 1

                if pos < len(self.code) and self.code[pos] == "~":
                    pos += 1

                    if pos >= len(self.code):
                        raise SyntaxError("Missing variable name")

                    name = self.code[pos]
                    pos += 1

                    if pos >= len(self.code) or self.code[pos] != ";":
                        raise SyntaxError("Assignment must end with ;")

                    self.vars[name] = value
                    self.ip = pos + 1
                    continue

                raise SyntaxError(
                    "Bare string literal unsupported"
                )

            # Number literal assignment:
            # 123~x;
            if ch.isdigit() or (
                ch == "-"
                and self.ip + 1 < len(self.code)
                and self.code[self.ip + 1].isdigit()
            ):
                value, pos = self.parse_number(self.ip)

                while pos < len(self.code) and self.code[pos].isspace():
                    pos += 1

                if pos < len(self.code) and self.code[pos] == "~":
                    pos += 1
                    name = self.code[pos]
                    pos += 1

                    if pos >= len(self.code) or self.code[pos] != ";":
                        raise SyntaxError("Assignment must end with ;")

                    self.vars[name] = value
                    self.ip = pos + 1
                    continue

                self.set(value)
                self.ip = pos
                continue

            # Core Deadfish++ commands

            if ch == "i":
                self.set(self.get() + 1)

            elif ch == "d":
                self.set(self.get() - 1)

            elif ch == "s":
                value = self.get()

                if isinstance(value, str):
                    raise TypeError("Cannot square a string")

                self.set(value * value)

            elif ch == "0":
                self.set(0)

            elif ch == "o":
                value = self.get()

                if isinstance(value, str):
                    raise TypeError("o cannot output a string")

                print(value, end="", flush=True)

            elif ch == "c":
                self.output_char(self.get())

            elif ch == "S":
                print(str(self.get()), end="", flush=True)

            elif ch == "l":
                self.ptr -= 1

            elif ch == "r":
                self.ptr += 1

            elif ch == "n":
                self.output_all_numbers()

            elif ch == "p":
                self.output_all_chars()

            elif ch == "y":
                self.set(int(input()))

            elif ch == "u":
                self.set(input())

            # while-style loop
            elif ch == "(":
                value = self.get()

                if value == 0 or value == "":
                    self.ip = self.find_forward(
                        self.ip, "(", ")"
                    )

            elif ch == ")":
                value = self.get()

                if value != 0 and value != "":
                    self.ip = self.find_backward(
                        self.ip, "(", ")"
                    )

            # Infinite loop
            elif ch == "[":
                # If this looks like [123], treat it as a
                # memory read instead of a loop.
                end = self.code.find("]", self.ip + 1)

                if end != -1:
                    inner = self.code[self.ip + 1:end]

                    if re.fullmatch(r"-?\d+", inner):
                        self.set(
                            self.mem.get(int(inner), 0)
                        )
                        self.ip = end

                    else:
                        pass

            elif ch == "]":
                self.ip = self.find_backward(
                    self.ip, "[", "]"
                )

            # mvar = load variable into current cell
            elif ch == "m":
                if self.ip + 1 >= len(self.code):
                    raise SyntaxError("Missing variable after m")

                name = self.code[self.ip + 1]

                if name not in self.vars:
                    raise NameError(
                        f"Unknown variable {name!r}"
                    )

                self.set(self.vars[name])
                self.ip += 1

            # g(number) = jump to cell
            elif ch == "g":
                m = re.match(
                    r"g\((-?\d+)\)",
                    self.code[self.ip:]
                )

                if not m:
                    raise SyntaxError(
                        f"Invalid g() at {self.ip}"
                    )

                self.ptr = int(m.group(1))
                self.ip += len(m.group(0)) - 1

            # Push first character of string to right cell
            elif ch == "P":
                value = self.get()

                if not isinstance(value, str):
                    raise TypeError("P requires a string")

                if value:
                    first = value[0]
                    self.set(value[1:])
                    self.mem[self.ptr + 1] = first

            # Push last character of string to right cell
            elif ch == "E":
                value = self.get()

                if not isinstance(value, str):
                    raise TypeError("E requires a string")

                if value:
                    last = value[-1]
                    self.set(value[:-1])
                    self.mem[self.ptr + 1] = last

            # Function-definition delimiters.
            # Full function handling isn't implemented yet.
            elif ch in "<>":
                pass

            else:
                raise SyntaxError(
                    f"Unknown/unimplemented instruction "
                    f"{ch!r} at position {self.ip}"
                )

            self.ip += 1


def main():
    if len(sys.argv) != 2:
        print(
            f"Usage: {sys.argv[0]} program.dfp",
            file=sys.stderr
        )
        raise SystemExit(1)

    with open(
        sys.argv[1],
        "r",
        encoding="utf-8"
    ) as f:
        code = f.read()

    vm = DeadfishPP(code)

    try:
        vm.run()

    except Exception as exc:
        print(
            f"\nDeadfish++ error at ip={vm.ip}: {exc}",
            file=sys.stderr
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()