# Cloud Deployment Guide (24/7 Production)

**Deploy your trading bot to a cloud VM for reliable 24/7 paper/live trading.**

> 💡 **Just testing locally?** See [DEPLOYMENT.md](../DEPLOYMENT.md) for quick laptop setup instead.  
> This guide is for **production-grade 24/7 deployment** on cloud infrastructure.

This guide covers AWS, DigitalOcean, and Google Cloud setup. Choose based on your budget and experience level.

---

## 📋 Why Cloud Deployment?

**Laptop Limitations**:
- ❌ Must stay powered on and connected
- ❌ Vulnerable to Windows updates, power outages
- ❌ Can't travel with bot running
- ❌ Higher power consumption

**Cloud VM Benefits**:
- ✅ 24/7 uptime (99.9%+ SLA)
- ✅ Remote access from anywhere
- ✅ Automatic backups
- ✅ Professional infrastructure
- ✅ Low cost ($0-10/month)

---

## 🎯 Provider Comparison

| Provider | Cost/Month | Free Tier | Complexity | Best For |
|----------|------------|-----------|------------|----------|
| **DigitalOcean** | $6 | $200 credit (60 days) | ⭐ Easy | Beginners |
| **AWS EC2** | $0-8 | 12 months free | ⭐⭐ Medium | Experienced devs |
| **Google Cloud** | $0-7 | Always free tier | ⭐⭐ Medium | Google users |
| **Azure** | $10 | $200 credit (30 days) | ⭐⭐⭐ Complex | Enterprise |

**Recommended**: Start with **DigitalOcean** (simplest) or **AWS** (best free tier).

---

## 🚀 Option 1: DigitalOcean (Easiest)

**Specs**: 1GB RAM, 1 CPU, 25GB SSD - Perfect for trading bot  
**Cost**: $6/month (first 60 days free with $200 credit)

### Step 1: Create Account
1. Go to https://www.digitalocean.com/
2. Sign up (credit card required, $200 free credit for 60 days)
3. Verify email

### Step 2: Create Droplet
1. Click **"Create" → "Droplets"**
2. **Choose Region**: Frankfurt or London (closest to Ireland)
3. **Choose Image**: Ubuntu 22.04 LTS
4. **Droplet Size**: 
   - CPU: Regular
   - Plan: $6/month (1GB RAM, 1 vCPU)
5. **Authentication**: 
   - Select **"SSH Key"** (recommended) OR **"Password"**
   - If SSH: Follow prompt to generate and add your SSH key
6. **Hostname**: `trading-bot` (or any name you like)
7. Click **"Create Droplet"** (takes ~60 seconds)
8. **Copy the IP address** (e.g., `159.65.123.45`)

### Step 3: Connect to Droplet

**Windows (PowerShell)**:
```bash
# If you used password authentication
ssh root@YOUR_DROPLET_IP

# If you used SSH key
ssh -i C:\Users\YourName\.ssh\id_rsa root@YOUR_DROPLET_IP
```

**First connection**: Type `yes` when asked about fingerprint.

### Step 4: Install Bot

Once connected to your droplet:

```bash
# Update system
apt update && apt upgrade -y

# Install Python 3.10+
apt install python3.10 python3.10-venv python3-pip git -y

# Clone repository
cd /root
git clone https://github.com/SamitDharia/Autonomous-Trading-Agent.git
cd Autonomous-Trading-Agent

# Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Set Credentials

```bash
# Add to ~/.bashrc for persistence
echo 'export ALPACA_API_KEY="your_paper_key_here"' >> ~/.bashrc
echo 'export ALPACA_SECRET_KEY="your_paper_secret_here"' >> ~/.bashrc
source ~/.bashrc

# Verify
echo $ALPACA_API_KEY  # Should print your key
```

### Step 6: Deploy Bot

```bash
# Test run (single check)
cd /root/Autonomous-Trading-Agent
source .venv/bin/activate
python scripts/alpaca_rsi_bot.py --symbol TSLA

# If successful, run in background (loop mode)
nohup python scripts/alpaca_rsi_bot.py --symbol TSLA --loop --sleep-min 5 > bot.log 2>&1 &

