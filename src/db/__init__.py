try:
    from .session import current_session, transactional
except:
    def transactional(*a, **k):
        def wrap(f):
            def needs_db(*a, **k):
                assert False, 'This function needs db to perform its task.'

            return needs_db

        return wrap

    def current_session():
        return None
