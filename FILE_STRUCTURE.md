# File Structure

```
medgemma-sagemaker-production-deployment/
│
├── 📖 README.md                   # Start here! Main tutorial
├── 📋 LICENSE                     # MIT license
│
├── 📁 config/                     # Your settings
│   ├── .env.example               # Copy this to .env
│   ├── requirements.txt           # Python packages
│   └── trust-policy.json          # AWS permissions
│
├── 📁 scripts/                    # Deployment & utility scripts
│   ├── deploy.py                  # ▶️  Deploy the model
│   ├── check_logs.py              # 📊 View activity
│   └── cleanup.py                 # 🧹 Stop billing
│
├── 📁 setup/                      # One-time setup
│   ├── setup_aws.sh               # ☁️  Configure AWS
│
├── 📁 src/                        # AI model code
│   └── inference.py               # How model works
│
├── 📁 tests/                      # Test files
│   ├── test_endpoint.py           # 🧪 Test deployment
│   ├── test_with_image.py         # 🖼️  Test with X-ray
│   └── test_images/               # Sample X-rays
│       ├── chest_xray.png
│       └── medical_image.png
│
├── 📁 docs/                       # Guides
│   ├── README.md                  # Documentation index
│   └── MODEL_SELECTION_GUIDE.md   # Pick the right model size
│
└── 📁 build/                      # Generated files
    ├── model.tar.gz               # (created during deploy)
    └── endpoint_info.txt          # (created during deploy)
```

## File Descriptions

### Root Files

| File | What It Does |
|------|--------------|
| `README.md` | **START HERE!** Main tutorial with 4 clear steps |
| `QUICKSTART.md` | 5-minute express version |
| `LICENSE` | Legal stuff (MIT license) |

### config/ - Your Settings

| File | What It Does |
|------|--------------|
| `.env.example` | Template - copy to `.env` and fill in your info |
| `requirements.txt` | Python packages needed |
| `trust-policy.json` | AWS permissions (don't edit) |

### scripts/ - Deployment & Utilities

| File | Command | What It Does |
|------|---------|--------------|
| `deploy.py` | `python scripts/deploy.py` | Deploy AI to AWS |
| `check_logs.py` | `python scripts/check_logs.py` | See what's happening |
| `cleanup.py` | `python scripts/cleanup.py` | **Delete everything (stops billing!)** |

### setup/ - One-Time Setup

| File | Command | What It Does |
|------|---------|--------------|
| `setup_aws.sh` | `bash setup/setup_aws.sh` | Configure AWS (creates bucket & role) |
| `setup_aws.sh` | `bash setup/setup_aws.sh` | Configure AWS resources |

### tests/ - Testing

| File | Command | What It Does |
|------|---------|--------------|
| `test_endpoint.py` | `python tests/test_endpoint.py` | Test with medical Q&A |
| `test_with_image.py` | `python tests/test_with_image.py` | Test with X-ray analysis |
| `test_images/` | - | Sample medical images for testing |

### src/ - AI Model Code

| File | What It Does |
|------|--------------|
| `inference.py` | The "brain" - loads model and answers questions |

### docs/ - Learning Materials

| File | For Who |
|------|---------|
| `MODEL_SELECTION_GUIDE.md` | Choose between 4B/27B models |
| `README.md` | 📖 Index of all docs |

## Typical Workflow

```
1. First Time:
   └── setup/setup_aws.sh              # Configure AWS
   └── setup/                         # One-time setup

2. Deploy:
   └── scripts/deploy.py               # Deploy AI (~8 min)

3. Test:
   └── tests/test_endpoint.py          # Test it works
   └── tests/test_with_image.py        # Test with X-ray

4. Monitor:
   └── scripts/check_logs.py           # View activity

5. Done:
   └── scripts/cleanup.py              # Stop billing!
```

## Directory Purposes

### `/scripts` - Actions you perform
- Deploy the model
- Clean up resources
- Check logs and status

### `/setup` - One-time configuration
- Set up AWS
- Validate connections
- Create IAM roles

### `/tests` - Verify functionality
- Test endpoints
- Test with sample data
- Validate deployments

### `/src` - Source code
- Model inference logic
- Core functionality

## Important Files to Edit

### You MUST edit:
- `config/.env` - Your AWS and HuggingFace settings

### You might edit:
- `tests/test_endpoint.py` - Try different questions
- `tests/test_endpoint.py` - Text + image smoke test

### Never edit:
- `config/trust-policy.json` - AWS needs this exactly as is
- `src/inference.py` - Unless you know what you're doing
- Files in `build/` - Auto-generated

---

**Lost?** Check the [README](README.md) or docs/README.md
