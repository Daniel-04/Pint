import json
import re


def isError(answer, param=None):
    return param.script_returncode != 0


def is_one_token(s, param=None):
    return bool(re.fullmatch(r"\[\w+\]", s))


def isYes(answer, param=None):
    text = answer.lower().strip()

    return text in ("yes", "yes.", "y", "true", "t", "1")


def isNo(answer, param=None):
    text = answer.lower().strip()

    return text in ("no", "no.", "n", "false", "f", "0")


def isShort(answer, param=None):
    length = 5
    try:
        length = int(param)
    except Exception:
        return False
    return len(answer, param) < length


def isLong(answer, param=None):
    length = 5
    try:
        length = int(param)
    except Exception:
        return False
    return len(answer, param) >= length


def isGreaterThan(answer, param=None):
    try:
        return float(answer) > float(param)
    except Exception:
        return False


def isLessThan(answer, param=None):
    try:
        return float(answer) < float(param)
    except Exception:
        return False


def isNumber(answer, param=None):
    try:
        float(answer)
        return True
    except Exception:
        return False


def isJson(answer, param=None):
    try:
        json.loads(answer)
        return True
    except Exception:
        return False


def isNotNumber(answer, param=None):
    return not isNumber(answer, param)


def isNotJson(answer, param=None):
    return not isJson(answer, param)


def isJsonList(answer, param=None):
    try:
        data = json.loads(answer)
        answer = isinstance(data, list)
        return answer
    except Exception:
        return False


def isNotJsonList(answer, param=None):
    return not isJsonList(answer, param)


def isCommaSeparatedList(answer, param=None):
    return "," in answer


def isNotCommaSeparatedList(answer, param=None):
    return not isCommaSeparatedList(answer, param)
