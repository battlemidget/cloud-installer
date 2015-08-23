# Copyright 2015 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cloudinstall.utils as utils
import logging
import os

log = logging.getLogger('cloudinstall.config')


class ConfigException(Exception):
    pass


class Config:
    # STYLES = [
    #     ('body', 'white', 'black'),
    #     ('header_menu', 'light gray', 'dark gray'),
    #     ('header_title', 'light gray,bold', 'dark magenta'),
    #     ('subheading', 'dark gray,bold', 'default'),
    #     ('deploy_highlight_start', 'dark gray', 'light green'),
    #     ('deploy_highlight_end', 'dark gray', 'dark green'),
    #     ('disabled_button', 'black', 'white'),
    #     ('disabled_button_focus', 'black', 'light gray'),
    #     ('divider_line', 'light gray', 'default'),
    #     ('filter', 'dark gray,underline', 'white'),
    #     ('filter_focus', 'dark gray,underline', 'light gray'),
    #     ('focus', 'white', 'dark gray'),
    #     ('radio focus', 'white,bold', 'dark magenta'),
    #     ('input', 'white', 'dark gray'),
    #     ('input focus', 'dark magenta,bold', 'dark gray'),
    #     ('dialog', 'white', 'dark gray'),
    #     ('status_extra', 'light gray,bold', 'dark gray'),
    #     ('error', 'white', 'dark red'),
    #     ('info', 'light green', 'default'),
    #     ('label', 'dark gray', 'default'),
    #     ('error_icon', 'light red,bold', 'default'),
    #     ('pending_icon_on', 'light blue,bold', 'default'),
    #     ('pending_icon', 'dark blue', 'default'),
    #     ('success_icon', 'light green', 'default'),
    #     ('button_primary', 'white', 'dark gray', 'default', 'white', '#d51'),
    #     ('button_primary focus', 'dark blue,bold', 'dark gray', 'default',
    #      'white', '#b30'),
    #     ('button_secondary', 'white', 'dark gray', 'default',
    #      '#aaa', 'dark gray'),
    #     ('button_secondary focus', 'dark blue,bold', 'dark gray', 'default',
    #      'white', 'dark gray')
    # ]

    _config = None

    # give some sense of protecting the config
    known_config_keys = [
        'admin_email',
        'admin_name',
        'advanced_config',
        'api_key',
        'api_password',
        'apt_https_proxy',
        'apt_mirror',
        'apt_proxy',
        'arch',
        'bin',
        'cfg_file',
        'cfg_path',
        'charm_config',
        'charm_plugin_path',
        'container_ip',
        'container_name',
        'environments_path',
        'headless',
        'home',
        'home_expanded',
        'http_proxy',
        'https_proxy',
        'image_metadata_url',
        'install_only',
        'install_type',
        'level',
        'lxc_network',
        'next_charms',
        'no_proxy',
        'password',
        'path',
        'pidfile',
        'placements_file',
        'release',
        'series',
        'server',
        'share',
        'tip',
        'tmpl',
        'tools_metadata_url',
        'upstream_deb_path',
        'upstream_ppa',
        'use_nclxd',
        'use_upstream_ppa',
    ]

    @classmethod
    def set(cls, section, key, val):
        """ sets config option """
        if key not in Config.known_config_keys:
            raise Exception(
                "Tried to set a value on unknown key: {}".format(key))
        Config.reload()
        try:
            Config._config[section][key] = val
            Config.save()
        except Exception as e:
            log.exception(
                "Failed to set {} to section {} option {}: {}".format(
                    val, section, key, e))
            raise e

    @classmethod
    def get(cls, section, key=None):
        Config.reload()
        try:
            if key is None:
                return Config._config[section]
            return Config._config[section].get(key, None)
        except Exception as e:
            log.exception("Failed to read section {} option {}: {}".format(
                section, key, e))
            raise e

    @classmethod
    def getboolean(cls, section, key):
        try:
            return Config._config[section].getboolean(key, False)
        except Exception as e:
            log.exception("Failed to read section {} option {}: {}".format(
                section, key, e))
            raise e

    @classmethod
    def save(cls):
        try:
            utils.write_ini(Config._config)
        except Exception as e:
            log.exception("Failed to save config: {}".format(e))
            raise e

    @classmethod
    def reload(cls):
        Config._config = utils.read_ini_existing()

    @classmethod
    def load(cls):
        Config.reload()

    @classmethod
    def to_dict(cls):
        return dict(Config._config)

    @classmethod
    def exists(cls):
        return os.path.isfile(
            os.path.join(utils.install_home(), '.cloud-install/config.conf'))
