# Nginx installation
sudo apt update
sudo apt install -y nginx

# Check installation
sudo systemctl enable --now nginx
sudo systemctl status nginx

# Creates virtual host
sudo nano /etc/nginx/sites-available/idp.abaqua.cat
# Copy to /etc/nginx/sites-available/idp.abaqua.cat contents of idp.abaqua.cat

# Enable the site
sudo ln -s /etc/nginx/sites-available/idp.abaqua.cat \
    /etc/nginx/sites-enabled/idp.abaqua.cat

# Deletes default nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Test syntax and reload nginx
sudo nginx -t
sudo systemctl reload nginx

# Test connectivity with web server
curl -I http://192.168.11.23
curl -I \
    -H 'Host: idp.abaqua.cat' \
    http://192.168.11.23

# Creates appropiate DNS records
idp.abaqua.cat  A  <IP pública de espmisroweb01>
# and test it
dig +short idp.abaqua.cat

# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Install certificate
sudo certbot --nginx -d idp.abaqua.cat

# Reboot nginx
sudo nginx -t
sudo systemctl reload nginx

# Test overall system
curl -I https://idp.abaqua.cat

# Test automatic renovation
sudo certbot renew --dry-run
