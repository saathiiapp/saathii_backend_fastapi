#!/usr/bin/env python3
"""
Security Check Script for Saathii Backend
Checks HTTPS status and security headers for all Saathii domains
"""

import requests
import ssl
import socket
from urllib.parse import urlparse
import json
from datetime import datetime

def check_https_status(url):
    """Check if a URL is properly secured with HTTPS"""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        return {
            'url': url,
            'status_code': response.status_code,
            'final_url': response.url,
            'is_https': response.url.startswith('https://'),
            'ssl_valid': True,
            'error': None
        }
    except requests.exceptions.SSLError as e:
        return {
            'url': url,
            'status_code': None,
            'final_url': None,
            'is_https': False,
            'ssl_valid': False,
            'error': f"SSL Error: {str(e)}"
        }
    except Exception as e:
        return {
            'url': url,
            'status_code': None,
            'final_url': None,
            'is_https': False,
            'ssl_valid': False,
            'error': f"Error: {str(e)}"
        }

def check_ssl_certificate(hostname, port=443):
    """Check SSL certificate details"""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                return {
                    'subject': dict(x[0] for x in cert['subject']),
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'version': cert['version'],
                    'serialNumber': cert['serialNumber'],
                    'notBefore': cert['notBefore'],
                    'notAfter': cert['notAfter'],
                    'valid': True
                }
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def check_security_headers(url):
    """Check security headers in response"""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        headers = response.headers
        
        security_headers = {
            'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
            'X-Frame-Options': headers.get('X-Frame-Options'),
            'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
            'X-XSS-Protection': headers.get('X-XSS-Protection'),
            'Content-Security-Policy': headers.get('Content-Security-Policy'),
            'Referrer-Policy': headers.get('Referrer-Policy'),
            'Permissions-Policy': headers.get('Permissions-Policy')
        }
        
        return {
            'url': url,
            'headers': security_headers,
            'has_hsts': 'Strict-Transport-Security' in headers,
            'has_csp': 'Content-Security-Policy' in headers
        }
    except Exception as e:
        return {'url': url, 'error': str(e)}

def main():
    """Main security check function"""
    print("🔒 Saathii Backend Security Check")
    print("=" * 50)
    
    # URLs to check
    urls = [
        "https://saathiiapp.com",
        "https://saathiiapp.com/redoc",
        "https://docs.saathiiapp.com",
        "https://docs.saathiiapp.com/docs/getting-started",
        "https://logs.saathiiapp.com"
    ]
    
    print(f"\n📅 Check performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🌐 Checking HTTPS Status...")
    print("-" * 30)
    
    for url in urls:
        result = check_https_status(url)
        status_icon = "✅" if result['is_https'] and result['ssl_valid'] else "❌"
        print(f"{status_icon} {url}")
        print(f"   Status: {result['status_code']}")
        print(f"   HTTPS: {result['is_https']}")
        print(f"   SSL Valid: {result['ssl_valid']}")
        if result['error']:
            print(f"   Error: {result['error']}")
        print()
    
    print("\n🔐 Checking SSL Certificates...")
    print("-" * 30)
    
    domains = ["saathiiapp.com", "docs.saathiiapp.com", "logs.saathiiapp.com"]
    for domain in domains:
        cert_info = check_ssl_certificate(domain)
        if cert_info['valid']:
            print(f"✅ {domain}")
            print(f"   Issuer: {cert_info['issuer'].get('organizationName', 'Unknown')}")
            print(f"   Valid Until: {cert_info['notAfter']}")
        else:
            print(f"❌ {domain}: {cert_info.get('error', 'Unknown error')}")
        print()
    
    print("\n🛡️ Checking Security Headers...")
    print("-" * 30)
    
    for url in urls:
        header_info = check_security_headers(url)
        if 'error' not in header_info:
            print(f"🔍 {url}")
            print(f"   HSTS: {'✅' if header_info['has_hsts'] else '❌'}")
            print(f"   CSP: {'✅' if header_info['has_csp'] else '❌'}")
            print(f"   X-Frame-Options: {'✅' if header_info['headers']['X-Frame-Options'] else '❌'}")
        else:
            print(f"❌ {url}: {header_info['error']}")
        print()

if __name__ == "__main__":
    main()
