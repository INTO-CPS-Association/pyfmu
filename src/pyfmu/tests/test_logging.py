from pyfmu.fmi2 import Fmi2CallbackLogger, Fmi2Status


def test_categoryNotRegistered_notLogged():

    logged = False

    def logging_callback(msg):
        nonlocal logged
        logged = True

    logger = Fmi2CallbackLogger(callback=logging_callback)
    logger.log("test")

    assert(not logged)


def test_customCategoryRegistered_logged():

    n = 0

    def callback(s, c, m):
        nonlocal n
        n += 1

    c = "my_category"
    logger = Fmi2CallbackLogger(callback)
    logger.register_log_category(c)
    logger.set_debug_logging(True, [c])

    before = n

    logger.log("hello world!", category=c)

    assert(n == before + 1)


def test_registerAlias_logged():

    n = 0

    def callback(s, c, m):
        nonlocal n
        n += 1

    logger = Fmi2CallbackLogger(callback)
    logger.register_log_category('ab', aliases={'a', 'b'})
    logger.set_debug_logging(True, ['ab'])

    before = n

    logger.log('test', 'a')
    logger.log('test', 'b')

    assert n == before + 2


def test_predicates():

    n = 0

    def callback(s, c, m):
        nonlocal n
        n += 1

    def log_all_predicate(s, c, m):
        return True

    logger = Fmi2CallbackLogger(callback)
    logger.register_log_category('all', predicate=log_all_predicate)
    logger.set_debug_logging(True, ['all'])

    before = n

    logger.log('test', 'a')
    logger.log('test', 'b')
    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)

    assert n == before + 4

# standard categories


def test_logEvent():

    n = 0

    def callback(s, c, m):
        nonlocal n
        n += 1

    cs = ["logEvents"]

    logger = Fmi2CallbackLogger(callback)
    logger.register_standard_categories(cs)
    logger.set_debug_logging(True, cs)

    before = n

    # every log message is treated as an event?
    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)

    assert n == before + 6


def test_logSingularLinearSystems():

    n = 0

    def callback(s, c, m):
        nonlocal n
        n += 1

    cs = ["logSingularLinearSystems"]

    logger = Fmi2CallbackLogger(callback)
    logger.register_standard_categories(cs)
    logger.set_debug_logging(True, cs)

    before = n

    # category aliases
    logger.log('test', category="SingularLinearSystem")
    logger.log('test', category="singularlinearsystem")
    logger.log('test', category="sls")

    # ignore everything else
    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)

    assert n == before + 3


def test_logNonLinearSystems():

    n = 0

    def callback(s, c, m):
        nonlocal n
        n += 1

    cs = ["logNonlinearSystems"]

    logger = Fmi2CallbackLogger(callback)
    logger.register_standard_categories(cs)
    logger.set_debug_logging(True, cs)

    before = n

    # category aliases
    logger.log('test', category="NonLinearSystems")
    logger.log('test', category="nonlinearsystems")
    logger.log('test', category="nls")

    # ignore everything else
    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)

    assert n == before + 3


def test_logDynamicStateSelection():

    n = 0

    def callback(s, c, m):
        nonlocal n
        n += 1

    cs = ["logDynamicStateSelection"]

    logger = Fmi2CallbackLogger(callback)
    logger.register_standard_categories(cs)
    logger.set_debug_logging(True, cs)

    before = n

    logger.log('test', category="DynamicStateSelection")
    logger.log('test', category="dynamicstateselection")
    logger.log('test', category="dss")

    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)

    assert n == before + 3


def test_statusLogLevels():

    n = 0

    def callback(s, c, m):
        print(f"{s}{c}{m}")
        nonlocal n
        n += 1

    logger = Fmi2CallbackLogger(callback)
    logger.register_all_standard_categories()

    ces = {
        ("logStatusWarning", Fmi2Status.warning),
        ("logStatusDiscard", Fmi2Status.discard),
        ("logStatusError", Fmi2Status.error),
        ("logStatusFatal", Fmi2Status.fatal),
        ("logStatusPending", Fmi2Status.pending)
    }

    for ce in ces:
        c, s = ce
        others = ces.difference({ce})
        logger.set_debug_logging(True, [c])

        before = n
        logger.log("", status=s)
        assert n == before + 1

        for co, so in others:
            logger.log("", status=so)

        assert n == before + 1
        logger.set_debug_logging(False, [c])


def test_logDefaultCategory_loggedWithEvent():

    n = 0

    def callback(s, c, m):
        print(f"{s}{c}{m}")
        nonlocal n
        n += 1

    cs = ["logEvents"]

    logger = Fmi2CallbackLogger(callback)
    logger.register_standard_categories(cs)
    logger.set_debug_logging(True, cs)

    before = n
    logger.log('test')
    assert n == before + 1
