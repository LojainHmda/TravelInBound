# Ubuntu VM Deployment - Where to Run Each Command

## Overview

You need to run commands in TWO places:
1. **On your LOCAL machine (Windows)** - To upload files and connect
2. **On the REMOTE VM (Ubuntu)** - To deploy the application

---

## Step-by-Step: Where to Run Each Command

### PART 1: On Your LOCAL Windows Machine (PowerShell)

Open **PowerShell** on your Windows computer (where your project files are).

#### Step 1: Upload the deployment script to VM

```powershell
# Replace 'vm-name' with your actual VM name
# Replace 'us-central1-a' with your VM's zone if different
gcloud compute scp deploy-on-vm.sh vm-name:/tmp/ --zone=us-central1-a
```

**Where to run:** PowerShell on your Windows machine  
**What it does:** Copies the deployment script to your VM

#### Step 2: Upload your application code to VM

```powershell
# Replace 'vm-name' with your actual VM name
gcloud compute scp --recurse . vm-name:/opt/travel-inbound --zone=us-central1-a
```

**Where to run:** PowerShell on your Windows machine  
**What it does:** Copies all your application files to `/opt/travel-inbound` on the VM

#### Step 3: Connect to your VM via SSH

```powershell
# Replace 'vm-name' with your actual VM name
gcloud compute ssh vm-name --zone=us-central1-a
```

**Where to run:** PowerShell on your Windows machine  
**What it does:** Opens an SSH connection to your Ubuntu VM

**After this command, you'll be INSIDE the VM!**

---

### PART 2: On Your REMOTE Ubuntu VM (Bash Terminal)

After Step 3 above, you'll be connected to your VM. The prompt will change to show you're on the VM.

#### Step 4: Run the deployment script

```bash
sudo bash /tmp/deploy-on-vm.sh
```

**Where to run:** Inside the VM (after SSH connection)  
**What it does:** Installs everything and deploys your application

---

## Complete Example Workflow

### On Your Windows Machine (PowerShell):

```powershell
# Navigate to your project directory
cd C:\Users\eyad\Desktop\TravelInbound7050126

# Step 1: Upload deployment script
gcloud compute scp deploy-on-vm.sh my-ubuntu-vm:/tmp/ --zone=us-central1-a

# Step 2: Upload application code
gcloud compute scp --recurse . my-ubuntu-vm:/opt/travel-inbound --zone=us-central1-a

# Step 3: Connect to VM
gcloud compute ssh my-ubuntu-vm --zone=us-central1-a
```

### After SSH Connection (Now Inside Ubuntu VM):

```bash
# Step 4: Run deployment script
sudo bash /tmp/deploy-on-vm.sh
```

---

## How to Know Where You Are

### On Windows (PowerShell):
- Prompt looks like: `PS C:\Users\eyad\Desktop\TravelInbound7050126>`
- You can run: `gcloud`, `docker`, Windows commands

### On Ubuntu VM (Bash):
- Prompt looks like: `username@vm-name:~$` or `username@vm-name:/opt/travel-inbound$`
- You can run: `sudo`, `apt-get`, Linux commands
- You'll see Linux-style paths like `/opt/travel-inbound`

---

## Finding Your VM Name and Zone

If you don't know your VM name and zone:

```powershell
# List all VMs
gcloud compute instances list

# This will show:
# NAME          ZONE           MACHINE_TYPE  STATUS
# my-vm-name    us-central1-a   e2-medium     RUNNING
```

Use the **NAME** and **ZONE** from the output.

---

## Quick Reference

| Command | Where to Run | Purpose |
|---------|--------------|---------|
| `gcloud compute scp ...` | Windows PowerShell | Upload files to VM |
| `gcloud compute ssh ...` | Windows PowerShell | Connect to VM |
| `sudo bash /tmp/deploy-on-vm.sh` | Ubuntu VM (after SSH) | Deploy application |

---

## Troubleshooting

### "Command not found: gcloud"
- You're on Windows but gcloud is not installed or not in PATH
- Install Google Cloud SDK

### "Permission denied" when uploading
- Make sure you're logged in: `gcloud auth login`
- Check VM exists: `gcloud compute instances list`

### "sudo: command not found" 
- You're still on Windows, not inside the VM
- Make sure you ran `gcloud compute ssh` first

### "No such file or directory" on VM
- You haven't uploaded the files yet
- Run the `gcloud compute scp` commands first

---

## Summary

1. **Commands 1-3** → Run on **Windows PowerShell** (your local machine)
2. **Command 4** → Run on **Ubuntu VM** (after SSH connection)

The key is: `gcloud compute ssh` switches you from Windows to Ubuntu VM!
