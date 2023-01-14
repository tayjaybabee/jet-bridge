import hashlib
import random
import time

try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    import warnings
    warnings.warn('A secure pseudo-random number generator is not available '
                  'on your system. Falling back to Mersenne Twister.')
    using_sysrandom = False


def get_random_string(length, allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', salt=''):
    """
    Returns a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    if not using_sysrandom:
        # This is ugly, and a hack, but it makes things better than
        # the alternative of predictability. This re-seeds the PRNG
        # using a value that is hard for an attacker to predict, every
        # time a random string is required. This may change the
        # properties of the chosen random sequence slightly, but this
        # is better than absolute predictability.
        random.seed(
            hashlib.sha256(
                f"{random.getstate()}{time.time()}{salt}".encode('utf-8')
            ).digest()
        )
    return ''.join(random.choice(allowed_chars) for _ in range(length))


def find_index(list, predicate):
    return next((i for i, value in enumerate(list) if predicate(value, i)), None)


# TODO: Fix non dict list items
# TODO: List merge is not universal
def merge(destination, source):
    for key, value in source.items():
        if (
            key == 'params'
            or not isinstance(value, dict)
            and not isinstance(value, list)
        ):
            destination[key] = value
        elif isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge(node, value)
        else:
            node = destination.setdefault(key, [])

            for item in value:
                index = find_index(node, lambda x, i: x['db_column'] == item['db_column'])
                if index is None:
                    continue
                node[index]
                merge(node[index], item)
    return destination


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


def get_set_first(value):
    return next(iter(value))


def any_type_sorter(value):
    return '' if value is None else str(value)


def unique(arr):
    result = []
    for item in arr:
        if item not in result:
            result.append(item)
    return result


def flatten(arr):
    result = []
    for item in arr:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result
