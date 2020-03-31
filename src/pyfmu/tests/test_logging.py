from pyfmu.fmi2 import Fmi2CallbackLogger, Fmi2StdLogCats, Fmi2Status, Fmi2Slave


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

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

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

    assert(len(logger))


def test_logNonLinearSystems():

    cs = ["logNonlinearSystems"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

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

    assert(len(logger) == 3)


def test_logDynamicStateSelection():

    cs = ["logDynamicStateSelection"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    logger.log('test', category="DynamicStateSelection")
    logger.log('test', category="dynamicstateselection")
    logger.log('test', category="dss")

    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)

    assert(len(logger) == 3)


def test_logWarning():

    cs = ["logStatusWarning"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    logger.log('test', status=Fmi2Status.ok)
    assert(len(logger) == 0)
    logger.log('test', status=Fmi2Status.warning)
    assert(len(logger) == 1)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)
    assert(len(logger) == 1)


def test_logError():

    cs = ["logStatusError"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    assert(len(logger) == 0)
    logger.log('test', status=Fmi2Status.error)
    assert(len(logger) == 1)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)
    assert(len(logger) == 1)


def test_logDiscard():

    cs = ["logStatusDiscard"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    assert(len(logger) == 0)
    logger.log('test', status=Fmi2Status.discard)
    assert(len(logger) == 1)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)
    assert(len(logger) == 1)


def test_logFatal():

    cs = ["logStatusFatal"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    assert(len(logger) == 0)
    logger.log('test', status=Fmi2Status.fatal)
    assert(len(logger) == 1)
    logger.log('test', status=Fmi2Status.pending)
    assert(len(logger) == 1)


def test_logPending():

    cs = ["logStatusPending"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    assert(len(logger) == 0)
    logger.log('test', status=Fmi2Status.pending)
    assert(len(logger) == 1)


def test_logAll():

    cs = ["logAll"]

    logger = Fmi2CallbackLogger()
    logger.set_active_log_categories(True, cs)
    logger.register_standard_categories(cs)

    logger.log('test', status=Fmi2Status.ok)
    logger.log('test', status=Fmi2Status.warning)
    logger.log('test', status=Fmi2Status.error)
    logger.log('test', status=Fmi2Status.discard)
    logger.log('test', status=Fmi2Status.fatal)
    logger.log('test', status=Fmi2Status.pending)

    assert(len(logger) == 6)

# defaults


def test_logDefaultCategory_loggedWithEvent():

    cs = ["logEvents"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    assert(len(logger) == 0)
    logger.log('test')
    assert(len(logger) == 1)


# message stack

def test_len_logIncreasesLength():

    cs = ["logAll"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    assert(len(logger) == 0)

    logger.log('test')

    assert(len(logger) == 1)

    logger.log('test')

    assert(len(logger) == 2)


def test_len_popDecreasesLength():
    cs = ["logAll"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    assert(len(logger) == 0)

    logger.log('test')

    assert(len(logger) == 1)

    logger.log('test')

    assert(len(logger) == 2)

    logger.pop_messages(1)

    assert(len(logger) == 1)

    logger.pop_messages(1)

    assert(len(logger) == 0)


def test_pop_returnsMessagesFifo():

    cs = ["logAll"]

    logger = Fmi2CallbackLogger()
    logger.register_standard_categories(cs)
    logger.set_active_log_categories(True, cs)

    logger.log("a")
    logger.log("b")

    messages = logger.pop_messages(2)
    messages = [m.message for m in messages]

    assert(messages == ['a', 'b'])
