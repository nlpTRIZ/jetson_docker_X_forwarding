sudo cp copy/drun.sh /usr/
source ~/.bashrc
[[ $(type -t drun) == function ]] && return
echo "
if [[ -f /usr/drun.sh ]]; then
    source /usr/drun.sh
fi" >> ~/.bashrc
source ~/.bashrc
