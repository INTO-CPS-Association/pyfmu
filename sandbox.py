import logging


class A:
    def __init__(self, logger):
        self.logger = logger

    def foo(self):
        self.logger.info("hello from A")


class B:
    def __init__(self, logger):
        self.logger = logger

    def foo(self):
        self.logger.info("hello from B")


if __name__ == "__main__":
    log = logging.getLogger(__name__)
    h = logging.StreamHandler()
    log.addHandler(h)

    # filters
    class LogAllFilter(logging.Filter):
        def filter(self, record: logging.LogRecord):
            return True

    f = LogAllFilter()
    log.addFilter(f)

    log.setLevel("DEBUG")
    a = A(log)
    b = B(log)

    a.foo()
    b.foo()
