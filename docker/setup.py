#!/usr/bin/env python3
"""
Docker 배포 사전 설정 스크립트

실행 방법:
    python setup.py

기능:
    1. 시스템 환경 체크 (Docker, GPU, 포트 등)
    2. GPU 감지 → .env 파일에 USE_GPU 자동 설정
    3. .env 파일 생성 (없는 경우)
    4. docker-compose.yml GPU 설정 자동 활성화
"""

import subprocess
import sys
import os
import socket
import re
import shutil
from pathlib import Path


# =============================================================
# 설정
# =============================================================

REQUIRED_PORTS = {
    8000: "Django",
    9000: "FastAPI",
    8042: "Orthanc HTTP",
    8080: "OpenEMR",
    8081: "HAPI FHIR",
    6379: "Redis",
    6380: "FastAPI Redis",
    3306: "Django MySQL",
    3308: "OpenEMR MariaDB",
    5432: "HAPI PostgreSQL",
}


# =============================================================
# 색상 출력
# =============================================================

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")


def print_ok(msg, detail=""):
    detail_text = f" - {detail}" if detail else ""
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}{detail_text}")


def print_warn(msg, detail=""):
    detail_text = f" - {detail}" if detail else ""
    print(f"  {Colors.YELLOW}!{Colors.END} {msg}{detail_text}")


def print_fail(msg, detail=""):
    detail_text = f" - {detail}" if detail else ""
    print(f"  {Colors.RED}✗{Colors.END} {msg}{detail_text}")


def print_info(msg):
    print(f"  {Colors.CYAN}→{Colors.END} {msg}")


# =============================================================
# 유틸리티
# =============================================================

def run_command(cmd, timeout=10):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str)
        )
        return result.returncode == 0, result.stdout.strip()
    except:
        return False, ""


def check_port(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('127.0.0.1', port)) != 0
    except:
        return True


def get_script_dir():
    return Path(__file__).resolve().parent


def get_project_root():
    script_dir = get_script_dir()
    if script_dir.name == "docker":
        return script_dir.parent
    return script_dir


# =============================================================
# 체크 함수
# =============================================================

def check_docker():
    """Docker 설치 확인"""
    print_header("1. Docker 체크")

    # Docker
    success, output = run_command(["docker", "--version"])
    if not success:
        print_fail("Docker가 설치되지 않았습니다")
        print_info("https://docs.docker.com/get-docker/ 에서 설치하세요")
        return False
    print_ok("Docker", output.split(",")[0])

    # Docker Compose
    success, output = run_command(["docker", "compose", "version"])
    if not success:
        success, output = run_command(["docker-compose", "--version"])
    if not success:
        print_fail("Docker Compose가 설치되지 않았습니다")
        return False
    print_ok("Docker Compose", output.split("\n")[0] if output else "")

    # Docker 실행 상태
    success, _ = run_command(["docker", "info"])
    if not success:
        print_fail("Docker 서비스가 실행되지 않았습니다")
        print_info("Docker Desktop을 시작하세요")
        return False
    print_ok("Docker 서비스 실행 중")

    return True


def check_gpu():
    """GPU 환경 확인 및 CUDA 버전 반환"""
    print_header("2. GPU 체크")

    success, output = run_command(["nvidia-smi"])
    if not success:
        print_warn("NVIDIA GPU 없음", "CPU 모드로 설정됩니다")
        return None

    # CUDA 버전 추출
    cuda_version = None
    match = re.search(r"CUDA Version:\s*(\d+\.\d+)", output)
    if match:
        cuda_version = match.group(1)

    # GPU 이름 추출
    gpu_name = "Unknown"
    for line in output.split("\n"):
        if "NVIDIA" in line and "Driver" not in line:
            parts = line.split("|")
            if len(parts) >= 2:
                gpu_name = parts[1].strip().split()[0:3]
                gpu_name = " ".join(gpu_name)
                break

    print_ok(f"GPU 감지됨", gpu_name)
    print_ok(f"CUDA Version", cuda_version or "Unknown")

    # NVIDIA Container Toolkit 체크
    success, _ = run_command(
        ["docker", "run", "--rm", "--gpus", "all",
         "hello-world"],
        timeout=30
    )
    if success:
        print_ok("NVIDIA Container Toolkit", "Docker GPU 지원 확인됨")
    else:
        print_warn("NVIDIA Container Toolkit 필요")
        print_info("설치: apt install nvidia-container-toolkit && systemctl restart docker")

    return cuda_version


def check_ports():
    """포트 사용 가능 여부 확인"""
    print_header("3. 포트 체크")

    all_ok = True
    for port, service in REQUIRED_PORTS.items():
        if check_port(port):
            print_ok(f"Port {port}", f"{service} 사용 가능")
        else:
            print_fail(f"Port {port}", f"{service} 이미 사용 중")
            all_ok = False

    return all_ok


