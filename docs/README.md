# Documentation

## Quick Links

### Getting Started
1. Read the [main README](../README.md)
3. Check [Troubleshooting](#troubleshooting) if you get stuck

### Common Tasks

**Deploy the model:** `python scripts/deploy.py`

**Test it:** `python tests/test_endpoint.py`

**Stop billing:** `python scripts/cleanup.py`

**View logs:** `python scripts/check_logs.py`

### Troubleshooting

**Deployment fails?**
- Check `python scripts/check_logs.py`

**Endpoint errors?**
- View logs: `python scripts/check_logs.py --tail 50`
- Verify status: `aws sagemaker describe-endpoint --endpoint-name $(cat build/endpoint_info.txt)`

**Forgot to cleanup?**
- Run `python scripts/cleanup.py` immediately

### Cost Management

- **While running**: ~$1.50/hour
- **After cleanup**: $0/hour (just pennies for S3)
- **Check costs**: [AWS Billing Console](https://console.aws.amazon.com/billing/)

---

## 🤖 About MedGemma

This tutorial deploys **MedGemma 4B Multimodal**, a medical AI model from Google Health AI built on Gemma 3 that can:
- ✅ Answer medical questions
- ✅ Analyze medical images (X-rays, CT scans, MRIs)
- ✅ Process extremely long documents (128K+ tokens)
- ✅ Provide clinical insights
- ✅ Support multi-turn conversations

**Model Details:**
- **Architecture**: Gemma 3 decoder-only transformer
- **Parameters**: 4 billion
- **Context**: 128K+ tokens (equivalent to ~300-page book!)
- **Modalities**: Text + Vision (multimodal)
- **Released**: May 2025 (Version 1.0.1)
- **Source**: [Google Health AI](https://developers.google.com/health-ai-developer-foundations/medgemma)
- **Paper**: [MedGemma Technical Report](https://arxiv.org/abs/2507.05201)

**Cost**: ~$1.52/hour while running (you'll learn how to stop it!)

**Need more help?** Open an issue or check the troubleshooting section in the [main README](../README.md).
