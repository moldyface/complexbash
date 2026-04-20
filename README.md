# complexbash
Complex Bash: Interactive Symbolic Geometry on the Unit Circle
===============================================================
A command-line tool for "bashing" Euclidean geometry problems using complex numbers,
based on Evan Chen's "Bashing Geometry with Complex Numbers".

Features:
- Define points with arbitrary algebraic expressions.
- Built-in functions for triangle centers, midpoints, feet, reflections, and arc midpoints.
- Assumes circumcircle is the unit circle (|z|=1), so conj(z) = 1/z.
- Symbolic verification of collinearity, perpendicularity, and concyclicity.

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