from manim import *

class EquationExplanation(Scene):
    def construct(self):
        title = Text("Understanding Equations", font_size=36).to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        equation1 = MathTex("x + 2 = 5").set_color(BLUE).scale(1.5)
        equation1.next_to(title, DOWN, buff=1.5)
        self.play(Write(equation1))
        self.wait(1)

        explanation1 = Text("Find the value of x that makes the equation true.", font_size=24).next_to(equation1, DOWN, buff=0.75)
        self.play(Write(explanation1))
        self.wait(1)

        solution1_step1 = MathTex("x = 5 - 2").set_color(GREEN).scale(1.2)
        solution1_step1.next_to(explanation1, DOWN, buff=0.5)
        self.play(Write(solution1_step1))
        self.wait(1)

        solution1_step2 = MathTex("x = 3").set_color(YELLOW).scale(1.2)
        solution1_step2.next_to(solution1_step1, RIGHT, buff=1)
        self.play(Write(solution1_step2))
        self.wait(1)


        equation2 = MathTex("2y - 4 = 6").set_color(PURPLE).scale(1.5).to_edge(LEFT, buff=1)
        self.play(Write(equation2))
        self.wait(1)

        explanation2 = Text("Solve for y.", font_size=24).next_to(equation2, RIGHT, buff=0.75)
        self.play(Write(explanation2))
        self.wait(1)


        solution2_step1 = MathTex("2y = 6 + 4").set_color(ORANGE).scale(1.2).next_to(equation2, DOWN, buff=0.5)
        self.play(Write(solution2_step1))
        self.wait(1)

        solution2_step2 = MathTex("2y = 10").set_color(RED).scale(1.2).next_to(solution2_step1, RIGHT, buff=1)
        self.play(Write(solution2_step2))
        self.wait(1)

        solution2_step3 = MathTex("y = 5").set_color(PINK).scale(1.2).next_to(solution2_step2, RIGHT, buff=1)
        self.play(Write(solution2_step3))
        self.wait(2)

        self.play(*[FadeOut(mob) for mob in self.mobjects])