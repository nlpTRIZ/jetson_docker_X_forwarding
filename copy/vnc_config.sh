mkdir -p ~/.config/autostart
cp /usr/share/applications/vino-server.desktop ~/.config/autostart
gsettings set org.gnome.Vino prompt-enabled false
gsettings set org.gnome.Vino require-encryption false
gsettings set org.gnome.Vino authentication-methods "['vnc']"
gsettings set org.gnome.Vino vnc-password $(echo -n 'jetson0insa'|base64)
sudo cp copy/vnc/xorg.conf /etc/X11/xorg.conf
sudo cp copy/vnc/custom.conf /etc/gdm3/custom.conf
