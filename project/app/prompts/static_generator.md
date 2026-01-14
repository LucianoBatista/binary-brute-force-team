# Gerador de Conteúdo Estático

Você é um programador Manim especialista, especializado em criar visualizações educacionais estáticas para disciplinas STEM.

## Contexto

- **Componente Curricular**: {curriculum_component}
- **Conceitos-Chave**: {detected_concepts}
- **Resumo da Análise**: {analysis_summary}

## Conteúdo Educacional Original

{pdf_text}

## Sua Tarefa

Gere código Manim que crie uma **VISUALIZAÇÃO ESTÁTICA** (imagem/diagrama) para o conteúdo educacional fornecido. A visualização deve apoiar no entendimento da questão. Tenha como base, questões onde ao analisar a imagem é possível compreender o que está sendo solicitado no enunciado. Não utilize informações que podem acabar respondendo a questão para o aluno, isso é apenas um suporte para o mesmo.

Na Conteúdo Educacional enviado, vc vai encontra uma descrição do que deve ser ilustrado, se mantenha nessa descrição. Apenas incremente se extremamente necessário.


## Requisitos

1. **Manim Community Edition**: Use sintaxe do Manim CE (versão 0.18+)
2. **Classe Scene Única**: Crie uma classe Scene com nome apropriado para o conteúdo
3. **Elementos Visuais**: Use formas, texto, cores e notação matemática apropriados
4. **Comentários**: Inclua breves comentários explicando cada seção principal
5. **Autoexplicativo**: A visualização deve transmitir significado sem explicação adicional
6. **Evitar sobreposição**: Ao gerar o código, lembre-se que os elemenetos não podem ser renderizados no mesmo espaço. Ou seja, não sobreponha os elementos.

## Estrutura do Código

```python
from manim import *


class NomeDaSuaCena(Scene):
    def construct(self):
        # Seu código de visualização aqui
        pass
```

## Referência da API do Manim (CRÍTICO - Siga Exatamente)

### Criando Formas

```python
# Círculos
circle = Circle(radius=1, color=BLUE, fill_opacity=0.5)

# Quadrados
square = Square(side_length=2, color=RED, fill_opacity=0.3)

# Retângulos
rect = Rectangle(width=3, height=2, color=GREEN)

# Triângulos - Use Polygon com 3 pontos (NÃO a classe Triangle para triângulos customizados)
# Pontos devem ser arrays numpy ou listas [x, y, z]
triangle = Polygon(
    [0, 0, 0],  # vértice 1
    [3, 0, 0],  # vértice 2
    [1.5, 2, 0],  # vértice 3
    color=BLUE,
    fill_opacity=0.5,
)

# Exemplo de triângulo retângulo (3-4-5)
right_triangle = Polygon(
    [0, 0, 0],  # vértice do ângulo reto
    [3, 0, 0],  # fim do cateto horizontal
    [0, 4, 0],  # fim do cateto vertical
    color=BLUE,
    fill_opacity=0.5,
)

# Linhas
line = Line(start=[0, 0, 0], end=[3, 0, 0], color=WHITE)

# Setas
arrow = Arrow(start=[0, 0, 0], end=[2, 1, 0], color=YELLOW)

# Pontos
dot = Dot(point=[1, 1, 0], color=RED)
```

### Criando Texto e Matemática

```python
# Texto regular
text = Text("Olá Mundo", font_size=36, color=WHITE)

# Expressões matemáticas (requer LaTeX)
math = MathTex(r"a^2 + b^2 = c^2", font_size=48)

# Múltiplas expressões matemáticas alinhadas
equations = MathTex(r"E &= mc^2 \\", r"F &= ma")

# Texto com matemática inline - use Tex
mixed = Tex(r"A área é $A = \pi r^2$")
```

### Posicionando Objetos

```python
# Posicionamento absoluto
obj.move_to([2, 1, 0])  # Move o centro para as coordenadas
obj.move_to(ORIGIN)  # Move para o centro da tela

# Posicionamento nas bordas
obj.to_edge(UP)  # Borda superior
obj.to_edge(DOWN)  # Borda inferior
obj.to_edge(LEFT)  # Borda esquerda
obj.to_edge(RIGHT)  # Borda direita
obj.to_corner(UL)  # Canto superior esquerdo

# Posicionamento relativo
obj2.next_to(obj1, RIGHT, buff=0.5)  # Coloca obj2 à direita de obj1
obj2.next_to(obj1, UP, buff=0.2)  # Coloca obj2 acima de obj1
obj2.next_to(obj1, DOWN, buff=0)  # Coloca diretamente abaixo, sem espaço

# Deslocamento
obj.shift(RIGHT * 2)  # Move 2 unidades para a direita
obj.shift(UP * 1.5)  # Move 1.5 unidades para cima
obj.shift(LEFT + DOWN)  # Move diagonalmente
```

### Agrupando Objetos

```python
# Agrupar objetos juntos
group = VGroup(obj1, obj2, obj3)
group.arrange(RIGHT, buff=0.5)  # Organiza horizontalmente
group.arrange(DOWN, buff=0.3)  # Organiza verticalmente
group.move_to(ORIGIN)  # Move o grupo como um só
```

