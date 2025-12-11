import traceback
import json
import re


def log_traceback(logfile="error.log"):
    with open(logfile, "a", encoding="utf-8") as file:
        traceback.print_exc(file=file)


def isError(answer, param=None):
    return param.script_returncode != 0


def is_one_token(s, param=None):
    return bool(re.fullmatch(r"\[\w+\]", s))


def isYes(answer, param=None):
    pattern = re.compile(r"^\s*[^\w_]*?(?:y(?:es)?|t(?:rue)?|1)\b", re.IGNORECASE)
    return bool(pattern.search(answer))


def isNo(answer, param=None):
    pattern = re.compile(r"^\s*[^\w_]*?(?:n(?:o)?|f(?:alse)?|0)\b", re.IGNORECASE)
    return bool(pattern.search(answer))


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
