"""Bounded scalar solving with explicit convergence outcomes."""
from dataclasses import dataclass
import math


class ConvergenceError(ValueError):
    """The requested numerical tolerance was not reached."""


@dataclass(frozen=True)
class RootResult:
    root: float
    residual: float
    iterations: int
    bracket_width: float


def bisect(function, lower, upper, *, x_tolerance=1e-14, max_iterations=200):
    """Solve a continuous scalar function on a sign-changing bracket.

    Convergence uses absolute bracket width, not a function-specific residual scale.
    The caller is responsible for continuity and for selecting units/tolerance.
    """
    for value in (lower, upper, x_tolerance):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Root bounds and tolerance must be finite numbers')
    if lower > upper or x_tolerance <= 0:
        raise ValueError('Ordered bounds and positive x_tolerance required')
    if type(max_iterations) is not int or not 1 <= max_iterations <= 10000:
        raise ValueError('max_iterations must be an integer in [1, 10000]')
    def evaluate(x):
        value = function(x)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Root function returned a non-finite/non-numeric value')
        return value
    flo, fhi = evaluate(lower), evaluate(upper)
    if flo == 0:
        return RootResult(lower, flo, 0, 0.0)
    if fhi == 0:
        return RootResult(upper, fhi, 0, 0.0)
    if (flo > 0) == (fhi > 0):
        raise ValueError('Root requires a sign-changing bracket')
    for iteration in range(1, max_iterations + 1):
        middle = lower / 2 + upper / 2
        value = evaluate(middle)
        if value == 0 or upper - lower <= x_tolerance:
            return RootResult(middle, value, iteration, upper - lower)
        if middle == lower or middle == upper:
            raise ConvergenceError('Floating-point resolution prevents requested tolerance')
        if (value > 0) == (flo > 0):
            lower, flo = middle, value
        else:
            upper = middle
    raise ConvergenceError(f'Root solver exceeded {max_iterations} iterations')


@dataclass(frozen=True)
class LinearResult:
    solution: tuple
    relative_residual: float
    minimum_scaled_pivot: float


def solve_linear(matrix, rhs, *, pivot_tolerance=1e-12, residual_tolerance=1e-10):
    """Dense square solve using row scaling and partial-pivot Gaussian elimination.

    Small systems only (up to 256 unknowns). Rejects singular/numerically unresolved
    systems. Residual is checked against original rows; this is not a condition
    number estimate or a forward-error guarantee.
    """
    def finite(value):
        return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value)
    if not isinstance(matrix,(list,tuple)) or not isinstance(rhs,(list,tuple)):
        raise ValueError('Linear system requires matrix and RHS sequences')
    n=len(rhs)
    if not 1 <= n <= 256 or len(matrix)!=n:
        raise ValueError('Linear system must be square with 1 to 256 unknowns')
    if any(not isinstance(row,(list,tuple)) or len(row)!=n for row in matrix):
        raise ValueError('Linear matrix rows must match RHS length')
    if any(not finite(v) for row in matrix for v in row) or any(not finite(v) for v in rhs):
        raise ValueError('Linear coefficients must be finite numbers')
    if any(not finite(t) or not 0 < t < 1 for t in (pivot_tolerance,residual_tolerance)):
        raise ValueError('Linear tolerances must be between zero and one')
    scales=[max(abs(v) for v in row) for row in matrix]
    if any(scale==0 for scale in scales):
        raise ConvergenceError('Singular linear system: a row has no coefficients')
    a=[[v/scales[i] for v in row] for i,row in enumerate(matrix)]
    b=[v/scales[i] for i,v in enumerate(rhs)]
    minimum_pivot=math.inf
    for col in range(n):
        pivot=max(range(col,n),key=lambda row:abs(a[row][col]))
        magnitude=abs(a[pivot][col])
        if magnitude <= pivot_tolerance:
            raise ConvergenceError('Singular or numerically unresolved linear system')
        minimum_pivot=min(minimum_pivot,magnitude)
        a[col],a[pivot]=a[pivot],a[col]
        b[col],b[pivot]=b[pivot],b[col]
        for row in range(col+1,n):
            factor=a[row][col]/a[col][col]
            a[row][col]=0.0
            for j in range(col+1,n):
                a[row][j]-=factor*a[col][j]
            b[row]-=factor*b[col]
    x=[0.0]*n
    for i in range(n-1,-1,-1):
        x[i]=(b[i]-math.fsum(a[i][j]*x[j] for j in range(i+1,n)))/a[i][i]
    if any(not finite(v) for v in x):
        raise ConvergenceError('Non-finite linear solution')
    residuals=[]
    for row,target in zip(matrix,rhs):
        terms=[v*value for v,value in zip(row,x)]
        residual=abs(math.fsum(terms)-target)
        scale=math.fsum(abs(v) for v in terms)+abs(target)
        residuals.append(residual/scale if scale else 0.0)
    relative=max(residuals)
    if not math.isfinite(relative) or relative > residual_tolerance:
        raise ConvergenceError('Linear residual exceeds tolerance')
    return LinearResult(tuple(x),relative,minimum_pivot)


