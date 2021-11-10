def validate_default(validator, s, default):
    if validator(s):
        return s
    else:
        return default
