
clear

echo "Re-directing into MiddleMan/..." >&2 # stderr
[ ! -d "MiddleMan" ] && { echo "MiddleMan/ directory does not exist." >&2; exit 1; }
cd MiddleMan/

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

