import math

# ==========================================================
# Токены
# ==========================================================
class TokenType:
    END = "END"
    NUMBER = "NUMBER"
    PLUS = "+"
    MINUS = "-"
    MUL = "*"
    DIV = "/"
    POW = "^"
    LPAREN = "("
    RPAREN = ")"
    SIN = "SIN"
    COS = "COS"
    FUNCTION = "FUNCTION"  # pow
    COMMA = ","

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        if self.type == TokenType.NUMBER:
            return f"NUMBER({self.value})"
        return self.type

# ==========================================================
# Лексер (разбивает строку на токены)
# ==========================================================
def tokenize(s: str):
    tokens = []
    i = 0
    n = len(s)
    
    while i < n:
        c = s[i]
        
        if c.isspace():
            i += 1
            continue
            
        if c.isdigit() or c == '.':
            start = i
            dot = (c == '.')
            i += 1
            while i < n and (s[i].isdigit() or s[i] == '.'):
                if s[i] == '.':
                    if dot:
                        raise ValueError("Invalid number format: multiple dots")
                    dot = True
                i += 1
            val = float(s[start:i])
            tokens.append(Token(TokenType.NUMBER, val))
            continue
            
        if c.isalpha():
            start = i
            while i < n and s[i].isalpha():
                i += 1
            func_name = s[start:i].lower()
            if func_name == "sin":
                tokens.append(Token(TokenType.SIN))
            elif func_name == "cos":
                tokens.append(Token(TokenType.COS))
            elif func_name == "pow":
                tokens.append(Token(TokenType.FUNCTION))
            else:
                raise ValueError(f"Unknown function: {func_name}")
            continue
            
        if c in "+-*/()^,":
            if c == '+':
                tokens.append(Token(TokenType.PLUS))
            elif c == '-':
                tokens.append(Token(TokenType.MINUS))
            elif c == '*':
                tokens.append(Token(TokenType.MUL))
            elif c == '/':
                tokens.append(Token(TokenType.DIV))
            elif c == '^':
                tokens.append(Token(TokenType.POW))
            elif c == '(':
                tokens.append(Token(TokenType.LPAREN))
            elif c == ')':
                tokens.append(Token(TokenType.RPAREN))
            elif c == ',':
                tokens.append(Token(TokenType.COMMA))
            i += 1
            continue
            
        raise ValueError(f"Unexpected character: '{c}'")
    
    tokens.append(Token(TokenType.END))
    return tokens

# ==========================================================
# AST (абстрактное синтаксическое дерево)
# ==========================================================
class Expr:
    def eval(self):
        raise NotImplementedError

    def to_string(self):
        raise NotImplementedError

class NumberExpr(Expr):
    def __init__(self, value):
        self.value = value
    
    def eval(self):
        return self.value
    
    def to_string(self):
        return str(self.value)

class UnaryExpr(Expr):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand
    
    def eval(self):
        v = self.operand.eval()
        return +v if self.op == '+' else -v
    
    def to_string(self):
        return f"{self.op}({self.operand.to_string()})"

class BinaryExpr(Expr):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right
    
    def eval(self):
        a = self.left.eval()
        b = self.right.eval()
        if self.op == '+':
            return a + b
        elif self.op == '-':
            return a - b
        elif self.op == '*':
            return a * b
        elif self.op == '/':
            if b == 0:
                raise ZeroDivisionError("Division by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operator {self.op}")
    
    def to_string(self):
        return f"({self.left.to_string()} {self.op} {self.right.to_string()})"

class PowExpr(Expr):
    def __init__(self, base, exponent):
        self.base = base
        self.exponent = exponent
    
    def eval(self):
        return math.pow(self.base.eval(), self.exponent.eval())
    
    def to_string(self):
        return f"({self.base.to_string()} ^ {self.exponent.to_string()})"

class FunctionExpr(Expr):
    def __init__(self, name, args):
        self.name = name
        self.args = args  # список аргументов (1 или 2)
    
    def eval(self):
        if self.name == "sin":
            return math.sin(self.args[0].eval())
        elif self.name == "cos":
            return math.cos(self.args[0].eval())
        elif self.name == "pow":
            if len(self.args) != 2:
                raise ValueError("pow() requires two arguments")
            return math.pow(self.args[0].eval(), self.args[1].eval())
        else:
            raise ValueError(f"Unknown function {self.name}")
    
    def to_string(self):
        arg_str = ", ".join(a.to_string() for a in self.args)
        return f"{self.name}({arg_str})"

