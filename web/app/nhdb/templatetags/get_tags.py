from django import template

from django.template import Library, Node, resolve_variable, TemplateSyntaxError
from django.template import (
    Context,
    Template,
    Node,
    resolve_variable,
    TemplateSyntaxError,
    Variable,
)

register = template.Library()


"""
Based on:
URL: http://django.mar.lt/2010/07/add-get-parameter-tag.html
"""


class DropGetParam(Node):
    def __init__(self, values):
        self.values = []
        for i in values:
            self.values.append([i[0], template.Variable(i[1])])

    def render(self, context):
        req = resolve_variable("request", context)
        params = req.GET.copy()

        for key, value in self.values:
            try:
                value = value.resolve(context)
            except template.VariableDoesNotExist:
                value = value
            g = params.getlist(key)
            if not g:
                g = []
            try:
                g.remove(value)
            except ValueError:
                continue

            params.setlist(key, g)
        return "?%s" % params.urlencode()


class HasGetParam(Node):
    """
    Checks for existance of the given K/V in the request
    """

    def __init__(self, values):
        self.values = []
        for i in values:
            self.values.append([i[0], template.Variable(i[1])])

    def render(self, context):
        req = resolve_variable("request", context)
        params = req.GET.copy()

        for key, value in self.values:
            try:
                value = value.resolve(context)
            except template.VariableDoesNotExist:
                continue

            if value in params.getlist(key):

                context["hasparam"] = True
                return ""
        context["hasparam"] = False
        return ""


class AddGetParameter(Node):
    def __init__(self, values):
        self.values = []
        for i in values:
            self.values.append([i[0], template.Variable(i[1])])

    def render(self, context):
        req = resolve_variable("request", context)
        params = req.GET.copy()
        for key, value in self.values:
            if key.startswith("__REPLACE__"):
                method = "replace"
                key = key.replace("__REPLACE__", "")

            else:
                method = "add"

            try:
                _value = value.resolve(context)
            except template.VariableDoesNotExist:
                _value = value

            if method == "replace":
                params.setlist(key, [_value])
            else:
                g = params.getlist(key)
                if not g:
                    g = []
                g.append(_value)
                params.setlist(key, g)
        return "?%s" % params.urlencode()


def getvals(token):
    from re import split

    contents = split(r"\s+", token.contents, 2)[1]
    pairs = split(r",", contents)
    values = []
    for pair in pairs:
        s = split(r"=", pair, 2)
        values.append([s[0], s[1]])
    return values


@register.tag
def get_add(parser, token):
    values = getvals(token)
    return AddGetParameter(values)


@register.tag
def get_drop(parser, token):
    values = getvals(token)
    return DropGetParam(values)


@register.tag
def get_has(parser, token):
    values = getvals(token)
    return HasGetParam(values)
