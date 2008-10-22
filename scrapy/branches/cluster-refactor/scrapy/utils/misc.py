"""
Auxiliary functions which doesn't fit anywhere else
"""
import re

from twisted.internet import defer

from scrapy.core.exceptions import UsageError
from scrapy.utils.python import flatten
from scrapy.utils.markup import remove_entities
from scrapy.utils.defer import defer_succeed

def dict_updatedefault(D, E, **F):
    """
    updatedefault(D, E, **F) -> None.

    Update D from E and F: for k in E: D.setdefault(k, E[k])
    (if E has keys else: for (k, v) in E: D.setdefault(k, v))
    then: for k in F: D.setdefault(k, F[k])
    """
    for k in E:
        if isinstance(k, tuple):
            k, v = k
        else:
            v = E[k]
        D.setdefault(k, v)

    for k in F:
        D.setdefault(k, F[k])

def memoize(cache, hash):
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = hash(*args, **kwargs)
            if key in cache:
                return defer_succeed(cache[key])

            def _store(_):
                cache[key] = _
                return _

            result = func(*args, **kwargs)
            if isinstance(result, defer.Deferred):
                return result.addBoth(_store)
            cache[key] = result
            return result
        return wrapper
    return decorator

def stats_getpath(dict_, path, default=None):
    for key in path.split('/'):
        if key in dict_:
            dict_ = dict_[key]
        else:
            return default
    return dict_

def load_class(class_path):
    """Load a class given its absolute class path, and return it without
    instantiating it"""
    try:
        dot = class_path.rindex('.')
    except ValueError:
        raise UsageError, '%s isn\'t a module' % class_path
    module, classname = class_path[:dot], class_path[dot+1:]
    try:
        mod = __import__(module, {}, {}, [''])
    except ImportError, e:
        raise UsageError, 'Error importing %s: "%s"' % (module, e)
    try:
        cls = getattr(mod, classname)
    except AttributeError:
        raise UsageError, 'module "%s" does not define a "%s" class' % (module, classname)

    return cls

def extract_regex(regex, text, encoding):
    """Extract a list of unicode strings from the given text/encoding using the following policies:
    
    * if the regex contains a named group called "extract" that will be returned
    * if the regex contains multiple numbered groups, all those will be returned (flattened)
    * if the regex doesn't contain any group the entire regex matching is returned
    """

    if isinstance(regex, basestring):
        regex = re.compile(regex)

    try:
        strings = [regex.search(text).group('extract')]   # named group
    except:
        strings = regex.findall(text)    # full regex or numbered groups
    strings = flatten(strings)

    if isinstance(text, unicode):
        return [remove_entities(s, keep=['lt', 'amp']) for s in strings]
    else:
        return [remove_entities(unicode(s, encoding), keep=['lt', 'amp']) for s in strings]