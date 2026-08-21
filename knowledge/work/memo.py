import json,re,sys,glob,os
p=sys.argv[1]
d=json.load(open(p)); c=d['fileContent']
m=re.search(r'\n#\s*\S*\s*\**文字起こし', c)
memo=c[:m.start()] if m else c
memo=re.sub(r'\s*\(\[\d\d:\d\d:\d\d\]\([^)]*\)\)','',memo)
memo=re.sub(r'\[([^\]]*)\]\((https?|\?)[^)]*\)',r'\1',memo)
print(memo)
