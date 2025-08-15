
#!/bin/sh
clear

cdmiddleman() {
    cd /root/MiddleMan/ || {
        echo "/root/MiddleMan/ directory does not exist." >&2
        exit 1
    }
}

sync_repo() {
    cdmiddleman
    git fetch origin
    git reset --hard origin/main
}

echo "Re-directing into MiddleMan/ directory..." >&2
cdmiddleman

echo "Syncing to repo..." >&2
sync_repo

echo "Updating /root/.profile ..." >&2
if [ ! -f "/root/MiddleMan/iphone_profile.sh" ]; then
    echo "iphone_profile.sh does not exist" >&2
    exit 1
fi
cp /root/MiddleMan/iphone_profile.sh /root/.profile

echo "" >&2
echo "ALL SET" >&2
echo "WELCOME, Youssef" >&2

ll() { ls -l "$@"; }
back() { cd .. && ls; }
cls() { clear; }
gs() { git status; }
reload() { . /root/.profile; }

send() {
    sync_repo
    cdmiddleman

    timestamp="$(date +%s)"
    line="$timestamp $*"
    echo "$line" >> middle_man.md

    git add /root/MiddleMan/middle_man.md
    git commit -m "$(date '+%b %d %Y, %-I:%M %p')"
    git push origin main
}
