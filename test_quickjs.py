import concurrent.futures
import json
import unittest

import quickjs


class LoadModule(unittest.TestCase):
    def test_42(self):
        self.assertEqual(quickjs.test(), 42)


class Context(unittest.TestCase):
    def setUp(self):
        self.context = quickjs.Context()

    def test_eval_int(self):
        self.assertEqual(self.context.eval("40 + 2"), 42)

    def test_eval_float(self):
        self.assertEqual(self.context.eval("40.0 + 2.0"), 42.0)

    def test_eval_str(self):
        self.assertEqual(self.context.eval("'4' + '2'"), "42")

    def test_eval_bool(self):
        self.assertEqual(self.context.eval("true || false"), True)
        self.assertEqual(self.context.eval("true && false"), False)

    def test_eval_null(self):
        self.assertIsNone(self.context.eval("null"))

    def test_eval_undefined(self):
        self.assertIsNone(self.context.eval("undefined"))

    def test_wrong_type(self):
        with self.assertRaises(TypeError):
            self.assertEqual(self.context.eval(1), 42)

    def test_context_between_calls(self):
        self.context.eval("x = 40; y = 2;")
        self.assertEqual(self.context.eval("x + y"), 42)

    def test_function(self):
        self.context.eval("""
            function special(x) {
                return 40 + x;
            }
            """)
        self.assertEqual(self.context.eval("special(2)"), 42)

    def test_get(self):
        self.context.eval("x = 42; y = 'foo';")
        self.assertEqual(self.context.get("x"), 42)
        self.assertEqual(self.context.get("y"), "foo")
        self.assertEqual(self.context.get("z"), None)

    def test_module(self):
        self.context.module("""   
            export function test() {
                return 42;
            }
        """)

    def test_error(self):
        with self.assertRaisesRegex(
            quickjs.JSException, "ReferenceError: missing is not defined"
        ):
            self.context.eval("missing + missing")

    def test_lifetime(self):
        def get_f():
            context = quickjs.Context()
            f = context.eval("""
            a = function(x) {
                return 40 + x;
            }
            """)
            return f

        f = get_f()
        self.assertTrue(f)
        # The context has left the scope after f. f needs to keep the context alive for the
        # its lifetime. Otherwise, we will get problems.

    def test_memory_limit(self):
        code = """
            (function() {
                let arr = [];
                for (let i = 0; i < 1000; ++i) {
                    arr.push(i);
                }
            })();
        """
        self.context.eval(code)
        self.context.set_memory_limit(1000)
        with self.assertRaisesRegex(quickjs.JSException, "null"):
            self.context.eval(code)
        self.context.set_memory_limit(1000000)
        self.context.eval(code)

    def test_time_limit(self):
        code = """
            (function() {
                let arr = [];
                for (let i = 0; i < 100000; ++i) {
                    arr.push(i);
                }
                return arr;
            })();
        """
        self.context.eval(code)
        self.context.set_time_limit(0)
        with self.assertRaisesRegex(quickjs.JSException, "InternalError: interrupted"):
            self.context.eval(code)
        self.context.set_time_limit(-1)
        self.context.eval(code)

    def test_memory_usage(self):
        self.assertIn("memory_used_size", self.context.memory().keys())


class Object(unittest.TestCase):
    def setUp(self):
        self.context = quickjs.Context()

    def test_function_is_object(self):
        f = self.context.eval("""
            a = function(x) {
                return 40 + x;
            }
            """)
        self.assertIsInstance(f, quickjs.Object)

    def test_function_call_int(self):
        f = self.context.eval("""
            f = function(x) {
                return 40 + x;
            }
            """)
        self.assertEqual(f(2), 42)

    def test_function_call_int_two_args(self):
        f = self.context.eval("""
            f = function(x, y) {
                return 40 + x + y;
            }
            """)
        self.assertEqual(f(3, -1), 42)

    def test_function_call_many_times(self):
        n = 1000
        f = self.context.eval("""
            f = function(x, y) {
                return x + y;
            }
            """)
        s = 0
        for i in range(n):
            s += f(1, 1)
        self.assertEqual(s, 2 * n)

    def test_function_call_str(self):
        f = self.context.eval("""
            f = function(a) {
                return a + " hej";
            }
            """)
        self.assertEqual(f("1"), "1 hej")

    def test_function_call_str_three_args(self):
        f = self.context.eval("""
            f = function(a, b, c) {
                return a + " hej " + b + " ho " + c;
            }
            """)
        self.assertEqual(f("1", "2", "3"), "1 hej 2 ho 3")

    def test_function_call_object(self):
        d = self.context.eval("d = {data: 42};")
        f = self.context.eval("""
            f = function(d) {
                return d.data;
            }
            """)
        self.assertEqual(f(d), 42)
        # Try again to make sure refcounting works.
        self.assertEqual(f(d), 42)
        self.assertEqual(f(d), 42)

    def test_function_call_unsupported_arg(self):
        f = self.context.eval("""
            f = function(x) {
                return 40 + x;
            }
            """)
        with self.assertRaisesRegex(TypeError, "Unsupported type"):
            self.assertEqual(f({}), 42)

    def test_json(self):
        d = self.context.eval("d = {data: 42};")
        self.assertEqual(json.loads(d.json()), {"data": 42})

    def test_call_nonfunction(self):
        d = self.context.eval("({data: 42})")
        with self.assertRaisesRegex(quickjs.JSException, "TypeError: not a function"):
            d(1)

    def test_wrong_context(self):
        context1 = quickjs.Context()
        context2 = quickjs.Context()
        f = context1.eval("(function(x) { return x.a; })")
        d = context2.eval("({a: 1})")
        with self.assertRaisesRegex(
            ValueError, "Can not mix JS objects from different contexts."
        ):
            f(d)


