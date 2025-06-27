from manim import *

class ResolverEcuacion(Scene):
    def construct(self):
        title = Text("Resolviendo la Ecuación: 2x + 3 = 7", color=YELLOW).scale(1.2).to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        equation = MathTex("2x + 3 = 7").next_to(title, DOWN, buff=1.5)
        self.play(Write(equation))
        self.wait(1)

        step1 = MathTex("\\text{Resta 3 a ambos lados:}").next_to(equation, DOWN, buff=0.7)
        self.play(Write(step1))
        self.wait(0.5)

        equation_step1 = MathTex("2x + 3 - 3 = 7 - 3").next_to(step1, DOWN, buff=0.5)
        self.play(Write(equation_step1))
        self.wait(1)

        equation_step1_simplified = MathTex("2x = 4").next_to(equation_step1, DOWN, buff=0.5)
        self.play(TransformMatchingTex(equation_step1, equation_step1_simplified))
        self.wait(1)

        step2 = MathTex("\\text{Divide ambos lados entre 2:}").next_to(equation_step1_simplified, DOWN, buff=0.7)
        self.play(Write(step2))
        self.wait(0.5)

        equation_step2 = MathTex("\\frac{2x}{2} = \\frac{4}{2}").next_to(step2, DOWN, buff=0.5)
        self.play(Write(equation_step2))
        self.wait(1)

        equation_solution = MathTex("x = 2").next_to(equation_step2, DOWN, buff=0.5).set_color(GREEN)
        self.play(TransformMatchingTex(equation_step2, equation_solution))
        self.wait(1)

        solution_text = Text("¡Solución! x = 2", color=PURPLE).next_to(equation_solution, DOWN, buff=0.7)
        self.play(Write(solution_text))
        self.wait(2)


        self.play(*[FadeOut(mob) for mob in self.mobjects])