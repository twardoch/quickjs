#include <Python.h>

#include "third-party/quickjs.h"

static PyObject* JSException = NULL;

static PyObject* quickjs_to_python(JSContext* context, JSValue value) {
    int tag = JS_VALUE_GET_TAG(value);
	PyObject *return_value = NULL;

	if (tag == JS_TAG_INT) {
		return_value = Py_BuildValue("i", JS_VALUE_GET_INT(value));
	} else if (tag == JS_TAG_BOOL) {
		return_value = Py_BuildValue("O", JS_VALUE_GET_BOOL(value) ? Py_True : Py_False);
	} else if (tag == JS_TAG_NULL) {
		return_value = Py_None;
	} else if (tag == JS_TAG_UNDEFINED) {
		return_value = Py_None;
	} else if (tag == JS_TAG_UNINITIALIZED) {
		return_value = Py_None;
	} else if (tag == JS_TAG_EXCEPTION) {
        JSValue exception = JS_GetException(context);
        JSValue error_string = JS_ToString(context, exception);
        const char *cstring = JS_ToCString(context, error_string);
        PyErr_Format(JSException, "%s", cstring);
		JS_FreeCString(context, cstring);
        JS_FreeValue(context, error_string);
        JS_FreeValue(context, exception);
	} else if (tag == JS_TAG_FLOAT64) {
		return_value = Py_BuildValue("d", JS_VALUE_GET_FLOAT64(value));
	} else if (tag == JS_TAG_STRING) {
		const char *cstring = JS_ToCString(context, value);
		return_value = Py_BuildValue("s", cstring);
		JS_FreeCString(context, cstring);
	} else {
		// TODO: Raise exception.
	}

	JS_FreeValue(context, value);
	if (return_value == Py_None) {
		Py_RETURN_NONE;
	}
	return return_value;
}

static PyObject *test(PyObject *self, PyObject *args) {
	return Py_BuildValue("i", 42);
}

struct module_state {};

typedef struct {
	PyObject_HEAD JSRuntime *runtime;
	JSContext *context;
} ContextData;

static PyObject *context_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
	ContextData *self;
	self = (ContextData *)type->tp_alloc(type, 0);
	if (self != NULL) {
		self->runtime = JS_NewRuntime();
		self->context = JS_NewContext(self->runtime);
	}
	return (PyObject *)self;
}

static void context_dealloc(ContextData *self) {
	JS_FreeContext(self->context);
	JS_FreeRuntime(self->runtime);
	Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *context_eval(ContextData *self, PyObject *args) {
	const char *code;
	if (!PyArg_ParseTuple(args, "s", &code)) {
		return NULL;
	}
	JSValue value = JS_Eval(self->context, code, strlen(code), "<input>", JS_EVAL_TYPE_GLOBAL);
    return quickjs_to_python(self->context, value);
}

static PyMethodDef context_methods[] = {
    {"eval", (PyCFunction)context_eval, METH_VARARGS, "Evaluates a Javascript string."},
    {NULL} /* Sentinel */
};

static PyTypeObject Context = {PyVarObject_HEAD_INIT(NULL, 0).tp_name = "_quickjs.Context",
                               .tp_doc = "Quickjs context",
                               .tp_basicsize = sizeof(ContextData),
                               .tp_itemsize = 0,
                               .tp_flags = Py_TPFLAGS_DEFAULT,
                               .tp_new = context_new,
                               .tp_dealloc = (destructor)context_dealloc,
                               .tp_methods = context_methods};

static PyMethodDef myextension_methods[] = {{"test", (PyCFunction)test, METH_NOARGS, NULL},
                                            {NULL, NULL}};

static struct PyModuleDef moduledef = {PyModuleDef_HEAD_INIT,
                                       "quickjs",
                                       NULL,
                                       sizeof(struct module_state),
                                       myextension_methods,
                                       NULL,
                                       NULL,
                                       NULL,
                                       NULL};

PyMODINIT_FUNC PyInit__quickjs(void) {
	if (PyType_Ready(&Context) < 0) {
		return NULL;
	}

	PyObject *module = PyModule_Create(&moduledef);
	if (module == NULL) {
		return NULL;
	}

    JSException = PyErr_NewException("_quickjs.JSException", NULL, NULL);
    if (JSException == NULL) {
        return NULL;
    }

	Py_INCREF(&Context);
	PyModule_AddObject(module, "Context", (PyObject *)&Context);
    PyModule_AddObject(module, "JSException", JSException);
	return module;
}
