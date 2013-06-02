# -*- coding: utf-8 -*-

class TestImport(object):
    def test_client_import(self):
        from game import autoenv
        autoenv.init('Client')

        import network
        import client.core

    def test_server_import(self):
        from game import autoenv
        autoenv.init('Server')

        import server.core

    def test_thb_import(self):
        from game import autoenv
        autoenv.init('Server')

        import gamepack.thb
        # import gamepack.thb.ui
        import gamepack.thb.cards
        import gamepack.thb.characters
