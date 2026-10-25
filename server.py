# This quickstart uses Flask, but the Auth0 Python SDK works with any
# framework. For FastAPI, see: https://github.com/auth0/auth0-fastapi
import json
import requests
from os import environ as env
from urllib.parse import urlparse

from auth0_server_python.auth_server.server_client import ServerClient
from auth0_server_python.auth_types import LogoutOptions, StartInteractiveLoginOptions, StateData, TransactionData
from auth0_server_python.store.abstract import AbstractDataStore
from dotenv import load_dotenv
from flask import Flask, after_this_request, redirect, request, render_template_string, session
from markupsafe import escape
from auth0_api import get_management_token

load_dotenv()

app = Flask(__name__)
app.secret_key = "ejemploclaveuwu123"

# highlight-start stores
# The SDK requires two stores: one for session data (user profile, tokens)
# and one for short-lived OAuth flow data (PKCE verifiers, state params).
# Both extend AbstractDataStore which provides encrypt() and decrypt().
# This implementation stores data in encrypted cookies, but you could
# also use Redis, PostgreSQL, or any other backend by implementing
# the same set/get/delete interface.
class CookieStore(AbstractDataStore):
    def __init__(self, secret, cookie_name, max_age, model):
        super().__init__({"secret": secret})
        self.cookie_name = cookie_name
        self.max_age = max_age
        self.model = model

    async def set(self, identifier, state, **_):
        @after_this_request
        def apply(response):
            data = state.model_dump() if hasattr(state, "model_dump") else state
            response.set_cookie(
                self.cookie_name,
                self.encrypt(identifier, data),
                httponly=True,
                samesite="Lax",
                secure=not env.get("APP_BASE_URL", "").startswith("http://"),
                max_age=self.max_age,
            )
            return response

    async def get(self, identifier, options=None):
        try:
            if isinstance(options, dict):
                req = options.get("request")
            else:
                req = options

            encrypted = req.cookies.get(self.cookie_name) if req else None

            return self.model.model_validate(self.decrypt(identifier, encrypted)) if encrypted else None
        except Exception:
            app.logger.warning("Failed to decrypt cookie %s", self.cookie_name, exc_info=True)
            return None

    async def delete(self, *_, **__):
        @after_this_request
        def apply(response):
            response.delete_cookie(self.cookie_name)
            return response
# highlight-end stores


# highlight-start auth-client
def auth0():
    session_secret = env.get("AUTH0_SECRET")

    return ServerClient(
        domain=env.get("AUTH0_DOMAIN"),
        client_id=env.get("AUTH0_CLIENT_ID"),
        client_secret=env.get("AUTH0_CLIENT_SECRET"),
        redirect_uri=env.get("APP_BASE_URL") + "/callback",
        authorization_params={"scope": "openid profile email"},
        secret=session_secret,
        state_store=CookieStore(session_secret, "_a0_session", 259200, StateData),  # 3 days
        transaction_store=CookieStore(session_secret, "_a0_tx", 300, TransactionData),  # 5 min
    )
# highlight-end auth-client


@app.route("/")
async def home():
    # highlight-start session
    user = await auth0().get_user({"request": request})
    # highlight-end session

    head = "<!DOCTYPE html><title>Auth0 Python Sample</title>"

    if user:
        user_id = user.get("sub")

        if user_id:
            token = get_management_token()
            domain = env.get("AUTH0_DOMAIN")

            url = f"https://{domain}/api/v2/users/{user_id}"
            headers = {"Authorization": f"Bearer {token}"}

            res = requests.get(url, headers=headers)

            if res.status_code == 200:
                datos = res.json()
                user["user_metadata"] = datos.get("user_metadata", {})

        return f"""
            {head}
            <p>Logged in as {escape(user.get("email", ""))}</p>
            <h1>User Profile</h1>
            <pre>{escape(json.dumps(user, indent=2))}</pre>
            <a href="/logout">Logout</a>
            <a href="/editar_perfil">Edit</a>
        """

    return f"""
        {head}
        <a href="/login?screen_hint=signup">Signup</a>
        <a href="/login">Login</a>
    """


@app.route("/login")
async def login():
    # highlight-start login
    url = await auth0().start_interactive_login(
        options=StartInteractiveLoginOptions(
            authorization_params=dict(request.args),
        ),
        store_options={"request": request},
    )
    # highlight-end login
    return redirect(url)


@app.route("/callback")
async def callback():
    try:
        # highlight-start callback
        await auth0().complete_interactive_login(
            url=request.url, store_options={"request": request},
        )
        # highlight-end callback
        return redirect("/")
    except Exception:
        app.logger.exception("Callback error")
        return "Something went wrong. Check server logs for details.", 400


@app.route("/logout")
async def logout():
    # highlight-start logout
    url = await auth0().logout(
        options=LogoutOptions(return_to=env.get("APP_BASE_URL")),
        store_options={"request": request},
    )
    # highlight-end logout
    return redirect(url)

@app.route("/editar_perfil", methods=["GET", "POST"])
async def edit_metadata():
    user = await auth0().get_session({"request": request})
    if not user or "user" not in user:
        return redirect("/login")

    user_id = user["user"].get("sub")

    token = get_management_token()
    domain = env.get("AUTH0_DOMAIN")
    url = f"https://{domain}/api/v2/users/{user_id}"

    if request.method == "POST":
        tipo_documento = request.form.get("tipo_documento")
        nro_documento = request.form.get("nro_documento")
        direccion = request.form.get("direccion")
        telefono = request.form.get("telefono")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "user_metadata": {
                "tipo_documento": tipo_documento,
                "nro_documento": nro_documento,
                "direccion": direccion,
                "telefono": telefono    
            }
        }

        res = requests.patch(url, json=payload, headers=headers)

        if res.status_code == 200:
            if "user_metadata" not in user:
                user["user_metadata"] = {}
            user["user_metadata"]["tipo_documento"] = tipo_documento
            user["user_metadata"]["nro_documento"] = nro_documento
            user["user_metadata"]["direccion"] = direccion
            user["user_metadata"]["telefono"] = telefono
            session["user"] = user

            print("¡Metadata guardada con éxito en Auth0 OwO!")
            return redirect("/")
        else:
            return f"Error al actualizar metadata en Auth0 UnU: {res.text}", res.status_code

    res = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    current_metadata = res.json().get("user_metadata", {})

    html = """
    <h2>Modificar Perfil (User Metadata)</h2>
    <form method="POST">
        <label>Tipo de documento:</label><br>
        <input type="text" name="tipo_documento" value="{{ metadata.get('tipo_documento', '') }}"><br><br>

        <label>Número de documento:</label><br>
        <input type="text" name="nro_documento" value="{{ metadata.get('nro_documento', '') }}"><br><br>

        <label>Dirección de residencia:</label><br>
        <input type="text" name="direccion" value="{{ metadata.get('direccion', '') }}"><br><br>

        <label>Teléfono:</label><br>
        <input type="text" name="telefono" value="{{ metadata.get('telefono', '') }}"><br><br>

        <button type="submit">Guardar cambios</button>
    </form>
    <br>
    <a href="/">Volver al inicio</a> 
    """
    return render_template_string(html, metadata=current_metadata)

if __name__ == "__main__":
    url = urlparse(env.get("APP_BASE_URL"))
    app.run(host=url.hostname, port=url.port or 5000)
