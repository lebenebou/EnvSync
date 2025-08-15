
clear

echo "Re-directing into MiddleMan/..." >&2 # stderr
[ ! -d "MiddleMan" ] && { echo "MiddleMan/ directory does not exist." >&2; exit 1; }
cd MiddleMan/

echo "Pulling from git..." >&2 # stderr
git pull origin main
git reset --hard origin/main

echo "Updating /root/.profile ..." >&2 # stderr
[ ! -f "iphone_profile.sh" ] && { echo "iphone_profile.sh does not exist" >&2; exit 1; }
cat /root/MiddleMan/iphone_profile.sh > /root/.profile

echo "ALL SET" >&2 # stderr
echo "WELCOME, Youssef" >&2 # stderr

