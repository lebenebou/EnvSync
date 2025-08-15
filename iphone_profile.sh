
clear
alias cdmiddleman='cd /root/MiddleMan/'
alias sync='cdmiddleman && git fetch origin && git reset --hard origin/main'

echo "Re-directing into MiddleMan/ directory..." >&2 # stderr
[ ! -d "/root/MiddleMan/" ] && { echo "/root/MiddleMan/ directory does not exist." >&2; return; }
cdmiddleman

echo "Syncing to repo..." >&2 # stderr
sync

echo "Updating /root/.profile ..." >&2 # stderr
[ ! -f "/root/MiddleMan/iphone_profile.sh" ] && { echo "iphone_profile.sh does not exist" >&2; return; }
cp /root/MiddleMan/iphone_profile.sh /root/.profile

echo "" >&2 # stderr
echo "ALL SET" >&2 # stderr
echo "WELCOME, Youssef" >&2 # stderr

alias ll='ls -l'
alias back='cd .. && ls'
alias cls='clear'
alias gs='git status'
alias reload='source /root/.profile'

send() {
	sync
	cdmiddleman

	line="$*" # Concatenate all parameters into a single string
	echo "$line" >> middle_man.md

	git add /root/MiddleMan/middle_man.md
	git commit -m "$(date '+%b %d %Y, %-I:%M %p')"
	git push origin main
}
