# Python Coding Constitution - PEP 8 Style Guide

**Based on PEP 8 – Style Guide for Python Code**

**For AI Coding Agents:** See [copilot-instructions.md](copilot-instructions.md) for Python-specific workflows (FastAPI development, virtual environment setup, Lambda deployment). This constitution defines Python coding standards; copilot-instructions provides operational context for Python development in TrailLens.

This document establishes the coding standards for all Python code in the TrailLens project, based on the official Python Enhancement Proposal 8 (PEP 8).

## Core Philosophy

> "Code is read much more often than it is written." - Guido van Rossum

**Key Principles:**
- **Readability counts** - Code should be optimized for human comprehension
- **Consistency is critical** - Within a project, module, and function
- **Practicality beats purity** - Know when to be inconsistent

## Code Layout

### Indentation

**REQUIRED:** Use **4 spaces** per indentation level. Never mix tabs and spaces.

```python
# Correct: Aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# Correct: Hanging indent with extra level
def long_function_name(
        var_one, var_two, var_three,
        var_four):
    print(var_one)

# Wrong: Arguments on first line without vertical alignment
foo = long_function_name(var_one, var_two,
    var_three, var_four)
```

### Maximum Line Length

**REQUIRED:**
- **79 characters** maximum for code
- **72 characters** maximum for comments and docstrings

**ALLOWED:** Teams may increase to **99 characters** for code (not comments) if agreed upon.

### Line Breaking

**PREFERRED:** Break before binary operators (following mathematical tradition):

```python
# Correct: operators aligned with operands
income = (gross_wages
          + taxable_interest
          + (dividends - qualified_dividends)
          - ira_deduction
          - student_loan_interest)

# Wrong: operators far from operands
income = (gross_wages +
          taxable_interest +
          (dividends - qualified_dividends) -
          ira_deduction -
          student_loan_interest)
```

### Blank Lines

**REQUIRED:**
- **2 blank lines** around top-level functions and class definitions
- **1 blank line** around method definitions inside classes
- Use blank lines sparingly within functions to indicate logical sections

### Imports

**REQUIRED:** Imports must be:
- At the top of the file (after module docstring, before globals)
- On separate lines (except `from` imports)
- Grouped in order: standard library, third-party, local imports
- Separated by blank lines between groups

```python
# Correct
import os
import sys
from subprocess import Popen, PIPE

# Wrong
import sys, os
```

**Grouping Order:**
1. Standard library imports
2. Related third party imports
3. Local application/library specific imports

**PREFERRED:** Use absolute imports:
```python
import mypkg.sibling
from mypkg import sibling
from mypkg.sibling import example
```

**PROHIBITED:** Wildcard imports (`from module import *`)

### Source File Encoding

**REQUIRED:** UTF-8 encoding (Python 3 default). No encoding declarations needed.

## String Quotes

**REQUIRED:** Be consistent within a project. Use the opposite quote type to avoid backslashes.

**REQUIRED:** Triple-quoted strings must use double quotes (`"""`) to align with docstring conventions.

## Whitespace in Expressions

### Pet Peeves - AVOID

**NO whitespace:**
- Inside parentheses, brackets, or braces: `spam(ham[1], {eggs: 2})`
- Before commas, semicolons, or colons: `if x == 4: print(x, y); x, y = y, x`
- Before function call parentheses: `spam(1)` not `spam (1)`
- Before indexing brackets: `dct['key']` not `dct ['key']`

**Correct slice spacing:**
```python
# Correct
ham[1:9], ham[1:9:3], ham[:9:3], ham[1::3]
ham[lower:upper], ham[lower+offset : upper+offset]

# Wrong
ham[1: 9], ham[1 :9], ham[1:9 :3]
```

### Required Whitespace

**REQUIRED:** Single space on both sides of:
- Assignment operators: `=`, `+=`, `-=`, etc.
- Comparisons: `==`, `<`, `>`, `!=`, `<=`, `>=`, `in`, `not in`, `is`, `is not`
- Booleans: `and`, `or`, `not`

