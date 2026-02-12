import json

from unittest.mock import mock_open
from unittest.mock import patch

from charms.layer.docker import write_daemon_json
from charms.layer.docker import set_daemon_json
from charms.layer.docker import delete_daemon_json
from charms.layer.docker import render_configuration_template


@patch("charmhelpers.core.unitdata.kv")
@patch("charmhelpers.core.hookenv.config")
def test_write_daemon_json(config, kv):
    daemon_opts = {
        "log-driver": "json-file",
        "log-opts": {"max-size": "10m", "max-file": "100"},
    }

    daemon_opts_additions = {
        "log-driver": "this-will-be-overwritten",
        "my-extra-config": "this-will-be-preserved",
    }

    charm_config = {"daemon-opts": json.dumps(daemon_opts)}

    def mock_config(key):
        return charm_config[key]

    config.side_effect = mock_config
    kv.return_value.get.return_value = daemon_opts_additions

    with patch("builtins.open", mock_open(), create=True):
        daemon_opts_additions.update(daemon_opts)
        result = write_daemon_json()
        assert result == daemon_opts_additions


@patch("charmhelpers.core.hookenv.config")
def test_set_daemon_json(config):
    daemon_opts = {
        "log-driver": "json-file",
        "log-opts": {"max-size": "10m", "max-file": "100"},
    }

    charm_config = {"daemon-opts": json.dumps(daemon_opts)}

    def mock_config(key):
        return charm_config[key]

    config.side_effect = mock_config

    # Test that charm can't override a config value
    assert set_daemon_json("log-driver", "new value") is False

    with patch("builtins.open", mock_open(), create=True):
        result = set_daemon_json("log-driver", "json-file")
        assert result["log-driver"] == "json-file"
        result = set_daemon_json("my-extra-config", "value")
        assert result["my-extra-config"] == "value"


@patch("charmhelpers.core.unitdata.kv")
def test_delete_daemon_json(kv):
    daemon_opts_additions = {"foo": "bar"}

    with patch("charms.layer.docker.write_daemon_json"):
        kv.return_value.get.return_value = {}
        assert delete_daemon_json("foo") is False

        kv.reset_mock()
        kv.return_value.get.return_value = daemon_opts_additions
        assert delete_daemon_json("foo") is True
        kv().set.assert_called_once_with("daemon-opts-additions", {})


@patch("charms.layer.docker.write_daemon_json")
@patch("charms.layer.docker.render")
@patch("charms.layer.docker.determine_apt_source")
@patch("charms.layer.docker.hookenv")
@patch("charms.layer.docker.DockerOpts")
def test_render_configuration_template_no_proxy(
    mock_docker_opts, mock_hookenv, mock_determine_apt, mock_render, mock_write_daemon
):
    """Test if the render_configuration_template produced the right dict."""
    mock_determine_apt.return_value = "apt"
    mock_docker_opts.return_value.to_s.return_value = ""
    env_proxy = {
        "http_proxy": "",
        "https_proxy": "",
        "NO_PROXY": "localhost, 10.0.0.0/30",
    }

    charm_config = {
        "docker-opts": "",
        "http_proxy": "",
        "https_proxy": "",
        "no_proxy": "",
    }
    mock_hookenv.config.side_effect = lambda *args: (
        charm_config[args[0]] if args else charm_config
    )
    mock_hookenv.config.return_value = charm_config
    mock_hookenv.env_proxy_settings.return_value = env_proxy

    render_configuration_template(service=True)

    config = mock_render.call_args_list[1][0][2]
    assert config["no_proxy"] == "localhost,10.0.0.0/30"


@patch("charms.layer.docker.write_daemon_json")
@patch("charms.layer.docker.render")
@patch("charms.layer.docker.determine_apt_source")
@patch("charms.layer.docker.hookenv")
@patch("charms.layer.docker.DockerOpts")
def test_render_configuration_template_empty_no_proxy(
    mock_docker_opts, mock_hookenv, mock_determine_apt, mock_render, mock_write_daemon
):
    """Test if the render_configuration_template produced the right dict."""
    mock_determine_apt.return_value = "apt"
    mock_docker_opts.return_value.to_s.return_value = ""
    env_proxy = {
        "http_proxy": "",
        "https_proxy": "",
        "NO_PROXY": "",
    }

    charm_config = {
        "docker-opts": "",
        "http_proxy": "",
        "https_proxy": "",
        "no_proxy": "",
    }
    mock_hookenv.config.side_effect = lambda *args: (
        charm_config[args[0]] if args else charm_config
    )
    mock_hookenv.config.return_value = charm_config
    mock_hookenv.env_proxy_settings.return_value = env_proxy

    render_configuration_template(service=True)

    config = mock_render.call_args_list[1][0][2]
    assert config["no_proxy"] == ""