# ==========================================================
# Парсер
# ==========================================================
class Parser:
    def __init__(self, input_str):
        self.tokens = tokenize(input_str)
        self.idx = 0
    
    def peek(self):
        return self.tokens[self.idx]
    
    def consume(self):
        tok = self.tokens[self.idx]
        self.idx += 1
        return tok
    
    def accept(self, t):
        if self.peek().type == t:
            self.consume()
            return True
        return False
    
    def expect(self, t, msg="Unexpected token"):
        if self.peek().type != t:
            raise SyntaxError(msg)
        self.consume()
    
    def parse(self):
        expr = self.parse_expression()
        if self.peek().type != TokenType.END:
            raise SyntaxError("Unexpected input after expression")
        return expr
    
    # grammar
    # expression := term { ("+" | "-") term }
    # term       := factor { ("*" | "/") factor }
    # factor     := power { ("^") factor }
    # power      := ("+" | "-") power | function | primary
    # function   := sin(expr) | cos(expr) | pow(expr,expr)
    # primary    := number | "(" expression ")"
    
    def parse_expression(self):
        left = self.parse_term()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.consume().type
            right = self.parse_term()
            left = BinaryExpr(op, left, right)
        return left
    
    def parse_term(self):
        left = self.parse_factor()
        while self.peek().type in (TokenType.MUL, TokenType.DIV):
            op = self.consume().type
            right = self.parse_factor()
            left = BinaryExpr(op, left, right)
        return left
    
    def parse_factor(self):
        left = self.parse_power()
        if self.peek().type == TokenType.POW:
            self.consume()
            right = self.parse_factor()  # правоассоциативно
            left = PowExpr(left, right)
        return left
    
    def parse_power(self):
        if self.peek().type == TokenType.PLUS:
            self.consume()
            return UnaryExpr('+', self.parse_power())
        if self.peek().type == TokenType.MINUS:
            self.consume()
            return UnaryExpr('-', self.parse_power())
        
        # функция или скобка / число
        if self.peek().type in (TokenType.SIN, TokenType.COS, TokenType.FUNCTION):
            return self.parse_function()
        return self.parse_primary()
    
    def parse_function(self):
        func_token = self.consume()
        func_name = {
            TokenType.SIN: "sin",
            TokenType.COS: "cos", 
            TokenType.FUNCTION: "pow"
        }[func_token.type]
        
        self.expect(TokenType.LPAREN, "Expected '(' after function name")
        args = [self.parse_expression()]
        
        # функция pow имеет два аргумента
        if func_name == "pow":
            if self.accept(TokenType.COMMA):
                args.append(self.parse_expression())
            else:
                # допускаем pow(2 3) через пробел
                if self.peek().type != TokenType.RPAREN:
                    args.append(self.parse_expression())
        
        self.expect(TokenType.RPAREN, "Expected ')' after function arguments")
        return FunctionExpr(func_name, args)
    
    def parse_primary(self):
        if self.peek().type == TokenType.NUMBER:
            val = self.peek().value
            self.consume()
            return NumberExpr(val)
        
        if self.accept(TokenType.LPAREN):
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Expected ')'")
            return expr
        
        raise SyntaxError("Expected number or '('")

# ==========================================================
# Тестирование
# ==========================================================
if __name__ == "__main__":
    tests = [
        "2 + 3 * 4",
        "(2 + 3) * 4", 
        "-5 + 2",
        "-(2 + 3) * 4",
        "2 ^ 3",
        "2 ^ 3 ^ 2",  # правоассоциативно: 2^(3^2)
        "sin(3.14159)",
        "cos(0)",
        "pow(2, 3)",
        "pow(2 3)",   # без запятой
        "2 + sin(0.5) * cos(1)",
        "pow(2, 3) + 4 ^ 2",
        "sin(cos(0.5))",
        "pow(2, pow(2, 3))"
    ]
    
    for expr in tests:
        try:
            p = Parser(expr)
            ast = p.parse()
            print(f"Expr: {expr}")
            print(f"AST: {ast.to_string()}")
            print(f"Eval: {ast.eval():.6f}\n")
        except Exception as e:
            print(f"Ошибка при обработке '{expr}': {e}\n")