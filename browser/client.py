import subprocess
import time
import json
import sys

from pathlib import Path
from urllib.parse import urlparse

ITERATIONS = 1
RETRIES = 1

fb_urls = [
    # 'https://scontent.xx.fbcdn.net/speedtest-0B',
    # 'https://scontent.xx.fbcdn.net/speedtest-1KB',
    # 'https://scontent.xx.fbcdn.net/speedtest-10KB',
    # 'https://scontent.xx.fbcdn.net/speedtest-100KB',
    # 'https://scontent.xx.fbcdn.net/speedtest-500KB',
    # 'https://scontent.xx.fbcdn.net/speedtest-1MB',
    # 'https://scontent.xx.fbcdn.net/speedtest-2MB',
    # 'https://scontent.xx.fbcdn.net/speedtest-5MB',
    'https://scontent.xx.fbcdn.net/speedtest-10MB',
]

cloudfare_urls = [
    'https://cloudflare-quic.com/1MB.png',
    'https://cloudflare-quic.com/5MB.png',
]

ms_urls = [
    'https://quic.westus.cloudapp.azure.com/1MBfile.txt',
    'https://quic.westus.cloudapp.azure.com/5000000.txt',
    'https://quic.westus.cloudapp.azure.com/10000000.txt',
]

f5_urls = [
    'https://f5quic.com:4433/50000',
    'https://f5quic.com:4433/5000000',
    'https://f5quic.com:4433/10000000',
]


def query(urls: list, client: str, loss: int):
    for h in ['h3']:
        for url in urls:
            times = {
                'total': []
            }

            url_obj = urlparse(url)
            url_host = url_obj.netloc
            url_path = url_obj.path[1:]

            results_dir = Path.joinpath(
                Path.cwd(), 'har', 'loss_{}'.format(loss), client, h, url_host)
            Path(results_dir).mkdir(parents=True, exist_ok=True)
            results_file = Path.joinpath(
                results_dir, '{}.json'.format(url_path))

            try:
                with open(results_file, 'r') as f:
                    times = json.load(f)
            except:
                pass

            if url_host == 'f5quic.com:4433' and h == 'h2':
                continue

            for i in range(ITERATIONS):
                print('{} - {} - Iteration: {}'.format(h, url, i))

                for retry in range(RETRIES):
                    if retry > 0:
                        print('Retrying')

                    start = time.time()
                    output = run_process(client, h, url)

                    if output is None:
                        break

                    if output == 'success' or str(output.stderr).count('Operation timed out') == 0:
                        # Python measures time in seconds
                        elapsed = time.time() - start
                        elapsed *= 1000
                        times['total'].append(elapsed)
                        break

                    if retry == RETRIES - 1:
                        raise "Failed retries"

            with open(results_file, 'w') as f:
                print(times)
                json.dump(times, f)


def run_process(client: str, h: str, url: str):
    url_obj = urlparse(url)
    url_host = url_obj.netloc
    url_path = url_obj.path[1:]

    if client == 'curl':
        if h == 'h2':
            return subprocess.run(
                ['curl', '--output', '/dev/null',
                    '--connect-timeout', '5',
                    '--max-time', '20', '--http2', url],
                capture_output=True
            )
        else:
            return subprocess.run(
                ['curl', '--output', '/dev/null',
                    '--connect-timeout', '5',
                    '--max-time', '20', '--http3', url],
                capture_output=True
            )
    elif client == 'hq':
        if h == 'h2':
            return None
        else:
            if url_host.count(':') > 0:
                [host, port] = url_host.split(':')
            else:
                host = url_host
                port = 443

            subprocess.run(
                [
                    './hq',
                    '--log_response=false',
                    '--mode=client',
                    '--draft_version=27',
                    '--host={}'.format(host),
                    '--port={}'.format(port),
                    '--path=/{}'.format(url_path),
                    '--v=0',
                    '>',
                    '/dev/null'
                ]
            )

            return 'success'


def main():
    client = sys.argv[1]
    loss = int(sys.argv[2])

    for urls in [fb_urls]:
        query(urls, client, loss)


if __name__ == "__main__":
    main()
