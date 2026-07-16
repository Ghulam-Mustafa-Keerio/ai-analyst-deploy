import codecs
for enc in ("utf-16", "utf-16-le", "utf-8"):
    try:
        with codecs.open("test_run.log", "r", encoding=enc) as f:
            data = f.read()
        with open("test_run_clean.txt", "w", encoding="utf-8") as out:
            out.write(data)
        print("decoded with", enc)
        break
    except Exception as e:
        print("fail", enc, e)
