import os
import glob
import csv
import re

# 引数に取ったpathにあるディレクトのリストを返す関数
# ただし.cのファイルが含まれないディレクトリは除く
def dirlist(path = "."):
    files = os.listdir(path)
    alldir_list = [f for f in files if os.path.isdir(os.path.join(path, f))]

    dir_list = [dir_check for dir_check in alldir_list if len(glob.glob(os.path.join(path, dir_check, "*.c"))) != 0]
  
    dir_list.sort()

    return dir_list

# dir_listのディレクトリの名前を先頭7文字だけに変更し
# 変更後のディレクトリのリストを返す関数
def renamedir(path, dir_list):
    renamed_dir_list = []
    for dir in dir_list:
        dir_path = os.path.join(path, dir)
        renamed_dir_list.append(dir[0:7])
        os.rename(dir_path, dir[0:7])
    return renamed_dir_list

# 引数に取った文字列からコメント行やスペース、改行を除去したものを返す関数
def removestr(str):
    # コメント行の除去
    comment = r"//.*?\n|/\*.*?\*/"
    for commstr in re.findall(comment, str):
        str = str.replace(commstr, "")

    str = str.replace(" ", "")
    str = str.replace("\n", "")
  
    # 対象の文字列の大文字を全て小文字に変換する
    # コード内容の完全一致を確かめる場合はコメントアウト推奨
    str = str.lower()

    return str

# 総当たりでソースコードを比較するための関数
# 比較結果をcsvファイルで出力する
# 戻り値は比較結果の二次元配列
def souatari(path, dir_list, ofile_name = "souatari.csv"):
    outlist = [["" for i in range(len(dir_list) + 1)]for j in range(len(dir_list) + 2)]

    j = 1
    for refdir in dir_list:
        outlist[0][j] = refdir

        # 参照用ソースコードの読み込み
        reffile_path = glob.glob(os.path.join(path, refdir, "*.c"))
        print("reference : " + refdir)    # 停止時の原因確認のためコメントアウト非推奨
        with open(reffile_path[0], "r") as reffile:
            refcode = reffile.read()

        refcode = removestr(refcode)

        count = 0
        i = 1
        for targetdir in dir_list:
            outlist[i][0] = targetdir

            # 比較対象のソースコードの読み込み
            targetfile_path = glob.glob(os.path.join(path, targetdir, "*.c"))
            print("target : " + targetdir)    # 停止時の原因確認のためコメントアウト非推奨
            with open(targetfile_path[0], "r") as targetfile:
                targetcode = targetfile.read()

            targetcode = removestr(targetcode)

            # 一致不一致を確かめ、outlistに結果を書き込む
            if targetcode == refcode:
                outlist[i][j] = "〇"
                count += 1
            else:
                outlist[i][j] = "×"

            i += 1
        outlist[i][j] = str(count)
        j += 1

    # 比較結果の出力
    with open(ofile_name, "w") as outf:
        writer = csv.writer(outf, lineterminator = "\n")
        writer.writerows(outlist)

    return outlist

# dir_listにある.cのファイルをコンパイル、実行する
# 第三引数にファイル名を指定するとコンパイル、実行を行わずバッチファイルを生成する
def compilerun(path, dir_list, batmakemode = "No"):
    if batmakemode != "No":
        outfile = open(batmakemode, "w")

    for refdir in dir_list:
        reffile_path = glob.glob(os.path.join(path, refdir, "*.c"))
        basefile_path = os.path.splitext(reffile_path[0])
        exefilename = basefile_path[0] + ".exe"
        txtfilename = basefile_path[0] + ".txt"
        print(reffile_path[0])

        if batmakemode == "No":
            os.system("gcc " + reffile_path[0] + " -o " + exefilename + "\n")
            os.system(exefilename + " > " + txtfilename + "\n")
        else:
            outfile.write("gcc " + reffile_path[0] + " -o " + exefilename + "\n")
            outfile.write(exefilename + " > " + txtfilename + "\n")

    if batmakemode != "No":
        outfile.close()

# リファレンスファイルと出力した実行結果を比較する関数
# 比較結果をcsvファイルで出力する
# 戻り値は比較結果の二次元配列
def comparetxt(path, dir_list, ref, ofile_name = "result.csv"):
    # リファレンスファイルの読み込み
    with open(os.path.join(path, ref), "r") as reftxt:
        refstr = reftxt.read()

    # 比較結果用の2次元配列の宣言と見出し行の作成
    outlist = [["" for i in range(4)]for j in range(len(dir_list) + 1)]
    outlist[0][0] = "number"
    outlist[0][1] = "refとの一致"
    outlist[0][2] = refstr
    outlist[0][3] = "出力結果がソースコードに含まれているか"

    refstr = removestr(refstr)

    i = 1
    for targetdir in dir_list:
        outlist[i][0] = targetdir
    
        # 対象のディレクトリにtxtファイルが存在しない場合の処理
        targetfile_path = glob.glob(os.path.join(path, targetdir, "*.txt"))
        if len(targetfile_path) == 0:
            outlist[i][1] = "Not exist"
            i += 1
            continue

        # 停止した際にどのファイルが原因か調べるため出力
        print(targetdir[0:7])

        # 比較対象のファイルの読み込み
        with open(targetfile_path[0], "r") as targetfile:
            targetstr = targetfile.read()

        outlist[i][2] = targetstr

        # 出力結果を直接printfしていないかチェックするためソースコードを読み込む
        scode_path = glob.glob(os.path.join(path, targetdir, "*.c"))
        with open(scode_path[0], "r") as scodefile:
            scodestr = scodefile.read()

        targetstr = removestr(targetstr)
        scodestr = removestr(scodestr)

        # refとの比較、またソースコードとの比較
        if targetstr == refstr:
            outlist[i][1] = "〇"
        else:
            outlist[i][1] = "×"
        if targetstr in scodestr:
            outlist[i][3] = "含まれている"

        i += 1

    # 比較結果の出力
    with open(ofile_name, "w") as outf:
        writer = csv.writer(outf, lineterminator = "\n")
        writer.writerows(outlist)

    return outlist

path = "."
dir_list = dirlist(path)
dir_list = renamedir(path, dir_list)
souatari(path, dir_list)
compilerun(path, dir_list)
comparetxt(path, dir_list, "reference.txt")
