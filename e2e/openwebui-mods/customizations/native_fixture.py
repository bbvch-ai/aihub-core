import hashlib
import hmac
import json
import os
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
from starlette.responses import JSONResponse
from starlette.routing import Route

Path(os.environ['DATA_DIR']).mkdir(parents=True, exist_ok=True)
from aihub_mods.main import app, host
from aihub_mods.mod_compiler import ModCompiler
from open_webui.models.users import Users
from open_webui.utils.auth import create_token

compatibility = json.loads(host.compatibility)
publications = {}
sources = {}
tokens = {}


def source_archive(files):
    output = BytesIO()
    with ZipFile(output, 'w') as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()


async def respond(request):
    assert request.headers['authorization'] == 'Bearer ' + host.client.api_key
    email = request.headers['x-openwebui-user-email']
    name = request.headers['x-openwebui-user-name']
    signature = hmac.new(host.client.signing_secret, f'name:{name},email:{email}'.encode(), hashlib.sha256).hexdigest()
    assert hmac.compare_digest(request.headers['x-openwebui-signature'], signature)
    assert email in {'mods@example.test', 'mods-user@example.test'}
    parts = request.url.path.split('/')
    tenant = parts[3]
    if tenant not in ('one', 'active'):
        return httpx.Response(403)
    if request.url.path.endswith('/configuration'):
        snapshot = {'tenant_id': 'one', 'compatibility': compatibility,
                    'configuration': {'mods': [{'mod_id': name, 'publication': revision, 'enabled': True,
                                               'settings': {'text': {'en': 'AI can make mistakes. Please verify answers.', 'de': 'KI kann Fehler machen. Bitte überprüfen Sie die Antworten.'}}}
                                              for name, (revision, _) in publications.items()]}}
        snapshot['revision'] = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        return httpx.Response(200, json=snapshot)
    for revision, archive in publications.values():
        if request.url.path.endswith(f'/publications/{revision}/source'):
            return httpx.Response(200, content=sources[revision], headers={'Content-Type': 'application/zip'})
        if request.url.path.endswith(f'/publications/{revision}/frontend'):
            return httpx.Response(200, content=archive, headers={'Content-Type': 'application/zip'})
    return httpx.Response(404)


previous = app.router.lifespan_context


@asynccontextmanager
async def lifespan(application):
    await host.client.http.aclose()
    host.client.http = httpx.AsyncClient(base_url='http://hub', transport=httpx.MockTransport(respond))
    compiler = ModCompiler(Path('/tmp/customizations-compiler'))
    for name in ['account-menu', 'chat-disclaimer', 'locale-recovery', 'speech-recovery', 'pdf-export-guard', 'streaming-indicator']:
        root = Path('/bundled') / name
        files = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}
        mod_id = json.loads(files['mod.json'])['id']
        source = source_archive(files)
        publication = await compiler.compile(source)
        revision = hashlib.sha256(publication).hexdigest()
        publications[mod_id] = (revision, publication)
        sources[revision] = source
    if not await Users.get_user_by_id('mods-user'):
        await Users.insert_new_user(id='mods-user', name='Mods test', email='mods@example.test', role='admin')
    if not await Users.get_user_by_id('mods-regular-user'):
        await Users.insert_new_user(id='mods-regular-user', name='Regular user', email='mods-user@example.test', role='user')
    tokens['admin'] = create_token({'id': 'mods-user'})
    tokens['user'] = create_token({'id': 'mods-regular-user'})
    async with previous(application) as state:
        yield state


app.router.lifespan_context = lifespan


async def bridge(request):
    return JSONResponse({'parentOrigin': os.environ['TEST_PARENT_ORIGIN']})


async def credentials(request):
    if request.headers.get('authorization') != f"Bearer {os.environ['SCIM_TOKEN']}":
        return JSONResponse({}, status_code=403)
    role = request.query_params.get('role', 'admin')
    if role not in tokens:
        return JSONResponse({}, status_code=400)
    return JSONResponse({'token': tokens[role]})


app.router.routes.insert(0, Route('/static/aihub-mods.json', bridge))
app.router.routes.insert(0, Route('/__test__/credentials', credentials))
