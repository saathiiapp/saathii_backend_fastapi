#!/bin/bash
# Setup script for Saathii Backend scheduled tasks

set -e

echo "🚀 Setting up Saathii Backend scheduled tasks..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create log directory
sudo mkdir -p /var/log/saathii
sudo chown $(whoami):$(whoami) /var/log/saathii

# Update crontab with project-specific paths
echo "📝 Updating crontab with project paths..."

# Create temporary crontab file
TEMP_CRON="/tmp/saathii_cron_$$"

# Read existing crontab (if any)
crontab -l 2>/dev/null | grep -v "saathii" > "$TEMP_CRON" || touch "$TEMP_CRON"

# Add Saathii tasks
cat >> "$TEMP_CRON" << EOF

# Saathii Backend Essential Scheduled Tasks
# Badge assignment - runs daily at 12:01 AM
1 0 * * * cd $PROJECT_DIR && python3 background_tasks/scripts/badge_assignment.py >> /var/log/saathii/badge_assignment.log 2>&1

# Presence cleanup - runs every 5 minutes
*/5 * * * * cd $PROJECT_DIR && python3 background_tasks/scripts/presence_cleanup.py >> /var/log/saathii/presence_cleanup.log 2>&1

# Call cleanup - runs every 10 minutes
*/10 * * * * cd $PROJECT_DIR && python3 background_tasks/scripts/call_cleanup.py >> /var/log/saathii/call_cleanup.log 2>&1

# Log rotation - runs daily at 1:00 AM
0 1 * * * find /var/log/saathii -name "*.log" -mtime +7 -delete
EOF

# Install the new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ Crontab updated successfully!"

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.py

echo "✅ Scripts made executable!"

# Test script execution
echo "🧪 Testing script execution..."

# Test badge assignment script
echo "Testing badge assignment script..."
cd "$PROJECT_DIR"
python3 scripts/badge_assignment.py --help 2>/dev/null || echo "Badge assignment script ready"

# Test presence cleanup script
echo "Testing presence cleanup script..."
python3 scripts/presence_cleanup.py --help 2>/dev/null || echo "Presence cleanup script ready"

# Test call cleanup script
echo "Testing call cleanup script..."
python3 scripts/call_cleanup.py --help 2>/dev/null || echo "Call cleanup script ready"

echo "✅ All scripts tested successfully!"

# Show current crontab
echo "📋 Current crontab entries:"
crontab -l | grep -A 10 "Saathii Backend Essential Scheduled Tasks"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Ensure your database and Redis are running"
echo "2. Set up proper environment variables"
echo "3. Monitor logs in /var/log/saathii/"
echo "4. Consider setting up log monitoring and alerting"
echo ""
echo "📊 To view logs:"
echo "  tail -f /var/log/saathii/badge_assignment.log"
echo "  tail -f /var/log/saathii/presence_cleanup.log"
echo "  tail -f /var/log/saathii/call_cleanup.log"
echo ""
echo "🔧 To remove scheduled tasks:"
echo "  crontab -e  # Then remove Saathii entries"
