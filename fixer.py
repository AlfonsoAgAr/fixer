from logging import FileHandler, Formatter, StreamHandler, getLogger
from typing import List, AnyStr, Optional, Dict
from argparse import ArgumentParser
import time
import os
import re


class LintRule:
    def __init__(self, line: str):
        self.line = line
        self.errorLine: Optional[int] = None
        self.errorPosition: Optional[int] = None
        self.message: Optional[AnyStr] = None
        self.errorType: Optional[AnyStr] = None

        self.__set(self.line)

    def __set(self, line: str) -> None:
        parts = line.split()

        self.errorLine = int(parts[0].split(':')[0])
        self.errorPosition = int(parts[0].split(':')[1])
        self.message = ' '.join(parts[2:-1])
        self.errorType = parts[-1]

    def fix(self, *args, **kwargs) -> str:
        raise NotImplementedError


class CamelCaseRule(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        return old_code_line


class IndentRule(LintRule):
    def __init__(self, line: str):
        self.space: str = " "
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        raw_line: str = old_code_line.lstrip()

        expected_indentation: int = int(
            re.search(
                r"Expected indentation of (\d+) spaces",
                self.message
            ).group(1)
        )
        correct_identation: str = self.space * expected_indentation

        return correct_identation + raw_line


class KeySpacingRule(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        old_code_line = re.sub(r":(?=\S)|:(\s{2,})", r": ", old_code_line)

        pattern = r"(\s):"
        replacement = r":"        

        return re.sub(pattern, replacement, old_code_line)


class ArrayBracketSpacingRule(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        if "A space is required" in self.message:
            old_code_line = re.sub(r"\{\s*\[", "{ [", old_code_line)
            old_code_line = re.sub(r"\]\s*\}", "] }", old_code_line)
            old_code_line = re.sub(r"\[\s*", "[ ", old_code_line)
            old_code_line = re.sub(r"\s*\]", " ]", old_code_line)

            pattern_brackets = r"\[\s*((.|\s)*?)\s*\]"

            replacement_brackets = lambda m: "[ " + m.group(1).strip() + " ]"

            return re.sub(pattern_brackets, replacement_brackets, old_code_line)

        elif "There should be no space" in self.message:
            return old_code_line.replace('[ ', '[').replace(' ]', ']')


class CommaSpacing(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        if "after" in self.message:
            return old_code_line.replace(',', ', ')

        elif "before" in self.message:
            return old_code_line.replace(' ,', ',')


class SingleQuote(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        return old_code_line.replace('"', "'").replace("`", "'")


class SpaceInParents(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        return old_code_line.replace('( ', "(").replace(" )", ")")


class SemiColon(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        return old_code_line + (';')


class SpaceInfixOps(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        pattern = r"\s*([<>=]{1,})\s*"

        replacement = r" \1 "

        return re.sub(pattern, replacement, old_code_line)


class SemiSpacing(LintRule):
    def __init__(self, line: str):
        self.space = " "
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        pattern = r"[;](\S)"
        num_spaces = len(old_code_line) - len(old_code_line.lstrip())
        spaces = num_spaces * self.space
        replacement = f";\n{spaces}"
        replacement = replacement + r"\1"

        return re.sub(pattern, replacement, old_code_line)


class LinesAroundComment(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        if old_code_line.strip().startswith("//"):
            return "\n" + old_code_line

        return old_code_line


class ComplexityRuleComment(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:

        ignore_msg = "// eslint-disable-next-line complexity"

        new_code_line = ignore_msg + "\n" + old_code_line

        return new_code_line


class NotImplementeLintRule(LintRule):
    def __init__(self, line: str):
        super().__init__(line)

    def fix(self, old_code_line: str) -> str:
        return old_code_line


class RulerFactory:
    matcher = {
        "camelcase": CamelCaseRule,
        "key-spacing": KeySpacingRule,
        "indent": IndentRule,
        "array-bracket-spacing": ArrayBracketSpacingRule,
        "lines-around-comment": LinesAroundComment,
        "comma-spacing": CommaSpacing,
        "semi": SemiColon,
        "space-infix-ops": SpaceInfixOps,
        "quotes": SingleQuote,
        "complexity": ComplexityRuleComment,
        "semi-spacing": SemiSpacing,
        "space-in-parens": SpaceInParents
    }


    @staticmethod
    def generate_rule(line: str) -> LintRule:
        error_type = line.split()[-1]

        return RulerFactory.matcher.get(error_type, NotImplementeLintRule)(line)


class ColoredFormatter(Formatter):
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    levelInfo = 20
    levelWarning = 30
    levelError = 40
    
    FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    
    COLORS = {
        levelInfo: GREEN,
        levelError: RED,
        levelWarning: YELLOW,
    }

    def __init__(self, fmt=FORMAT):
        super().__init__(fmt)

    def format(self, record):
        original_format = self._style._fmt
        self._style._fmt = self.COLORS.get(record.levelno, self.RESET) + ColoredFormatter.FORMAT + self.RESET

        formatted_record = super().format(record)
        self._style._fmt = original_format
        return formatted_record


class FixerLogger:
    logger = getLogger("FixerLogger")
    formatLogger = Formatter("[%(asctime)s %(levelname)s %(name)s]: %(message)s")
    levelInfo = 20
    levelWarning = 30
    levelError = 40

    @classmethod
    def set_logger(cls):
        cls.logger.setLevel(cls.levelInfo)

        try:
            file_handler = FileHandler('lint-fixer.log')
            file_handler.setLevel(cls.levelInfo)
            file_handler.setFormatter(cls.formatLogger)
            cls.logger.addHandler(file_handler)
        except Exception as e:
            cls.logger.error(e)

        console_handler = StreamHandler()
        console_handler.setLevel(cls.levelInfo)
        console_handler.setFormatter(ColoredFormatter())
        cls.logger.addHandler(console_handler)

    @staticmethod
    def error(msg: str):
        FixerLogger.logger.error(msg)

    @staticmethod
    def info(msg: str):
        FixerLogger.logger.info(msg)

    @staticmethod
    def warning(msg: str):
        FixerLogger.logger.warning(msg)



class Fixer:
    def __init__(self, path: str) -> None:
        self.path: str = path
        self.readMode: str = "r"
        self.writeMode: str = "w"
        self.errorCode: int = -1

        try:
            if not os.path.isfile(self.path):
                raise FileNotFoundError(self.path)
        except FileNotFoundError as exc:
            FixerLogger.error(f"Archivo no encontrado: {exc}")
            FixerLogger.error(f"Abortando la ejecución del script {self.errorCode}")
            exit(self.errorCode)

    def __build_error_map(self) -> Dict[AnyStr, List[LintRule]]:

        errors_map: Dict[AnyStr, List[LintRule]] = {}
        current_file: Optional[str] = None
        exist: bool = False

        with open(self.path, self.readMode) as file:
            text: List[AnyStr] = file

            for line in text:

                line = line.rstrip()

                if os.path.isfile(line):
                    current_file = line
                    exist = True
                    errors_map[current_file] = []
                elif not os.path.isfile(line) and line.endswith(".js"):
                    exist = False
                elif exist and line:
                    rule = RulerFactory.generate_rule(line)
                    errors_map[current_file].append(rule)

        return errors_map
    
    def __fix_by_file(self, file_to_modify: str, rules_to_apply: List[LintRule]) -> None:

        FixerLogger.info(f"Se modifica el siguiente archivo: '{file_to_modify}'")

        with open(file_to_modify, self.readMode) as old_file:
            file_lines: List[str] = old_file.readlines()
        
        file_lines: List[str] = [line.rstrip() for line in file_lines]

        total_fixes: int = 0
        non_fixes: int = 0        

        for rule in rules_to_apply:
            old_code_line: str = file_lines[rule.errorLine - 1]
            new_code_line: str = rule.fix(old_code_line)
            file_lines[rule.errorLine - 1] = new_code_line
            
            if old_code_line != new_code_line:
                total_fixes += 1
            else:
                non_fixes += 1

        formatted_new_code: List[str] = [line + "\n" for line in file_lines]

        with open(file_to_modify, self.writeMode) as new_file:
            new_file.writelines(formatted_new_code)
        
        message =f"""
            \033[0m+---------------------------------------+                          
            |Total de correciones del archivo:\033[92m    {total_fixes}\033[0m|
            |Total de omisiones del archivo:\033[33m      {non_fixes}\033[0m|
            +---------------------------------------+"""
        
        FixerLogger.info(message)
        


    def fix(self) -> None:
        error_map: Dict[AnyStr, List[LintRule]] = self.__build_error_map()

        for file_to_modify, rules_to_apply in error_map.items():
            self.__fix_by_file(file_to_modify, rules_to_apply)

        return

FixerLogger.set_logger()

parser = ArgumentParser()

parser.add_argument("-f", "--file", dest="filename",
                    help="Ruta del archivo que contiene el log de los errores por el linteo", metavar="FILE")

args = parser.parse_args()

ascii_art_fixer = f"""
(_)(_)(_)(_)(_)         (_)(_)(_)         (_)_       _(_)      (_)(_)(_)(_)(_)      (_)(_)(_)(_) _    
(_)                        (_)              (_)_   _(_)        (_)                  (_)         (_)   
(_) _  _                   (_)                (_)_(_)          (_) _  _             (_) _  _  _ (_)   
(_)(_)(_)                  (_)                 _(_)_           (_)(_)(_)            (_)(_)(_)(_)      
(_)                        (_)               _(_) (_)_         (_)                  (_)   (_) _       
(_)                      _ (_) _           _(_)     (_)_       (_) _  _  _  _       (_)      (_) _    
(_)                     (_)(_)(_)         (_)         (_)      (_)(_)(_)(_)(_)      (_)         (_)   
"""

if args.filename:
    FixerLogger.info(ascii_art_fixer)

    start: float = time.time()

    ### Execution
    fixer = Fixer(args.filename)
    fixer.fix()

    ### Getting stats
    final: float = time.time() - start
    FixerLogger.info(f"Ejecución exitosa. Tiempo total: {final:.4f}s")

else:
    FixerLogger.error("No se proporcionó un archivo de log. Por favor, use la opción -f para especificar el archivo.")
