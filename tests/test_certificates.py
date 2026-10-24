import ssl
from importlib.metadata import version

import certifi


def test_installed_certifi_excludes_compromised_root():
    assert tuple(map(int, version("certifi").split("."))) >= (2026, 10, 19)
    context = ssl.create_default_context(cafile=certifi.where())
    common_names = {
        value
        for certificate in context.get_ca_certs()
        for rdn in certificate["subject"]
        for key, value in rdn
        if key == "commonName"
    }
    assert "emSign ECC Root CA - G3" not in common_names
