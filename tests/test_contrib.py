from __future__ import with_statement
import unittest
from mock import patch

from .fixtures import app, feature_setup
import flask_featureflags
from flask_featureflags.contrib import GutterFeaturesHandler
from gutter.client.default import gutter
from gutter.client.models import Switch, Condition

class TestGutterHandler(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app
        self.app.config[flask_featureflags.FEATURE_FLAGS_CONFIG] = {}
        self.test_client = app.test_client()

    def test_registering_global_and_disabled_switches_from_config(self):
        self.app.config[flask_featureflags.FEATURE_FLAGS_CONFIG] = {
          'enabled-feature': True,
          'disabled-feature': False
        }

        gutter_handler = GutterFeaturesHandler(self.app, autocreate=False)
        feature_setup.clear_handlers()
        feature_setup.add_handler(gutter_handler)

        self.assertTrue('disabled-feature', gutter_handler.switches)
        self.assertTrue('enabled-feature', gutter_handler.switches)

        # Check Gutter
        self.assertFalse(gutter.active('disabled-feature'))
        self.assertTrue(gutter.active('enabled-feature'))

        # Check GutterHandler
        self.assertFalse(gutter_handler.check('disabled-feature'))
        self.assertTrue(gutter_handler.check('enabled-feature'))

        # Check Feature-Flag
        self.assertFalse(feature_setup.check('disabled-feature'))
        self.assertTrue(feature_setup.check('enabled-feature'))

    def test_existing_switches_are_not_overriden_when_reading_config_by_default(self):
        switch_name = 'existent-feature'

        # Fill gutter with a previous switch
        switch = Switch(switch_name, state=Switch.states.GLOBAL)
        gutter.register(switch)

        self.app.config[flask_featureflags.FEATURE_FLAGS_CONFIG] = {
          switch_name: False
        }
        gutter_handler = GutterFeaturesHandler(self.app, autocreate=False)
        feature_setup.clear_handlers()
        feature_setup.add_handler(gutter_handler)

        # Check Gutter
        self.assertTrue(gutter.active(switch_name))

        # Check GutterHandler
        self.assertTrue(gutter_handler.check(switch_name))

        # Check Feature-Flag
        self.assertTrue(feature_setup.check(switch_name))

    def test_existing_switches_can_be_overriden_when_reading_config_if_specified(self):
        switch_name = 'existent-feature'

        # Fill gutter with a previous switch
        switch = Switch(switch_name, state=Switch.states.GLOBAL)
        gutter.register(switch)

        self.app.config[flask_featureflags.FEATURE_FLAGS_CONFIG] = {
          switch_name: False
        }
        gutter_handler = GutterFeaturesHandler(self.app, autocreate=False,
                                               override_switches=True)
        feature_setup.clear_handlers()
        feature_setup.add_handler(gutter_handler)

        # Check Gutter
        self.assertFalse(gutter.active(switch_name))

        # Check GutterHandler
        self.assertFalse(gutter_handler.check(switch_name))

        # Check Feature-Flag
        self.assertFalse(feature_setup.check(switch_name))

    def test_rename_switch(self):
        old_name = 'old_name'
        new_name = 'new_name'

        self.app.config[flask_featureflags.FEATURE_FLAGS_CONFIG] = {
          old_name: True
        }

        gutter_handler = GutterFeaturesHandler(self.app, autocreate=False)

        self.assertIn(old_name, gutter_handler.switches)
        self.assertNotIn(new_name, gutter_handler.switches)

        gutter_handler.rename_switch(old_name, new_name)

        self.assertIn(new_name, gutter_handler.switches)
        self.assertNotIn(old_name, gutter_handler.switches)

        self.assertEqual(new_name, gutter.switch(new_name).name)

    def test_unregister_switch(self):
        switch_name = 'switch_name'

        self.app.config[flask_featureflags.FEATURE_FLAGS_CONFIG] = {
          switch_name: True
        }

        gutter_handler = GutterFeaturesHandler(self.app, autocreate=False)

        self.assertIn(switch_name, gutter_handler.switches)
        gutter_handler.unregister_switch(switch_name)
        self.assertNotIn(switch_name, gutter_handler.switches)

