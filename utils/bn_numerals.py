BN_DIGITS = {
    '0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪',
    '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯',
}

EN_DIGITS = {v: k for k, v in BN_DIGITS.items()}


def to_bn(n):
    return ''.join(BN_DIGITS.get(d, d) for d in str(n))


def to_en(n):
    return ''.join(EN_DIGITS.get(c, c) for c in str(n))
