from manim import *

class QuadraticEquation(Scene):
    def construct(self):
        equation = MathTex("x^2 + 3x + 2 = 0")
        self.play(Write(equation))
        self.wait(1)

        # Factoring
        factoring_steps = [
            MathTex("x^2 + 2x + x + 2 = 0"),
            MathTex("x(x+2) + 1(x+2) = 0"),
            MathTex("(x+1)(x+2) = 0"),
        ]

        for step in factoring_steps:
            self.play(TransformMatchingTex(equation, step))
            self.wait(1)
            equation = step

        # Solutions
        solutions = MathTex("x + 1 = 0 \\quad \\text{or} \\quad x + 2 = 0")
        self.play(TransformMatchingTex(equation, solutions))
        self.wait(1)

        final_solutions = MathTex("x = -1 \\quad \\text{or} \\quad x = -2")
        self.play(TransformMatchingTex(solutions, final_solutions))
        self.wait(2)