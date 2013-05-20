from __future__ import absolute_import
import re

from django import template
from django.template.defaultfilters import escape

from daguerre.adjustments import adjustments
from daguerre.helpers import AdjustmentHelper, AdjustmentInfoDict


register = template.Library()
kwarg_re = re.compile("(\w+)=(.+)")


class AdjustmentNode(template.Node):
    def __init__(self, image, adjustments, asvar=None):
        self.image = image
        self.adjustments = adjustments
        self.asvar = asvar

    def render(self, context):
        image = self.image.resolve(context)

        adj_instances = []
        for adj_to_resolve, kwargs_to_resolve in self.adjustments:
            adj = adj_to_resolve.resolve(context)
            kwargs = dict((k, v.resolve(context))
                          for k, v in kwargs_to_resolve.iteritems())
            try:
                adj_cls = adjustments[adj]
                adj_instances.append(adj_cls(**kwargs))
            except (KeyError, ValueError):
                if self.asvar is not None:
                    context[self.asvar] = AdjustmentInfoDict()
                return ''

        helper = AdjustmentHelper([image], adj_instances)
        info_dict = helper.info_dicts()[0][1]

        if self.asvar is not None:
            context[self.asvar] = info_dict
            return ''
        return escape(info_dict.get('url', ''))


class BulkAdjustmentNode(template.Node):
    def __init__(self, iterable, adjustments, asvar):
        self.iterable = iterable
        self.adjustments = adjustments
        self.asvar = asvar

    def render(self, context):
        iterable = self.iterable.resolve(context)

        adj_list = []
        for adj, kwargs in self.adjustments:
            adj_list.append((adj.resolve(context),
                             dict((k, v.resolve(context))
                             for k, v in kwargs.iteritems())))

        # First adjustment *might* be a lookup.
        # We consider it a lookup if it is not an adjustment name.
        if adj_list and adj_list[0][0] in adjustments:
            lookup = None
        else:
            lookup = adj_list[0][0]
            adj_list = adj_list[1:]

        adj_instances = []
        for adj, kwargs in adj_list:
            try:
                adj_cls = adjustments[adj]
                adj_instances.append(adj_cls(**kwargs))
            except (KeyError, ValueError):
                context[self.asvar] = []
                return ''

        helper = AdjustmentHelper(iterable, adj_instances, lookup)
        context[self.asvar] = helper.info_dicts()
        return ''


def _get_adjustments(parser, tag_name, bits):
    """Helper function to get adjustment defs from a list of bits."""
    adjustments = []
    current_kwargs = None

    for bit in bits:
        match = kwarg_re.match(bit)
        if not match:
            current_kwargs = {}
            adjustments.append((parser.compile_filter(bit), current_kwargs))
        else:
            if current_kwargs is None:
                raise template.TemplateSyntaxError(
                    "Malformed arguments to `%s` tag" % tag_name)
            key, value = match.groups()
            current_kwargs[str(key)] = parser.compile_filter(value)

    return adjustments


@register.tag
def adjust(parser, token):
    """
    Returns a url to the adjusted image,
    or (with ``as``) stores a variable in the context containing an
    :class:`~AdjustmentInfoDict`.

    Syntax::

        {% adjust <image> <adj> <key>=<val> ... <adj> <key>=<val> [as <varname>] %}

    Where <image> is either an image file (like you would get as an
    ImageField's value) or a direct storage path for an image.

    If only one of width/height is supplied,
    the proportions are automatically constrained.

    Cropping and resizing will each only take place if the
    relevant variables are defined.

    The optional keyword arguments must be among:

    * width
    * height
    * max_width
    * max_height
    * adjustment
    * crop
    """
    bits = token.split_contents()
    tag_name = bits[0]

    if len(bits) < 2:
        raise template.TemplateSyntaxError(
            '"{0}" template tag requires at'
            ' least two arguments'.format(tag_name))

    image = parser.compile_filter(bits[1])
    bits = bits[2:]
    asvar = None

    if len(bits) > 1:
        if bits[-2] == 'as':
            asvar = bits[-1]
            bits = bits[:-2]

    return AdjustmentNode(
        image,
        _get_adjustments(parser, tag_name, bits),
        asvar=asvar)


@register.tag
def adjust_bulk(parser, token):
    """
    Stores a variable in the context mapping instances from the iterable
    with adjusted images for those instances.

    Syntax::

        {% adjust_bulk <iterable> [<lookup>] <adj> <key>=<val> ... as varname %}

    The keyword arguments have the same meaning as for :ttag:`{% adjust %}`.

    ``lookup`` has the same format as a template variable
    (for example, ``"get_profile.image"``).
    The lookup will be performed on each item in the
    ``iterable`` to get the image which should be adjusted.
    """
    bits = token.split_contents()
    tag_name = bits[0]

    if len(bits) < 4:
        raise template.TemplateSyntaxError(
            '"{0}" template tag requires at'
            ' least four arguments'.format(tag_name))

    if bits[-2] != 'as':
        raise template.TemplateSyntaxError(
            'The second to last argument to'
            ' {0} must be "as".'.format(tag_name))

    iterable = parser.compile_filter(bits[1])
    asvar = bits[-1]
    adjustments = _get_adjustments(parser, tag_name, bits[2:-2])

    return BulkAdjustmentNode(iterable, adjustments, asvar)