```python
# Correct
i = i + 1
submitted += 1
x = x*2 - 1
hypot2 = x*x + y*y
c = (a+b) * (a-b)

# Wrong
i=i+1
submitted +=1
x = x * 2 - 1
```

**Function annotations:**
```python
# Correct
def munge(input: AnyStr) -> PosInt: ...

# Wrong
def munge(input:AnyStr)->PosInt: ...
```

**Keyword arguments:**
```python
# Correct
def complex(real, imag=0.0):
    return magic(r=real, i=imag)

# With annotations and defaults
def munge(input: AnyStr, sep: AnyStr = None): ...

# Wrong
def complex(real, imag = 0.0):
    return magic(r = real, i = imag)
```

### Trailing Commas

**REQUIRED:** For single-element tuples:
```python
FILES = ('setup.cfg',)
```

**RECOMMENDED:** For version-controlled multi-line structures:
```python
FILES = [
    'setup.cfg',
    'tox.ini',
]
```

## Comments

### General Rules

**REQUIRED:**
- Comments must be complete sentences
- First word capitalized (unless it's an identifier)
- Comments contradicting code are worse than no comments
- Keep comments up-to-date with code changes
- Write in English for open-source projects

### Block Comments

**FORMAT:**
- Apply to code that follows
- Indented to same level as code
- Each line starts with `#` and single space
- Paragraphs separated by line with single `#`

### Inline Comments

**USE SPARINGLY** - Must be separated by at least 2 spaces from statement:

```python
x = x + 1  # Compensate for border
```

**PROHIBITED:** Obvious inline comments:
```python
x = x + 1  # Increment x  # DON'T DO THIS
```

### Documentation Strings (Docstrings)

**REQUIRED:** Write docstrings for all public modules, functions, classes, and methods.

**FORMAT:**
```python
"""Return a foobang.

Optional plotz says to frobnicate the bizbaz first.
"""

# One-liners keep closing quotes on same line
"""Return an ex-parrot."""
```

See PEP 257 for detailed docstring conventions.

## Naming Conventions

### General Styles

- `lowercase`
- `lower_case_with_underscores`
- `UPPERCASE`
- `UPPER_CASE_WITH_UNDERSCORES`
- `CapitalizedWords` (CapWords/CamelCase)
- `mixedCase` (differs by initial lowercase)

### Specific Conventions

| Type           | Convention                              | Example             |
| -------------- | --------------------------------------- | ------------------- |
| **Modules**    | `lowercase` or `lower_with_underscores` | `mymodule.py`       |
| **Packages**   | `lowercase` (no underscores preferred)  | `mypackage`         |
| **Classes**    | `CapWords`                              | `MyClass`           |
| **Exceptions** | `CapWords` + `Error` suffix             | `ValueError`        |
| **Functions**  | `lowercase_with_underscores`            | `my_function()`     |
| **Variables**  | `lowercase_with_underscores`            | `my_variable`       |
| **Constants**  | `UPPER_CASE_WITH_UNDERSCORES`           | `MAX_OVERFLOW`      |
| **Methods**    | `lowercase_with_underscores`            | `instance_method()` |

### Special Naming Patterns

**REQUIRED:**
- `self` for first argument to instance methods
- `cls` for first argument to class methods

**Underscore Conventions:**
- `_single_leading_underscore`: weak "internal use" indicator
- `single_trailing_underscore_`: avoid keyword conflicts
- `__double_leading_underscore`: name mangling for class attributes
- `__double_leading_and_trailing__`: "magic" objects (don't invent these)

### Names to Avoid

**PROHIBITED:** Never use single characters `l` (lowercase L), `O` (uppercase o), or `I` (uppercase i) as variable names - they're indistinguishable from 1 and 0 in some fonts.

## Programming Recommendations

### Comparisons

**REQUIRED:**
```python
# Correct: Singletons
if foo is not None:

# Wrong
if not foo is None:
```

**REQUIRED:** Use `isinstance()` for type checking:
```python
# Correct
if isinstance(obj, int):

# Wrong
if type(obj) is type(1):
```

### Sequences

**PREFERRED:** Use empty sequence truth value:
```python
# Correct
if not seq:
if seq:

# Wrong
if len(seq):
if not len(seq):
```

### Boolean Comparisons

**PROHIBITED:** Don't compare to `True` or `False`:
```python
# Correct
if greeting:

# Wrong
if greeting == True:
```

### Function Definitions

**REQUIRED:** Use `def` statements, not lambda assignments:
```python
# Correct
def f(x): return 2*x

# Wrong
f = lambda x: 2*x
```

### Exception Handling

**REQUIRED:**
- Derive exceptions from `Exception`, not `BaseException`
- Be specific in exception catching:
```python
# Correct
try:
    import platform_specific_module
except ImportError:
    platform_specific_module = None

# Wrong: bare except
try:
    import platform_specific_module
except:
    platform_specific_module = None
```

**REQUIRED:** Limit `try` clauses to minimum necessary code:
```python
# Correct
try:
    value = collection[key]
except KeyError:
    return key_not_found(key)
else:
    return handle_value(value)

# Wrong
try:
    return handle_value(collection[key])
except KeyError:
    return key_not_found(key)
```

### Context Managers

**REQUIRED:** Use `with` statements for resource management:
```python
# Correct
with conn.begin_transaction():
    do_stuff_in_transaction(conn)
```

### Return Statements

**REQUIRED:** Be consistent - all return statements should return an expression, or none should:
```python
# Correct
def foo(x):
    if x >= 0:
        return math.sqrt(x)
    else:
        return None

# Wrong
def foo(x):
    if x >= 0:
        return math.sqrt(x)
```

### String Methods

**PREFERRED:** Use string methods over string module:
```python
# Correct
if foo.startswith('bar'):

# Wrong
if foo[:3] == 'bar':
```

## Type Annotations

### Function Annotations

**REQUIRED:** Use PEP 484 syntax for type hints:

```python
def greeting(name: str) -> str:
    return f'Hello {name}'
```

**REQUIRED:** Proper spacing:
```python
# Correct
def munge(input: AnyStr): ...
def munge() -> PosInt: ...

# Wrong
def munge(input:AnyStr): ...
def munge()->PosInt: ...
```

### Variable Annotations

**REQUIRED:** Spacing for variable annotations:
```python
# Correct
code: int
class Point:
    coords: Tuple[int, int]
    label: str = '<unknown>'

# Wrong
code:int  # No space after colon
code : int  # Space before colon
result: int=0  # No spaces around equality
```

## Public vs Internal Interfaces

**REQUIRED:**
- Use `__all__` to explicitly declare public API
- Prefix internal interfaces with single underscore `_`
- Document public interfaces clearly
- Assume undocumented interfaces are internal

## Enforcement

### Automated Tools

**RECOMMENDED:**
- `black` - Code formatting
- `flake8` or `pylint` - Linting
- `mypy` - Type checking
- `isort` - Import sorting

### Code Review

All code must pass:
1. Automated linting (flake8/pylint)
2. Type checking (mypy) where applicable
3. Peer review for style adherence

## Exceptions

**ALLOWED:** Break these rules when:
1. Following the guideline would make code less readable
2. Being consistent with surrounding code that breaks the rule
3. Code predates the guideline
4. Maintaining compatibility with older Python versions

**ALWAYS PRIORITIZE:**
1. Function consistency > Module consistency > Project consistency > PEP 8
2. Readability > Rigid adherence to rules

## References

- **Original PEP 8:** https://peps.python.org/pep-0008/
- **PEP 257 (Docstrings):** https://peps.python.org/pep-0257/
- **PEP 484 (Type Hints):** https://peps.python.org/pep-0484/
- **PEP 526 (Variable Annotations):** https://peps.python.org/pep-0526/

---

**Document Status:** Active
**Last Updated:** November 22, 2025
**Applies To:** All Python code in TrailLens project (api-dynamo, scripts, infrastructure)
**Authority:** PEP 8 - Style Guide for Python Code (Public Domain)