# Save the process ID
echo $! > bot.pid
```

### Step 7: Monitor

```bash
# View live logs (Ctrl+C to exit)
tail -f bot.log

# Check if bot is running
ps aux | grep alpaca_rsi_bot

# View trading log
cat alpaca_rsi_log.csv

# Run performance analysis
python scripts/analyze_trading_log.py
```

### Step 8: Stop/Restart Bot

```bash
# Stop bot
kill $(cat bot.pid)

# Or force kill
pkill -f alpaca_rsi_bot

# Restart
cd /root/Autonomous-Trading-Agent
source .venv/bin/activate
nohup python scripts/alpaca_rsi_bot.py --symbol TSLA --loop --sleep-min 5 > bot.log 2>&1 &
echo $! > bot.pid
```

---

## 🚀 Option 2: AWS EC2 (Free Tier)

**Specs**: 1GB RAM, 1 vCPU - Good for testing  
**Cost**: FREE for 12 months (750 hrs/month), then ~$8/month

### Step 1: Create AWS Account
1. Go to https://aws.amazon.com/
2. Click **"Create an AWS Account"**
3. Enter email, password, account name
4. Add payment method (required, won't be charged during free tier)
5. Verify phone number
6. Select **"Basic Support (Free)"**

### Step 2: Launch EC2 Instance
1. Sign in to AWS Console
2. Search for **"EC2"** in top search bar
3. Click **"Launch Instance"**
4. **Name**: `trading-bot`
5. **AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
6. **Instance Type**: `t2.micro` (Free tier eligible - 1GB RAM)
7. **Key Pair**: 
   - Click **"Create new key pair"**
   - Name: `trading-bot-key`
   - Type: RSA
   - Format: `.pem` (for SSH)
   - **Download and save** the `.pem` file (you can't re-download it!)
8. **Network Settings**:
   - Allow SSH traffic from: Your IP (or Anywhere for ease)
9. **Storage**: 8 GB (default, free tier)
10. Click **"Launch Instance"**
11. Wait ~2 minutes, then click instance ID
12. **Copy "Public IPv4 address"** (e.g., `54.123.45.67`)

### Step 3: Connect to Instance

**Windows (PowerShell)**:
```bash
# Navigate to where you saved the .pem file
cd C:\Users\YourName\Downloads

# Set permissions (Windows may skip this)
icacls trading-bot-key.pem /inheritance:r
icacls trading-bot-key.pem /grant:r "%username%:R"

# Connect (replace with your IP)
ssh -i trading-bot-key.pem ubuntu@YOUR_EC2_IP
```

**First connection**: Type `yes` when asked about fingerprint.

### Step 4: Install Bot

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Git
sudo apt install python3.10 python3.10-venv python3-pip git -y

# Clone repository
cd ~
git clone https://github.com/SamitDharia/Autonomous-Trading-Agent.git
cd Autonomous-Trading-Agent

# Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Set Credentials

```bash
# Add to ~/.bashrc
echo 'export ALPACA_API_KEY="your_paper_key_here"' >> ~/.bashrc
echo 'export ALPACA_SECRET_KEY="your_paper_secret_here"' >> ~/.bashrc
source ~/.bashrc

# Verify
echo $ALPACA_API_KEY
```

### Step 6: Deploy Bot

```bash
# Test run
cd ~/Autonomous-Trading-Agent
source .venv/bin/activate
python scripts/alpaca_rsi_bot.py --symbol TSLA

