
clear
alias cdmiddleman='cd /root/MiddleMan/'

echo "Re-directing into MiddleMan/..." >&2 # stderr
[ ! -d "/root/MiddleMan/" ] && { echo "/root/MiddleMan/ directory does not exist." >&2; exit 1; }
cd cdmiddleman

echo "Pulling from git..." >&2 # stderr
git pull origin main 2>/dev/null
git reset --hard origin/main > /dev/null 2>&1

echo "Updating /root/.profile ..." >&2 # stderr
[ ! -f "iphone_profile.sh" ] && { echo "iphone_profile.sh does not exist" >&2; exit 1; }
cat /root/MiddleMan/iphone_profile.sh > /root/.profile

echo "ALL SET" >&2 # stderr
echo "WELCOME, Youssef" >&2 # stderr

alias ll='ls -l'
alias back='cd .. && ls'
alias cls='clear'
alias reload='source /root/.profile'

send() {
	line="$*" # Concatenate all parameters into a single string

	echo "$line" >> /root/MiddleMan/middle_man.md

	cdmiddleman
	git add /root/MiddleMan/middle_man.md
	git commit -m "$(date +%d-%m-%y)"
	git push origin main
}