@dataclass(frozen=True)
class NonlinearResult:
    solution: tuple
    scaled_residual: float
    iterations: int
    backtracks: int


def solve_nonlinear(evaluate, initial, residual_scales, *, tolerance=1e-10,
                    max_iterations=100, max_backtracks=40, pivot_tolerance=1e-12):
    """Damped Newton with analytic Jacobian and fixed equation residual scales.

    evaluate(x) returns (residual vector, Jacobian). A decreasing scaled infinity
    norm is required for each accepted step. Overflow during a trial causes step
    reduction, not equation clipping. Nonconvergence is explicit.
    """
    def finite(value):
        return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value)
    if not isinstance(initial,(list,tuple)) or not 1 <= len(initial) <= 256:
        raise ValueError('Nonlinear initial state must have 1 to 256 entries')
    n=len(initial)
    if (not isinstance(residual_scales,(list,tuple)) or len(residual_scales)!=n
            or any(not finite(v) or v<=0 for v in residual_scales)):
        raise ValueError('Each nonlinear equation needs a positive finite residual scale')
    if any(not finite(v) for v in initial) or not finite(tolerance) or not 0<tolerance<1:
        raise ValueError('Finite initial values and tolerance in (0,1) required')
    for name,value,limit in [('max_iterations',max_iterations,1000),('max_backtracks',max_backtracks,100)]:
        if type(value) is not int or not 1<=value<=limit:
            raise ValueError(f'{name} must be an integer in [1,{limit}]')
    if not finite(pivot_tolerance) or not 0<pivot_tolerance<1:
        raise ValueError('pivot_tolerance must be in (0,1)')
    def checked(x):
        residual,jacobian=evaluate(tuple(x))
        if len(residual)!=n or len(jacobian)!=n or any(len(row)!=n for row in jacobian):
            raise ValueError('Residual/Jacobian shape mismatch')
        if any(not finite(v) for v in residual) or any(not finite(v) for row in jacobian for v in row):
            raise OverflowError('Non-finite nonlinear residual or Jacobian')
        norm=max(abs(v)/s for v,s in zip(residual,residual_scales))
        if not math.isfinite(norm):
            raise OverflowError('Non-finite scaled residual')
        return residual,jacobian,norm
    x=list(initial); backtracks=0
    try:
        residual,jacobian,norm=checked(x)
    except OverflowError as error:
        raise ConvergenceError('Initial nonlinear evaluation overflowed') from error
    for iteration in range(max_iterations+1):
        # Also reject an underdetermined initial root; do not label it unique.
        step=solve_linear(jacobian,[-v for v in residual],pivot_tolerance=pivot_tolerance).solution
        if norm<=tolerance:
            return NonlinearResult(tuple(x),norm,iteration,backtracks)
        if iteration==max_iterations:
            break
        accepted=False
        for reduction in range(max_backtracks+1):
            alpha=2.0**(-reduction)
            candidate=[v+alpha*dv for v,dv in zip(x,step)]
            try:
                new_residual,new_jacobian,new_norm=checked(candidate)
            except OverflowError:
                continue
            if new_norm<norm*(1-1e-4*alpha) or new_norm<=tolerance:
                x,residual,jacobian,norm=candidate,new_residual,new_jacobian,new_norm
                backtracks+=reduction; accepted=True
                break
        if not accepted:
            raise ConvergenceError('Nonlinear line search failed to reduce residual')
    raise ConvergenceError(f'Nonlinear solver exceeded {max_iterations} iterations')
