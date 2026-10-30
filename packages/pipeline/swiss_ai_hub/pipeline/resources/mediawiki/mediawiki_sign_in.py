from typing import Annotated, Literal
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, Tag
from requests import Response

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError

MediaWikiAuthMethod = Literal["anonymous", "bot_password", "web_form", "oauth"]

_LOGIN_PAGE = "index.php?title=Special:UserLogin"
_MAX_REDIRECTS = 10
# The login form names its fields after the authentication provider: MediaWiki's own uses wpName/wpPassword, while
# extensions such as PluggableAuth (LDAP, SAML gateways) render username/password.
_USERNAME_FIELDS = ("wpName", "username")
_PASSWORD_FIELDS = ("wpPassword", "password")
_REDIRECT_TO_GET = {301, 302, 303}


class MediaWikiSignIn:
    """Signs a client's session in to the wiki, so its cookies carry the account into every later request.

    Credentials are posted through the bare session, never through dlt's ``RESTClient``, which logs a request's form
    data at debug level. Whether the session really reads as the account is checked by ``MediaWikiPreflight`` for every
    method, because a wiki answers a failed sign-in in many ways and an anonymous session reads only public pages.
    An OAuth access token needs no sign-in: the client sends it with every request.
    """

    @classmethod
    def sign_in(
        cls,
        client: Annotated[MediaWikiClient, "Client whose session is signed in"],
        method: Annotated[MediaWikiAuthMethod, "How the wiki takes credentials"],
        username: Annotated[str, "Account name; User@BotName for a bot password"],
        password: Annotated[str, "Account password or bot password"],
    ) -> None:
        match method:
            case "anonymous" | "oauth":
                return
            case "bot_password":
                cls._with_bot_password(client, username, password)
            case "web_form":
                cls._with_web_form(client, username, password)

    @staticmethod
    def _with_bot_password(client: MediaWikiClient, username: str, password: str) -> None:
        """``action=login`` takes only bot passwords (Special:BotPasswords); a main-account password is refused."""
        answer = client.session.post(
            client.api_url,
            data={
                "action": "login",
                "lgname": username,
                "lgpassword": password,
                "lgtoken": client.token("login"),
                "format": "json",
                "formatversion": 2,
            },
            hooks={"response": [client.raise_for_error]},
            allow_redirects=False,
        ).json()
        login = answer.get("login") or {}
        if login.get("result") != "Success":
            raise ValueError(
                f"MediaWiki at {client.site_url} refused the bot password of {username}: "
                f"{login.get('reason') or login.get('result')}. A bot password is created at Special:BotPasswords and "
                "signs in as User@BotName; a wiki whose sign-in goes through an extension takes the web form instead."
            )

    @classmethod
    def _with_web_form(cls, client: MediaWikiClient, username: str, password: str) -> None:
        """Fills in the wiki's own login page, for wikis whose sign-in an extension handles and the API cannot reach.

        Every hidden field of the form is sent back as rendered, which carries the login token and whatever the
        authentication provider needs. A page that still shows the form afterwards refused the credentials.
        """
        page = cls._follow(client, "GET", urljoin(f"{client.site_url}/", _LOGIN_PAGE))
        form = cls._login_form(page)
        if form is None:
            raise ValueError(f"MediaWiki at {client.site_url} shows no login form at {page.url}.")
        fields = {
            field["name"]: field.get("value", "") for field in form.find_all(["input", "button"]) if field.get("name")
        }
        fields[cls._field(fields, _USERNAME_FIELDS, client)] = username
        fields[cls._field(fields, _PASSWORD_FIELDS, client)] = password
        answer = cls._follow(client, "POST", urljoin(page.url, str(form.get("action") or page.url)), fields)
        if cls._login_form(answer) is not None:
            raise ValueError(f"MediaWiki at {client.site_url} refused the user name or password of {username}.")

    @staticmethod
    def _login_form(page: Response) -> Tag | None:
        return BeautifulSoup(page.text, "html.parser").find("form", attrs={"name": "userlogin"})

    @staticmethod
    def _field(fields: dict[str, str], candidates: tuple[str, ...], client: MediaWikiClient) -> str:
        name = next((candidate for candidate in candidates if candidate in fields), None)
        if name is None:
            raise ValueError(f"The login form of {client.site_url} has none of the fields {', '.join(candidates)}.")
        return name

    @staticmethod
    def _follow(client: MediaWikiClient, method: str, url: str, data: dict[str, str] | None = None) -> Response:
        """Follows redirects by hand, and only on the wiki's own host: the address guard checked that host alone, and
        the session's cookies must not travel elsewhere. Upgrading to https is followed, downgrading is not."""
        site = urlsplit(client.site_url)
        for _ in range(_MAX_REDIRECTS + 1):
            target = urlsplit(url)
            if target.netloc != site.netloc or target.scheme not in {site.scheme, "https"}:
                raise ValueError(
                    f"Signing in to {client.site_url} redirected to {url}; only the wiki's host is followed."
                )
            response = client.session.request(method, url, data=data, allow_redirects=False)
            if not response.is_redirect:
                if not response.ok:
                    raise MediaWikiRequestError.from_response(response)
                return response
            url = urljoin(url, response.headers["Location"])
            if response.status_code in _REDIRECT_TO_GET:
                method, data = "GET", None
        raise ValueError(f"Signing in to {client.site_url} redirected more than {_MAX_REDIRECTS} times.")
