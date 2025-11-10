# Documentation

## For Beginners

- **[Simple Deployment Guide](SIMPLE_DEPLOYMENT_GUIDE.md)** - Start here! Complete walkthrough for beginners

## Reference

- **[Full Deployment Guide](DEPLOYMENT.md)** - Detailed technical documentation

## Quick Links

### Getting Started
1. Read the [main README](../README.md)
2. Follow the [Simple Deployment Guide](SIMPLE_DEPLOYMENT_GUIDE.md)
3. Check [Troubleshooting](#troubleshooting) if you get stuck

### Common Tasks

**Deploy the model:**
```bash
python scripts/deploy.py
```

**Test it:**
```bash
python tests/test_endpoint.py
```

**Stop billing:**
```bash
python scripts/cleanup.py
```

**View logs:**
```bash
python scripts/check_logs.py
```

### Troubleshooting

**Deployment fails?**
- Run `python setup/test_aws_connections.py`
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

**Need more help?** Open an issue or check the troubleshooting section in the [main README](../README.md).
