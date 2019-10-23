#!/bin/sh
# Uninstaller for removing previous installations of Apple Service Toolkit (not for uninstalling this server)

# Unload LaunchDaemons
launchctl unload /Library/LaunchDaemons/com.apple.gw_controld.plist
launchctl unload /Library/LaunchDaemons/com.apple.gw_datad.plist
launchctl unload /Library/LaunchDaemons/com.apple.gw_logd.plist

# Remove Keychain Items
rm /Library/Keychains/AppleServiceToolkit.keychain

# Remove Launch Daemons
rm /Library/LaunchDaemons/com.apple.gw_controld.plist
rm /Library/LaunchDaemons/com.apple.gw_datad.plist
rm /Library/LaunchDaemons/com.apple.gw_logd.plist

# Remove Preferences
rm /Library/Preferences/com.apple.gateway.plist
rm ~/Library/Preferences/com.apple.GatewayManager.plist

# Remove command line utilities
rm /usr/local/libexec/gw_controld
rm /usr/local/libexec/gw_datad
rm /usr/local/libexec/gw_logd

# Remove man8
rm -rf /share/man/man8/gw_controld.8
rm -rf /share/man/man8/gw_datad.8
rm -rf /share/man/man8/gw_logd.8

# Remove SysLog Config
rm -rf /private/etc/newsyslog.d/gateway.conf

# Remove Diagnostics Gateway & support files
rm -rf /Applications/Gateway\ Manager.app
rm -rf /private/var/adg

# Remove Netboot Sets
#rm -rf /Library/NetBoot/NetBootSP0/AppleServiceToolkit.nbi
#rm -rf /Library/NetBoot/NetBootSP0/AppleDiagnosticOSs
#rm -rf /Library/NetBoot/NetBootSP0/AppleDiagnosticOS
#rm -rf /Library/NetBoot/NetBootSP0/AST64bit.nbi
#rm -rf /Library/NetBoot/NetBootSP0/ASTLegacy.nbi
#rm -rf /Library/NetBoot/NetBootSP0/Diagnostics.nbi
#rm -rf /Library/NetBoot/NetBootSP0/i386
#rm -rf /Library/NetBoot/NetBootSP0/TAOS_*

# Remove receipts
#rm /Library/Receipts/apple.com.astos*

# Remove log files
rm -rf /private/var/log/adg

exit 0
