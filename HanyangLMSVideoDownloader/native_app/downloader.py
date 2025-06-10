import sys
import json
import subprocess
import shutil
import os
import traceback

# 로그 파일 경로: Local AppData 폴더
LOG_PATH = os.path.join(os.path.expanduser('~'), 'downloader_debug.log')

def log(message):
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(message + '\n')
    except Exception:
        pass  # 로그 실패 시 무시


def read_message():
    # 4바이트 메시지 길이 수신
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    length = int.from_bytes(raw_length, 'little')
    data = sys.stdin.buffer.read(length)
    return json.loads(data.decode('utf-8'))


def send_message(response):
    # stdout에만 네이티브 메시지 프로토콜로 출력
    try:
        encoded = json.dumps(response).encode('utf-8')
        sys.stdout.buffer.write(len(encoded).to_bytes(4, 'little'))
        sys.stdout.buffer.write(encoded)
        sys.stdout.flush()
    except Exception as e:  
        log(f'send_message error: {e}')


def install_ffmpeg_if_needed():
    if not shutil.which('ffmpeg'):
        log('Installing ffmpeg via choco...')
        subprocess.call(['choco', 'install', '-y', 'ffmpeg'], shell=True)
        log('ffmpeg install complete')


def run_ffmpeg(url):
    downloads = os.path.join(os.getenv('USERPROFILE'), 'Downloads')
    os.makedirs(downloads, exist_ok=True)
    output = os.path.join(downloads, 'screen.mp4')

    headers = (
        'Referer: https://hycms.hanyang.ac.kr/\r\n'
        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36\r\n'
    )
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file without asking
        '-headers', headers,
        '-i', url, 
        '-c', 'copy',
        output
    ]
    log(f'Running command: {cmd} in Downloads Folder')
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.getenv('USERPROFILE\\Downloads'),
        )
        log(f'ffmpeg stdout: {result.stdout.strip()}')
        if result.stderr:
            log(f'ffmpeg stderr: {result.stderr.strip()}')
    except Exception as e:
        log(f'ffmpeg execution error: {e}')


def main():
    try:
        log('Downloader started')
        install_ffmpeg_if_needed()
        log('Waiting for message...')
        while True:
            msg = read_message()
            if msg is None:
                log('No message, exiting')
                break
            url = msg.get('url')
            log(f'Received URL: {url}')
            run_ffmpeg(url)
            send_message({'status': 'done'})
            log('Response sent')
    except Exception as e:
        log('Unexpected error: ' + traceback.format_exc())

if __name__ == '__main__':
    main()