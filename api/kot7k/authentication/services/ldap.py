from django.contrib.auth import get_user_model
from ldap3 import Connection, Server, Tls, SUBTREE
from ldap3.utils.conv import escape_filter_chars

from kot7k.organizations.services import IdentityProviderConnectionError, resolve_provider_secret


def _server(configuration):
    uri = str(configuration["server_uri"])
    use_ssl = uri.lower().startswith("ldaps://")
    host = uri.split("://", 1)[-1].split(":", 1)[0]
    port = int(configuration.get("port") or (636 if use_ssl else 389))
    return Server(host, port=port, use_ssl=use_ssl, connect_timeout=10, tls=Tls())


def authenticate_ldap(provider, email, password):
    config = provider.configuration
    try:
        bind_password = resolve_provider_secret(provider)
        service = Connection(
            _server(config), user=config.get("bind_dn", ""), password=bind_password,
            auto_bind=True, receive_timeout=10,
        )
        search_filter = str(config["user_filter"]).replace(
            "{email}", escape_filter_chars(email)
        )
        found = service.search(
            str(config["base_dn"]), search_filter, search_scope=SUBTREE,
            attributes=[str(config["email_attribute"])], size_limit=2,
        )
        if not found or len(service.entries) != 1:
            service.unbind()
            return None
        user_dn = service.entries[0].entry_dn
        service.unbind()
        user_connection = Connection(
            _server(config), user=user_dn, password=password,
            auto_bind=True, receive_timeout=10,
        )
        user_connection.unbind()
    except Exception:
        # LDAP deliberately returns the same authentication result for lookup,
        # bind, and connectivity failures to avoid account enumeration.
        return None

    return get_user_model().objects.filter(email=email, is_active=True).first()
