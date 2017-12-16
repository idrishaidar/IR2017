Biar nyoba2nya gampang, di-clone ke root disk C

run via cmd 
create index dari collection (koleksi yang dipake: korpusA.txt)
C:\Python34\python.exe C:\Python34\createIndex.py C:\Python34\stopwords_indo.txt C:\Python34\korpusA.txt C:\Python34\testIndex.dat C:\Python34\titleIndex.txt

tes query (masukin input query nanti outputnya id dokumen yang mengandung kata tersebut berdasarkan index yang udah dibuat)
C:\Python34\python.exe C:\Python34\queryIndex.py C:\Python34\stopwords_indo.txt C:\Python34\testIndex.dat C:\Python34\titleIndex.txt