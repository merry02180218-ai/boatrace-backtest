import urllib.request, re

URL='https://odds.kyotei24.jp/odds3t-omura-20260901-6.html'
req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0'})
with urllib.request.urlopen(req,timeout=30) as r:
    b=r.read().decode('utf-8','replace')
print('status ok len',len(b))
print('deadline label', '締切時オッズ' in b)
for pat in ['1-2-3','1-4-5','odds','trifecta','3連単','締切時オッズ']:
    print('\nPAT',pat)
    for m in list(re.finditer(re.escape(pat),b,re.I))[:5]:
        i=m.start(); print(b[max(0,i-500):i+1200])
# Print compact tag-stripped text prefix for structural inspection.
txt=re.sub(r'<script.*?</script>|<style.*?</style>',' ',b,flags=re.S|re.I)
txt=re.sub(r'<[^>]+>','\n',txt)
txt='\n'.join(x.strip() for x in txt.splitlines() if x.strip())
print('\nTEXT PREFIX\n',txt[:15000])
# retrigger after workflow creation
