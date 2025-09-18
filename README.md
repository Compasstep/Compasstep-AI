# CompassStep AI
CompassStep의 레퍼런스 탐색, 평판 분석, 가사 감정 분석에 사용되는 AI입니다.

# Setup Guide (MacOS)

### 1. Install `uv`

```shell
curl -Ls https://astral.sh/uv/install.sh | bash
```

### 2. Add `uv` to PATH

```shell
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

### 3. Apply configuration

```shell
source ~/.zshrc
```

### 4. Verify installation

```shell
uv --version
```

### 5. Create a virtual environment

```shell
uv venv --python 3.12
```

### 6. Add desired packages

```shell
uv add <package_name>
```

### 7. Sync dependencies (update `pyproject.toml`)

```shell
uv sync
```

### 8. Run FastAPI server

```shell
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

---

이제 `shell` 태그가 붙어 있어서, GitHub나 다른 마크다운 뷰어에서도 명령어 하이라이팅이 잘 보일 거예요.

혹시 제가 이 README에 **"Requirements" (Python 3.12, uv) 섹션**이나 **"Quick Start" 섹션**까지 추가해드릴까요?
