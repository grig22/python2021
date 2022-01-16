#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://gist.github.com/zkid18/013aab9d796561a3997fbec77ae6990a

from functools import update_wrapper
from functools import wraps


def disable(func):
    """
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:
    # >>> memo = disable
    """
    def wrapper(*args):
        return func(*args)
    return wrapper


def decorator(deco):
    """
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    """
    # https://stackoverflow.com/questions/308999/what-does-functools-wraps-do
    # https://docs.python.org/3/library/functools.html#functools.wraps
    # @wraps(deco)
    def deco_wrapper(*args):
        func = args[0]
        print('DECO =', deco.__name__, 'FUNC =', func.__name__, 'ARGS =', args)
        decorated = deco(*args)
        print("RATED =", decorated)
        update_wrapper(decorated, func)
        return decorated
    return deco_wrapper


@decorator
def countcalls(func):
    """Decorator that counts calls made to the function decorated."""
    def count_wrapper(*args):
        count_wrapper.calls += 1
        print('! count_wrapper.calls =', count_wrapper.calls)
        res = func(*args)
        return res
    # https://stackoverflow.com/questions/17043524/adding-new-member-variables-to-python-objects
    # https://docs.python.org/2/tutorial/classes.html#odds-and-ends
    count_wrapper.calls = 0
    return count_wrapper


@decorator
def memo(func):
    """
    Memoize a function so that it caches all return values for
    faster future lookups.
    """
    cache = {}

    def memorize_function(*args):
        print('! memorize_function, cache =', cache)
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result
        return result
    return memorize_function


@decorator
def n_ary(func):
    """
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    """
    def n_ary_f(x, *args):
        return x if not args else func(x, n_ary_f(*args))

    return n_ary_f


def trace(indent=' '*4):
    """Trace calls made to function decorated.
    @trace("____")
    def fib(n):
        ....
    # >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3
    """
    def trace_func(func):
        @wraps(func)
        def wrapper(*args):
            print(indent * wrapper.depth, '--> {0}({1})'.format(func.__name__, *args))
            wrapper.depth += 1
            result = func(*args)
            wrapper.depth -= 1
            print(indent * wrapper.depth, "<-- {0}({1}) == {2}".format(func.__name__, *args, result))
            return result
        wrapper.depth = 0
        return wrapper
    return trace_func


# @countcalls
@memo
@countcalls
# @n_ary
def foo(a, b):
    """Foooo Doccc"""
    print('FOO', a, b)
    return a + b


# @countcalls
# @memo
# @n_ary
# def bar(a, b):
#     return a * b
#
#
# @countcalls
# @trace("####")
# @memo
# def fib(n):
#     """FIBBOONNACCIII"""
#     return 1 if n <= 1 else fib(n-1) + fib(n-2)


def main():
    print('----?', foo.__name__, foo.__doc__)
    print(foo(4, 3))
    # print(foo(4, 3, 2))
    print(foo(4, 3))
    print(foo(4, 5))
    print("foo was called", foo.calls, "times")

    # print(bar(4, 3))
    # print(bar(4, 3, 2))
    # print(bar(4, 3, 2, 1))
    # print("bar was called", bar.calls, "times")
    #
    # print(fib.__doc__)
    # fib(3)
    # print(fib.calls, 'calls made')


if __name__ == '__main__':
    main()
