from flask_featureflags import ImproperlyConfigured, FEATURE_FLAGS_CONFIG

try:
  from gutter.client.settings import manager as manager_settings
  from gutter.client.models import Switch, Condition
  from gutter.client.default import gutter
  is_gutter_available = True
except ImportError:
  is_gutter_available = False


class GutterFeaturesHandler(object):
    """
      Responsible for handling the communication with gutter and Flask-FeatureFlags
      It helps managing config for gutter from flask app's config and acts
      as an API, providing an abstraction layer on top of gutter.
    """

    def __init__(self, app=None, storage_engine=None, autocreate=False,
                 override_switches=False):
        """
          Initialise and configure Gutter
          :param storage_engine:
            The storage engine that will be used to store the switches. By default
            it will store engines in memory, but you can specify a custom engine
            provided by durabledict library, which supports redis, zookeeper, etc
          :param autocreate:
            If it's asked to check if a switch is active, but it's not created, this
            switch will be automatically created if `autocreate` is set to `True`.
          :param override_switches:
            Determine if the switches loaded from config should replace the ones
            that are already registered at `storage_engine`. When using an engine
            like redis or zookeeper, this is preferable to be False, since you
            can lose your changes if they aren't equal to the config file anymore.
        """
        if not is_gutter_available:
            raise ImproperlyConfigured("You should install Gutter in order to use" \
                                       " GutterFeaturesHandler.")

        if app is not None:
          self.init_app(app, storage_engine, autocreate, override_switches)

    def init_app(self, app, storage_engine=None, autocreate=False,
                 override_switches=False):
        self.app = app
        if storage_engine is not None:
            manager_settings.storage_engine = storage_engine
        manager_settings.autocreate = autocreate

        self.override_switches = override_switches
        self._conditions = {}
        self._load_switches()

    @property
    def switches(self):
      """
        Get the current switches from gutter in a dict, with the keys being the
        switches names.
      """
      return {switch.name: switch for switch in gutter.switches}

    def __call__(self, feature, *inputs):
        """
          Since Flask-FeatureFlags treats handlers as functions, this class implement
          __call__ as being the function to handle checking if a feature is active.
        """
        return self.check(feature, *inputs)

    def check(self, feature):
        """
          Check whether a feature is active or not.
        """
        return gutter.active(feature)

    def rename_switch(self, old_name, new_name):
        """
          Rename a switch
        """
        switch = gutter.switch(old_name)
        switch.name = new_name
        switch.save()

    def unregister_switch(self, switch_name):
        """
          A wrapper function to provide a top-level API
        """
        gutter.unregister(switch_name)

    def _load_switches(self):
        """
          Load switches from flask app config. It'll search the FEATURE_FLAGS dict
          and register each feature. If the feature's value is True, it'll be
          registered as globally enabled, if False, as disabled.
        """
        switches = self.app.config.get(FEATURE_FLAGS_CONFIG)
        for switch_name, switch_value in switches.iteritems():
            if switch_value:
                switch_state = Switch.states.GLOBAL
            else:
                switch_state = Switch.states.DISABLED
            self.register_switch(switch_name, switch_state,
                                 override=self.override_switches)

    def register_switch(self, switch_name, state, override=False):
        """
          Registers a switch if it doesn't exist already or override is `True`
        """
        if override or not switch_name in self.switches:
            switch = Switch(switch_name, state=state)
            gutter.register(switch)
            return switch