# =============================================================
# 설정 파일 업데이트
# =============================================================

def setup_env_file(use_gpu: bool, cuda_version: str = None):
    """환경 변수 파일 설정"""
    print_header("4. 환경 변수 설정")

    script_dir = get_script_dir()
    env_example = script_dir / ".env.example"
    env_file = script_dir / ".env"

    # .env 파일이 없으면 생성
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print_ok(".env 파일 생성됨", ".env.example에서 복사")
        else:
            print_fail(".env.example 파일이 없습니다")
            return False
    else:
        print_ok(".env 파일 존재")

    # .env 파일 읽기
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # USE_GPU 업데이트
    use_gpu_value = "true" if use_gpu else "false"
    if "USE_GPU=" in content:
        content = re.sub(r'USE_GPU=\w+', f'USE_GPU={use_gpu_value}', content)
        print_ok(f"USE_GPU={use_gpu_value}", "자동 설정됨")
    else:
        content += f"\nUSE_GPU={use_gpu_value}\n"
        print_ok(f"USE_GPU={use_gpu_value}", "추가됨")

    # 파일 저장
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # 경고: 수정 필요한 항목
    if "192.168.x.x" in content:
        print_warn("MAIN_VM_IP 설정 필요", "실제 IP로 변경하세요")
    if "your-" in content.lower():
        print_warn("기본 비밀번호 변경 필요", ".env 파일을 확인하세요")

    return True


def setup_docker_compose_gpu(enable_gpu: bool):
    """docker-compose.fastapi.yml GPU 설정"""
    print_header("5. Docker Compose GPU 설정")

    script_dir = get_script_dir()
    compose_file = script_dir / "docker-compose.fastapi.yml"

    if not compose_file.exists():
        print_fail("docker-compose.fastapi.yml 없음")
        return False

    with open(compose_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if enable_gpu:
        # GPU 섹션 주석 해제
        # deploy: 부터 capabilities: [gpu] 까지
        gpu_section_commented = """    # GPU Support - USE_GPU=true일 때 아래 주석 해제
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]"""

        gpu_section_enabled = """    # GPU Support - 활성화됨
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]"""

        if gpu_section_commented in content:
            content = content.replace(gpu_section_commented, gpu_section_enabled)
            print_ok("GPU 설정 활성화됨", "docker-compose.fastapi.yml")
        elif "# GPU Support - 활성화됨" in content:
            print_ok("GPU 설정 이미 활성화됨")
        else:
            print_warn("GPU 설정을 수동으로 활성화하세요")
    else:
        print_info("CPU 모드 - GPU 설정 변경 없음")

    with open(compose_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return True


# =============================================================
# 메인
# =============================================================

def main():
    print(f"""
{Colors.BOLD}{Colors.CYAN}{'='*60}
   Brain Tumor CDSS - Docker 배포 설정
{'='*60}{Colors.END}
""")

    errors = []

    # 1. Docker 체크
    if not check_docker():
        errors.append("Docker")

    # 2. GPU 체크
    cuda_version = check_gpu()
    use_gpu = cuda_version is not None

    # 3. 포트 체크
    if not check_ports():
        print_warn("일부 포트가 사용 중입니다. 충돌이 발생할 수 있습니다.")

    # 4. 환경 변수 설정
    if not setup_env_file(use_gpu, cuda_version):
        errors.append("환경 변수")

    # 5. Docker Compose GPU 설정
    setup_docker_compose_gpu(use_gpu)

    # 결과 요약
    print_header("설정 완료")

    if errors:
        print(f"\n  {Colors.RED}✗ 오류 발생: {', '.join(errors)}{Colors.END}")
        print(f"  {Colors.RED}  위 문제를 해결한 후 다시 실행하세요.{Colors.END}\n")
        sys.exit(1)

    print(f"\n  {Colors.GREEN}✓ 설정 완료!{Colors.END}\n")

    # 다음 단계 안내
    print(f"  {Colors.BOLD}다음 단계:{Colors.END}")
    print(f"  1. .env 파일에서 IP 주소와 비밀번호를 수정하세요")
    print(f"  2. 아래 명령어로 Docker를 실행하세요:\n")

    if use_gpu:
        print(f"     {Colors.CYAN}# FastAPI VM (GPU){Colors.END}")
        print(f"     docker compose -f docker-compose.fastapi.yml up -d --build\n")
    else:
        print(f"     {Colors.CYAN}# 메인 VM{Colors.END}")
        print(f"     docker compose -f docker-compose.yml \\")
        print(f"                    -f docker-compose.django.yml \\")
        print(f"                    -f docker-compose.emr.yml up -d --build\n")

        print(f"     {Colors.CYAN}# FastAPI VM (CPU){Colors.END}")
        print(f"     docker compose -f docker-compose.fastapi.yml up -d --build\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
