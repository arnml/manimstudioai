from manim import *

class EcuacionSin(Scene):
    def construct(self):
        title = Tex("Una ecuación de:", color=YELLOW).scale(1.2).to_edge(UP)
        equation = MathTex(r"\sin(2\sin(xy))", color=BLUE).scale(1.5)
        equation.next_to(title, DOWN, buff=0.5)

        x_explanation = Tex("x: variable independiente", color=GREEN).scale(0.8)
        y_explanation = Tex("y: variable independiente", color=GREEN).scale(0.8)
        x_explanation.next_to(equation, DOWN, buff=1, aligned_edge=LEFT)
        y_explanation.next_to(x_explanation, RIGHT, buff=1)


        self.play(Write(title), run_time=1)
        self.wait(0.5)
        self.play(Write(equation), run_time=2)
        self.wait(0.5)
        self.play(FadeIn(x_explanation), FadeIn(y_explanation), run_time=1)
        self.wait(1)

        self.play(*[FadeOut(mob) for mob in self.mobjects])