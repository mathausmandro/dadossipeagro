# Abre o painel de Fertilizantes do MAPA num Chrome invisível e extrai produtos, garantias e contatos.
# Usa só a biblioteca padrão do Python (protocolo DevTools via WebSocket).
# Uso: python3 -I baixar_qlik.py <pasta_base>
import base64, json, os, socket, struct, subprocess, sys, time, urllib.request, shutil

BASE = sys.argv[1]
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
URL = 'https://mapa-indicadores.agricultura.gov.br/publico/extensions/Fertilizantes/Fertilizantes.html'
PORT = 9333
PERFIL = os.path.join(BASE, 'dados', 'chrome-perfil')
SAIDA = os.path.join(BASE, 'dados', 'qlik.json')


class WS:
    def __init__(self, url):
        host, rest = url[len('ws://'):].split('/', 1)
        h, p = host.split(':')
        self.s = socket.create_connection((h, int(p)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f'GET /{rest} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                        f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        self.extra = buf.split(b'\r\n\r\n', 1)[1]
        self.n = 0

    def _read(self, n):
        while len(self.extra) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk:
                raise ConnectionError('conexão fechada')
            self.extra += chunk
        d, self.extra = self.extra[:n], self.extra[n:]
        return d

    def send(self, obj):
        data = json.dumps(obj).encode()
        hdr = bytearray([0x81])
        n = len(data)
        if n < 126: hdr.append(0x80 | n)
        elif n < 65536: hdr += bytes([0x80 | 126]) + struct.pack('>H', n)
        else: hdr += bytes([0x80 | 127]) + struct.pack('>Q', n)
        mask = os.urandom(4)
        self.s.sendall(bytes(hdr) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        msg = b''
        while True:
            b1, b2 = self._read(2)
            n = b2 & 0x7f
            if n == 126: n = struct.unpack('>H', self._read(2))[0]
            elif n == 127: n = struct.unpack('>Q', self._read(8))[0]
            msg += self._read(n)
            if b1 & 0x80:
                return json.loads(msg)

    def call(self, method, params=None):
        self.n += 1
        my = self.n
        self.send({'id': my, 'method': method, 'params': params or {}})
        while True:
            r = self.recv()
            if r.get('id') == my:
                return r


def main():
    js = open(os.path.join(BASE, 'tools', 'extrair_qlik.js'), encoding='utf-8').read()
    shutil.rmtree(PERFIL, ignore_errors=True)
    chrome = subprocess.Popen([CHROME, '--headless=new', f'--remote-debugging-port={PORT}', f'--user-data-dir={PERFIL}',
                               '--no-first-run', '--no-default-browser-check', 'about:blank'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                pages = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/list'))
                page = next(p for p in pages if p['type'] == 'page')
                break
            except Exception:
                time.sleep(0.5)
        ws = WS(page['webSocketDebuggerUrl'])
        ws.call('Page.enable')
        ws.call('Page.navigate', {'url': URL})
        time.sleep(20)
        r = ws.call('Runtime.evaluate', {'expression': js, 'awaitPromise': True, 'returnByValue': True, 'timeout': 600000})
        val = r.get('result', {}).get('result', {}).get('value')
        if not val:
            raise RuntimeError('extração falhou: ' + json.dumps(r)[:500])
        d = json.loads(val)
        if len(d['produtos']) < 1000:
            raise RuntimeError(f"poucos produtos ({len(d['produtos'])}); painel pode ter mudado")
        open(SAIDA, 'w', encoding='utf-8').write(val)
        print(f"Qlik: {len(d['produtos'])} produtos, {len(d['contatos'])} contatos")
    finally:
        chrome.terminate()
        try: chrome.wait(10)
        except Exception: chrome.kill()
        shutil.rmtree(PERFIL, ignore_errors=True)


main()