# Run in background
nohup python scripts/alpaca_rsi_bot.py --symbol TSLA --loop --sleep-min 5 > bot.log 2>&1 &
echo $! > bot.pid
```

### Step 7: Monitor

Same as DigitalOcean (see above).

---

## 🚀 Option 3: Google Cloud (Always Free Tier)

**Specs**: 0.6GB RAM, 1 shared vCPU  
**Cost**: FREE (always free tier, no expiration)

### Step 1: Create Account
1. Go to https://cloud.google.com/
2. Click **"Get started for free"**
3. Sign in with Google account
4. Add payment method ($300 free credit for 90 days)
5. Accept terms

### Step 2: Create VM Instance
1. Go to **Console** → **Compute Engine** → **VM Instances**
2. Click **"Create Instance"**
3. **Name**: `trading-bot`
4. **Region**: `europe-west1` (Belgium, closest to Ireland)
5. **Zone**: Any
6. **Machine Type**: 
   - Series: E2
   - Machine type: **e2-micro** (0.25-1 vCPU, 1GB RAM) - Always free!
7. **Boot Disk**: 
   - OS: Ubuntu
   - Version: 22.04 LTS
   - Size: 30 GB (free tier allows up to 30GB)
8. **Firewall**: Allow HTTP/HTTPS traffic (optional)
9. Click **"Create"**
10. **Copy "External IP"** (e.g., `35.123.45.67`)

### Step 3: Connect to Instance

**Browser (Easiest)**:
1. In VM Instances list, click **"SSH"** button next to your instance
2. Opens browser-based terminal (no keys needed!)

**OR SSH from PowerShell**:
```bash
# First time: Install gcloud CLI
# Download from: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Connect
gcloud compute ssh trading-bot --zone=europe-west1-b
```

### Step 4: Install Bot

Same as DigitalOcean/AWS (see Step 4 above), but use `sudo` before `apt` commands:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3.10 python3.10-venv python3-pip git -y
# ... rest same as above
```

---

## 🔒 Security Best Practices

### 1. Firewall Configuration
**Only allow SSH from your IP** (not Anywhere):

**DigitalOcean**:
1. Droplet → Networking → Firewalls
2. Create firewall: Allow SSH only from your IP

**AWS**:
1. EC2 → Security Groups → Edit inbound rules
2. SSH: Source = My IP

**Google Cloud**:
1. VPC Network → Firewall → Create rule
2. Source IP ranges: Your IP only

### 2. Use SSH Keys (Not Passwords)

**Generate SSH key** (Windows PowerShell):
```bash
ssh-keygen -t rsa -b 4096 -f C:\Users\YourName\.ssh\trading_bot_key
```

Then add public key to your VM.

### 3. Keep Credentials Secure

**Never hardcode API keys in scripts!**

✅ Use environment variables (as shown above)  
❌ Don't commit credentials to Git  
❌ Don't share your `.pem` files

### 4. Regular Updates

```bash
# Weekly security updates
sudo apt update && sudo apt upgrade -y

# Monthly: Pull latest bot code
cd ~/Autonomous-Trading-Agent
git pull origin main
```

---

## 📊 Monitoring & Maintenance

### Daily Health Check

**Create monitoring script** (`~/check_bot.sh`):
```bash
#!/bin/bash
cd ~/Autonomous-Trading-Agent
source .venv/bin/activate

# Check if bot is running
if ! ps aux | grep -q "[a]lpaca_rsi_bot"; then
    echo "⚠️ Bot not running! Restarting..."
    nohup python scripts/alpaca_rsi_bot.py --symbol TSLA --loop --sleep-min 5 > bot.log 2>&1 &
    echo $! > bot.pid
else
    echo "✅ Bot is running"
fi

# Show performance
python scripts/analyze_trading_log.py
```

**Make executable and schedule**:
```bash
chmod +x ~/check_bot.sh

# Add to crontab (runs daily at 9 PM Ireland time)
crontab -e
# Add this line:
0 21 * * * ~/check_bot.sh >> ~/check_bot_daily.log 2>&1
```

### Auto-Restart on Reboot

```bash
# Edit crontab
crontab -e

# Add this line (starts bot on VM reboot)
@reboot cd ~/Autonomous-Trading-Agent && source .venv/bin/activate && nohup python scripts/alpaca_rsi_bot.py --symbol TSLA --loop --sleep-min 5 > bot.log 2>&1 &
```

### Download Logs Remotely

**From your laptop** (PowerShell):
```bash
# DigitalOcean/AWS
scp -i your_key.pem user@VM_IP:~/Autonomous-Trading-Agent/alpaca_rsi_log.csv ./

# Copy to local
# Then open in Excel or analyze locally
```

---

## 🐛 Troubleshooting

