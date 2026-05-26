FROM kalilinux/kali-rolling:latest
RUN apt-get update && apt-get install -y --no-install-recommends \
    nikto sqlmap gobuster ffuf hydra whois curl wget dnsutils nmap \
    python3 python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /work