class FunctionTest(unittest.TestCase):
    def test_adder(self):
        f = quickjs.Function(
            "adder",
            """
            function adder(x, y) {
                return x + y;
            }
            """,
        )
        self.assertEqual(f(1, 1), 2)
        self.assertEqual(f(100, 200), 300)
        self.assertEqual(f("a", "b"), "ab")

    def test_identity(self):
        identity = quickjs.Function(
            "identity",
            """
            function identity(x) {
                return x;
            }
            """,
        )
        for x in [True, [1], {"a": 2}, 1, 1.5, "hej", None]:
            self.assertEqual(identity(x), x)

    def test_bool(self):
        f = quickjs.Function(
            "f",
            """
            function f(x) {
                return [typeof x ,!x];
            }
            """,
        )
        self.assertEqual(f(False), ["boolean", True])
        self.assertEqual(f(True), ["boolean", False])

    def test_empty(self):
        f = quickjs.Function("f", "function f() { }")
        self.assertEqual(f(), None)

    def test_lists(self):
        f = quickjs.Function(
            "f",
            """
            function f(arr) {
                const result = [];
                arr.forEach(function(elem) {
                    result.push(elem + 42);
                });
                return result;
            }""",
        )
        self.assertEqual(f([0, 1, 2]), [42, 43, 44])

    def test_dict(self):
        f = quickjs.Function(
            "f",
            """
            function f(obj) {
                return obj.data;
            }""",
        )
        self.assertEqual(f({"data": {"value": 42}}), {"value": 42})

    def test_time_limit(self):
        f = quickjs.Function(
            "f",
            """
            function f() {
                let arr = [];
                for (let i = 0; i < 100000; ++i) {
                    arr.push(i);
                }
                return arr;
            }
        """,
        )
        f()
        f.set_time_limit(0)
        with self.assertRaisesRegex(quickjs.JSException, "InternalError: interrupted"):
            f()
        f.set_time_limit(-1)
        f()

    def test_garbage_collection(self):
        f = quickjs.Function(
            "f",
            """
            function f() {
                let a = {};
                let b = {};
                a.b = b;
                b.a = a;
                a.i = 42;
                return a.i;
            }
        """,
        )
        initial_count = f.memory()["obj_count"]
        for i in range(10):
            prev_count = f.memory()["obj_count"]
            self.assertEqual(f(run_gc=False), 42)
            current_count = f.memory()["obj_count"]
            self.assertGreater(current_count, prev_count)

        f.gc()
        self.assertLessEqual(f.memory()["obj_count"], initial_count)

    def test_deep_recursion(self):
        f = quickjs.Function(
            "f",
            """
            function f(v) {
                if (v <= 0) {
                    return 0;
                } else {
                    return 1 + f(v - 1);
                }
            }
        """,
        )

        self.assertEqual(f(100), 100)
        limit = 500
        with self.assertRaises(quickjs.StackOverflow):
            f(limit)
        f.set_max_stack_size(2000 * limit)
        self.assertEqual(f(limit), limit)


class Strings(unittest.TestCase):
    def test_unicode(self):
        identity = quickjs.Function(
            "identity",
            """
            function identity(x) {
                return x;
            }
            """,
        )
        context = quickjs.Context()
        for x in ["äpple", "≤≥", "☺"]:
            self.assertEqual(identity(x), x)
            self.assertEqual(context.eval('(function(){ return "' + x + '";})()'), x)


class Threads(unittest.TestCase):
    def setUp(self):
        self.context = quickjs.Context()
        self.executor = concurrent.futures.ThreadPoolExecutor()

    def tearDown(self):
        self.executor.shutdown()

    def test_concurrent(self):
        """Demonstrates that the execution will crash unless the function executes on the same
        thread every time.

        If the executor in Function is not present, this test will fail.
        """
        data = list(range(1000))
        jssum = quickjs.Function(
            "sum",
            """
                function sum(data) {
                    return data.reduce((a, b) => a + b, 0)
                }
            """,
        )

        futures = [self.executor.submit(jssum, data) for _ in range(10)]
        expected = sum(data)
        for future in concurrent.futures.as_completed(futures):
            self.assertEqual(future.result(), expected)

    def test_concurrent_own_executor(self):
        data = list(range(1000))
        jssum1 = quickjs.Function(
            "sum",
            """
                                    function sum(data) {
                                        return data.reduce((a, b) => a + b, 0)
                                    }
                                  """,
            own_executor=True,
        )
        jssum2 = quickjs.Function(
            "sum",
            """
                                    function sum(data) {
                                        return data.reduce((a, b) => a + b, 0)
                                    }
                                  """,
            own_executor=True,
        )

        futures = [
            self.executor.submit(f, data) for _ in range(10) for f in (jssum1, jssum2)
        ]
        expected = sum(data)
        for future in concurrent.futures.as_completed(futures):
            self.assertEqual(future.result(), expected)


class QJS:
    def __init__(self):
        self.interp = quickjs.Context()
        self.interp.eval('var foo = "bar";')


class QuickJSContextInClass(unittest.TestCase):
    @unittest.expectedFailure
    def test_github_issue_7(self):
        # This gives stack overflow internal error, due to how QuickJS calculates stack frames.
        qjs = QJS()
        self.assertEqual(qjs.interp.eval("2+2"), 4)