### Bot Won't Start
```bash
# Check error logs
tail -50 bot.log

# Common issues:
# 1. Credentials not set
echo $ALPACA_API_KEY  # Should print your key

# 2. Dependencies missing
source .venv/bin/activate
pip install -r requirements.txt

# 3. Port already in use (rare)
pkill -f alpaca_rsi_bot
```

### Can't Connect via SSH
1. Check VM is running (AWS/GCP/DO console)
2. Verify security group allows SSH from your IP
3. Confirm you're using correct key and username:
   - AWS: `ubuntu@IP`
   - DigitalOcean: `root@IP`
   - Google Cloud: `yourname@IP`

### Out of Memory
```bash
# Check memory usage
free -h

# If using >80%, upgrade VM:
# - DigitalOcean: Resize to $12/month (2GB)
# - AWS: Change to t2.small (~$17/month)
# - GCP: Switch to e2-small (~$14/month)
```

### SSL Certificate Errors
```bash
# Install certificates
sudo apt install ca-certificates -y
sudo update-ca-certificates
```

---

## 💰 Cost Optimization

### Free Tier Limits

**AWS** (12 months):
- 750 hours/month of t2.micro (= 24/7 for 1 instance)
- After 12 months: ~$8/month

**Google Cloud** (Forever):
- e2-micro always free (1 instance only)
- 30GB storage free
- **Can run trading bot forever at $0/month!**

**DigitalOcean**:
- $200 credit (60 days)
- After that: $6/month (cheapest option)

### Reduce Costs

1. **Stop VM during non-market hours** (9:30 PM - 2 PM Ireland):
   ```bash
   # Cron to stop at 9:30 PM
   30 21 * * * sudo shutdown -h now
   
   # Manually restart at 2:45 PM (from DO/AWS/GCP console)
   ```
   
2. **Use Google Cloud e2-micro** - Free forever!

3. **Delete snapshots/volumes** you don't need

---

## 🎯 Recommended Setup (After Paper Trading)

**For live trading**, I recommend:

1. **Platform**: DigitalOcean ($6/month)
   - Simplest interface
   - Great support
   - Reliable uptime

2. **Monitoring**: 
   - Daily cron job runs `analyze_trading_log.py`
   - Email yourself results (add to script)
   - Check logs weekly via SSH

3. **Backups**:
   - Enable DigitalOcean automatic backups (+20% = $7.20/month total)
   - Or manual: `git pull` daily to sync code changes

4. **Alerts**:
   - Set up Discord/Slack webhook in bot (future enhancement)
   - Get notified of trades/errors on your phone

---

## ✅ Quick Reference

| Task | Command |
|------|---------|
| **Connect** | `ssh root@YOUR_IP` or `ssh -i key.pem ubuntu@YOUR_IP` |
| **Start bot** | `cd ~/Autonomous-Trading-Agent && source .venv/bin/activate && nohup python scripts/alpaca_rsi_bot.py --symbol TSLA --loop > bot.log 2>&1 &` |
| **Check status** | `ps aux \| grep alpaca_rsi_bot` |
| **View logs** | `tail -f ~/Autonomous-Trading-Agent/bot.log` |
| **Stop bot** | `pkill -f alpaca_rsi_bot` |
| **Analyze trades** | `cd ~/Autonomous-Trading-Agent && source .venv/bin/activate && python scripts/analyze_trading_log.py` |
| **Update code** | `cd ~/Autonomous-Trading-Agent && git pull origin main` |
| **Restart VM** | `sudo reboot` |

---

## 📅 Migration Timeline

**Week 6 (Current)**: Paper trading on laptop (5-7 days)  
**Week 7**: If results good → Deploy to DigitalOcean  
**Week 8+**: Monitor live trading, add multi-symbol support

---

## 🆘 Need Help?

- **DigitalOcean Docs**: https://docs.digitalocean.com/
- **AWS EC2 Docs**: https://docs.aws.amazon.com/ec2/
- **Google Cloud Docs**: https://cloud.google.com/compute/docs

**Common issues**: See [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section.

---

**Ready to deploy?** Start with laptop paper trading first, then migrate to cloud if results are promising!
