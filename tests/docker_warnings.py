import warnings

def fxn():
    warnings.warn("resource", ResourceWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()
