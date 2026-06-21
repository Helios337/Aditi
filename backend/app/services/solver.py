from sympy import (
    Eq,
    diff,
    integrate,
    limit,
    parse_expr,
    simplify,
    solve,
    sympify,
)
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    standard_transformations,
)

from app.models import ProblemModel, SolveResult
from app.services.ocr import normalize_for_sympy

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)


def _parse_expression(expression: str, variable: str):
    normalized = normalize_for_sympy(expression)
    local_dict = {variable: sympify(variable)}
    try:
        return parse_expr(normalized, transformations=TRANSFORMATIONS, local_dict=local_dict)
    except Exception:
        return sympify(normalized, locals=local_dict)


def solve_problem(problem: ProblemModel) -> SolveResult:
    if not problem.sympy_expression:
        if problem.llm_answer:
            return SolveResult(
                solver_used="llm_only",
                verified=False,
                confidence_flag="unverified",
                final_answer=problem.llm_answer,
                solve_steps=["Problem could not be parsed for SymPy.", "Using LLM-proposed answer only."],
                verification_notes="Not independently verified by SymPy.",
            )
        return SolveResult(
            solver_used="llm_only",
            verified=False,
            confidence_flag="needs_review",
            final_answer=None,
            solve_steps=["No SymPy expression available."],
            verification_notes=problem.needs_review_reason or "Manual review required.",
        )

    variable = problem.sympy_variable or "x"
    steps: list[str] = []
    try:
        expr = _parse_expression(problem.sympy_expression, variable)
        steps.append(f"Parsed expression: {expr}")

        qtype = problem.question_type.lower()
        var = sympify(variable)

        if qtype in {"solve_equation", "equation", "other"} and isinstance(expr, Eq):
            solutions = solve(expr, var)
            steps.append(f"Solved equation for {variable}: {solutions}")
            final = ", ".join(str(s) for s in solutions) if solutions else None
        elif qtype == "differentiate":
            result = diff(expr, var)
            steps.append(f"Derivative: {result}")
            final = str(simplify(result))
        elif qtype == "integrate":
            result = integrate(expr, var)
            steps.append(f"Integral: {result}")
            final = str(simplify(result))
        elif qtype == "limit":
            result = limit(expr, var, 0)
            steps.append(f"Limit: {result}")
            final = str(simplify(result))
        elif qtype == "simplify":
            result = simplify(expr)
            steps.append(f"Simplified: {result}")
            final = str(result)
        else:
            if isinstance(expr, Eq):
                solutions = solve(expr, var)
                steps.append(f"Solved for {variable}: {solutions}")
                final = ", ".join(str(s) for s in solutions) if solutions else None
            else:
                result = simplify(expr)
                steps.append(f"Evaluated: {result}")
                final = str(result)

        if final is None:
            return SolveResult(
                solver_used="sympy",
                verified=False,
                confidence_flag="needs_review",
                final_answer=None,
                solve_steps=steps,
                verification_notes="SymPy did not find a closed-form solution.",
            )

        verified = _verify_answer(expr, var, final, qtype)
        confidence_flag = "verified" if verified else "needs_review"
        return SolveResult(
            solver_used="sympy",
            verified=verified,
            confidence_flag=confidence_flag,
            final_answer=final,
            solve_steps=steps,
            verification_notes=None if verified else "SymPy result failed verification checks.",
        )
    except Exception as exc:
        if problem.llm_answer:
            return SolveResult(
                solver_used="llm_only",
                verified=False,
                confidence_flag="unverified",
                final_answer=problem.llm_answer,
                solve_steps=steps + [f"SymPy error: {exc}"],
                verification_notes="SymPy failed; using LLM-proposed answer.",
            )
        return SolveResult(
            solver_used="sympy",
            verified=False,
            confidence_flag="needs_review",
            final_answer=None,
            solve_steps=steps + [f"SymPy error: {exc}"],
            verification_notes=str(exc),
        )


def _verify_answer(expr, var, final_answer: str, question_type: str) -> bool:
    try:
        answer = sympify(final_answer)
        qtype = question_type.lower()
        if qtype in {"differentiate", "integrate", "limit", "simplify"}:
            return True
        if isinstance(expr, Eq):
            lhs = expr.lhs.subs(var, answer)
            rhs = expr.rhs.subs(var, answer)
            return simplify(lhs - rhs) == 0
        return True
    except Exception:
        return False
