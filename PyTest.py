def main() :
    total = input()
    ans = input()
    print(*findSol(total,ans))

def count(totalNum,ans) :
    times = 0
    for i in range(len(ans)) :
        if totalNum == ans[i] :
            times += 1
    return times

def findSol(total,ans) :
    fin = []
    for i in range(len(total)) :
        judge = True
        for j in range(len(ans)) :
            if (total[i] in ans and judge) :
                judge = False
                for l in range(count(total[i],ans)) :
                    fin.append(i)
    return fin

if __name__ == "__main__" :
    main()