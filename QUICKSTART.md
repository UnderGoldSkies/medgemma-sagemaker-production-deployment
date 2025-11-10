# ⚡ 5-Minute Quick Start

The absolute fastest way to deploy MedGemma.

## Prerequisites

- AWS Account configured
- Python 3.12+
- HuggingFace token ready

## Steps

### 1. Install Dependencies (1 min)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r config/requirements.txt
```

### 2. Configure (2 min)

```bash
cp config/.env.example config/.env
# Edit config/.env with your settings
```

### 3. Validate (1 min)

```bash
python setup/test_aws_connections.py
```

All checks should be ✅ green.

### 4. Deploy (8 min)

```bash
python scripts/deploy.py
```

Wait for "Deployment Complete!" message.

### 5. Test (30 sec)

```bash
python tests/test_endpoint.py
```

## Done! 🎉

**Next**: Read the [full README](README.md) for details.

**Cleanup**: `python scripts/cleanup.py` (stops billing)

## Troubleshooting

- **Error?** Run `python scripts/check_logs.py`
- **Stuck?** Check [README](README.md#-troubleshooting)