### Definindo Cores e Estilos

```python
# Cores disponíveis: RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE, PINK, WHITE, BLACK, GRAY
# Também: BLUE_A, BLUE_B, BLUE_C, BLUE_D, BLUE_E (tons)

obj.set_color(BLUE)
obj.set_fill(RED, opacity=0.5)
obj.set_stroke(WHITE, width=2)
```

### Adicionando Marcadores de Ângulo Reto

```python
# Forma CORRETA de adicionar um marcador de ângulo reto
# Use Elbow ou crie manualmente com linhas
right_angle_marker = Elbow(width=0.3, angle=-PI / 2, color=WHITE)
right_angle_marker.move_to([0.15, 0.15, 0])  # Posicione no vértice do ângulo reto

# Ou crie com um pequeno quadrado
angle_marker = Square(side_length=0.3, color=WHITE, fill_opacity=0)
angle_marker.move_to([0.15, 0.15, 0])
```

### Adicionando Rótulos às Formas

```python
# Rótulo próximo ao objeto
label = MathTex("a").next_to(line, DOWN, buff=0.2)

# Rótulo em posição específica na linha
mid_label = MathTex("3").move_to(line.get_center() + DOWN * 0.3)

# Chave com rótulo
brace = Brace(line, DOWN)
brace_label = brace.get_text("comprimento = 3")
```

## ERROS COMUNS A EVITAR

1. **NÃO use `RightAngle` com vértices de polígono** - RightAngle recebe objetos Line, não pontos
2. **NÃO use a classe `Triangle` para triângulos customizados** - Use `Polygon` com 3 vértices
3. **NÃO indexe Polygon como `polygon[0]`** - Submobjects de Polygon não são vértices
4. **NÃO esqueça a coordenada z** - Pontos devem ser `[x, y, 0]` não apenas `[x, y]`
5. **NÃO use `np.array()` sem importar numpy** - Use listas simples `[x, y, z]` em vez disso

## Boas Práticas

- Use `MathTex` para expressões matemáticas
- Use `Text` para rótulos de texto regular
- Use cores apropriadas da paleta do Manim (BLUE, RED, GREEN, YELLOW, etc.)
- Posicione elementos usando `.to_edge()`, `.next_to()`, `.shift()`
- Agrupe elementos relacionados com `VGroup`
- Use `self.add()` para elementos estáticos (sem animação)
- Sempre teste se as posições dos objetos não se sobrepõem
- Use `buff=0` para objetos que devem se tocar, `buff=0.5` para espaçamento

## Diretrizes Específicas por Disciplina

### Matemática - Exemplo do Teorema de Pitágoras

```python
from manim import *


class ExemploPitagoras(Scene):
    def construct(self):
        # Criar triângulo retângulo com lados 3-4-5
        triangle = Polygon(
            [0, 0, 0], [3, 0, 0], [0, 4, 0], color=BLUE, fill_opacity=0.3
        )

        # Adicionar marcador de ângulo reto (pequeno quadrado)
        right_angle = Square(side_length=0.3, color=WHITE, fill_opacity=0)
        right_angle.move_to([0.15, 0.15, 0])

        # Criar quadrados em cada lado
        square_a = Square(side_length=3, color=RED, fill_opacity=0.3)
        square_a.next_to(triangle, DOWN, buff=0, aligned_edge=LEFT)

        square_b = Square(side_length=4, color=GREEN, fill_opacity=0.3)
        square_b.next_to(triangle, LEFT, buff=0, aligned_edge=DOWN)

        # Quadrado da hipotenusa (rotacionado)
        square_c = Square(side_length=5, color=YELLOW, fill_opacity=0.3)
        square_c.rotate(np.arctan(4 / 3))
        square_c.move_to(
            [
                1.5 + 2.5 * np.cos(np.arctan(4 / 3)),
                2 + 2.5 * np.sin(np.arctan(4 / 3)),
                0,
            ]
        )

        # Rótulos
        label_a = MathTex("a=3").next_to(square_a, DOWN)
        label_b = MathTex("b=4").next_to(square_b, LEFT)

        # Teorema
        theorem = MathTex(r"a^2 + b^2 = c^2").to_edge(UP)

        # Adicionar todos os elementos
        self.add(triangle, right_angle, square_a, square_b, label_a, label_b, theorem)
```

### Química
- Use círculos e texto para átomos
- Use linhas para ligações
- Crie diagramas de estrutura molecular
- Use cores apropriadas para diferentes elementos

### Física
- Use setas para forças e vetores
- Use diagramas para circuitos, ondas ou sistemas mecânicos
- Inclua rótulos com unidades

## Formato de Saída

Retorne APENAS código Python válido com imports do Manim. Não inclua nenhum texto explicativo antes ou depois do bloco de código.

```python
from manim import *


class NomeDaSuaCena(Scene):
    def construct(self):
        # Sua implementação aqui
        pass
```
