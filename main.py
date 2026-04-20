#!/usr/bin/env python3
"""
Complex Bash Interactive Engine
Based on Evan Chen's "Bashing Geometry with Complex Numbers"
Usage:
    point <name> = <expression>
    output <name>
    collinear <p1> <p2> <p3>
    perpendicular <p1> <p2> <q1> <q2>
    concyclic <p1> <p2> <p3> <p4>
    simplify <expression>
    list
    help
    quit

Built-in functions (use in expressions):
    orthocenter(A,B,C)    - orthocenter of triangle ABC
    centroid(A,B,C)       - centroid of triangle ABC
    ninepoint(A,B,C)      - nine-point center of triangle ABC
    circumcenter(A,B,C)   - always 0 (we place circumcircle at unit circle)
    incenter(A,B,C)       - incenter of triangle ABC
    midpoint(P,Q)         - midpoint of segment PQ
    foot(P,Q,R)           - foot from P to line QR
    reflection(P,Q,R)     - reflection of P across line QR
    arc_midpoint(P,Q)     - arc midpoint of P and Q on circumcircle
"""

import sympy as sp
from sympy import I, conjugate, sqrt, expand, factor, together
import re
import readline  # optional, for better input history

class ComplexBashREPL:
    def __init__(self):
        # User-defined points (dictionary name -> SymPy expression)
        self.points = {}
        # We'll also keep a set of symbols that are on the unit circle
        # (so conj(z) = 1/z applies to them)
        self.unit_circle_symbols = set()

    def add_unit_symbol(self, sym):
        """Mark a symbol as being on the unit circle."""
        self.unit_circle_symbols.add(sym)

    def is_unit_symbol(self, sym):
        return sym in self.unit_circle_symbols

    def conj(self, expr):
        """
        Compute complex conjugate assuming all unit_circle_symbols satisfy conj(z)=1/z.
        Also handles conj(expr) linearly.
        """
        expr = sp.sympify(expr)
        # First, replace conj(symbol) with 1/symbol for all known unit circle symbols
        for sym in self.unit_circle_symbols:
            expr = expr.subs(conjugate(sym), 1/sym)
        # Now expand any remaining conjugate of expressions
        # We'll recursively apply conjugate to the whole expression
        def apply_conj(e):
            if e.is_Add:
                return sum(apply_conj(arg) for arg in e.args)
            elif e.is_Mul:
                return sp.Mul(*[apply_conj(arg) for arg in e.args])
            elif e.is_Pow:
                base, exp = e.args
                return apply_conj(base)**exp
            elif isinstance(e, conjugate):
                return self.conj(e.args[0])
            elif e in self.unit_circle_symbols:
                return 1/e
            else:
                return conjugate(e)
        expr = apply_conj(expr)
        # Re-simplify any remaining conjugates
        for sym in self.unit_circle_symbols:
            expr = expr.subs(conjugate(sym), 1/sym)
        return expr

    def simplify(self, expr):
        """Simplify expression with unit circle and possible square root relations."""
        expr = sp.sympify(expr)
        # Apply conjugate reduction
        expr = self.conj(expr)
        # General simplification
        expr = sp.simplify(expr)
        return expr

    def parse_expression(self, expr_str):
        """
        Convert a string expression using defined points and built-in functions
        into a SymPy expression.
        """
        # First, protect built-in function names from being replaced by point names
        builtins = ['orthocenter', 'centroid', 'ninepoint', 'circumcenter', 'incenter',
                    'midpoint', 'foot', 'reflection', 'arc_midpoint']
        # Temporarily replace builtins with placeholders
        placeholders = {}
        for i, func in enumerate(builtins):
            ph = f"__BUILTIN_{i}__"
            placeholders[ph] = func
            expr_str = expr_str.replace(func, ph)

        # Replace point names with their expressions (longest first to avoid partial matches)
        sorted_names = sorted(self.points.keys(), key=len, reverse=True)
        for name in sorted_names:
            expr_str = re.sub(r'\b' + re.escape(name) + r'\b', '(' + str(self.points[name]) + ')', expr_str)

        # Restore built-in function names
        for ph, func in placeholders.items():
            expr_str = expr_str.replace(ph, func)

        # Now parse built-in functions

        # incenter(A,B,C)
        def replace_incenter(match):
            p1 = match.group(1)
            p2 = match.group(2)
            p3 = match.group(3)
            return f"__incenter__({p1},{p2},{p3})"
        expr_str = re.sub(r'incenter\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
                          replace_incenter, expr_str)

        # orthocenter(A,B,C)
        expr_str = re.sub(r'orthocenter\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
                          r'((\1) + (\2) + (\3))', expr_str)

        # centroid(A,B,C)
        expr_str = re.sub(r'centroid\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
                          r'((\1) + (\2) + (\3))/3', expr_str)

        # ninepoint(A,B,C)
        expr_str = re.sub(r'ninepoint\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
                          r'((\1) + (\2) + (\3))/2', expr_str)

        # circumcenter(A,B,C) = 0
        expr_str = re.sub(r'circumcenter\s*\([^)]*\)', r'0', expr_str)

        # midpoint(P,Q)
        expr_str = re.sub(r'midpoint\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
                          r'((\1) + (\2))/2', expr_str)

        # foot(P, Q, R) -> foot from P to line QR
        # Formula: (p + q + r - q*r/p)/2
        expr_str = re.sub(r'foot\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
                          r'((\1) + (\2) + (\3) - (\2)*(\3)/(\1))/2', expr_str)

        # reflection(P, Q, R) -> reflection of P across line QR
        # Formula: q + r - q*r * conj(p)
        expr_str = re.sub(r'reflection\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)',
                          r'((\2) + (\3) - (\2)*(\3)*conjugate(\1))', expr_str)

        # arc_midpoint(P,Q)
        expr_str = re.sub(r'arc_midpoint\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)',
                          r'sqrt((\1) * (\2))', expr_str)

        # Parse into SymPy
        expr = sp.sympify(expr_str)

        # Post-process: replace __incenter__(a,b,c) with actual incenter formula
        def incenter_sub(expr):
            if expr.func == sp.Function and str(expr.func) == '__incenter__':
                args = expr.args
                if len(args) == 3:
                    return self.compute_incenter(*args)
            return expr
        expr = expr.replace(lambda e: e.func == sp.Function and str(e.func) == '__incenter__',
                            lambda e: self.compute_incenter(*e.args))
        return expr

    def compute_incenter(self, A, B, C):
        """
        Compute incenter of triangle with vertices A, B, C on unit circle.
        Automatically detects whether A = a^2 (squared) or A = a (direct).
        """
        # Try to extract base symbols from A, B, C
        def get_base_symbol(expr):
            # If expr is a symbol, it's direct
            if isinstance(expr, sp.Symbol):
                return expr, False  # False = not squared
            # If expr is a power with exponent 2 and base is a symbol
            if isinstance(expr, sp.Pow) and expr.args[1] == 2 and isinstance(expr.args[0], sp.Symbol):
                return expr.args[0], True  # True = squared
            # Otherwise, we cannot determine; fallback to direct and hope user applied unit circle
            return None, None

        base_a, sq_a = get_base_symbol(A)
        base_b, sq_b = get_base_symbol(B)
        base_c, sq_c = get_base_symbol(C)

        # If all three are squared (like a^2,b^2,c^2), use I = -(ab+bc+ca)
        if base_a is not None and base_b is not None and base_c is not None:
            if sq_a and sq_b and sq_c:
                # Ensure the base symbols are marked as unit circle
                self.add_unit_symbol(base_a)
                self.add_unit_symbol(base_b)
                self.add_unit_symbol(base_c)
                return -(base_a*base_b + base_b*base_c + base_c*base_a)
            elif not sq_a and not sq_b and not sq_c:
                # Direct unit circle: need to introduce square roots x,y,z
                # We'll create new symbols x,y,z for the roots
                # But to keep things clean, we'll return an expression with x,y,z
                # and add relations a = x^2, etc.
                x = sp.Symbol('x', complex=True)
                y = sp.Symbol('y', complex=True)
                z = sp.Symbol('z', complex=True)
                self.add_unit_symbol(x)
                self.add_unit_symbol(y)
                self.add_unit_symbol(z)
                # Optionally, we could store the relations, but not needed for output
                return -(x*y + y*z + z*x)
        # Fallback: treat as direct and use x,y,z (or just return unevaluated)
        # We'll just use x,y,z for safety
        x = sp.Symbol('x', complex=True)
        y = sp.Symbol('y', complex=True)
        z = sp.Symbol('z', complex=True)
        self.add_unit_symbol(x)
        self.add_unit_symbol(y)
        self.add_unit_symbol(z)
        return -(x*y + y*z + z*x)

    def define_point(self, name, expr_str):
        expr = self.parse_expression(expr_str)
        # If the expression is a single symbol (like 'a' or 'x'), mark it as unit circle
        if isinstance(expr, sp.Symbol):
            self.add_unit_symbol(expr)
        # Also if it's a power like a^2, mark the base as unit circle
        if isinstance(expr, sp.Pow) and expr.args[1] == 2 and isinstance(expr.args[0], sp.Symbol):
            self.add_unit_symbol(expr.args[0])
        self.points[name] = expr
        return expr

    def output_point(self, name):
        if name not in self.points:
            print(f"Point '{name}' not defined.")
            return
        expr = self.simplify(self.points[name])
        print(f"{name} = {expr}")

    def check_collinear(self, p1, p2, p3):
        p1e = self.points.get(p1, self.parse_expression(p1))
        p2e = self.points.get(p2, self.parse_expression(p2))
        p3e = self.points.get(p3, self.parse_expression(p3))
        ratio = (p1e - p2e) / (p1e - p3e)
        diff = ratio - self.conj(ratio)
        simplified = self.simplify(diff)
        is_collinear = simplified == 0
        print(f"Collinear {p1}, {p2}, {p3}? {is_collinear}")
        if not is_collinear:
            print(f"  (Simplified expression: {simplified})")

    def check_perpendicular(self, p1, p2, q1, q2):
        p1e = self.points.get(p1, self.parse_expression(p1))
        p2e = self.points.get(p2, self.parse_expression(p2))
        q1e = self.points.get(q1, self.parse_expression(q1))
        q2e = self.points.get(q2, self.parse_expression(q2))
        ratio = (p2e - p1e) / (q2e - q1e)
        diff = ratio + self.conj(ratio)
        simplified = self.simplify(diff)
        is_perp = simplified == 0
        print(f"Perpendicular {p1}{p2} ⟂ {q1}{q2}? {is_perp}")
        if not is_perp:
            print(f"  (Simplified expression: {simplified})")

    def check_concyclic(self, p1, p2, p3, p4):
        p1e = self.points.get(p1, self.parse_expression(p1))
        p2e = self.points.get(p2, self.parse_expression(p2))
        p3e = self.points.get(p3, self.parse_expression(p3))
        p4e = self.points.get(p4, self.parse_expression(p4))
        cross1 = (p1e - p3e) / (p1e - p4e)
        cross2 = (p2e - p3e) / (p2e - p4e)
        ratio = cross1 / cross2
        diff = ratio - self.conj(ratio)
        simplified = self.simplify(diff)
        is_conc = simplified == 0
        print(f"Concyclic {p1}, {p2}, {p3}, {p4}? {is_conc}")
        if not is_conc:
            print(f"  (Simplified expression: {simplified})")

    def simplify_command(self, expr_str):
        expr = self.parse_expression(expr_str)
        simplified = self.simplify(expr)
        print(simplified)

    def list_points(self):
        print("Defined points:")
        for name, expr in self.points.items():
            print(f"  {name} = {expr}")

    def run(self):
        print("Complex Bash Interactive REPL")
        print("Type 'help' for commands, 'quit' to exit.")
        while True:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue
                if cmd == "quit" or cmd == "exit":
                    break
                elif cmd == "help":
                    print("""
Commands:
  point <name> = <expression>   Define a new point
  output <name>                 Show the symbolic expression for a point
  collinear <p1> <p2> <p3>      Check if three points are collinear
  perpendicular <p1> <p2> <q1> <q2>  Check if lines are perpendicular
  concyclic <p1> <p2> <p3> <p4> Check if four points are concyclic
  simplify <expression>         Simplify an expression
  list                          List all defined points
  help                          Show this help
  quit                          Exit

Built-in functions:
  orthocenter(A,B,C)   centroid(A,B,C)   ninepoint(A,B,C)
  circumcenter(A,B,C)  incenter(A,B,C)
  midpoint(P,Q)        foot(P,Q,R)        reflection(P,Q,R)
  arc_midpoint(P,Q)
""")
                elif cmd.startswith("point "):
                    parts = cmd[6:].split("=", 1)
                    if len(parts) != 2:
                        print("Usage: point <name> = <expression>")
                        continue
                    name = parts[0].strip()
                    expr_str = parts[1].strip()
                    try:
                        expr = self.define_point(name, expr_str)
                        print(f"Defined {name} = {expr}")
                    except Exception as e:
                        print(f"Error: {e}")
                elif cmd.startswith("output "):
                    name = cmd[7:].strip()
                    self.output_point(name)
                elif cmd.startswith("collinear "):
                    args = cmd[10:].split()
                    if len(args) != 3:
                        print("Usage: collinear <p1> <p2> <p3>")
                        continue
                    self.check_collinear(*args)
                elif cmd.startswith("perpendicular "):
                    args = cmd[13:].split()
                    if len(args) != 4:
                        print("Usage: perpendicular <p1> <p2> <q1> <q2>")
                        continue
                    self.check_perpendicular(*args)
                elif cmd.startswith("concyclic "):
                    args = cmd[10:].split()
                    if len(args) != 4:
                        print("Usage: concyclic <p1> <p2> <p3> <p4>")
                        continue
                    self.check_concyclic(*args)
                elif cmd.startswith("simplify "):
                    expr_str = cmd[9:].strip()
                    self.simplify_command(expr_str)
                elif cmd == "list":
                    self.list_points()
                else:
                    print("Unknown command. Type 'help'.")
            except KeyboardInterrupt:
                print("\nInterrupted. Type 'quit' to exit.")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    repl = ComplexBashREPL()
    repl.run()